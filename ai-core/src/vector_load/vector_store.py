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
from src.pre_process.chunking import chunk_all_documents, chunk_single_project, chunk_single_document

# ── Configuración ─────────────────────────────────────────────────────────────

CHROMA_PATH = "./chroma_db"
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

def build_vector_store() -> Chroma:
    print("── Cargando y chunkeando documentos ──")
    chunks = chunk_all_documents()

    if not chunks:
        raise ValueError("No se generaron chunks. Verificá los archivos y la DB.")

    print(f"\n── Inicializando ChromaDB en: {CHROMA_PATH} ──")
    embedding_fn = get_embedding_function()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_fn,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH,
        collection_metadata={"hnsw:space": "cosine"},
    )

    print(f"✓ {len(chunks)} chunks indexados en la colección '{COLLECTION_NAME}'.")
    return vector_store


def build_single_vector(pk_entry: int) -> None:
    print(f"── Procesando KnowledgeEntry id={pk_entry} ──")
    chunks = chunk_single_project(pk_entry)

    if not chunks:
        print(f"  [WARN] No se generaron chunks para entry {pk_entry}.")
        return

    vs = load_vector_store() #la colección ya existe en disco, solo se agregan los chunks nuevos
    vs.add_documents(chunks)
    print(f"✓ {len(chunks)} chunks indexados para entry {pk_entry}.")


def build_single_document(pk_document: int) -> None:
    print(f"── Procesando Document id={pk_document} ──")
    chunks = chunk_single_document(pk_document)

    if not chunks:
        print(f"  [WARN] No se generaron chunks para document {pk_document}.")
        return

    vs = load_vector_store() #la colección ya existe en disco, solo se agregan los chunks nuevos
    vs.add_documents(chunks)
    print(f"✓ {len(chunks)} chunks indexados para document {pk_document}.")

# ── Carga (sin re-indexar) ────────────────────────────────────────────────────

def load_vector_store() -> Chroma:
    embedding_fn = get_embedding_function()
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH,
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
    
    build_vector_store()  # Solo ejecutar la primera vez o cuando se agreguen muchos documentos nuevos
    #build_single_document(31)
    """
    vs = load_vector_store()

    # Test 1: ¿Están los chunks de esos proyectos en Chroma?
    results = vs.similarity_search(
        query="proyectos web realizados",
        k=20,
        filter={"area": "Web"}
    )
    print(f"Con filtro area=Web: {len(results)} resultados")
    for d in results:
        print(d.metadata.get("entry_name"), "|", d.page_content[:80])

    # Test 2: Sin filtro, ¿en qué posición aparecen?
    results_nf = vs.similarity_search(
        query="proyectos web realizados",
        k=20,
    )
    print("\nSin filtro, Top-20:")
    for i, d in enumerate(results_nf):
        print(i+1, d.metadata.get("entry_name"), "|", d.metadata.get("area"), "|", d.metadata.get("area_secondary"))
    """