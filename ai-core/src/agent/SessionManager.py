
from langchain_community.chat_message_histories import ChatMessageHistory
from threading import Lock



class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class SessionManager(metaclass=SingletonMeta):
    _session_store: dict[str, ChatMessageHistory]
    
    def __init__(self):
        self._session_store = {}
        self.HISTORY_K = 6   # Últimos N mensajes del historial que se pasan al LLM
        
    def create_session(self, session_id):
        self._session_store[session_id] = ChatMessageHistory()

    def get_session(self, session_id):
        if session_id not in self._session_store:
            self.create_session(session_id)
        
        history = self._session_store[session_id]
        # Mantener solo los últimos HISTORY_K mensajes
        if len(history.messages) > self.HISTORY_K:
            history.messages = history.messages[-self.HISTORY_K:]
        return history

    async def delete_session(self, session_id):
        if session_id in self._session_store:
            del self._session_store[session_id]
            return {"detail": f"Sesión '{session_id}' eliminada correctamente."}
        return {"detail": f"Sesión '{session_id}' no encontrada."}
