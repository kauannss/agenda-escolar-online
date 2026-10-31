from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from src.api.dtos.users import userRegistration, userLogin
from src.datalayer.data import (
    SessionStorageNotConfigured,
    create_session,
    create_user,
    get_session_user_id,
    consultar_user_login,
)
from datetime import datetime
from src.api.session_config import (
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
    SESSION_TTL_SECONDS,
)

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
async def login(body: userLogin, response: Response):
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

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path="/",
    )
    return {"message": "Login realizado com sucesso."}


async def require_session(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> str:
    if not session_token:
        raise HTTPException(status_code=401, detail="Sessão não encontrada.")

    try:
        user_id = get_session_user_id(session_token)
    except SessionStorageNotConfigured as error:
        raise HTTPException(
            status_code=503,
            detail="A consulta de sessão não está configurada no servidor.",
        ) from error

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida ou expirada.",
        )

    return user_id


@router.get("/me")
async def current_user(user_id: str = Depends(require_session)):
    return {"id": user_id}
