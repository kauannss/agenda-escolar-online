from fastapi import FastAPI
from src.api.routers import users

#função para conectar rotas
def configure_routes(app: FastAPI):
    app.include_router(users.router)