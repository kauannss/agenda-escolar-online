from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from src.api.dtos.users import (
    GuardianNameUpdate,
    userRegistration,
    userUpdate,
    userLogin,
)
from src.datalayer.data import (
    SessionStorageNotConfigured,
    create_session,
    create_user,
    delete_user,
    get_classes_for_user,
    get_manager_count,
    get_user_for_management,
    list_users,
    get_user_profile,
    get_session_user_id,
    get_user_type,
    revoke_session,
    consultar_user_login,
    update_student_guardian_name,
    update_user,
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


def require_manager(user_id: str = Depends(require_session)) -> str:
    try:
        user_type = get_user_type(user_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado.",
        ) from None
    if user_type != "gestao":
        raise HTTPException(
            status_code=403,
            detail="Somente a gestão pode gerenciar usuários.",
        )
    return user_id


@router.get("/", tags=["users"])
@router.get("", include_in_schema=False)
async def read_users(_user_id: str = Depends(require_manager)):
    return list_users()


@router.get("/classes")
async def list_registration_classes(
    _user_id: str = Depends(require_manager),
):
    return get_classes_for_user(_user_id)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: userRegistration,
    _user_id: str = Depends(require_manager),
):
    if body.type in {"aluno", "professor"} and not body.id_turma:
        raise HTTPException(
            status_code=422,
            detail="Selecione uma turma para aluno ou professor.",
        )

    if body.type in {"aluno", "professor"}:
        allowed_class_ids = {
            class_option["id"] for class_option in get_classes_for_user(_user_id)
        }
        if body.id_turma not in allowed_class_ids:
            raise HTTPException(status_code=422, detail="A turma selecionada não existe.")

    return create_user(
        body.id,
        body.type,
        body.name,
        body.date_of_birth.isoformat(),
        body.id_turma,
    )


@router.get("/me")
async def current_user(user_id: str = Depends(require_session)):
    try:
        return get_user_profile(user_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado.",
        ) from None


@router.put("/me/responsavel")
async def update_current_student_guardian(
    body: GuardianNameUpdate,
    user_id: str = Depends(require_session),
):
    try:
        user_type = get_user_type(user_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado.",
        ) from None
    if user_type != "aluno":
        raise HTTPException(
            status_code=403,
            detail="Somente o aluno pode informar o nome do responsável.",
        )
    try:
        return {
            "nome_responsavel": update_student_guardian_name(
                user_id,
                body.nome_responsavel,
            )
        }
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Vínculo de aluno não encontrado.",
        ) from None


@router.get("/{target_user_id}")
async def read_user_for_management(
    target_user_id: str,
    _user_id: str = Depends(require_manager),
):
    try:
        return get_user_for_management(target_user_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.") from None


@router.put("/{target_user_id}")
async def edit_user(
    target_user_id: str,
    body: userUpdate,
    manager_id: str = Depends(require_manager),
):
    if body.type == "aluno" and len(body.id_turmas) != 1:
        raise HTTPException(
            status_code=422,
            detail="Aluno deve estar vinculado a exatamente uma turma.",
        )
    if body.type == "professor" and not body.id_turmas:
        raise HTTPException(
            status_code=422,
            detail="Professor deve estar vinculado a pelo menos uma turma.",
        )
    if body.type == "gestor" and body.id_turmas:
        raise HTTPException(
            status_code=422,
            detail="Gestor não deve possuir vínculo com turma.",
        )

    allowed_class_ids = {
        class_option["id"] for class_option in get_classes_for_user(manager_id)
    }
    if not set(body.id_turmas).issubset(allowed_class_ids):
        raise HTTPException(status_code=422, detail="Uma turma selecionada não existe.")

    try:
        current_user = get_user_for_management(target_user_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.") from None

    if (
        current_user["tipo"] == "gestao"
        and body.type != "gestor"
        and get_manager_count() <= 1
    ):
        raise HTTPException(
            status_code=409,
            detail="Não é possível remover o último usuário da gestão.",
        )

    return update_user(
        target_user_id,
        "gestao" if body.type == "gestor" else body.type,
        body.name,
        body.date_of_birth.isoformat(),
        body.id_turmas,
    )


@router.delete("/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
    target_user_id: str,
    manager_id: str = Depends(require_manager),
):
    if target_user_id == manager_id:
        raise HTTPException(
            status_code=409,
            detail="Você não pode remover sua própria conta.",
        )

    try:
        target_user = get_user_for_management(target_user_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.") from None

    if target_user["tipo"] == "gestao" and get_manager_count() <= 1:
        raise HTTPException(
            status_code=409,
            detail="Não é possível remover o último usuário da gestão.",
        )

    delete_user(target_user_id)


@router.post("/logout")
async def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    if session_token:
        revoke_session(session_token)

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
    )
    return {"message": "Logout realizado com sucesso."}
