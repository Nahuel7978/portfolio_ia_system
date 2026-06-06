"""
chunking.py
Carga documentos desde la DB y aplica la estrategia de chunking
según el doc_type de cada documento.

Uso: python chunking.py
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_classic.schema import Document
from db_model.base import KnowledgeEntry, Document as DBDocument, KnowledgeEntryTechnology
from sqlalchemy.orm import joinedload

DB_URL = "sqlite:///./db_SQLite/knowledge.db"

# ── Constantes de chunking ────────────────────────────────────────────────────

SUMMARY_CHUNK_SIZE = 900        # tokens aprox para summaries y academic/extSracurricular
SUMMARY_CHUNK_OVERLAP = 0

TECHNICAL_CHUNK_SIZE = 450      # tokens aprox para informes técnicos
TECHNICAL_CHUNK_OVERLAP = 50    # ~11% de overlap

MARKDOWN_HEADERS = [
    ("#", "Header1"),
    ("##", "Header2"),
    ("###", "Header3"),
]

# doc_types que usan RecursiveCharacterTextSplitter
TECHNICAL_DOC_TYPES = {"technical_report", "dev_report", "design_decisions"}

# doc_types que usan MarkdownHeaderTextSplitter
SUMMARY_DOC_TYPES = {"summary", "academic_record", "work_experience", "extracurricular"}


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_document(file_path: str) -> list[Document]:
    path = Path(file_path)

    if not path.exists():
        print(f"  [WARN] Archivo no encontrado: {file_path}")
        return []

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        loader = PyPDFLoader(file_path)
        return loader.load()
    elif suffix == ".md":
        loader = UnstructuredMarkdownLoader(file_path)
        return loader.load()
    else:
        print(f"  [WARN] Extensión no soportada: {suffix} ({file_path})")
        return []


# ── Splitters ─────────────────────────────────────────────────────────────────

def get_splitter(doc_type: str):
    if doc_type in TECHNICAL_DOC_TYPES:
        return RecursiveCharacterTextSplitter(
            chunk_size=TECHNICAL_CHUNK_SIZE,
            chunk_overlap=TECHNICAL_CHUNK_OVERLAP,
            length_function=len,
        )
    else:
        return MarkdownHeaderTextSplitter(
            headers_to_split_on=MARKDOWN_HEADERS,
        )


# ── Pipeline principal ────────────────────────────────────────────────────────

def chunk_all_documents() -> list[Document]:
    engine = create_engine(DB_URL, echo=False)
    all_chunks = []

    with Session(engine) as session:
        entries = session.query(KnowledgeEntry).options(
            joinedload(KnowledgeEntry.technologies).joinedload(KnowledgeEntryTechnology.technology),
            joinedload(KnowledgeEntry.documents),
        ).all()

        for entry in entries:

            for db_doc in entry.documents:
                print(f"\n[Entry] {entry.name} | doc_type: {db_doc.doc_type}")
                print(f"  [Doc] {db_doc.document_name}")

                raw_docs = load_document(db_doc.file_path)
                if not raw_docs:
                    continue

                splitter = get_splitter(db_doc.doc_type)

                # MarkdownHeaderTextSplitter opera sobre string, no sobre Documents
                if db_doc.doc_type in SUMMARY_DOC_TYPES:
                    full_text = "\n\n".join(doc.page_content for doc in raw_docs)
                    chunks = splitter.split_text(full_text)
                else:
                    chunks = splitter.split_documents(raw_docs)

                tech_names = [ket.technology.name for ket in entry.technologies]
                tech_categories = [ket.technology.category for ket in entry.technologies]

                # Enriquecer cada chunk con metadatos de la DB
                for chunk in chunks:
                    chunk.metadata.update({
                        "entry_id": entry.id,
                        "entry_name": entry.name,
                        "doc_type": db_doc.doc_type,
                        "area": entry.area,
                        "area_secondary": entry.area_secondary,
                        "status": entry.status,
                        "technologies": ", ".join(tech_names),        # "Python, DQN, Webots"
                        "tech_categories": ", ".join(tech_categories),  # "Programming, ML, Robotics"       
                        "document_id": db_doc.id,
                        "document_name": db_doc.document_name,
                        "file_path": db_doc.file_path,
                        "technical_depth": db_doc.technical_depth,
                        "language": db_doc.language,
                        "importance": db_doc.importance,
                    })
                    metadata_header = f"[Contexto del fragmento -> Proyecto: {entry.name} | Área: {entry.area} | Tecnologías utilizadas: {', '.join(tech_names)}]\n"        
                    # Sobrescribes el contenido del chunk agregando la cabecera
                    chunk.page_content = metadata_header + chunk.page_content
                    
                all_chunks.extend(chunks)
                print(f"    → {len(chunks)} chunks generados")

    print(f"\n✓ Total chunks generados: {len(all_chunks)}")
    return all_chunks

def chunk_single_project(pk_entry: int) -> list[Document]:
    engine = create_engine(DB_URL, echo=False)
    chunks = []

    with Session(engine) as session:
        entry = session.query(KnowledgeEntry).options(
            joinedload(KnowledgeEntry.technologies).joinedload(KnowledgeEntryTechnology.technology),
            joinedload(KnowledgeEntry.documents),
        ).filter(KnowledgeEntry.id == pk_entry).first()
        
        if not entry:
            print(f"  [ERROR] No se encontró KnowledgeEntry con id={pk_entry}")
            return []

        print(f"\n[Entry] {entry.name} | doc_type: {entry.doc_type}")

        for db_doc in entry.documents:
            print(f"  [Doc] {db_doc.document_name}")

            raw_docs = load_document(db_doc.file_path)
            if not raw_docs:
                continue

            splitter = get_splitter(db_doc.doc_type)

            if db_doc.doc_type in SUMMARY_DOC_TYPES:
                full_text = "\n\n".join(doc.page_content for doc in raw_docs)
                doc_chunks = splitter.split_text(full_text)
            else:
                doc_chunks = splitter.split_documents(raw_docs)

            tech_names = [ket.technology.name for ket in entry.technologies]
            tech_categories = [ket.technology.category for ket in entry.technologies]

            for chunk in doc_chunks:
                chunk.metadata.update({
                    "entry_id": entry.id,
                    "entry_name": entry.name,
                    "doc_type": entry.doc_type,
                    "area": entry.area,
                    "area_secondary": entry.area_secondary,
                    "status": entry.status,
                    "technologies": ", ".join(tech_names),       
                    "tech_categories": ", ".join(tech_categories),
                    "document_id": db_doc.id,
                    "document_name": db_doc.document_name,
                    "file_path": db_doc.file_path,
                    "technical_depth": db_doc.technical_depth,
                    "language": db_doc.language,
                    "importance": db_doc.importance,
                })

            chunks.extend(doc_chunks)
            print(f"    → {len(doc_chunks)} chunks generados")

    print(f"\n✓ Total chunks generados para entry {pk_entry}: {len(chunks)}")
    return chunks


def chunk_single_document(pk_document: int) -> list[Document]:
    engine = create_engine(DB_URL, echo=False)
    chunks = []

    with Session(engine) as session:
        db_doc = session.get(DBDocument, pk_document)

        if not db_doc:
            print(f"  [ERROR] No se encontró Document con id={pk_document}")
            return []

        entry = session.query(KnowledgeEntry).options(
            joinedload(KnowledgeEntry.technologies).joinedload(KnowledgeEntryTechnology.technology),
        ).filter(KnowledgeEntry.id == db_doc.entry_id).first()
        
        print(f"\n[Doc] {db_doc.document_name} | entry: {entry.name}")

        raw_docs = load_document(db_doc.file_path)
        if not raw_docs:
            return []

        splitter = get_splitter(db_doc.doc_type)

        if db_doc.doc_type in SUMMARY_DOC_TYPES:
            full_text = "\n\n".join(doc.page_content for doc in raw_docs)
            chunks = splitter.split_text(full_text)
        else:
            chunks = splitter.split_documents(raw_docs)

        tech_names = [ket.technology.name for ket in entry.technologies]
        tech_categories = [ket.technology.category for ket in entry.technologies]

        for chunk in chunks:
            chunk.metadata.update({
                "entry_id": entry.id,
                "entry_name": entry.name,
                "doc_type": db_doc.doc_type,
                "area": entry.area,
                "area_secondary": entry.area_secondary,
                "status": entry.status,
                "technologies": ", ".join(tech_names),        # "Python, DQN, Webots"
                "tech_categories": ", ".join(tech_categories),
                "document_id": db_doc.id,
                "document_name": db_doc.document_name,
                "file_path": db_doc.file_path,
                "technical_depth": db_doc.technical_depth,
                "language": db_doc.language,
                "importance": db_doc.importance,
            })
            metadata_header = f"[Contexto del fragmento -> Proyecto: {entry.name} | Área: {entry.area} | Tecnologías utilizadas: {', '.join(tech_names)}]\n"        
            # Sobrescribes el contenido del chunk agregando la cabecera
            chunk.page_content = metadata_header + chunk.page_content

    print(f"✓ Total chunks generados para document {pk_document}: {len(chunks)}")
    return chunks


if __name__ == "__main__":
    chunks = chunk_all_documents()