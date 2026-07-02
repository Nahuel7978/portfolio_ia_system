import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from src.retrieval.retriever import build_retriever
from src.agent.router_chain import build_router, classify_query
from src.agent.state.AgentState import AgentState
from langchain_openai import ChatOpenAI

load_dotenv()

AGENT_MODEL = "meta-llama/llama-3.3-70b-instruct"

# Instancias globales para los nodos
llm = ChatOpenAI(model=AGENT_MODEL, api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1",temperature=0.2, max_tokens=1000)
retriever = build_retriever()
router_chain = build_router()

# Cargar el prompt desde el archivo
current_dir = Path(__file__).resolve().parent   
prompt_path = current_dir.parent / "prompts" / "SYSTEM_PROMPT.txt"
with open(prompt_path, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Prompt principal (se usa para RAG y Direct)
agent_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])


HISTORY_K = 6
#-------------------------------------------------------------------------

def router_node(state: AgentState):
    """Clasifica la intención del usuario basándose en el último mensaje."""
    last_message = state["messages"][-1].content
    route = classify_query(router_chain, last_message)
    return {"route": route}

def retrieve_node(state: AgentState):
    """Recupera documentos de ChromaDB si la ruta es 'rag'."""
    last_message = state["messages"][-1].content
    docs = retriever.invoke(last_message)
    return {"context": docs}

def generate_rag_node(state: AgentState):
    """Genera la respuesta utilizando el contexto recuperado."""
    context_str = "\n\n".join([doc.page_content for doc in state.get("context", [])])
    
    # Se toman los ultimo HISTORY_K mensajes para mantener el contexto reciente.
    recent_messages = state["messages"][-HISTORY_K:] if len(state["messages"]) > HISTORY_K else state["messages"]

    # Inyectamos el contexto dinámicamente en el prompt del sistema
    formatted_prompt = agent_prompt.partial(context=context_str)
    chain = formatted_prompt | llm
    
    response = chain.invoke({"messages": recent_messages})
    return {"messages": [response]}

def generate_direct_node(state: AgentState):
    """Genera la respuesta directa para saludos/charlas casuales."""
    recent_messages = state["messages"][-HISTORY_K:] if len(state["messages"]) > HISTORY_K else state["messages"]
    # Para interacciones directas, el contexto está vacío
    formatted_prompt = agent_prompt.partial(context="")
    chain = formatted_prompt | llm
    
    response = chain.invoke({"messages": recent_messages})
    return {"messages": [response]}

def block_node(state: AgentState):
    """Genera la respuesta estática de bloqueo."""
    from langchain_core.messages import AIMessage
    block_msg = AIMessage(content="Sólo puedo responder preguntas que sean estrictamente sobre la trayectoria de Nahuel Román y sus proyectos.")
    return {"messages": [block_msg]}

def route_decision(state: AgentState) -> str:
    """Retorna el nombre del siguiente nodo basado en la clasificación."""
    route = state.get("route")
    if route == "rag":
        return "retrieve"
    elif route == "direct":
        return "generate_direct"
    elif route == "block":
        return "block"
    # Fallback de seguridad
    return "block"