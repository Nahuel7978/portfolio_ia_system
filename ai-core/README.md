# AI Core - CV BOT: Vector Engine and Conversational Agent (RAG)
This is a microservice responsible for managing a Conversational Artificial Intelligence Agent. Its purpose is not to generate generic text, but to act as a highly accurate representative of the technical profile, answering queries based *strictly* on the portfolio, experience, and published articles.

To achieve fast, secure, and hallucination-free answers, this service implements an advanced **Recovery Augmented Generation (RAG)** system that is completely decoupled from traditional relational databases.


![AI Core Architecture](https://drive.google.com/thumbnail?id=1tZu5agECbDPYaZ0egWUhsD69LsS2aiXK&sz=w900)

*Figure 1: Internal architecture of the Artificial Intelligence microservice.*

---

## Technologies and Architectural Decisions

The service is built in **Python 3.10+** using **FastAPI** for its high performance and native asynchronous support. The cognitive orchestrator is **LangChain**.

**Key Decision**
**ChromaDB runs independently as an HTTP server.** All filtering and semantic searching occurs directly in the vector space, eliminating the reliance on relational databases in the AI ​​layer.

---

## API and Security Contracts

The microservice exposes two strictly separate communication channels to protect the LLM API consumption:

### 1. Internal Route: Ingest Pipeline (Document ETL)
When the administrator uploads a new project to the Web Core, the system sends the Markdown files to the AI ​​Core.

* **Endpoint:** `POST /internal/documents/upsert`
* **Security:** Protected by a symmetric key shared between containers (`X-Internal-Secret`). Not accessible from the internet.

* **Process:** The API processes the file, applies chunking algorithms, dynamically injects category and technology metadata into each fragment, and stores them in ChromaDB.

### 2. Public Channel: The Secured Chat Agent
To prevent denial-of-service (DoS) attacks or automated abuse that exhausts the LLM quota, the public chat requires a two-step mechanism:
* **Token Generation (`GET /api/auth/chat-token`):** Applies strict Rate Limiting per IP using **SlowAPI**. If the request is valid, it issues an **ephemeral JWT** containing a cryptographically embedded, unique `session_id`.

* **Chat Streaming (`POST /api/chat`):** Validates the JWT and establishes a *Server-Sent Events (SSE)* connection with Angular, transmitting the AI ​​response token by token for a seamless experience.

---

## Intelligent Routing: The Router Agent

Before a query reaches the vector search engine or the generative language model, it passes through a validation and classification layer known as the **Router Agent**.

This component acts as a "traffic light" that analyzes the user's intent and classifies the query into three strict categories. This optimizes response times, reduces API costs, and protects the system:

1. **Direct:** If the query is a greeting, a social interaction, or a question that can be answered without consulting information or searching documents, the router routes it directly to the response agent. The agent generates the message based solely on the information in its system prompt, avoiding the cost of a vector search.

2. **Retrieval:** If the query requires specific knowledge about my background, experience, training, or projects, the router activates the retrieval pipeline in the knowledge base.

3. **Block:** If the system detects malicious intent (prompt injection), queries about prohibited topics, policy violations, or any request outside the scope of my professional duties, the query is intercepted. The system aborts the call to the LLM and returns an automated response. The original message and the blocking action are recorded in the session history.

---

## The Advanced Retrieval Pipeline (Advanced RAG)

When the Router Agent classifies a query as a **RAG**, our three-phase retrieval pipeline is activated. A **Retrieval combination** is used:

1. **Base Retrieval:** A similarity search is performed.
2. **Diversified Retrieval:**

- _Extract Technology_: The query passes through an agent that determines if a specific technology was searched for and returns that technology.

- _Extract Area_: The query passes through an agent that determines if a specific area was searched for and returns that area.

- First, it is verified whether the query is about a specific technology, a specific area, or is a 'free' question.

- If it contains a technology or area, a new vector search is performed, filtered by the metadata containing the detected technology or area.

- To prevent a massive or highly detailed project from monopolizing all the search results, the algorithm groups the returned fragments and forces a diversified selection, ensuring that the LLM receives a rich context from multiple experiences.

3. **Reranking:** The diversified fragments are re-evaluated and semantically reordered in relation to the original question, delivering to the LLM only the most accurate and context-rich fragments.

---

## Session Generation and Memory Management

The Generator Agent receives the final fragments and drafts the response. To maintain a coherent conversation without saturating the LLM context window, an Internal Session Manager was developed:

* The `session_id` injected into the user's JWT links their messages to the Python server's RAM.

* Strict Limit: A maximum of 5 interactions (questions/answers) are retained per session.

* Asynchronous Garbage Collector: A background task constantly sweeps memory, removing inactive or expired sessions, ensuring that the Docker container never suffers memory leaks.

---

## Continuous Quality Assessment (LangSmith)

An AI agent in production must be tested and evaluated; for this reason, **LangSmith** was integrated into the `evals/` directory.

Through these evaluation scripts and smoke tests, the model's latency, token consumption, and, most importantly, the deviation of responses to changes in the System Prompt are continuously monitored, ensuring that the agent always responds with the required professional tone and without any apparent issues.


---
# Spanish Version
---

# AI Core - CV BOT: Motor Vectorial y Agente Conversacional (RAG)

Este es un microservicio encargado de manejar a un Agente de Inteligencia Artificial Conversacional. Su propósito no es generar texto genérico, sino actuar como un representante altamente preciso del perfil técnico, respondiendo consultas basándose *estrictamente* en el portafolio, experiencia y artículos publicados.

Para lograr respuestas rápidas, seguras y libres de alucinaciones, este servicio implementa un sistema avanzado de **Generación Aumentada por Recuperación (RAG)** totalmente desacoplado de las bases de datos relacionales tradicionales.


![AI Core Architecture](https://drive.google.com/thumbnail?id=1tZu5agECbDPYaZ0egWUhsD69LsS2aiXK&sz=w900)

*Figura 1: Arquitectura interna del microservicio de Inteligencia Artificial.*

---

## Tecnologías y Decisiones Arquitectónicas

El servicio está construido en **Python 3.10+** utilizando **FastAPI** por su alto rendimiento y soporte asíncrono nativo. El orquestador cognitivo es **LangChain**.

**Decisión Clave**
**ChromaDB se ejecuta de forma independiente como un servidor HTTP**. Todo el filtrado y búsqueda semántica ocurre directamente en el espacio vectorial, eliminando la dependencia de bases de datos relacionales en la capa de IA.

---

## API y Contratos de Seguridad

El microservicio expone dos vías de comunicación estrictamente separadas para proteger el consumo de la API del LLM:

### 1. Vía Interna: Pipeline de Ingesta (ETL Documental)
Cuando el administrador sube un nuevo proyecto en el Web Core, el sistema envía los archivos Markdown hacia el AI Core.
* **Endpoint:** `POST /internal/documents/upsert`
* **Seguridad:** Protegido por una clave simétrica compartida entre contenedores (`X-Internal-Secret`). No accesible desde internet.
* **Proceso:** La API procesa el archivo, aplica algoritmos de *Chunking*, inyecta dinámicamente los metadatos de categoría y tecnología en cada fragmento, y los almacena en ChromaDB.

### 2. Vía Pública: El Agente de Chat Segurizado
Para evitar ataques de denegación de servicio (DoS) o abusos automatizados que agoten la cuota del LLM, el chat público exige un mecanismo de dos pasos:
* **Generación de Token (`GET /api/auth/chat-token`):** Aplica un Rate Limiting estricto por IP mediante **SlowAPI**. Si la petición es válida, emite un **JWT efímero** que contiene un `session_id` único incrustado criptográficamente.
* **Streaming del Chat (`POST /api/chat`):** Valida el JWT y establece una conexión *Server-Sent Events (SSE)* con Angular, transmitiendo la respuesta de la IA token por token para una experiencia fluida.

---

## Enrutamiento Inteligente: El Agente Router

Antes de que una pregunta acceda al motor de búsqueda vectorial o al modelo de lenguaje generativo, pasa por una capa de validación y clasificación conocida como el **Agente Router**. 

Este componente actúa como un "semáforo" que analiza la intención del usuario y clasifica la consulta en tres categorías estrictas. Esto optimiza los tiempos de respuesta, reduce costos de API y protege el sistema:

1. **Direct (Directo):** Si la consulta es un saludo, una interacción social o una pregunta que puede responderse sin consultar información o buscar documentos, el Router la desvía directamente al agente de respuesta. Este genera el mensaje basándose únicamente en la información base de su *System Prompt*, evitando el costo de una búsqueda vectorial.
2. **RAG (Recuperación):** Si la consulta requiere conocimientos específicos sobre mi trayectoria, experiencia, formación o proyectos, el Router activa el pipeline de recuperación en la base de conocimientos.
3. **Block (Bloqueo):** Si el sistema detecta intenciones maliciosas (*Prompt Injection*), consultas sobre temas prohibidos, política o cualquier solicitud fuera del alcance profesional, la consulta es interceptada. El sistema aborta la llamada al LLM y devuelve una respuesta automática. El mensaje original y el bloqueo quedan registrados en el historial de la sesión.

---

## El Pipeline de Recuperación Avanzado (Advanced RAG)

Cuando el Agente Router clasifica una consulta como **RAG**, se activa nuestro pipeline de búsqueda en tres fases. Se utiliza una **Retrieval combination**:

1. **Base Retrieval:** Se realiza una búsqueda por similitud.
2. **Diversified Retrieval:**
  - _Extract Technology_: La query pasa por un agente que determina si se consultó por una tecnología especifica y se devuelve dicha tecnología.
  - _Extract Area_: La query pasa por un agente que determina si se consultó por una área especifica y se devuelve dicha área.
  - Primero se verifica si la consulta es sobre una tecnología especifica, un área especifica o es una pregunta 'libre'.
  - Si contiene una tecnología o área se hace una nueva búsqueda vectorial filtrado por los métadatos que contengan la tecnología o área detectada.
  - Para evitar que un proyecto inmenso o muy detallado acapare todos los resultados de la búsqueda, el algoritmo agrupa los fragmentos devueltos y fuerza una selección diversificada, garantizando que el LLM reciba un contexto rico de múltiples experiencias.
3. **Reranking:** Los fragmentos diversificados son reevaluados y reordenados semánticamente en relación con la pregunta original, entregando al LLM únicamente los fragmentos más precisos y ricos en contexto.

---

## Generación y Memory Management (Gestión de Sesión)

El Agente Generador recibe los fragmentos finales y redacta la respuesta. Para mantener una conversación coherente sin saturar la ventana de contexto del LLM, se desarrolló un **Manejador de Sesiones Interno**:

* El `session_id` inyectado en el JWT del usuario vincula sus mensajes en la memoria RAM del servidor de Python.
* **Límite Estricto:** Se retiene un máximo de 5 interacciones (preguntas/respuestas) por sesión.
* **Garbage Collector Asíncrono:** Una tarea en segundo plano barre constantemente la memoria, eliminando las sesiones inactivas o expiradas, garantizando que el contenedor de Docker jamás sufra fugas de memoria (*Memory Leaks*).

---

##  Evaluación de Calidad Continua (LangSmith)

Un Agente de IA en producción debe ser probado y evaluado, por este motivo se integró **LangSmith** en el directorio `evals/`. 

A través de estos scripts de evaluación y *smoke tests*, se monitorea continuamente la latencia del modelo, el consumo de tokens y, lo más importante, la desviación de las respuestas ante cambios en el *System Prompt*, asegurando que el agente responda siempre con el tono profesional requerido y sin alucinaciones.
