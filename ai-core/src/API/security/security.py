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
        raise HTTPException(status_code=401, detail="El token de chat ha expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token de chat inválido")