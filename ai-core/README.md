# AI Core: Vector Engine and State Graph-Based Architecture (LangGraph & RAG)
This microservice represents the cognitive component of the platform, designed to act as an expert agent capable of providing accurate and contextualized answers about my career path, education, and projects.

![AI Core Architecture](https://drive.google.com/thumbnail?id=1V_TvWsFU28i7F8qj10K8Ta63HDUz9cJU&sz=w900)

This service implements a **State Graph Architecture**, ensuring granular control over the conversation flow, the security of the responses, and the optimization of the retrieved context.

---

## Technologies and Architectural Decisions

The service is built in **Python 3.10+** using **FastAPI** for its high performance and native asynchronous support. The cognitive orchestrator is **LangGraph**.

### Key Decision
* **Orchestration with LangGraph:** All conversational logic is structured as a directed acyclic graph where the conversation state propagates transparently between specialized nodes.

* **Vector Decoupling:** **ChromaDB** operates independently as an isolated HTTP server within Docker's internal network (`portfolio-network`). All indexing and semantic similarity searches are performed via direct network requests to this server, eliminating intermediate relational layers in the AI ​​domain.

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

## Cognitive Flow: Native State Graph

The agent's intelligence is fragmented into logical execution units called **Nodes**, which manipulate and react to a centralized state provided natively by LangGraph. The flow consists of 5 critical nodes:

1. **Router Node:** This is the entry point for the user's query. It semantically analyzes the intent of the question and performs conditional routing to one of three possible paths: `direct`, `rag`, or `block`.

2. **Retriever Node:** This node is activated only if the Router classifies the query as `rag`. It is responsible for isolating the query, interacting with ChromaDB, and executing the advanced retrieval pipeline.

3. **Direct Response Node:** This node is executed if the Router determines that the query is a greeting or a general interaction that does not require access to my professional profile. It generates a quick response based on the behavior guidelines of its *System Prompt*.

4. **Rag Response Node:** Absorbs the context cleaned by the *Retriever Node*, merges the conversational history, and formulates the final structured response, ensuring that each claim is supported by the retrieved documents.

5. **Block Node:** Acts as a semantic firewall. If the Router detects attempts at *prompt injection* or topics outside the professional scope, this node intercepts the session and statically issues the restriction message: *"I can only answer questions that are strictly about Nahuel Román's career and projects."*, saving the event to the history without consuming LLM resources.

![Graph](https://drive.google.com/thumbnail?id=1Y6SxUOPtQ65quYYKu9hnCwl05ygBgsc8&sz=w900)


---

## State and Memory Management in RAM

Conversation persistence and thread tracking are entirely delegated to LangGraph's native memory system:

* **State Management with MemorySaver:** The microservice uses a checkpointer in RAM that automatically associates the conversation history with the `session_id` from the JWT.

* **State Lifecycle:** By relying on LangGraph's native graph primitives for persistence, thread management, message buffering, and data expiration occur in a controlled and optimized manner within the application's memory space, ensuring complete isolation between sessions of different concurrent users.

---

## Continuous Evaluation and Quality (LangSmith)

To ensure that modifications to system instructions or node behavior do not degrade the agent's accuracy, the `evals/` directory includes a suite of automated tests integrated with LangSmith.

These tests continuously evaluate response fidelity, the relevance of the retrieved context, and the latency of each node in the graph, ensuring deterministic behavior before each production deployment.

![Langsmith](https://drive.google.com/thumbnail?id=1tLes9p9RQrXg4PellgRKx_cMNYkUKGPd&sz=w900)

---

# Spanish Version

---

# AI Core: Motor Vectorial y Arquitectura Basada en Grafos de Estado (LangGraph & RAG) 
Este microservicio representa el componente cognitivo de la plataforma, diseñado para actuar como un agente experto capaz de responder de manera precisa y contextualizada sobre mi trayectoria, formación y proyectos. 

![AI Core Architecture](https://drive.google.com/thumbnail?id=1V_TvWsFU28i7F8qj10K8Ta63HDUz9cJU&sz=w900)

Este servicio implementa una **Arquitectura Basada en Grafos de Estado**, garantizando un control granular sobre el flujo de la conversación, la seguridad de las respuestas y la optimización del contexto recuperado.

---

## Tecnologías y Decisiones Arquitectónicas

El servicio está desarrollado en **Python 3.10+** y expuesto mediante **FastAPI**.

### Arquitectura:
* **Orquestación con LangGraph:** Toda la lógica conversacional está estructurada como un grafo dirigido acíclico donde el estado de la conversación se propaga de manera transparente entre nodos especializados.
* **Desacoplamiento Vectorial:** **ChromaDB** opera de manera independiente como un servidor HTTP aislado dentro de la red interna de Docker (`portfolio-network`). Toda la indexación y búsquedas por similitud semántica se realizan mediante peticiones de red directas a este servidor, eliminando capas relacionales intermedias en el dominio de la IA.

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

## Flujo Cognitivo: Grafo de Estados Nativo

La inteligencia del agente está fragmentada en unidades de ejecución lógica denominadas **Nodos**, los cuales manipulan y reaccionan a un estado centralizado provisto de forma nativa por LangGraph. El flujo se compone de 5 nodos críticos:

1. **Nodo Router:** Es el punto de entrada de la consulta del usuario. Analiza semánticamente la intención de la pregunta y realiza un enrutamiento condicional hacia tres caminos posibles: `direct`, `rag` o `block`.
2. **Nodo Retriever:** Se activa únicamente si el Router clasifica la consulta como `rag`. Se encarga de aislar la consulta, interactuar con ChromaDB y ejecutar el pipeline de recuperación avanzada.
3. **Nodo Direct Response:** Se ejecuta si el Router determina que la consulta es un saludo o una interacción general que no requiere de mi expediente profesional. Genera una respuesta ágil basada en las directrices de comportamiento de su *System Prompt*.
4. **Nodo Rag Response:** Absorbe el contexto depurado por el *Nodo Retriever*, fusiona la historia conversacional y formula la respuesta final estructurada, garantizando que cada afirmación esté respaldada por los documentos recuperados.
5. **Nodo Block:** Actúa como un cortafuegos semántico. Si el Router detecta intentos de *prompt injection* o temas ajenos al ámbito profesional, este nodo intercepta la sesión y emite de forma estática el mensaje de restricción: *"Sólo puedo responder preguntas que sean estrictamente sobre la trayectoria de Nahuel Román y sus proyectos."*, guardando el evento en el historial sin consumir recursos del LLM.

![Graph](https://drive.google.com/thumbnail?id=1Y6SxUOPtQ65quYYKu9hnCwl05ygBgsc8&sz=w900)

---

## Pipeline de Recuperación Avanzado

Dentro del **Nodo Retriever**, la búsqueda de información no se confía a una consulta simple por similitud. Para evitar sesgos y maximizar la relevancia del contexto, se ejecuta un proceso en tres fases:

1. **Base Retrieval:** Se realiza una búsqueda por similitud.
2. **Diversified Retrieval:**
  - _Extract Technology_: La query pasa por un agente que determina si se consultó por una tecnología especifica y se devuelve dicha tecnología.
  - _Extract Area_: La query pasa por un agente que determina si se consultó por una área especifica y se devuelve dicha área.
  - Primero se verifica si la consulta es sobre una tecnología especifica, un área especifica o es una pregunta 'libre'.
  - Si contiene una tecnología o área se hace una nueva búsqueda vectorial filtrado por los métadatos que contengan la tecnología o área detectada.
  - Para evitar que un proyecto inmenso o muy detallado acapare todos los resultados de la búsqueda, el algoritmo agrupa los fragmentos devueltos y fuerza una selección diversificada, garantizando que el LLM reciba un contexto rico de múltiples experiencias.
3. **Reranking:** Los fragmentos diversificados son reevaluados y reordenados semánticamente en relación con la pregunta original, entregando al LLM únicamente los fragmentos más precisos y ricos en contexto.
---

## Gestión de Estado y Memoria en RAM

La persistencia de las conversaciones y el seguimiento del hilo conductor se delegan por completo al sistema de memoria nativo de LangGraph:

* **Manejo de Estado con MemorySaver:** El microservicio utiliza un checkpointer en memoria RAM que asocia automáticamente el historial de la conversación con el `session_id` proveniente del JWT.
* **Ciclo de Vida del Estado:** Al confiar la persistencia a las primitivas nativas del grafo de LangGraph, la gestión de hilos, el almacenamiento intermedio de los mensajes y la expiración de datos ocurren de manera controlada y optimizada en el espacio de memoria de la aplicación, garantizando aislamiento total entre las sesiones de diferentes usuarios concurrentes.

---

## Evaluación y Calidad Continua (LangSmith)

Para asegurar que las modificaciones en las instrucciones del sistema o el comportamiento de los nodos no degraden la precisión del agente, el directorio `evals/` incluye una suite de pruebas automatizadas integradas con **LangSmith**.

A través de estos tests, se evalúa de manera constante la fidelidad de las respuestas (*Faithfulness*), la relevancia del contexto recuperado y los tiempos de latencia de cada nodo del grafo, asegurando un comportamiento determinista antes de cada despliegue a producción.

![Langsmith](https://drive.google.com/thumbnail?id=1tLes9p9RQrXg4PellgRKx_cMNYkUKGPd&sz=w900)

