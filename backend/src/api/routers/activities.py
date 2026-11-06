from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dtos.activities import ActivityWrite
from src.api.routers.users import require_manager, require_session
from src.datalayer.data import (
    create_activity,
    delete_activity,
    get_activities_for_user,
    get_activity,
    get_classes_for_user,
    get_user_class_ids,
    get_user_type,
    list_teachers,
    update_activity,
)

router = APIRouter(prefix="/atividades", tags=["atividades"])


def _activity_editor(user_id: str) -> tuple[str, set[str]]:
    try:
        user_type = get_user_type(user_id)
        class_ids = set(get_user_class_ids(user_id))
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado.",
        ) from None

    if user_type not in {"professor", "gestao"}:
        raise HTTPException(
            status_code=403,
            detail="Seu perfil não pode gerenciar atividades.",
        )
    return user_type, class_ids


def _resolve_teacher_id(
    body: ActivityWrite,
    user_id: str,
    user_type: str,
) -> str:
    if user_type == "professor":
        if body.professor_id and body.professor_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Professor não pode atribuir atividade a outro usuário.",
            )
        return user_id

    if not body.professor_id:
        raise HTTPException(
            status_code=422,
            detail="Selecione o professor responsável pela atividade.",
        )
    try:
        selected_type = get_user_type(body.professor_id)
    except LookupError:
        raise HTTPException(status_code=422, detail="Professor não encontrado.") from None
    if selected_type != "professor":
        raise HTTPException(
            status_code=422,
            detail="O responsável selecionado não é um professor.",
        )
    return body.professor_id


@router.get("/professores")
async def activity_teachers(_manager_id: str = Depends(require_manager)):
    return list_teachers()


@router.get("/turmas")
async def activity_classes(user_id: str = Depends(require_session)):
    _activity_editor(user_id)
    return get_classes_for_user(user_id)


@router.get("")
async def list_activities(user_id: str = Depends(require_session)):
    try:
        return get_activities_for_user(user_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Usuário da sessão não encontrado.",
        ) from None


@router.post("", status_code=status.HTTP_201_CREATED)
async def publish_activity(
    body: ActivityWrite,
    user_id: str = Depends(require_session),
):
    user_type, allowed_class_ids = _activity_editor(user_id)
    if not set(body.id_turmas).issubset(allowed_class_ids):
        raise HTTPException(
            status_code=403,
            detail="Você não pode criar atividades para uma ou mais turmas selecionadas.",
        )

    professor_id = _resolve_teacher_id(body, user_id, user_type)
    return create_activity(
        body.nome,
        body.descricao,
        body.materia,
        body.data_limite.isoformat(),
        professor_id,
        body.id_turmas,
    )


@router.put("/{activity_id}")
async def edit_activity(
    activity_id: str,
    body: ActivityWrite,
    user_id: str = Depends(require_session),
):
    user_type, allowed_class_ids = _activity_editor(user_id)
    try:
        current = get_activity(activity_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.") from None

    if user_type == "professor" and current.get("professor_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="Você só pode editar atividades atribuídas a você.",
        )
    current_class_ids = current.get("id_turmas")
    preserved_class_ids = (
        {str(class_id) for class_id in current_class_ids}
        if isinstance(current_class_ids, list)
        else set()
    )
    if not set(body.id_turmas).issubset(allowed_class_ids | preserved_class_ids):
        raise HTTPException(
            status_code=403,
            detail="Você não pode vincular a atividade a uma ou mais turmas selecionadas.",
        )

    professor_id = _resolve_teacher_id(body, user_id, user_type)
    return update_activity(
        activity_id,
        body.nome,
        body.descricao,
        body.materia,
        body.data_limite.isoformat(),
        professor_id,
        body.id_turmas,
    )


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_activity(
    activity_id: str,
    user_id: str = Depends(require_session),
):
    user_type, _ = _activity_editor(user_id)
    try:
        activity = get_activity(activity_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.") from None

    if user_type == "professor" and activity.get("professor_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="Você só pode excluir atividades atribuídas a você.",
        )
    delete_activity(activity_id)
