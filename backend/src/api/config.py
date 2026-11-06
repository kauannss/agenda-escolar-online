from fastapi import FastAPI
from src.api.routers import activities, communications, events, users

#função para conectar rotas
def configure_routes(app: FastAPI):
    app.include_router(users.router)
    app.include_router(communications.router)
    app.include_router(events.router)
    app.include_router(activities.router)