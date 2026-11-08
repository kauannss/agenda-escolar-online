from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dtos.communications import CommunicationCreate
from src.api.routers.users import require_manager, require_session
from src.datalayer.data import (
    create_communication,
    delete_communication,
    get_classes_for_user,
    get_communications_for_user,
    get_user_class_ids,
    get_user_type,
    update_communication,
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


@router.put("/{communication_id}")
async def edit_communication(
    communication_id: str,
    body: CommunicationCreate,
    manager_id: str = Depends(require_manager),
):
    allowed_class_ids = {
        class_option["id"] for class_option in get_classes_for_user(manager_id)
    }
    if not set(body.id_turmas).issubset(allowed_class_ids):
        raise HTTPException(
            status_code=422,
            detail="Uma ou mais turmas selecionadas não existem.",
        )
    try:
        return update_communication(
            communication_id,
            body.title,
            body.description,
            body.id_turmas,
        )
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Comunicado não encontrado.",
        ) from None


@router.delete(
    "/{communication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_communication(
    communication_id: str,
    _manager_id: str = Depends(require_manager),
):
    try:
        delete_communication(communication_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Comunicado não encontrado.",
        ) from None
