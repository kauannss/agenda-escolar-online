import hashlib
import os
import random
import secrets
import time
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
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
    """Fetch the signed-in user's name and, for students, their class."""
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
            .select("id_turma")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if enrollment.data:
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
    # Cria uma nova turma com nome e turno.
    data = {"nome": nome, "turno": turno}
    try:
        test = supabase.table("turmas").insert(data).execute()
        print("Conexão bem-sucedida!", test.data)
    except Exception as e:
        print("Erro ao conectar ao Supabase:", e)

def deletar_sala(nome: str):
    # Remove uma turma pelo campo 'nome'.
    try:
        test = supabase.table("turmas").delete().eq("nome", nome).execute()
        print("Deleção bem sucedida!", test.data)
    except Exception as e:
        print("Deleção mal sucedida!", e)

def editar_sala(id: str, nome: str, turno: str):
    # Atualiza os dados de uma turma identificada pelo id.
    data = {"nome": nome, "turno": turno}
    try:
        test = supabase.table("turmas").update(data).eq("id", id).execute()
        print("Edição bem sucedida!", test.data)
    except Exception as e:
        print("Edição mal sucedida!", e)

# -----------------------------------------------------------------------------
# GERENCIAMENTO DE USUÁRIOS
# -----------------------------------------------------------------------------
# As funções abaixo tratam da criação e atualização dos usuários do sistema,
# incluindo o relacionamento entre alunos/professores e turmas.
# -----------------------------------------------------------------------------

def criar_dados_alunos(id:str, id_turma:str,):
    # Guarda o relacionamento de um aluno com a turma em que está matriculado.
    data = {"id":id, "id_turma":id_turma,}

    try:
        test = supabase.table("usuarios_dados_alunos").insert(data).execute()
        print("Conexão bem-sucedida!", test.data)
    except Exception as e:
        print("Erro ao conectar ao Supabase:", e)


def create_user(id: str, type: str, name: str, date_of_birth: str, id_turma:str):
    # Cria um usuário genérico com base no tipo informado.
    # Para alunos: salva na tabela 'usuarios' e também no relacionamento 'usuarios_dados_alunos'.
    # Para professores: salva na tabela 'usuarios' e liga o professor à turma.
    data = {"id": id, "tipo": type, "nome": name, "data_nascimento": date_of_birth}

    if data["tipo"] == "aluno":
        try:
            test = supabase.table("usuarios").insert(data).execute()
            print("Conexão bem-sucedida!", test.data)
        except Exception as e:
            print("Erro ao conectar ao Supabase:", e) 
            
        criar_dados_alunos(id=id, id_turma=id_turma,)

    elif data["tipo"] == "professor":
        try:
            test = supabase.table("usuarios").insert(data).execute()
            print("Conexão bem-sucedida!", test.data)
        except Exception as e:
            print("Erro ao conectar ao Supabase:", e)

        criar_dados_professores(id_turma=id_turma, id_professor=data["id"])


def delete_user(id: str):
    # Remove um usuário pela chave primária 'id'.
    try:
        test = supabase.table("usuarios").delete().eq("id", id).execute()
        print("Deleção bem sucedida!", test.data)
    except Exception as e:
        print("Deleção mal sucedida!", e)

def edite_user(id: str, name: str, date_of_birth: str):
    # Atualiza nome e data de nascimento de um usuário.
    data = {"id": id, "nome": name, "data_nascimento": date_of_birth}
    try:
        test = supabase.table("usuarios").update(data).eq("id", id).execute()
        print("Edição bem sucedida!", test.data)
    except Exception as e:
        print("Edição mal sucedida!", e)

def criar_dados_professores(id_turma:str, id_professor:str):
    # Cria a associação entre professor e turma.
    data = {"id_turma": id_turma, "id_professor": id_professor}

    try:
        test = supabase.table("turmas_professores").insert(data).execute()
        print("Conexão bem-sucedida!", test.data)
    except Exception as e:
        print("Erro ao conectar ao Supabase:", e)

def consultar_user_login(id:str):
    result = supabase.table("usuarios").select("*").eq("id", id).execute()
    if not result.data:
        raise LookupError("usuário não encontrado")

    return result.data[0]["data_nascimento"]
    
