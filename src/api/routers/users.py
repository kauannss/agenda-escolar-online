from fastapi import APIRouter
from src.api.dtos.users import userRegistration, userLogin
from src.datalayer.data import create_user, consultar_user_login
from datetime import datetime

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

@router.get("/login")
async def read_users(body: userLogin):
    #faça um busca no banco de dados
    consultar_user_login(body.id, body.date_of_birth)


    #verificar se o acesso existe se não retorna email/senha incorretos
    #se acesso existir testa senha se senha não for correta retorna email/senha incorretos
