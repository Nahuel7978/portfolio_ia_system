"""
chunking.py
Carga documentos desde la DB y aplica la estrategia de chunking
según el doc_type de cada documento.

Uso: python chunking.py
"""

from pathlib import Path
from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_classic.schema import Document

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

def chunk_incoming_file(file_path: str, metadata: dict) -> list[Document]:
    """
    Carga el archivo físico usando LangChain, realiza el split y adjunta los metadatos.
    """
    doc_type = metadata.get("doc_type", "summary")
    splitter = get_splitter(doc_type)

    raw_docs = load_document(file_path)
    if not raw_docs:
        raise ValueError(f"No se pudo extraer texto del archivo: {file_path}")

    if doc_type in SUMMARY_DOC_TYPES:
        full_text = "\n\n".join(doc.page_content for doc in raw_docs)
        chunks = splitter.split_text(full_text)
    else:
        chunks = splitter.split_documents(raw_docs)

    techs = str.lower(metadata.get("technologies", ""))
    area = str.lower(metadata.get("area", ""))
    entry_name = str.lower(metadata.get("entry_name", ""))
    area_secondary = metadata.get("area_secondary", "")
    if(area_secondary!=None):
        area_secondary = str.lower(area_secondary)

    for chunk in chunks:
        chunk.metadata.update(metadata)
        metadata_header = f"[Fragment Context -> Project: {entry_name} | Area: {area} | Area Sencondary: {area_secondary} | Technologies: {techs}]\n"
        chunk.page_content = metadata_header + chunk.page_content

    return chunks


#if __name__ == "__main__":
    #chunks = chunk_all_documents()
