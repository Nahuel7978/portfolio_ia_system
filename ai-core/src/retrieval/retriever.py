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
from langchain_groq import ChatGroq
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma

from langchain_core.messages import HumanMessage
from src.vector_load.vector_store import load_vector_store
from langchain_core.documents import Document
from typing import Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

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
    "computer vision", "data analytics", "education", "activity", "languages"
}

GROQ_MODEL      = "llama-3.3-70b-versatile"
COHERE_MODEL    = "rerank-multilingual-v3.0"  # Soporta español
DB_URL = "sqlite:///./db_SQLite/knowledge.db"
                        
#log.basicConfig(level=log.DEBUG)

# ── LLM para MultiQueryRetriever ──────────────────────────────────────────────

def _get_query_llm() -> ChatGroq:
    #LLM liviano usado SOLO para generar variaciones de la pregunta.
    #No es el LLM que responde al usuario final.
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No se encontró GROQ_API_KEY en las variables de entorno.\n"
            "Asegurate de tener un archivo .env con: GROQ_API_KEY=tu_key"
        )
    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
        api_key=api_key,
    )
    
#-- Extracción de tecnología o area mencionada en la pregunta ─────────────────────────────────────────────    
def _extract_technology(query: str, llm: ChatGroq) -> str | None:
    """
    Usa el LLM para detectar si la pregunta menciona una tecnología específica.
    Devuelve el nombre exacto de la tecnología o None si no hay ninguna.
    """
    prompt = f"""Tu tarea es detectar si la consulta del usuario menciona UNA tecnología específica.

            DEFINICIÓN DE TECNOLOGÍA VÁLIDA:
            Solo considera tecnologías de alguno de estos tipos:
            - Lenguajes de programación
            - Frameworks
            - Librerías
            - Herramientas de desarrollo
            - Plataformas cloud
            - Infraestructura
            - Bases de datos
            - APIs
            - Algoritmos
            - Modelos de IA/ML
            - Protocolos
            - Motores
            - Tecnologías web

            REGLAS:
            1. Responde ÚNICAMENTE con:
            - el nombre exacto de la tecnología en inglés
            - o NONE
            2. No agregues explicaciones, puntuación ni texto adicional.
            3. Si aparecen múltiples tecnologías:
                - responde la más relevante para la intención principal de la consulta
                - si no existe una claramente principal, responde la primera tecnología explícitamente mencionada
            4. Si la consulta es general y no menciona claramente una tecnología específica, responde: NONE
            5. Usa inferencia semántica y reconoce variaciones de escritura.
            6. La consulta puede venir en español, inglés o mezclando ambos idiomas.
            7. La consulta puede venir en cualquier idioma.
            8. Debes detectar tecnologías independientemente del idioma utilizado por el usuario.
            9. La respuesta SIEMPRE debe estar normalizada al nombre oficial o más común de la tecnología en inglés.
            10. Si la tecnología aparece traducida, transliterada o abreviada, conviértela a su nombre estándar en inglés.

            IMPORTANTE:
            NO consideres como tecnologías:
            - empresas
            - marcas
            - universidades
            - personas
            - equipos
            - productos genéricos
            - áreas temáticas
            - conceptos abstractos

            Ejemplos que deben responder NONE:
            - NVIDIA
            - Google
            - OpenAI
            - Microsoft
            - UNICEN
            - NeuroAI Lab
            - inteligencia artificial
            - machine learning
            - backend
            - frontend

            EXCEPCIÓN:
            Si el nombre de una empresa o marca aparece como referencia explícita a una tecnología concreta, sí debes detectarla.

            Ejemplos válidos:
            - AWS
            - Azure
            - GPT-4
            - TensorFlow
            - PyTorch
            - CUDA

            MAPEO SEMÁNTICO Y NORMALIZACIÓN:
            - reactjs → React
            - react.js → React
            - node → Node.js
            - tf → TensorFlow
            - js → JavaScript
            - py → Python
            - postgres → PostgreSQL
            - pytorch lightning → PyTorch Lightning
            - scikit learn → scikit-learn
            - open cv → OpenCV
            - docker compose → Docker Compose
            - k8s → Kubernetes
            - vue → Vue.js
            - next → Next.js
            - nest → NestJS

            EJEMPLOS:

            Pregunta: "¿Ha utilizado React en algún proyecto?"
            Respuesta: React

            Pregunta: "Dentro del proyecto Simulation Control App se utilizó el algoritmo DQN?"
            Respuesta: DQN

            Pregunta: "¿Tiene experiencia con FastAPI?"
            Respuesta: FastAPI

            Pregunta: "¿Qué aprendió en el workshop de Nvidia?"
            Respuesta: NONE

            Pregunta: "¿Trabajó con cloud computing?"
            Respuesta: NONE

            Pregunta: "¿Usó AWS para desplegar modelos?"
            Respuesta: AWS

            Pregunta: "Does he use TensorFlow or PyTorch?"
            Respuesta: TensorFlow

            Pregunta: "¿Tiene experiencia en backend?"
            Respuesta: NONE

            Pregunta: "Has he used redes neuronales convolucionales con TensorFlow?"
            Respuesta: TensorFlow

            Pregunta: "¿Trabajó con visión artificial usando OpenCV?"
            Respuesta: OpenCV

            Pregunta: "Utilizou Python em projetos de IA?"
            Respuesta: Python

            Pregunta: "A-t-il utilisé Docker pour le déploiement ?"
            Respuesta: Docker

            Pregunta: "Did he develop APIs with FastAPI?"
            Respuesta: FastAPI

            Pregunta del usuario:
            {query}

            Respuesta:"""
    response = llm.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()
    return None if result == "NONE" else result

def _extract_area(query: str, llm: ChatGroq) -> str | None:
    """
    Detecta si la pregunta hace referencia a un área temática conocida.
    Solo se invoca cuando no se detectó tecnología específica.
    Devuelve el nombre del área en el formato exacto de la BD o None.
    """
    from langchain_core.messages import HumanMessage
    areas_list = ", ".join(VALID_AREAS)
    prompt = f"""Tu tarea es clasificar la consulta del usuario en UNA única área temática.

                ÁREAS VÁLIDAS:
                {areas_list}

                REGLAS:
                1. Responde ÚNICAMENTE con:
                - el nombre exacto de una de las áreas válidas
                - o NONE
                2. No agregues explicaciones, puntuación, comentarios ni texto adicional.
                3. La clasificación debe basarse en la intención principal de la consulta.
                4. Si la consulta menciona múltiples áreas, elige la más relevante.
                5. Si la consulta es general y no se relaciona claramente con un área específica, responde:
                NONE
                6. Usa inferencia semántica y sinónimos.
                7. Considera variaciones lingüísticas, términos técnicos y lenguaje informal.
                8. La consulta puede venir en español, inglés o mezclando ambos idiomas.
                9. Debes detectar equivalencias semánticas independientemente del idioma utilizado.
                10. Si una consulta contiene términos técnicos en inglés, clasifícala igualmente usando las áreas válidas.


                MAPEO SEMÁNTICO IMPORTANTE:

                - education:
                cursos, curso, capacitación, capacitaciones, formación, estudios, universidad,
                carrera, certificaciones, certificación, aprendizaje, materias, educación,
                entrenamiento, bootcamp, diplomatura, workshop, talleres, courses, course, training,
                education, studies, degree, university,certifications, certification, learning, 
                bootcamp, workshops, academic background

                - ai:
                inteligencia artificial, ia, agentes inteligentes, llm, modelos generativos,
                ai agents, genai, artificial intelligence, deep learning, redes neuronales, 
                deep reinforcement learning,  artificial intelligence, intelligent agents, generative ai,
                genai, llm, large language models

                - ml:
                machine learning, aprendizaje automático, reinforcement learning, predictive models

                - robotics:
                robots, robótica, automatización física, sistemas autónomos,  autonomous systems, automation

                - nlp:
                procesamiento de lenguaje natural, lenguaje natural, chatbots,
                transformers, embeddings, texto,  natural language processing, nlp, 
                chatbots, transformers, embeddings, text processing

                - web:
                frontend, backend, full stack, react, fastapi, api, web app, sitio web,
                web development, web application

                - programming:
                programación, algoritmos, código, coding, software development,
                python, java, c++, javascript, programming, coding, software engineering,
                software development, algorithms

                - computer vision:
                visión por computadora, computer vision, imágenes, detección,
                segmentación, video, reconocimiento visual, image processing, object detection,
                segmentation, video analysis, visual recognition  

                - data analytics:
                análisis de datos, dashboards, métricas, business intelligence,
                visualización de datos, analytics, data analytics, data analysis, dashboards,
                business intelligence, data visualization

                - activity:
                actividades, voluntariado, eventos, participación, mentorías,
                comunidades, activities, volunteering, events, mentoring,
                communities, community participation


                - languages:
                idiomas, inglés, español, language skills, nivel de inglés,
                languages, english, spanish, language skills, fluency, proficiency

                EJEMPLOS:

                Pregunta: "¿Qué cursos realizó Nahuel?"
                Respuesta: education

                Pregunta: "¿Tiene experiencia en redes neuronales?"
                Respuesta: ml

                Pregunta: "¿Qué proyectos hizo con agentes inteligentes?"
                Respuesta: ai

                Pregunta: "¿Participó en comunidades o eventos?"
                Respuesta: activity

                Pregunta: "¿Cuál es su experiencia laboral?"
                Respuesta: NONE

                Pregunta: "¿Habla inglés?"
                Respuesta: languages

                Pregunta: "What courses has Nahuel completed?"
                Respuesta: education

                Pregunta: "Does he have experience with neural networks?"
                Respuesta: ml

                Pregunta: "Tell me about his AI projects"
                Respuesta: ai

                Pregunta del usuario:
                {query}

                Respuesta:"""
    response = llm.invoke([HumanMessage(content=prompt)])
    result = response.content.strip()
    return None if result.upper() == "NONE" else result
#-- Busqueda de entry_ids por tecnología y por área ─────────────────────────────────────────────────
def _get_entry_ids_by_technology(tech_name: str) -> list[int]:
    """
    Consulta SQLite para obtener entry_ids que usan una tecnología específica.
    Búsqueda case-insensitive por nombre de tecnología.
    """
    engine = create_engine(DB_URL, echo=False)
    with Session(engine) as session:
        rows = session.execute(
            text("""
                SELECT ket.entry_id
                FROM knowledge_entry_technologies ket
                JOIN technologies t ON ket.technology_id = t.id
                WHERE LOWER(t.name) = LOWER(:tech_name)
            """),
            {"tech_name": tech_name}
        ).fetchall()
    return [row[0] for row in rows]

def _get_entry_ids_by_area(area_name: str) -> list[int]:
    """
    Consulta SQLite para obtener entry_ids cuya área primaria o secundaria
    coincida con el área detectada. Case-insensitive.
    """
    engine = create_engine(DB_URL, echo=False)
    with Session(engine) as session:
        rows = session.execute(
            text("""
                SELECT id FROM knowledge_entries
                WHERE LOWER(area) = LOWER(:area_name)
                   OR LOWER(area_secondary) = LOWER(:area_name)
            """),
            {"area_name": area_name}
        ).fetchall()
    return [row[0] for row in rows]

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
            entry_ids = _get_entry_ids_by_technology(tech)
            if entry_ids:
                combined_docs.extend([Document(page_content="", metadata={"entry_id": eid}) for eid in entry_ids])
        else:
            # Solo evaluamos área si no hay tecnología específica
            area = _extract_area(query, self.llm)
            print("🔍 Área detectada:", area)
            if area:
                entry_ids = _get_entry_ids_by_area(area)
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
            entry_ids = _get_entry_ids_by_technology(tech)
            if entry_ids:
                combined_docs.extend([Document(page_content="", metadata={"entry_id": eid}) for eid in entry_ids])
        else:
            area = _extract_area(query, self.llm)
            print("🔍 Área detectada:", area)
            if area:
                entry_ids = _get_entry_ids_by_area(area)
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
    print("✓ LLM para query generation listo:", GROQ_MODEL)

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
    docs = retriever.invoke("¿Qué tecnologías se usó para desarrollar la plataforma de entrenamiento?")
    print(f"Total docs al LLM: {len(docs)}")
    for d in docs:
        print(d.metadata.get("entry_name"), "|", d.metadata.get("doc_type"), "|", d.page_content[:120])