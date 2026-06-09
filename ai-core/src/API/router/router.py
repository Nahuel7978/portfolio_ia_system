"""
api.py
Endpoint FastAPI que expone el Agente CV de Nahuel Román.

Endpoints:
    POST /chat         → Enviar un mensaje al agente CV
    DELETE /session    → Limpiar el historial de una sesión

Uso: uvicorn src.agent.api:app --reload
"""

from fastapi import APIRouter, HTTPException, Header, Depends, File, UploadFile, Form, Request
from src.API.security.security import create_chat_token, verify_chat_token, limiter
from src.agent.Chain import build_cv_agent, _session_store
import json
import os
from pydantic import BaseModel
from pathlib import Path
from src.pre_process.chunking import chunk_incoming_file
from src.vector_load.vector_store import upsert_documents
from dotenv import load_dotenv
from src.vector_load.vector_store import upsert_documents
from src.API.models.DocumentUpsertRequest import DocumentUpsertRequest
from src.agent.Chain import build_cv_agent, _session_store

router = APIRouter()
load_dotenv()

# Inicializar el agente una sola vez al levantar el servidor
cv_agent = build_cv_agent()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str


# --- Endpoint para generar token------
@router.get("/auth/chat-token")
@limiter.limit("5/minute") # Máximo 5 sesiones nuevas por minuto por IP
async def get_chat_token(request: Request):
    token = create_chat_token()
    return {"access_token": token, "token_type": "bearer"}

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=dict)
@limiter.limit("15/minute") # Límite para evitar spam de mensajes
async def chat(
    request: Request, 
    payload: ChatRequest, 
    session_id: str = Depends(verify_chat_token)
):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    result = cv_agent.invoke(
        {"input": payload.message},
        config={"configurable": {"session_id": session_id}},
    )

    return {"answer": result["answer"]}


@router.delete("/session/{session_id}")
async def clear_session(session_id: str) -> dict:
    """
    Elimina el historial de una sesión específica.
    Útil cuando el usuario cierra el chat desde el frontend.
    """
    return await cv_agent.clear_session(session_id)  # Limpia la memoria del agente para esa sesión


def verify_internal_secret(x_internal_secret: str = Header(...)):
    expected_secret = os.getenv("X_INTERNAL_SECRET")
    if not expected_secret or x_internal_secret != expected_secret:
        raise HTTPException(status_code=403, detail="Acceso denegado (Invalid Secret)")


@router.post("/internal/documents/upsert", dependencies=[Depends(verify_internal_secret)])
async def upsert_internal_document(
    file: UploadFile = File(...),
    metadata: str = Form(...) # Recibimos el JSON serializado como un string
):
    try:
        # 1. Parsear los metadatos desde el string
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="El campo metadata debe ser un JSON válido.")

        # 2. Guardar el archivo temporalmente en el contenedor
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        # 3. Procesar y Vectorizar
        try:
            chunks = chunk_incoming_file(temp_file_path, meta_dict)
            upsert_documents(chunks)
        finally:
            # 4. Limpieza Crítica: Siempre eliminar el archivo temporal
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        return {"status": "success", "message": f"{len(chunks)} chunks vectorizados exitosamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/health")
async def health() -> dict:
    """Verificación de estado del servidor."""
    return {"status": "ok"}

