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
import asyncio
from pydantic import BaseModel
from pathlib import Path
from src.pre_process.chunking import chunk_incoming_file
from src.vector_load.vector_store import upsert_documents, delete_document_chunks
from dotenv import load_dotenv
from src.vector_load.vector_store import upsert_documents
from src.API.models.DocumentUpsertRequest import DocumentUpsertRequest
from src.agent.Chain import build_cv_agent, _session_store

router = APIRouter()
load_dotenv()
vector_db_lock = asyncio.Lock()
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

class ChatRequest(BaseModel):
    message: str

@router.post("/chat", response_model=dict)
@limiter.limit("15/minute")
async def chat(
    request: Request, 
    payload: ChatRequest, 
    session_id: str = Depends(verify_chat_token)
):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    # BLOQUEO CRÍTICO: Si hay un Upsert/Delete en curso, el chat hace una pausa aquí
    async with vector_db_lock:
        # NOTA: Usamos ainvoke (Async Invoke) para que no bloquee el event loop de FastAPI
        result = await cv_agent.ainvoke(
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
    metadata: str = Form(...) 
):
    try:
        meta_dict = json.loads(metadata)
        document_id = meta_dict.get("document_id")
        
        if document_id is None:
             raise HTTPException(status_code=400, detail="Falta document_id en metadata")

        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        try:
            chunks = chunk_incoming_file(temp_file_path, meta_dict)
            
            # BLOQUEO CRÍTICO: Operación Atómica de Reemplazo
            async with vector_db_lock:
                delete_document_chunks(document_id) # 1. Purgar versión vieja
                upsert_documents(chunks)            # 2. Insertar versión nueva
                
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        return {"status": "success", "message": f"Documento {document_id} actualizado ({len(chunks)} chunks)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/internal/documents/{document_id}", dependencies=[Depends(verify_internal_secret)])
async def delete_internal_document(document_id: int):
    """
    Endpoint invocado por Spring Boot cuando se elimina un archivo o proyecto.
    """
    try:
        # BLOQUEO CRÍTICO: Evita que el RAG lea mientras se borra
        async with vector_db_lock:
            delete_document_chunks(document_id)
            
        return {"status": "success", "message": f"Documento {document_id} purgado de la base vectorial."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/health")
async def health() -> dict:
    """Verificación de estado del servidor."""
    return {"status": "ok"}

