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


def _session_supabase_client() -> Client:
    secret_key = os.getenv("SUPABASE_SECRET_KEY")
    if not secret_key:
        raise SessionStorageNotConfigured(
            "Configure SUPABASE_SECRET_KEY in the backend environment."
        )
    return create_client(url, secret_key)


def create_session(user_id: str) -> str:
    """Persist a session token hash and return the original token to the caller."""
    session_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    session_client = _session_supabase_client()
    session_client.table("sessions").insert(
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
    session_client = _session_supabase_client()
    result = (
        session_client.table("sessions")
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
    
