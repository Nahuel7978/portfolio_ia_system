# src/agent/SessionManager.py
import asyncio
from pydantic import Field
from datetime import datetime, timezone
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

class LimitedChatMessageHistory(ChatMessageHistory):
    """
    Historial de chat personalizado que trunca automáticamente la memoria
    para retener únicamente los últimos N mensajes individuales.
    """
    max_messages: int = Field(default=10)
    def __init__(self, max_messages: int = 10):
        super().__init__()
        self.max_messages = max_messages

    def add_message(self, message):
        super().add_message(message)
        # Si excede el límite de memoria asignado, rebanamos reteniendo el final
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

class SessionManager:
    max_messages: int = Field(default=10)

    def __init__(self, max_messages: int = 10):
        # Almacena: { session_id: {"history": LimitedChatMessageHistory, "last_accessed": datetime} }
        self.sessions = {}
        self.max_messages = max_messages
        self._lock = asyncio.Lock()

    def get_session(self, session_id: str) -> BaseChatMessageHistory:
        """Obtiene o crea una sesión de chat, actualizando su marca de tiempo de actividad."""
        now = datetime.now(timezone.utc)
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": LimitedChatMessageHistory(max_messages=self.max_messages),
                "last_accessed": now
            }
        else:
            self.sessions[session_id]["last_accessed"] = now
            
        return self.sessions[session_id]["history"]

    async def delete_session(self, session_id: str) -> dict:
        """Elimina de forma explícita una sesión de la memoria RAM."""
        async with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return {"status": "success", "message": f"Sesión {session_id} purgada."}
            return {"status": "error", "message": "Sesión no encontrada."}

    def cleanup_sessions(self, max_idle_minutes: int = 60) -> int:
        """
        Escanea y remueve de la memoria RAM todas las sesiones que hayan
        superado el límite tolerable de inactividad.
        """
        now = datetime.now(timezone.utc)
        expired_ids = []
        # Identificar sesiones inactivas
        for session_id, data in self.sessions.items():
            idle_duration = now - data["last_accessed"]
            if idle_duration.total_seconds() > (max_idle_minutes * 60):
                expired_ids.append(session_id)
        
        # Eliminar llaves fuera de rango de tiempo
        for session_id in expired_ids:
            del self.sessions[session_id]
            
        return len(expired_ids)