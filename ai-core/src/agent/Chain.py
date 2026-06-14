"""
chain.py
Agente CV: responde preguntas sobre la trayectoria profesional de Nahuel Román.

Flujo:
    Pregunta + Historial → SelfQuery+Reranker → Contexto → LLM → Respuesta

"""

import os
from pathlib import Path
from langchain_openai import ChatOpenAI
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
from src.agent.router_chain import build_router, classify_query

# ── Configuración ─────────────────────────────────────────────────────────────

AGENT_MODEL = "meta-llama/llama-3.3-70b-instruct"
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

def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=AGENT_MODEL,
        temperature=0.2,
        max_tokens=1000
    )

# ── Historial en memoria ───────────────────────────────────────────────────────

# Almacena los historiales de sesión en RAM.
# Se pierde al cerrar el servidor (comportamiento esperado).
_session_store = SessionManager()


# ── Chain principal ────────────────────────────────────────────────────────────

def build_cv_agent():
    """
    Construye y retorna el agente CV con routing previo al RAG.
    """
    load_dotenv()
    retriever = build_retriever()
    system_prompt = load_system_prompt()
    router_chain = build_router()

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(
        llm=_get_llm(),
        prompt=prompt,
    )

    rag_chain = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=question_answer_chain,
    )

    agent_with_history = RunnableWithMessageHistory(
        rag_chain,
        get_session_history=_session_store.get_session,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    # LLM directo (sin RAG) para rutas 'direct'
    direct_chain = prompt | _get_llm()

    async def routed_invoke(query: str, session_id: str) -> str:
        route = classify_query(router_chain, query)
        log.info(f"[ROUTER] session={session_id} route={route} query={query!r}")

        if route == "block":
            return {"answer": "Sólo puedo responder preguntas que sean estrictamente sobre la trayectoria de Nahuel Román y sus proyectos.", 
                    "context": []}

        history = _session_store.get_session(session_id)
        chat_history = history.messages[-HISTORY_K:]

        if route == "direct":
            async with _lock:
                response = await direct_chain.ainvoke({
                    "input": query,
                    "context": [],
                    "chat_history": chat_history,
                })
            return {"answer": response.content, "context": []}

        # route == "rag"
        async with _lock:
            response = await agent_with_history.ainvoke(
                {"input": query},
                config={"configurable": {"session_id": session_id}},
            )
        return {"answer": response["answer"], "context": response["context"]}

    return routed_invoke
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
