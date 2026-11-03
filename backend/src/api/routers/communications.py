from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dtos.communications import CommunicationCreate
from src.api.routers.users import require_session
from src.datalayer.data import (
    create_communication,
    get_classes_for_user,
    get_communications_for_user,
    get_user_class_ids,
    get_user_type,
)

router = APIRouter(prefix="/comunicados", tags=["comunicados"])


def _require_publisher(user_id: str) -> list[str]:
    try:
        user_type = get_user_type(user_id)
        class_ids = get_user_class_ids(user_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado.",
        ) from None

    if user_type not in {"professor", "gestao"}:
        raise HTTPException(
            status_code=403,
            detail="Seu perfil não pode publicar comunicados.",
        )
    if not class_ids:
        raise HTTPException(
            status_code=403,
            detail="Não há turmas vinculadas ao seu perfil.",
        )
    return class_ids


@router.get("/turmas")
async def list_publishable_classes(user_id: str = Depends(require_session)):
    _require_publisher(user_id)
    return get_classes_for_user(user_id)


@router.get("")
async def list_communications(user_id: str = Depends(require_session)):
    try:
        return get_communications_for_user(user_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado.",
        ) from None


@router.post("", status_code=status.HTTP_201_CREATED)
async def publish_communication(
    body: CommunicationCreate,
    user_id: str = Depends(require_session),
):
    allowed_class_ids = set(_require_publisher(user_id))
    if not set(body.id_turmas).issubset(allowed_class_ids):
        raise HTTPException(
            status_code=403,
            detail="Você não pode publicar para uma ou mais turmas selecionadas.",
        )

    return create_communication(body.title, body.description, body.id_turmas)
