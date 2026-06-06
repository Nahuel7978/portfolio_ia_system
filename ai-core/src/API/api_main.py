# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from src.API.router import router

logger = logging.getLogger("scapi")
scheduler = None
job_cleaner = None


# Eventos (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de inicialización
    logger.info("API arrancando: inicializando recursos...")
    try:    
        logger.info("✅ Inicialización completada")
        
    except Exception as e:
        logger.error(f"❌ Error durante inicialización: {e}")
        raise
    
    yield
    # Código de limpieza
    logger.info("API apagándose: cerrando recursos...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="CV_BOT_API",
        version="1.0.0",
        description="API para recibir preguntas del usuario y devolver respuestas del agente CV.",
        lifespan=lifespan
    )

    # Middlewares: CORS ejemplo (ajustar CORS_ORIGINS en config)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routers
    app.include_router(router.router, prefix="/CV_BOT_API/v1")

    return app

app = create_app()