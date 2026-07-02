# src/API/security.py
import os
from dotenv import load_dotenv
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from langchain_core.messages import RemoveMessage

load_dotenv()
CHAT_JWT_SECRET = os.getenv("CHAT_JWT_SECRET", "default_secret_fallback")
ALGORITHM = "HS256"
TOKEN_EXPIRATION_MINUTES = 60

security_scheme = HTTPBearer()

# Inicializador de SlowAPI (Límite por IP)
limiter = Limiter(key_func=get_remote_address)

def create_chat_token() -> str:
    """Genera un JWT válido por 60 minutos con un session_id único."""
    session_id = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
    to_encode = {"sub": session_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, CHAT_JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def verify_chat_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> str:
    """Valida el JWT y extrae el session_id."""
    try:
        payload = jwt.decode(credentials.credentials, CHAT_JWT_SECRET, algorithms=[ALGORITHM])
        session_id: str = payload.get("sub")
        if session_id is None:
            raise HTTPException(status_code=401, detail="Token inválido: Sin Session ID")
        return session_id
    except jwt.ExpiredSignatureError:
        try:
            payload_expired = jwt.decode(
                credentials.credentials, 
                CHAT_JWT_SECRET, 
                algorithms=[ALGORITHM], 
                options={"verify_exp": False}
            )
            session_id = payload_expired.get("sub")
            if session_id:
                # Importación dinámica para resolver la instancia global sin romper las dependencias de FastAPI
                from src.agent.graph import cv_agent_app
                # Ejecutamos la limpieza automática en la RAM del servidor
                purge_session_memory(session_id, cv_agent_app)
        except Exception:
            # Si el token expirado está corrupto o falla el parseo, no bloqueamos el flujo y dejamos que lance el 401
            pass
        raise HTTPException(status_code=401, detail="El token de chat ha expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token de chat inválido")
    
def purge_session_memory(session_id: str, cv_agent_app) -> int:
    """
    Botón de Pánico / Garbage Collector: 
    Busca la sesión en la RAM y purga los mensajes enviando comandos RemoveMessage.
    """

    config = {"configurable": {"thread_id": session_id}}
    state = cv_agent_app.get_state(config)
    
    # Verificamos si existe el estado y si tiene mensajes
    if state and "messages" in state.values and state.values["messages"]:
        # Mapeamos los IDs de los mensajes actuales a objetos RemoveMessage
        messages_to_remove = [RemoveMessage(id=m.id) for m in state.values["messages"]]
        
        # Enviamos la orden de actualización al Grafo para destruirlos
        cv_agent_app.update_state(config, {"messages": messages_to_remove})
        return len(messages_to_remove)
    return 0