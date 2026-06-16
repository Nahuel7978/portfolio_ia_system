# Portfolio Agent and AI: A Hybrid Ecosystem of Showcase and RAG

This project is a **hybrid web platform** designed from the ground up to function as a traditional Content Management System (CMS) and, simultaneously, as a highly specialized **Conversational Artificial Intelligence Agent (RAG)**.

The main objective of this system is to demonstrate, in a practical and tangible way, my capabilities in Software Architecture, AI Automation, and Full-Stack Development, offering recruiters and clients an interactive way to learn about my profile.

---

## Architectural Decisions

To support the load of an Artificial Intelligence engine and a transactional CMS without sacrificing performance or SEO, the system was developed using a **Service-Oriented Architecture (SOA)**, separating responsibilities into three main parts:

1. **The Transactional Core (Web Core):** Written in **Java with Spring Boot**. It acts as the "Single Source of Truth." It manages the security of the administrative panel, CRUD portfolio operations, and the physical handling of binary files in the database.

2. **The AI ​​Engine (AI Core):** Written in **Python with FastAPI and LangChain**. Completely decoupled from the relational world, it handles natural language processing, document chunking, and real-time chat interaction.

3. **The Presentation Layer (Frontend):** Built in **Angular with Server-Side Rendering (SSR)**. It ensures that search engines index the blog's dynamic content, while delivering an ultra-smooth Single Page Application (SPA) experience.

![Global System Architecture](https://drive.google.com/thumbnail?id=15Cy9HPN9fgD332ea88sdUrevI4qU5p27&sz=w1000)
*Figure 1: Macro view of the Service-Oriented Architecture (SOA).*

## The Data Flow: Eventual Consistency and RAG

One of the biggest challenges in systems that combine relational (SQL) and vector databases is keeping the information synchronized. To solve this, we implement the **Eventual Consistency pattern**.

![Data Flow and Eventual Consistency](https://drive.google.com/thumbnail?id=1JMC4Y3XqD49_DaJUVLsuhiuKcXh9pUuj&sz=w1000)
*Figure 2: Asynchronous synchronization between Spring Boot, FastAPI, and ChromaDB.*

### 1. The Ingestion Pipeline (Documentary ETL)
When the administrator uploads a new project in Markdown format, **PostgreSQL** securely stores it as a binary (`BYTEA`) with a `PENDING` status. A **scheduler** (cron job) in Spring Boot detects this new file and sends an asynchronous request (protected by an internal secret) to FastAPI. FastAPI processes the document, injects the metadata, and vectorizes it in **ChromaDB**. Upon completion, PostgreSQL updates to `SYNCED`.

### 2. The Consumption Flow (The RAG Agent)
When a visitor opens the chat, Angular requests an **ephemeral JWT token** directly from FastAPI. The user's questions travel directly to the Python microservice (avoiding the double network hop via Java), where the RAG engine retrieves the exact fragments from ChromaDB and generates the response using **OpenRouter**, returning it to the interface via *streaming*.

---

## 🐳 Infrastructure Orchestration: Docker Compose

The entire ecosystem is contained within a monorepo and is set up with a single `docker-compose.yml` file, which orchestrates **5 independent containers**:

1. 🟢 `app-frontend`: Node.js server running Angular Universal (SSR).

2. 🔵 `app-web-core`: Java Virtual Machine (JVM) instance with Spring Boot.

3. 🟡 `app-ai-core`: Uvicorn server running FastAPI and LangChain.

4. 🐘 `db-postgres`: PostgreSQL 15+ relational database.

5. 🗄️ `db-chroma`: ChromaDB HTTP server (vector database).

### The Internal Network: `portfolio-network`
Network security is strict. The databases (`db-postgres` and `db-chroma`) **do not expose ports to the outside world**. They operate exclusively within an isolated Docker Bridge network (`portfolio-network`). Only the Spring Boot and FastAPI APIs have internal routing permissions to interact with them.

---

### 📂 Monorepo Structure

* `/frontend`: Public UI and Admin Panel (Angular 18+).

* `/web-core`: API Gateway, JWT Security, and Transactional CMS (Spring Boot).

* `/ai-core`: RAG Conversational Agent, Chunking, and Vectorization (FastAPI).

> *For detailed installation and local execution instructions, please refer to the specific `README.md` files within each directory.*

---

# Spanish Version:

---
# Portfolio & AI Agent: Un Ecosistema Híbrido de Showcase y RAG

![Global System Architecture](https://drive.google.com/thumbnail?id=15Cy9HPN9fgD332ea88sdUrevI4qU5p27&sz=w1000)
*Figura 1: Vista macro de la Arquitectura Orientada a Servicios Ligeros (SOA).*

Este proyecto  es una **plataforma web híbrida** diseñada desde cero para funcionar como un Gestor de Contenidos (CMS) tradicional y, al mismo tiempo, como un **Agente de Inteligencia Artificial Conversacional (RAG)** altamente especializado. 

El objetivo principal de este sistema es demostrar, de forma práctica y tangible, mis capacidades en Arquitectura de Software, Automatización de IA y Desarrollo Full-Stack, ofreciendo a reclutadores y clientes una forma interactiva de conocer mi perfil.

---

## Decisiones Arquitectónicas.

Para soportar la carga de un motor de Inteligencia Artificial y un CMS transaccional sin sacrificar rendimiento ni SEO, el sistema se desarrolló en favor de una **Arquitectura Orientada a Servicios Ligeros (SOA)**, separando las responsabilidades en tres grantes partes:

1. **El Núcleo Transaccional (Web Core):** Escrito en **Java con Spring Boot**. Actúa como la "Única Fuente de la Verdad" (Source of Truth). Gestiona la seguridad del panel administrativo, las operaciones CRUD del portafolio y el manejo físico de archivos binarios en base de datos.
2. **El Motor de IA (AI Core):** Escrito en **Python con FastAPI y LangChain**. Totalmente desacoplado del mundo relacional, se encarga del procesamiento de lenguaje natural, el *chunking* de documentos y la interacción del chat en tiempo real.
3. **La Capa de Presentación (Frontend):** Construida en **Angular con Server-Side Rendering (SSR)**. Garantiza que los motores de búsqueda indexen el contenido dinámico del blog, mientras ofrece una experiencia de Single Page Application (SPA) ultra fluida.

---

## El Flujo de Datos: Consistencia Eventual y RAG

Uno de los mayores desafíos en sistemas que combinan bases de datos relacionales (SQL) y vectoriales es mantener la información sincronizada. Para resolverlo, implementamos el patrón de **Consistencia Eventual**.

![Data Flow and Eventual Consistency](https://drive.google.com/thumbnail?id=1JMC4Y3XqD49_DaJUVLsuhiuKcXh9pUuj&sz=w1000)
*Figura 2: Sincronización asíncrona entre Spring Boot, FastAPI y ChromaDB.*

### 1. El Pipeline de Ingesta (ETL Documental)
Cuando el administrador sube un nuevo proyecto en formato Markdown, **PostgreSQL** lo almacena de forma segura como un binario (`BYTEA`) con un estado `PENDING`. Un *Scheduler* (Cron Job) en Spring Boot detecta este nuevo archivo y emite una petición asíncrona (protegida por un secreto interno) hacia FastAPI. FastAPI procesa el documento, inyecta los metadatos y lo vectoriza en **ChromaDB**. Al finalizar, PostgreSQL se actualiza a `SYNCED`.

### 2. El Flujo de Consumo (El Agente RAG)
Cuando un visitante abre el chat, Angular solicita un **Token JWT efímero** directamente a FastAPI. Las preguntas del usuario viajan directamente al microservicio de Python (evitando el doble salto de red por Java), donde el motor RAG recupera los fragmentos exactos desde ChromaDB y genera la respuesta mediante **OpenRouter**, devolviéndola a la interfaz mediante *Streaming*.

---

## 🐳 Orquestación de Infraestructura: Docker Compose

Todo el ecosistema está contenido dentro de un monorepo y se levanta con un único archivo `docker-compose.yml`, el cual orquesta **5 contenedores independientes**:

1. 🟢 `app-frontend`: Servidor Node.js ejecutando Angular Universal (SSR).
2. 🔵 `app-web-core`: Instancia de la Máquina Virtual de Java (JVM) con Spring Boot.
3. 🟡 `app-ai-core`: Servidor Uvicorn corriendo FastAPI y LangChain.
4. 🐘 `db-postgres`: Base de Datos Relacional PostgreSQL 15+.
5. 🗄️ `db-chroma`: Servidor HTTP de ChromaDB (Base de datos vectorial).

### La Red Interna: `portfolio-network`
La seguridad a nivel de red es estricta. Las bases de datos (`db-postgres` y `db-chroma`) **no exponen puertos al mundo exterior**. Operan exclusivamente dentro de una red Bridge aislada de Docker (`portfolio-network`). Solo las APIs de Spring Boot y FastAPI tienen los permisos de enrutamiento interno para interactuar con ellas.

---

### 📂 Estructura del Monorepo

* `/frontend`: UI Pública y Panel de Administración (Angular 18+).
* `/web-core`: API Gateway, Seguridad JWT y CMS Transaccional (Spring Boot).
* `/ai-core`: Agente Conversacional RAG, Chunking y Vectorización (FastAPI).

> *Para instrucciones detalladas de instalación y ejecución local, por favor consulta los `README.md` específicos dentro de cada directorio.*
