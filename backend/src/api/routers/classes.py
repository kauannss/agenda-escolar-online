from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dtos.classes import ClassCreate
from src.api.routers.users import require_manager
from src.datalayer.data import (
    criar_sala,
    deletar_sala,
    editar_sala,
    listar_turmas,
)

router = APIRouter(prefix="/turmas", tags=["turmas"])


@router.get("")
async def read_classes(_manager_id: str = Depends(require_manager)):
    return listar_turmas()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_class(
    body: ClassCreate,
    _manager_id: str = Depends(require_manager),
):
    return criar_sala(body.nome, body.turno)


@router.put("/{class_id}")
async def edit_class(
    class_id: str,
    body: ClassCreate,
    _manager_id: str = Depends(require_manager),
):
    try:
        return editar_sala(class_id, body.nome, body.turno)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Turma não encontrada.",
        ) from None


@router.delete(
    "/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_class(
    class_id: str,
    _manager_id: str = Depends(require_manager),
):
    try:
        deletar_sala(class_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Turma não encontrada.",
        ) from None
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error
