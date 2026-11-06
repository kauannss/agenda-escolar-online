from fastapi import APIRouter, Depends, status

from src.api.dtos.classes import ClassCreate
from src.api.routers.users import require_manager
from src.datalayer.data import criar_sala, listar_turmas

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
