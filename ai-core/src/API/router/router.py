"""
api.py
Endpoint FastAPI que expone el Agente CV de Nahuel Román.

Endpoints:
    POST /chat         → Enviar un mensaje al agente CV
    DELETE /session    → Limpiar el historial de una sesión

Uso: uvicorn src.agent.api:app --reload
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from src.agent.Chain import build_cv_agent, _session_store

router = APIRouter()
load_dotenv()

# Inicializar el agente una sola vez al levantar el servidor
cv_agent = build_cv_agent()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Recibe un mensaje del usuario y devuelve la respuesta del agente CV.
    El historial de la sesión se mantiene en memoria mientras el servidor esté activo.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    result = cv_agent.invoke(
        {"input": request.message},
        config={"configurable": {"session_id": request.session_id}},
    )

    return ChatResponse(
        session_id=request.session_id,
        answer=result["answer"],
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str) -> dict:
    """
    Elimina el historial de una sesión específica.
    Útil cuando el usuario cierra el chat desde el frontend.
    """
    return await cv_agent.clear_session(session_id)  # Limpia la memoria del agente para esa sesión


@router.get("/health")
async def health() -> dict:
    """Verificación de estado del servidor."""
    return {"status": "ok"}