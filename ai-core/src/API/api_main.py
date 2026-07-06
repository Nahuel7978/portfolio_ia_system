# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from src.API.router import router
import asyncio
import logging

logger = logging.getLogger("CV_BOT_API")
scheduler = None 
job_cleaner = None


# Eventos (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API arrancando: inicializando recursos...")
    yield
    logger.info("✅ Recursos y tareas de la API cerradas con éxito.")

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
        allow_origins=["http://173.249.28.153"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routers
    app.include_router(router.router)

    return app

app = create_app()
