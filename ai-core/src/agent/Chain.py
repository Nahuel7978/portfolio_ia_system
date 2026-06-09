"""
chain.py
Agente CV: responde preguntas sobre la trayectoria profesional de Nahuel Román.

Flujo:
    Pregunta + Historial → SelfQuery+Reranker → Contexto → LLM → Respuesta

"""

import os
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from src.retrieval.retriever import build_retriever
import logging as log
from dotenv import load_dotenv
import asyncio
from src.agent.SessionManager import SessionManager

# ── Configuración ─────────────────────────────────────────────────────────────

GROQ_MODEL    = "llama-3.3-70b-versatile"
HISTORY_K     = 6   # Últimos N mensajes del historial que se pasan al LLM
load_dotenv()
_lock = asyncio.Lock()

# ── System Prompt ─────────────────────────────────────────────────────────────
def load_system_prompt() -> str:
    """Lee el prompt del sistema desde el archivo físico."""
    base_dir = Path(__file__).resolve().parent
    prompt_path = base_dir / "prompts" / "SYSTEM_PROMPT.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
    
# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatGroq:
    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0.2,
        max_tokens=1000,
        api_key=os.environ["GROQ_API_KEY"],
    )

# ── Historial en memoria ───────────────────────────────────────────────────────

# Almacena los historiales de sesión en RAM.
# Se pierde al cerrar el servidor (comportamiento esperado).
_session_store = SessionManager()


# ── Chain principal ────────────────────────────────────────────────────────────

def build_cv_agent() -> RunnableWithMessageHistory:
    """
    Construye y retorna el agente CV completo con memoria de sesión.

    Returns:
        RunnableWithMessageHistory listo para invocar con session_id.
    """
    load_dotenv()
    retriever = build_retriever()
    system_prompt = load_system_prompt()

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    # Chain que combina el contexto recuperado con el prompt y el LLM
    question_answer_chain = create_stuff_documents_chain(
        llm=_get_llm(),
        prompt=prompt,
    )

    # Chain completa: retriever → question_answer_chain
    rag_chain = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=question_answer_chain,
    )

    # Envolver con memoria de sesión
    agent_with_history = RunnableWithMessageHistory(
        rag_chain,
        get_session_history=_session_store.get_session,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    return agent_with_history

#────────────────Clean────────────────────────────────────────────────────────────
async def clear_session(session_id: str) -> dict:
    """
    Elimina el historial de una sesión específica.

    Args:
        session_id: ID de la sesión a eliminar.

    Returns:
        Dict con mensaje de éxito o error.
    """
    await _session_store.delete_session(session_id)