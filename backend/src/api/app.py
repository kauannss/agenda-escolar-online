import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import configure_routes


LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://agenda-escolar-online-sz6h.vercel.app",
]


def create_app():
    app = FastAPI()

    # Em produção, informe as origens exatas do front-end em CORS_ORIGINS,
    # separadas por vírgula, sem barra no final.
    configured_origins = os.getenv("CORS_ORIGINS")
    allowed_origins = (
        [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
        if configured_origins is not None
        else LOCAL_FRONTEND_ORIGINS
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    #incluir rotas
    configure_routes(app)

    return app

app = create_app()
