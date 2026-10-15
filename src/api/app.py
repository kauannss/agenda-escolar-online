from fastapi import FastAPI
from src.api.config import configure_routes

def create_app():
    app = FastAPI()

    #incluir rotas
    configure_routes(app)

    return app

app = create_app()
