from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dtos.events import EventCreate
from src.api.routers.users import require_session
from src.datalayer.data import (
    create_event,
    get_classes_for_user,
    get_events_for_user,
    get_user_class_ids,
    get_user_type,
)

router = APIRouter(prefix="/eventos", tags=["eventos"])


def _require_event_editor(user_id: str) -> list[str]:
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
            detail="Seu perfil não pode criar eventos.",
        )
    if not class_ids:
        raise HTTPException(
            status_code=403,
            detail="Não há turmas vinculadas ao seu perfil.",
        )
    return class_ids


@router.get("/turmas")
async def list_event_classes(user_id: str = Depends(require_session)):
    _require_event_editor(user_id)
    return get_classes_for_user(user_id)


@router.get("")
async def list_events(user_id: str = Depends(require_session)):
    try:
        return get_events_for_user(user_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado.",
        ) from None


@router.post("", status_code=status.HTTP_201_CREATED)
async def publish_event(
    body: EventCreate,
    user_id: str = Depends(require_session),
):
    allowed_class_ids = set(_require_event_editor(user_id))
    if not set(body.id_turmas).issubset(allowed_class_ids):
        raise HTTPException(
            status_code=403,
            detail="Você não pode criar eventos para uma ou mais turmas selecionadas.",
        )

    return create_event(body.nome, body.data.isoformat(), body.id_turmas)
