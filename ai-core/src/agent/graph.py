from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.agent.state.AgentState import AgentState
from src.agent.nodes.nodes import ( router_node, retrieve_node, generate_rag_node, generate_direct_node, block_node, route_decision )

def _build_cv_graph():
    # 1. Inicializar el Grafo
    workflow = StateGraph(AgentState)

    # 2. Añadir Nodos
    workflow.add_node("router", router_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate_rag", generate_rag_node)
    workflow.add_node("generate_direct", generate_direct_node)
    workflow.add_node("block", block_node)

    # 3. Definir el flujo (Aristas)
    workflow.add_edge(START, "router")
    
    # La arista condicional después del router
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "retrieve": "retrieve",
            "generate_direct": "generate_direct",
            "block": "block"
        }
    )

    # Conectar los nodos de generación al final
    workflow.add_edge("retrieve", "generate_rag")
    workflow.add_edge("generate_rag", END)
    workflow.add_edge("generate_direct", END)
    workflow.add_edge("block", END)

    # 4. Compilar con memoria en RAM
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

cv_agent_app = _build_cv_graph()