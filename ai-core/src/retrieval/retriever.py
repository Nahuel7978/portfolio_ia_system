"""
retriever.py
Pipeline de búsqueda de alta precisión para el agente CV.

Flujo:
    MultiQueryRetriever (Top-10) → CohereRerank → Top-4 → LLM

Ubicación: src/retrieval/retriever.py
"""

import os
import logging as log
from dotenv import load_dotenv
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_core.retrievers import BaseRetriever

from langchain_cohere import CohereRerank
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma

from langchain_core.messages import HumanMessage
from src.vector_load.vector_store import load_vector_store
from langchain_core.documents import Document
from typing import Any
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────────────────────
load_dotenv()

TOP_K_RETRIEVER = 30   # Fragmentos que busca el MultiQueryRetriever
TOP_N_RERANKER  = 5    # Fragmentos que pasan al LLM tras el reranking
MAX_CHUNKS_PER_ENTRY = 1  # Para evitar que un solo proyecto con muchos documentos domine los resultados 
MAX_CHUNKS_TECHNICAL = 5  # Chunks a tomar si solo hay technical_report

DOC_TYPE_PRIORITY = [
    "summary",
    "design_decisions",
    "dev_report",
    "work_experience",
    "academic_record",
    "extracurricular",
    "technical_report",
]
VALID_AREAS = {
    "ai", "ml", "robotics", "nlp", "web", "programming",
    "computer vision", "data analytics", "education", "activity", "languages", "experience"
}

GPT_MODEL      = "meta-llama/llama-3.3-70b-instruct"
COHERE_MODEL    = "rerank-multilingual-v3.0"  # Soporta español
                        
#log.basicConfig(level=log.DEBUG)

# ── LLM para MultiQueryRetriever ──────────────────────────────────────────────

def _get_query_llm() -> ChatOpenAI:
    #LLM liviano usado SOLO para generar variaciones de la pregunta.
    #No es el LLM que responde al usuario final.
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No se encontró OPENROUTER_API_KEY en las variables de entorno.\n"
            "Asegurate de tener un archivo .env con: OPENROUTER_API_KEY=tu_key"
        )
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model=GPT_MODEL,
        temperature=0,
    )
    
def load_prompt(filename: str) -> str:
    """Lee un prompt desde un archivo físico en la carpeta agent/prompts."""
    base_dir = Path(__file__).resolve().parent.parent / "agent" / "prompts"
    prompt_path = base_dir / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def _extract_technology(query: str, llm: ChatOpenAI) -> str | None:
    raw_prompt = load_prompt("tech_prompt.txt")
    prompt = raw_prompt.format(query=query)
    response = llm.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()
    return None if result == "NONE" else str.lower(result)

def _extract_area(query: str, llm: ChatOpenAI) -> str | None:
    areas_list = ", ".join(VALID_AREAS)
    raw_prompt = load_prompt("area_prompt.txt")
    prompt = raw_prompt.format(areas_list=areas_list, query=query)
    response = llm.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()
    return None if result.upper() == "NONE" else result

#-- Busqueda de entry_ids por tecnología y por área ─────────────────────────────────────────────────
def _get_entry_ids_by_technology(tech_name: str, vector_store: Chroma) -> list[int]:
    """Consulta ChromaDB para obtener entry_ids que contengan la tecnología."""
    results = vector_store.get(
        where={"technologies": {"$contains": tech_name}},
        include=["metadatas"]
    )
    if not results or not results["metadatas"]:
        return []
    # Usamos set() para eliminar duplicados
    return list(set(meta.get("entry_id") for meta in results["metadatas"] if meta.get("entry_id") is not None))

def _get_entry_ids_by_area(area_name: str, vector_store: Chroma) -> list[int]:
    """Consulta ChromaDB para obtener entry_ids por área primaria o secundaria."""
    results = vector_store.get(
        where={
            "$or": [
                {"area": area_name},
                {"area_secondary": area_name}
            ]
        },
        include=["metadatas"]
    )
    if not results or not results["metadatas"]:
        return []
    return list(set(meta.get("entry_id") for meta in results["metadatas"] if meta.get("entry_id") is not None))

#-- Diversificación y recuperación de documentos padre (entry_id) ──────────────────────────────────────────────

def _diversify_by_entry(docs: list, max_per_entry: int = MAX_CHUNKS_PER_ENTRY) -> list:
    seen: dict = {}
    result = []
    for doc in docs:
        entry_id = doc.metadata.get("entry_id")
        if entry_id is None: # Si no tiene ID, lo dejamos pasar o lo descartamos
            result.append(doc)
            continue
        
        count = seen.get(entry_id, 0)
        if count < max_per_entry:
            result.append(doc)
            seen[entry_id] = count + 1
    return result

def _fetch_parent_docs(docs: list, vector_store: Chroma) -> list:
    """
    Conserva los chunks originales y los enriquece añadiendo sus documentos padre 
    aplicando un truncado de seguridad para evitar límites de TPM en Groq.
    """
    # ── Configuración de Truncado ─────────────────────────────────────────────
    # 2000 caracteres son aprox. 500 tokens. Con 10 docs + 10 padres = ~10k tokens.
    MAX_TEXT_CHARS = 2000 
    
    unique_entry_ids = list(set(doc.metadata.get("entry_id") for doc in docs if doc.metadata.get("entry_id") is not None))
    
    if not unique_entry_ids:
        return docs

    # 1. Consulta masiva a Chroma (se mantiene igual)
    parent_types = DOC_TYPE_PRIORITY[:-1] 
    
    all_candidates = vector_store.get(
        where={
            "$and": [
                {"entry_id": {"$in": unique_entry_ids}},
                {"doc_type": {"$in": parent_types}}
            ]
        }
    )

    # Organizar padres (se mantiene igual)
    parent_map = {}
    for i in range(len(all_candidates["ids"])):
        eid = all_candidates["metadatas"][i]["entry_id"]
        if eid not in parent_map:
            parent_map[eid] = []
        parent_map[eid].append(Document(
            page_content=all_candidates["documents"][i],
            metadata=all_candidates["metadatas"][i]
        ))

    # 2. MODIFICACIÓN: Truncar los chunks originales de alta similitud
    enriched_results = []
    for d in docs:
        # Aplicamos truncado preventivo al contenido original
        d.page_content = d.page_content[:MAX_TEXT_CHARS]
        enriched_results.append(d)
        
    added_parents = set()

    # 3. MODIFICACIÓN: Truncar el documento padre antes de añadirlo
    for eid in unique_entry_ids:
        project_parents = parent_map.get(eid, [])
        
        for priority_type in parent_types:
            best_doc = next((d for d in project_parents if d.metadata.get("doc_type") == priority_type), None)
            if best_doc:
                # Truncamos el documento padre (ej. el summary)
                best_doc.page_content = best_doc.page_content[:MAX_TEXT_CHARS]
                
                doc_content_hash = hash(best_doc.page_content[:100])
                if doc_content_hash not in added_parents:
                    enriched_results.append(best_doc)
                    added_parents.add(doc_content_hash)
                break 

    return enriched_results
class DiversifiedRetriever(BaseRetriever):
    base_retriever: BaseRetriever
    max_per_entry: int = MAX_CHUNKS_PER_ENTRY
    vector_store: Any
    llm: Any

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None) -> List[Document]:
        combined_docs = []
        
        # 1. Búsqueda libre vectorial SIEMPRE se ejecuta
        vector_docs = self.base_retriever._get_relevant_documents(query, run_manager=run_manager)
        combined_docs.extend(vector_docs)

        # 2. Evaluación de filtros SQL (Soft Filters)
        tech = _extract_technology(query, self.llm)
        print("🔍 Tecnología detectada:", tech)
        if tech:
            entry_ids = _get_entry_ids_by_technology(tech, self.vector_store)
            if entry_ids:
                combined_docs.extend([Document(page_content="", metadata={"entry_id": eid}) for eid in entry_ids])
        else:
            # Solo evaluamos área si no hay tecnología específica
            area = _extract_area(query, self.llm)
            print("🔍 Área detectada:", area)
            if area:
                entry_ids = _get_entry_ids_by_area(area, self.vector_store)
                if entry_ids:
                    combined_docs.extend([Document(page_content="", metadata={"entry_id": eid}) for eid in entry_ids])

        # 3. Diversificación y Enriquecimiento
        diversified = _diversify_by_entry(combined_docs, self.max_per_entry)
        return _fetch_parent_docs(diversified, self.vector_store)

    async def _aget_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None) -> List[Document]:
        combined_docs = []
        
        # 1. Búsqueda libre vectorial SIEMPRE se ejecuta
        # Nota: Asumiendo que base_retriever soporta async
        if hasattr(self.base_retriever, "_aget_relevant_documents"):
            vector_docs = await self.base_retriever._aget_relevant_documents(query, run_manager=run_manager)
        else:
            vector_docs = self.base_retriever._get_relevant_documents(query, run_manager=run_manager)
        combined_docs.extend(vector_docs)

        # 2. Evaluación de filtros SQL (Soft Filters)
        tech = _extract_technology(query, self.llm)
        print("🔍 Tecnología detectada:", tech)
        if tech:
            entry_ids = _get_entry_ids_by_technology(tech, self.vector_store)
            if entry_ids:
                combined_docs.extend([Document(page_content="", metadata={"entry_id": eid}) for eid in entry_ids])
        else:
            area = _extract_area(query, self.llm)
            print("🔍 Área detectada:", area)
            if area:
                entry_ids = _get_entry_ids_by_area(area, self.vector_store)
                if entry_ids:
                    combined_docs.extend([Document(page_content="", metadata={"entry_id": eid}) for eid in entry_ids])
            
        # 3. Diversificación y Enriquecimiento
        diversified = _diversify_by_entry(combined_docs, self.max_per_entry)
        return _fetch_parent_docs(diversified, self.vector_store)
    
# ── Pipeline principal ────────────────────────────────────────────────────────

def build_retriever() -> ContextualCompressionRetriever:
    load_dotenv()
    vector_store = load_vector_store()
    llm = _get_query_llm()
    print("✓ LLM para query generation listo:", GPT_MODEL)

    # Detectar si la pregunta menciona una tecnología específica
    # Se pasa el llm al DiversifiedRetriever para usarlo en el invoke
    base_retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K_RETRIEVER},
    )

    reranker = CohereRerank(
        model=COHERE_MODEL,
        top_n=TOP_N_RERANKER,
        cohere_api_key=os.getenv("COHERE_API_KEY"),
    )

    diversified_retriever = DiversifiedRetriever(
        base_retriever=base_retriever,
        vector_store=vector_store,
        llm=llm,
    )

    pipeline = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=diversified_retriever,
    )
    return pipeline


if __name__ == "__main__":
    retriever = build_retriever()
    docs = retriever.invoke("¿agente noticias veribot?")
    print(f"Total docs al LLM: {len(docs)}")
    for d in docs:
        print(d.metadata.get("entry_name"), "|", d.metadata, "|", d.page_content[:120])
