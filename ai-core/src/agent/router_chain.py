"""
router.py
Clasifica la query antes de ejecutar el pipeline RAG.

Rutas posibles:
    - "rag"     → requiere búsqueda vectorial
    - "direct"  → se responde con info del system prompt
    - "block"   → fuera de scope o intento de manipulación
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path

ROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"


def load_system_prompt() -> str:
    """Lee el prompt del sistema desde el archivo físico."""
    base_dir = Path(__file__).resolve().parent
    prompt_path = base_dir / "prompts" / "router_prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def build_router() -> callable:
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=ROUTER_MODEL,
        temperature=0,
        max_tokens=5,
    )

    ROUTER_PROMPT = ChatPromptTemplate.from_messages([
        ("system", load_system_prompt()),
        ("human", "{input}")
    ])

    chain = ROUTER_PROMPT | llm
    return chain

def classify_query(router_chain, query: str) -> str:
    """
    Retorna: 'rag', 'direct' o 'block'.
    Si la respuesta no es válida, default a 'rag' por seguridad.
    """
    result = router_chain.invoke({"input": query})
    route = result.content.strip().lower()
    if route not in ("rag", "direct", "block"):
        return "rag"
    return route