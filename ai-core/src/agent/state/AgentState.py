from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.documents import Document

class AgentState(TypedDict):
    # add_messages asegura que los nuevos mensajes se concatenen al historial
    messages: Annotated[Sequence[BaseMessage], add_messages]
    route: str
    context: list[Document]