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
from src.agent.Chain import _session_store

logger = logging.getLogger("CV_BOT_API")
scheduler = None 
job_cleaner = None


# Eventos (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API arrancando: inicializando recursos...")
    
    # Tarea en segundo plano para el recolector de basura (Garbage Collector)
    async def session_garbage_collector():
        try:
            while True:
                # Duerme por 60 segundos antes de realizar el siguiente ciclo de inspección
                await asyncio.sleep(60)
                purged_count = _session_store.cleanup_sessions(max_idle_minutes=60)
                if purged_count > 0:
                    logger.info(f"[Garbage Collector] Se liberaron {purged_count} sesiones inactivas de la RAM.")
        except asyncio.CancelledError:
            logger.info("[Garbage Collector] Tarea de limpieza finalizada de forma segura.")

    # Registramos e iniciamos la tarea asíncrona concurrente
    gc_task = asyncio.create_task(session_garbage_collector())
    
    yield
    
    logger.info("API apagándose: cancelando subtareas y cerrando recursos...")
    gc_task.cancel()
    # Esperamos que la tarea responda a la cancelación de forma limpia
    await asyncio.gather(gc_task, return_exceptions=True)
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
