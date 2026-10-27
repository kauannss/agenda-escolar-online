from fastapi import APIRouter
from src.api.dtos.users import userRegistration, userLogin
from src.datalayer.data import (
    SessionStorageNotConfigured,
    create_session,
    create_user,
    consultar_user_login,
)
from datetime import datetime
from fastapi import HTTPException

#definindo funções rota

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", tags=["users"])
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.post("/register")
async def register(body: userRegistration):
    print("register:", body)

    date_data = datetime.strptime(body.date_of_birth, "%d/%m/%Y").date().isoformat()

    
    create_user(
        body.id,
        body.type,
        body.name,
        date_data,
        body.id_turma,
    )

@router.post("/login")
async def login(body: userLogin):
    try:
        date_of_birth = consultar_user_login(body.id)
    except LookupError:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas"
        ) from None

    try:
        expected_password = datetime.strptime(
            date_of_birth, "%Y-%m-%d"
        ).strftime("%d%m%Y")
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Data de nascimento do usuário inválida no cadastro.",
        ) from None

    if expected_password != body.password:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas"
        )

    try:
        session_token = create_session(body.id)
    except SessionStorageNotConfigured as error:
        raise HTTPException(
            status_code=503,
            detail="A criação de sessão ainda não está configurada no servidor.",
        ) from error

    return {
        "access_token": session_token,
        "token_type": "bearer",
    }
