import hashlib
import os
import random
import secrets
import time
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from postgrest.exceptions import APIError
from supabase import create_client, Client
from src.api.session_config import SESSION_TTL_SECONDS

# -----------------------------------------------------------------------------
# CAMADA DE DADOS
# -----------------------------------------------------------------------------
# Este módulo centraliza a comunicação com o Supabase.
# Ele é responsável por:
#   1. carregar as variáveis de ambiente;
#   2. criar a conexão com o banco;
#   3. executar operações de leitura e escrita em tabelas de turmas e usuários.
# -----------------------------------------------------------------------------

load_dotenv()

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA CONEXÃO
# -----------------------------------------------------------------------------
# O projeto espera que existam as variáveis no arquivo .env:
#   SUPABASE_URL
#   SUPABASE_PUBLISHABLE_KEY
# Isso permite manter a conexão segura e desacoplada do código.
# -----------------------------------------------------------------------------
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_PUBLISHABLE_KEY")

supabase: Client = create_client(url, key)


class SessionStorageNotConfigured(RuntimeError):
    """Raised when the backend-only Supabase key for sessions is missing."""


class UserAlreadyExistsError(ValueError):
    """Raised when a user identifier is already registered."""


class UserRegistrationError(RuntimeError):
    """Raised when a user or its class association could not be created."""





def create_session(user_id: str) -> str:
    """Persist a session token hash and return the original token to the caller."""
    session_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()

    supabase.table("sessions").insert(
        {
            "token": token_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "id_usuarios": user_id,
        }
    ).execute()

    return session_token


def get_session_user_id(session_token: str) -> str | None:
    """Return the user id for a valid, unexpired session token."""
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    result = (
        supabase.table("sessions")
        .select("id_usuarios,created_at")
        .eq("token", token_hash)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None

    session = result.data[0]
    created_at_value = session.get("created_at")
    if not isinstance(created_at_value, str):
        return None

    try:
        created_at = datetime.fromisoformat(created_at_value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if created_at > now or now - created_at > timedelta(seconds=SESSION_TTL_SECONDS):
        return None

    user_id = session.get("id_usuarios")
    return user_id if isinstance(user_id, str) and user_id else None


def revoke_session(session_token: str) -> None:
    """Delete the stored hash for a session token."""
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    supabase.table("sessions").delete().eq("token", token_hash).execute()


def get_user_profile(user_id: str) -> dict[str, str]:
    """Fetch the signed-in user's name and student enrollment details."""
    result = (
        supabase.table("usuarios")
        .select("id,nome,tipo")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise LookupError("usuário não encontrado")

    user = result.data[0]
    user_type = _normalize_user_type(user.get("tipo"))
    profile = {
        "id": user_id,
        "nome": user.get("nome") or "",
        "tipo": user_type,
        "turma": "",
        "pai": "",
    }

    if profile["tipo"] == "aluno":
        enrollment = (
            supabase.table("usuarios_dados_alunos")
            .select("id_turma,nome_responsavel")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if enrollment.data:
            profile["pai"] = enrollment.data[0].get("nome_responsavel") or ""
            class_id = enrollment.data[0].get("id_turma")
            if class_id:
                class_result = (
                    supabase.table("turmas")
                    .select("nome")
                    .eq("id", class_id)
                    .limit(1)
                    .execute()
                )
                if class_result.data:
                    profile["turma"] = class_result.data[0].get("nome") or ""

    return profile


def update_student_guardian_name(user_id: str, guardian_name: str) -> str:
    enrollment = (
        supabase.table("usuarios_dados_alunos")
        .select("id")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not enrollment.data:
        raise LookupError("vínculo de aluno não encontrado")

    result = (
        supabase.table("usuarios_dados_alunos")
        .update({"nome_responsavel": guardian_name})
        .eq("id", user_id)
        .select("nome_responsavel")
        .execute()
    )
    if not result.data:
        raise RuntimeError("Supabase não retornou o nome do responsável atualizado.")
    return result.data[0].get("nome_responsavel") or guardian_name


def list_users() -> list[dict[str, object]]:
    """List users and their class names without exposing birth dates."""
    users_result = (
        supabase.table("usuarios")
        .select("id,nome,tipo")
        .order("nome")
        .execute()
    )
    users = users_result.data
    if not users:
        return []

    user_ids = [str(user["id"]) for user in users if user.get("id") is not None]
    classes_by_user: dict[str, set[str]] = {}
    class_ids: set[str] = set()

    student_links = (
        supabase.table("usuarios_dados_alunos")
        .select("id,id_turma")
        .in_("id", user_ids)
        .execute()
    )
    teacher_links = (
        supabase.table("turmas_professores")
        .select("id_professor,id_turma")
        .in_("id_professor", user_ids)
        .execute()
    )

    for link, user_key in (
        *((row, "id") for row in student_links.data),
        *((row, "id_professor") for row in teacher_links.data),
    ):
        user_id = link.get(user_key)
        class_id = link.get("id_turma")
        if user_id is None or class_id is None:
            continue
        user_id_str = str(user_id)
        class_id_str = str(class_id)
        classes_by_user.setdefault(user_id_str, set()).add(class_id_str)
        class_ids.add(class_id_str)

    class_names: dict[str, str] = {}
    if class_ids:
        classes_result = (
            supabase.table("turmas")
            .select("id,nome")
            .in_("id", list(class_ids))
            .execute()
        )
        class_names = {
            str(row["id"]): row.get("nome") or ""
            for row in classes_result.data
            if row.get("id") is not None
        }

    return [
        {
            "id": str(user["id"]),
            "nome": user.get("nome") or "",
            "tipo": _normalize_user_type(user.get("tipo")),
            "id_turmas": sorted(
                classes_by_user.get(str(user.get("id")), set())
            ),
            "turmas": sorted(
                class_names[class_id]
                for class_id in classes_by_user.get(str(user.get("id")), set())
                if class_id in class_names
            ),
        }
        for user in users
        if user.get("id") is not None
    ]


def get_manager_count() -> int:
    result = supabase.table("usuarios").select("tipo").execute()
    return sum(
        _normalize_user_type(user.get("tipo")) == "gestao"
        for user in result.data
    )


def get_user_for_management(user_id: str) -> dict[str, object]:
    result = (
        supabase.table("usuarios")
        .select("id,nome,tipo,data_nascimento")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise LookupError("usuário não encontrado")

    user = result.data[0]
    user_type = _normalize_user_type(user.get("tipo"))
    if user_type == "aluno":
        links = (
            supabase.table("usuarios_dados_alunos")
            .select("id_turma")
            .eq("id", user_id)
            .execute()
        )
    elif user_type == "professor":
        links = (
            supabase.table("turmas_professores")
            .select("id_turma")
            .eq("id_professor", user_id)
            .execute()
        )
    else:
        links = None

    return {
        "id": str(user["id"]),
        "nome": user.get("nome") or "",
        "tipo": user_type,
        "date_of_birth": str(user.get("data_nascimento") or ""),
        "id_turmas": [
            str(row["id_turma"])
            for row in (links.data if links else [])
            if row.get("id_turma") is not None
        ],
    }


def get_user_class_ids(user_id: str) -> list[str]:
    """Return only the classes the signed-in user is allowed to access."""
    user_result = (
        supabase.table("usuarios")
        .select("tipo")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not user_result.data:
        raise LookupError("usuário não encontrado")

    user_type = _normalize_user_type(user_result.data[0].get("tipo"))
    if user_type == "aluno":
        result = (
            supabase.table("usuarios_dados_alunos")
            .select("id_turma")
            .eq("id", user_id)
            .execute()
        )
        return [
            str(row["id_turma"])
            for row in result.data
            if row.get("id_turma") is not None
        ]

    if user_type == "professor":
        result = (
            supabase.table("turmas_professores")
            .select("id_turma")
            .eq("id_professor", user_id)
            .execute()
        )
        return [
            str(row["id_turma"])
            for row in result.data
            if row.get("id_turma") is not None
        ]

    if user_type == "gestao":
        result = supabase.table("turmas").select("id").execute()
        return [str(row["id"]) for row in result.data if row.get("id") is not None]

    return []


def get_user_type(user_id: str) -> str:
    result = (
        supabase.table("usuarios")
        .select("tipo")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise LookupError("usuário não encontrado")
    return _normalize_user_type(result.data[0].get("tipo"))


def _normalize_user_type(user_type: object) -> str:
    normalized = user_type.strip().lower() if isinstance(user_type, str) else ""
    if normalized in {"gestor", "gestão"}:
        return "gestao"
    return normalized


def get_classes_for_user(user_id: str) -> list[dict[str, str]]:
    """Return class options limited to the user's authorized classes."""
    class_ids = get_user_class_ids(user_id)
    if not class_ids:
        return []

    result = (
        supabase.table("turmas")
        .select("id,nome")
        .in_("id", class_ids)
        .order("nome")
        .execute()
    )
    return [
        {"id": str(row["id"]), "nome": row.get("nome") or ""}
        for row in result.data
        if row.get("id") is not None
    ]


def get_communications_for_user(user_id: str) -> list[dict[str, object]]:
    """List communications linked to classes the user is authorized to access."""
    class_ids = get_user_class_ids(user_id)
    if not class_ids:
        return []

    links = (
        supabase.table("comunicated_turmas")
        .select("id_comunicado,id_turma")
        .in_("id_turma", class_ids)
        .execute()
    )
    classes_by_notice: dict[str, set[str]] = {}
    for link in links.data:
        notice_id = link.get("id_comunicado")
        class_id = link.get("id_turma")
        if notice_id is not None and class_id is not None:
            classes_by_notice.setdefault(str(notice_id), set()).add(str(class_id))

    if not classes_by_notice:
        return []

    notice_ids = list(classes_by_notice)
    result = (
        supabase.table("comunicated")
        .select("id,title,description,created_at")
        .in_("id", notice_ids)
        .order("created_at", desc=True)
        .execute()
    )
    return [
        {
            **notice,
            "id_turmas": sorted(classes_by_notice[str(notice["id"])]),
        }
        for notice in result.data
        if str(notice.get("id")) in classes_by_notice
    ]


def create_communication(
    title: str,
    description: str,
    class_ids: list[str],
) -> dict[str, object]:
    """Create one communication and link it to all selected classes."""
    result = (
        supabase.table("comunicated")
        .insert({"title": title, "description": description})
        .execute()
    )
    if not result.data:
        raise RuntimeError("Supabase não retornou o comunicado criado.")

    notice = result.data[0]
    notice_id = notice.get("id")
    if notice_id is None:
        raise RuntimeError("O comunicado criado não possui identificador.")

    supabase.table("comunicated_turmas").insert(
        [
            {"id_comunicado": notice_id, "id_turma": class_id}
            for class_id in class_ids
        ]
    ).execute()

    return {**notice, "id_turmas": class_ids}


def update_communication(
    communication_id: str,
    title: str,
    description: str,
    class_ids: list[str],
) -> dict[str, object]:
    existing = (
        supabase.table("comunicated")
        .select("id")
        .eq("id", communication_id)
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise LookupError("comunicado não encontrado")

    current_links = (
        supabase.table("comunicated_turmas")
        .select("id_turma")
        .eq("id_comunicado", communication_id)
        .execute()
    )
    current_class_ids = {
        str(row["id_turma"])
        for row in current_links.data
        if row.get("id_turma") is not None
    }
    new_class_ids = set(class_ids)
    class_ids_to_add = new_class_ids - current_class_ids
    class_ids_to_remove = current_class_ids - new_class_ids

    if class_ids_to_add:
        supabase.table("comunicated_turmas").insert(
            [
                {"id_comunicado": communication_id, "id_turma": class_id}
                for class_id in sorted(class_ids_to_add)
            ]
        ).execute()

    result = (
        supabase.table("comunicated")
        .update({"title": title, "description": description})
        .eq("id", communication_id)
        .select("id,title,description,created_at")
        .execute()
    )
    if not result.data:
        raise RuntimeError("Supabase não retornou o comunicado atualizado.")

    for class_id in class_ids_to_remove:
        supabase.table("comunicated_turmas").delete().eq(
            "id_comunicado", communication_id
        ).eq("id_turma", class_id).execute()

    return {**result.data[0], "id_turmas": class_ids}


def delete_communication(communication_id: str) -> None:
    existing = (
        supabase.table("comunicated")
        .select("id")
        .eq("id", communication_id)
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise LookupError("comunicado não encontrado")

    supabase.table("comunicated_turmas").delete().eq(
        "id_comunicado", communication_id
    ).execute()
    supabase.table("comunicated").delete().eq(
        "id", communication_id
    ).execute()


def get_events_for_user(user_id: str) -> list[dict[str, object]]:
    """List events linked to classes the signed-in user can access."""
    class_ids = get_user_class_ids(user_id)
    if not class_ids:
        return []

    links = (
        supabase.table("eventos_turmas")
        .select("id_eventos,id_turmas")
        .in_("id_turmas", class_ids)
        .execute()
    )
    classes_by_event: dict[str, set[str]] = {}
    for link in links.data:
        event_id = link.get("id_eventos")
        class_id = link.get("id_turmas")
        if event_id is not None and class_id is not None:
            classes_by_event.setdefault(str(event_id), set()).add(str(class_id))

    if not classes_by_event:
        return []

    linked_class_ids = {
        class_id
        for event_class_ids in classes_by_event.values()
        for class_id in event_class_ids
    }
    class_result = (
        supabase.table("turmas")
        .select("id,nome")
        .in_("id", list(linked_class_ids))
        .execute()
    )
    class_names = {
        str(row["id"]): row.get("nome") or ""
        for row in class_result.data
        if row.get("id") is not None
    }

    result = (
        supabase.table("eventos")
        .select("id,nome,data")
        .in_("id", list(classes_by_event))
        .order("data")
        .execute()
    )
    return [
        {
            **event,
            "id_turmas": sorted(classes_by_event[str(event["id"])]),
            "turmas": sorted(
                class_names[class_id]
                for class_id in classes_by_event[str(event["id"])]
                if class_id in class_names
            ),
        }
        for event in result.data
        if str(event.get("id")) in classes_by_event
    ]


def create_event(
    name: str,
    event_date: str,
    class_ids: list[str],
) -> dict[str, object]:
    """Create one event and link it to all selected classes."""
    result = (
        supabase.table("eventos")
        .insert({"nome": name, "data": event_date})
        .execute()
    )
    if not result.data:
        raise RuntimeError("Supabase não retornou o evento criado.")

    event = result.data[0]
    event_id = event.get("id")
    if event_id is None:
        raise RuntimeError("O evento criado não possui identificador.")

    supabase.table("eventos_turmas").insert(
        [
            {"id_eventos": event_id, "id_turmas": class_id}
            for class_id in class_ids
        ]
    ).execute()

    return {**event, "id_turmas": class_ids}


def delete_event(event_id: str) -> None:
    event = (
        supabase.table("eventos")
        .select("id")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not event.data:
        raise LookupError("evento não encontrado")

    supabase.table("eventos_turmas").delete().eq(
        "id_eventos", event_id
    ).execute()
    supabase.table("eventos").delete().eq("id", event_id).execute()


def list_teachers() -> list[dict[str, str]]:
    result = supabase.table("usuarios").select("id,nome,tipo").order("nome").execute()
    return [
        {"id": str(row["id"]), "nome": row.get("nome") or ""}
        for row in result.data
        if row.get("id") is not None
        and _normalize_user_type(row.get("tipo")) == "professor"
    ]


def get_activity(activity_id: str) -> dict[str, object]:
    result = (
        supabase.table("atividades")
        .select("id,created_at,nome,professor_id,descricao,data_limite,materia")
        .eq("id", activity_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise LookupError("atividade não encontrada")

    activity = result.data[0]
    links = (
        supabase.table("atividades_turmas")
        .select("turma_id")
        .eq("atividade_id", activity_id)
        .execute()
    )
    class_ids = sorted({
        str(row["turma_id"])
        for row in links.data
        if row.get("turma_id") is not None
    })
    return {**activity, "id_turmas": class_ids}


def get_activities_for_user(user_id: str) -> list[dict[str, object]]:
    user_type = get_user_type(user_id)
    class_ids = get_user_class_ids(user_id)
    if user_type == "professor":
        activity_result = (
            supabase.table("atividades")
            .select("id,created_at,nome,professor_id,descricao,data_limite,materia")
            .eq("professor_id", user_id)
            .order("data_limite")
            .execute()
        )
        activity_rows = activity_result.data
        if not activity_rows:
            return []

        links = (
            supabase.table("atividades_turmas")
            .select("atividade_id,turma_id")
            .in_("atividade_id", [str(row["id"]) for row in activity_rows])
            .execute()
        )
    else:
        if not class_ids:
            return []
        links = (
            supabase.table("atividades_turmas")
            .select("atividade_id,turma_id")
            .in_("turma_id", class_ids)
            .execute()
        )

    classes_by_activity: dict[str, set[str]] = {}
    for link in links.data:
        activity_id = link.get("atividade_id")
        class_id = link.get("turma_id")
        if activity_id is not None and class_id is not None:
            classes_by_activity.setdefault(str(activity_id), set()).add(str(class_id))
    if not classes_by_activity:
        return []

    if user_type != "professor":
        result = (
            supabase.table("atividades")
            .select("id,created_at,nome,professor_id,descricao,data_limite,materia")
            .in_("id", list(classes_by_activity))
            .order("data_limite")
            .execute()
        )
        activity_rows = result.data

    linked_class_ids = {
        class_id
        for activity_class_ids in classes_by_activity.values()
        for class_id in activity_class_ids
    }
    class_result = (
        supabase.table("turmas")
        .select("id,nome")
        .in_("id", list(linked_class_ids))
        .execute()
    )
    class_names = {
        str(row["id"]): row.get("nome") or ""
        for row in class_result.data
        if row.get("id") is not None
    }
    teacher_ids = list({
        str(row["professor_id"])
        for row in activity_rows
        if row.get("professor_id") is not None
    })
    teacher_names: dict[str, str] = {}
    if teacher_ids:
        teacher_result = (
            supabase.table("usuarios")
            .select("id,nome")
            .in_("id", teacher_ids)
            .execute()
        )
        teacher_names = {
            str(row["id"]): row.get("nome") or ""
            for row in teacher_result.data
            if row.get("id") is not None
        }

    activities: list[dict[str, object]] = []
    for activity in activity_rows:
        activity_id = str(activity.get("id"))
        if activity_id not in classes_by_activity:
            continue
        activity_class_ids = sorted(classes_by_activity[activity_id])
        activities.append({
            **activity,
            "id": activity_id,
            "professor_nome": teacher_names.get(str(activity.get("professor_id")), ""),
            "id_turmas": activity_class_ids,
            "turmas": [
                class_names[class_id]
                for class_id in activity_class_ids
                if class_id in class_names
            ],
        })
    return activities


def create_activity(
    name: str,
    description: str,
    subject: str,
    due_date: str,
    professor_id: str,
    class_ids: list[str],
) -> dict[str, object]:
    result = (
        supabase.table("atividades")
        .insert({
            "nome": name,
            "descricao": description,
            "materia": subject,
            "data_limite": due_date,
            "professor_id": professor_id,
        })
        .execute()
    )
    if not result.data:
        raise RuntimeError("Supabase não retornou a atividade criada.")

    activity = result.data[0]
    activity_id = activity.get("id")
    if activity_id is None:
        raise RuntimeError("A atividade criada não possui identificador.")
    supabase.table("atividades_turmas").insert(
        [
            {"atividade_id": activity_id, "turma_id": class_id}
            for class_id in class_ids
        ]
    ).execute()
    return {**activity, "id_turmas": class_ids}


def update_activity(
    activity_id: str,
    name: str,
    description: str,
    subject: str,
    due_date: str,
    professor_id: str,
    class_ids: list[str],
) -> dict[str, object]:
    result = (
        supabase.table("atividades")
        .update({
            "nome": name,
            "descricao": description,
            "materia": subject,
            "data_limite": due_date,
            "professor_id": professor_id,
        })
        .eq("id", activity_id)
        .execute()
    )
    if not result.data:
        raise LookupError("atividade não encontrada")

    supabase.table("atividades_turmas").delete().eq(
        "atividade_id", activity_id
    ).execute()
    supabase.table("atividades_turmas").insert(
        [
            {"atividade_id": activity_id, "turma_id": class_id}
            for class_id in class_ids
        ]
    ).execute()
    return {**result.data[0], "id_turmas": class_ids}


def delete_activity(activity_id: str) -> None:
    if not get_activity(activity_id):
        raise LookupError("atividade não encontrada")
    supabase.table("atividades_turmas").delete().eq(
        "atividade_id", activity_id
    ).execute()
    supabase.table("atividades").delete().eq("id", activity_id).execute()


# -----------------------------------------------------------------------------
# BLOCO DE FUNÇÕES ANTIGAS / REFERÊNCIA
# -----------------------------------------------------------------------------
# Os trechos abaixo foram mantidos apenas como referência histórica do projeto.
# Eles mostram exemplos de inserção/consulta de dados em uma tabela anterior
# chamada 'lancamentos'.
# Caso estas funções sejam reaproveitadas, deve-se adaptar a estrutura real das
# tabelas do Supabase atual.
# -----------------------------------------------------------------------------
# #inserindo dados iniciais no banco de dados 
# def insert_data_random():
#     data = {"client_supplier": "John Doe", "value": 30, "date": "2024-06-01", "operation": "compra", "description": "Compra de materiais de escritório"}
#     for i in range(50):
#         data["value"] = random.randint(10, 1000)
#         data["date"] = f"2024-06-{random.randint(1,30):02d}"
#         data["description"] = f"Compra de materiais de escritório {i}"
#         data["operation"] = "compra" if i % 2 == 0 else "venda"
#         data["client_supplier"] = random.choice(["John Doe", "Jane Smith", "Acme Corp", "Globex Inc"])
        
#         try:
#             test = supabase.table("lancamentos").insert(data).execute()
#             print("Conexão bem-sucedida!", test.data)
#         except Exception as e:
#             print("Erro ao conectar ao Supabase:", e)

# def insert_data(client_supplier: str, valor: str, date: str, description: str, operation: str):
#     data = {"client_supplier": client_supplier, "value": valor, "date": date, "operation": operation , "description": description}
        
#     try:
#         test = supabase.table("lancamentos").insert(data).execute()
#         print("Conexão bem-sucedida!", test.data)
#     except Exception as e:
#         print("Erro ao conectar ao Supabase:", e)

# -----------------------------------------------------------------------------
# CONSULTA GERAL
# -----------------------------------------------------------------------------
# Esta função busca todos os registros da tabela 'turmas'.
# É útil para testes iniciais e validação da conexão com o banco.
# -----------------------------------------------------------------------------
def select_data():
    try:
        test2 = supabase.table("turmas").select("*").execute()
        print(test2)
        return test2.data  
        
    except Exception as e:
        return "Erro ao conectar ao Supabase:", e
    

# Chamada inicial para verificar a conexão ao importar o módulo.
# Mantida apenas para facilitar testes localizados durante a construção do backend.

# -----------------------------------------------------------------------------
# GERENCIAMENTO DE TURMAS
# -----------------------------------------------------------------------------
# A partir deste ponto, todas as funções estão relacionadas ao cadastro,
# atualização e exclusão de turmas no banco.
# -----------------------------------------------------------------------------

def criar_sala(nome: str, turno: str):
    data = {"nome": nome, "turno": turno}
    result = supabase.table("turmas").insert(data).execute()
    if not result.data:
        raise RuntimeError("Supabase não retornou a turma criada.")
    row = result.data[0]
    if row.get("id") is None:
        raise RuntimeError("Supabase não retornou o identificador da turma criada.")
    return {
        "id": str(row["id"]),
        "nome": row.get("nome") or nome,
        "turno": row.get("turno") or turno,
    }


def listar_turmas() -> list[dict[str, object]]:
    result = (
        supabase.table("turmas")
        .select("id,nome,turno")
        .order("nome")
        .execute()
    )
    return [
        {
            "id": str(row["id"]),
            "nome": row.get("nome") or "",
            "turno": row.get("turno") or "",
        }
        for row in result.data
        if row.get("id") is not None
    ]


def editar_sala(id: str, nome: str, turno: str) -> dict[str, object]:
    existing = (
        supabase.table("turmas")
        .select("id")
        .eq("id", id)
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise LookupError("turma não encontrada")

    data = {"nome": nome, "turno": turno}
    result = (
        supabase.table("turmas")
        .update(data)
        .eq("id", id)
        .select("id,nome,turno")
        .execute()
    )
    if not result.data:
        raise RuntimeError("Supabase não retornou a turma atualizada.")
    row = result.data[0]
    return {
        "id": str(row.get("id") or id),
        "nome": row.get("nome") or nome,
        "turno": row.get("turno") or turno,
    }


def deletar_sala(id: str) -> None:
    existing = (
        supabase.table("turmas")
        .select("id")
        .eq("id", id)
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise LookupError("turma não encontrada")

    references = (
        ("usuarios_dados_alunos", "id_turma"),
        ("turmas_professores", "id_turma"),
        ("comunicated_turmas", "id_turma"),
        ("eventos_turmas", "id_turmas"),
        ("atividades_turmas", "turma_id"),
    )
    for table, class_column in references:
        result = (
            supabase.table(table)
            .select(class_column)
            .eq(class_column, id)
            .limit(1)
            .execute()
        )
        if result.data:
            raise ValueError(
                "A turma possui alunos, professores, comunicados, eventos ou "
                "atividades vinculados. Remova os vínculos antes de excluí-la."
            )

    supabase.table("turmas").delete().eq("id", id).execute()

# -----------------------------------------------------------------------------
# GERENCIAMENTO DE USUÁRIOS
# -----------------------------------------------------------------------------
# As funções abaixo tratam da criação e atualização dos usuários do sistema,
# incluindo o relacionamento entre alunos/professores e turmas.
# -----------------------------------------------------------------------------

def criar_dados_alunos(id: str, id_turma: str):
    # Guarda o relacionamento de um aluno com a turma em que está matriculado.
    data = {"id": id, "id_turma": id_turma}
    return supabase.table("usuarios_dados_alunos").insert(data).execute().data


def create_user(
    id: str,
    type: str,
    name: str,
    date_of_birth: str,
    id_turma: str | None = None,
):
    # Cria um usuário genérico com base no tipo informado.
    # Para alunos: salva na tabela 'usuarios' e também no relacionamento 'usuarios_dados_alunos'.
    # Para professores: salva na tabela 'usuarios' e liga o professor à turma.
    user_type = _normalize_user_type(type)
    if user_type not in {"aluno", "professor", "gestao"}:
        raise ValueError("Tipo de usuário inválido.")
    class_id = id_turma or ""
    if user_type in {"aluno", "professor"} and not class_id:
        raise ValueError("Aluno e professor precisam estar vinculados a uma turma.")

    data = {
        "id": id,
        "tipo": "gestor" if user_type == "gestao" else user_type,
        "nome": name,
        "data_nascimento": date_of_birth,
    }
    existing = (
        supabase.table("usuarios")
        .select("id")
        .eq("id", id)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise UserAlreadyExistsError("Já existe um usuário com esse identificador.")

    try:
        result = supabase.table("usuarios").insert(data).execute()
    except APIError as error:
        if error.code == "23505" and (
            "usuarios_pkey" in (error.details or "")
            or "Key (id)=" in (error.details or "")
        ):
            raise UserAlreadyExistsError(
                "Já existe um usuário com esse identificador."
            ) from error
        raise

    if not result.data:
        raise UserRegistrationError("Supabase não retornou o usuário criado.")

    try:
        if user_type == "aluno":
            criar_dados_alunos(id=id, id_turma=class_id)
        elif user_type == "professor":
            criar_dados_professores(id_turma=class_id, id_professor=id)
    except APIError as error:
        try:
            supabase.table("usuarios").delete().eq("id", id).execute()
        except APIError as rollback_error:
            raise UserRegistrationError(
                "Falha ao criar o vínculo com a turma e ao desfazer o cadastro "
                "do usuário. Verifique a tabela usuarios antes de tentar novamente."
            ) from rollback_error
        raise UserRegistrationError(
            "Não foi possível vincular o usuário à turma. O cadastro foi desfeito."
        ) from error

    return result.data[0]


def update_user(
    user_id: str,
    user_type: str,
    name: str,
    date_of_birth: str,
    class_ids: list[str],
) -> dict[str, object]:
    current = (
        supabase.table("usuarios")
        .select("id")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not current.data:
        raise LookupError("usuário não encontrado")

    result = (
        supabase.table("usuarios")
        .update({
            "nome": name,
            "tipo": "gestor" if user_type == "gestao" else user_type,
            "data_nascimento": date_of_birth,
        })
        .eq("id", user_id)
        .execute()
    )

    supabase.table("usuarios_dados_alunos").delete().eq("id", user_id).execute()
    supabase.table("turmas_professores").delete().eq(
        "id_professor", user_id
    ).execute()

    if user_type == "aluno":
        criar_dados_alunos(id=user_id, id_turma=class_ids[0])
    elif user_type == "professor":
        supabase.table("turmas_professores").insert(
            [
                {"id_professor": user_id, "id_turma": class_id}
                for class_id in class_ids
            ]
        ).execute()

    if not result.data:
        return {
            "id": user_id,
            "nome": name,
            "tipo": user_type,
            "date_of_birth": date_of_birth,
            "id_turmas": class_ids,
        }
    return result.data[0]


def delete_user(user_id: str) -> None:
    current = (
        supabase.table("usuarios")
        .select("id")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not current.data:
        raise LookupError("usuário não encontrado")

    supabase.table("sessions").delete().eq("id_usuarios", user_id).execute()
    supabase.table("usuarios_dados_alunos").delete().eq("id", user_id).execute()
    supabase.table("turmas_professores").delete().eq(
        "id_professor", user_id
    ).execute()
    supabase.table("usuarios").delete().eq("id", user_id).execute()

def criar_dados_professores(id_turma: str, id_professor: str):
    # Cria a associação entre professor e turma.
    data = {"id_turma": id_turma, "id_professor": id_professor}
    return supabase.table("turmas_professores").insert(data).execute().data

def consultar_user_login(id:str):
    result = supabase.table("usuarios").select("*").eq("id", id).execute()
    if not result.data:
        raise LookupError("usuário não encontrado")

    return result.data[0]["data_nascimento"]
    
