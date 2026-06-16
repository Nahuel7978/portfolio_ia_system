"""
vector_store.py
Configura ChromaDB, genera embeddings con MiniLM e indexa
todos los chunks producidos por chunking.py.

Uso: python vector_store.py
"""

import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# ── Configuración ─────────────────────────────────────────────────────────────
COLLECTION_NAME = "knowledge_base"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

load_dotenv()
# ── Embeddings ────────────────────────────────────────────────────────────────

def get_embedding_function() -> HuggingFaceEndpointEmbeddings:
    return HuggingFaceEndpointEmbeddings(
        huggingfacehub_api_token=os.getenv("HF_API_KEY"),
        model=EMBEDDING_MODEL,
    )


# ── Ingesta ───────────────────────────────────────────────────────────────────

def upsert_documents(chunks: list[Document]) -> None:
    """
    Recibe los chunks procesados en el endpoint HTTP y los persiste en ChromaDB.
    """
    if not chunks:
        print("  [WARN] No hay chunks para insertar.")
        return

    vs = load_vector_store() # Tu función actual que usa chromadb.HttpClient
    vs.add_documents(chunks)
    print(f"✓ {len(chunks)} chunks indexados en ChromaDB vía HTTP.")


# ── Eliminación ───────────────────────────────────────────────────────────────────
def delete_document_chunks(document_id: int) -> None:
    """
    Elimina todos los fragmentos asociados a un document_id específico.
    Utiliza el motor nativo de ChromaDB para filtrar por metadata.
    """
    vs = load_vector_store()
    try:
        # Accedemos a la colección nativa subyacente de ChromaDB
        vs._collection.delete(where={"document_id": document_id})
        print(f"🗑️ [ChromaDB] Chunks del documento {document_id} purgados.")
    except Exception as e:
        print(f"⚠️ [ChromaDB] Error al purgar documento {document_id}: {e}")
# ── Carga (sin re-indexar) ────────────────────────────────────────────────────

def load_vector_store() -> Chroma:
    # Usamos db-chroma que es el nombre del contenedor en la red de Docker
    chroma_host = os.getenv("CHROMA_HOST", "db-chroma")
    chroma_port = int(os.getenv("CHROMA_PORT", 8000))
    
    http_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    embedding_fn = get_embedding_function()
    return Chroma(
        client=http_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )


# ── Validación ────────────────────────────────────────────────────────────────

def validate_retrieval(vector_store: Chroma) -> None:
    print("\n── Validación de retrieval ──")

    test_cases = [
        {
            "query": "detalles técnicos de la tesis de robótica",
            "filter": {"doc_type": "technical_report"},
            "description": "Informe técnico - tesis",
        },
        {
            "query": "proyectos de visión por computadora",
            "filter": {"area": "Computer Vision"},
            "description": "Filtro por área Computer Vision",
        },
        {
            "query": "experiencia laboral en NeuroIA Lab",
            "filter": {"doc_type": "work_experience"},
            "description": "Filtro por work_experience",
        },
    ]

    for case in test_cases:
        print(f"\n  [Test] {case['description']}")
        results = vector_store.similarity_search(
            query=case["query"],
            k=3,
            filter=case["filter"],
        )
        print(f"  → {len(results)} resultados recuperados")
        for i, doc in enumerate(results):
            print(
                f"    {i+1}. {doc.metadata.get('entry_name')} | "
                f"{doc.metadata.get('document_name')} | "
                f"depth: {doc.metadata.get('technical_depth')}"
            )


if __name__ == "__main__":
    
    vs = load_vector_store()

    # Test 1: ¿Están los chunks de esos proyectos en Chroma?
    results = vs.similarity_search(
        query="Veribot is a",
        k=20,
        filter={"area": "ai"}
    )
    print(f"Con filtro area=ai: {len(results)} resultados")
    for d in results:
        print(d.metadata.get("entry_name"), "|", d.page_content[:80])

    # Test 2: Sin filtro, ¿en qué posición aparecen?
    results_nf = vs.similarity_search(
        query="VeriBot is a ",
        k=20,
    )
    print("\nSin filtro, Top-20:")
    for i, d in enumerate(results_nf):
        print(i+1, d.metadata.get("entry_name"), "|", d.metadata.get("area"), "|", d.metadata.get("area_secondary"))
    
