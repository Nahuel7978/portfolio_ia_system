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

## 🕵️‍♂️ El Pipeline de Recuperación Avanzado (Advanced RAG)

Cuando el Agente Router clasifica una consulta como **RAG**, se activa nuestro pipeline de búsqueda en tres fases. Se utiliza una **Retrieval combination**:

1. **Base Retrieval:** Se realiza una búsqueda por similitud.
2. **Diversified Retrieval:**
  - _Extract Technology_: La query pasa por un agente que determina si se consultó por una tecnología especifica y se devuelve dicha tecnología.
  - _Extract Area_: La query pasa por un agente que determina si se consultó por una área especifica y se devuelve dicha área.
  - Primero se verifica si la consulta es sobre una tecnología especifica, un área especifica o es una pregunta 'libre'.
  - Si contiene una tecnología o área se hace una nueva búsqueda vectorial filtrado por los métadatos que contengan la tecnología o área detectada.
  - Para evitar que un proyecto inmenso o muy detallado acapare todos los resultados de la búsqueda, el algoritmo agrupa los fragmentos devueltos y fuerza una selección diversificada, garantizando que el LLM reciba un contexto rico de múltiples experiencias.
4. **Reranking:** Los fragmentos diversificados son reevaluados y reordenados semánticamente en relación con la pregunta original, entregando al LLM únicamente los fragmentos más precisos y ricos en contexto.

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
