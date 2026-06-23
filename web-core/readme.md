# Backend / Web Core: Transactional Core and Source of Truth

This component is the transactional heart of the system and acts as the **Single Source of Truth** for the entire ecosystem. While the AI ​​Core handles the cognitive logic of the RAG Agent, this Java microservice manages portfolio content integrity, admin panel security, and the pipeline that feeds the vector database.

<img width="1024" height="559" alt="imagen" src="https://github.com/user-attachments/assets/00e0c763-aa1f-4cdc-801b-3958feb1a1bd" />

*Figure 1: Layered internal architecture and persistence flow of the Web Core.*

---

## Technologies and Architectural Decisions

The service is built on the **Java** platform and the **Spring Boot** framework, leveraging its robustness, maturity, and enterprise ecosystem to ensure maximum stability.

### Critical Design Decisions:
* **Advanced Persistence:** **PostgreSQL 15+** is used as the relational database engine. To avoid dependency on third-party storage services (such as AWS S3), physical Markdown project files are stored directly in the database using binary blocks (`BYTEA`).

* **Memory Optimization (Lazy Loading):** To prevent reading project listings from overwhelming the JVM's RAM, entities use the `@Lob` annotation explicitly configured with *FetchType.LAZY*. The physical file is only retrieved from the database when explicitly required by the synchronization scheduler.

* * **Stateless Security:** The administration panel's authentication is based on **Spring Security** and self-contained **JWT (JSON Web Tokens)**, ensuring a stateless design that facilitates deployment in Docker containers.

---
## Code Structure: Clean Layered Architecture

The code is organized following a **Layered Architecture** pattern, strictly isolating responsibilities to facilitate maintenance and unit/integration testing:

```text
src/main/java/com/portfolio/core/
│
├── controllers/ # Input Layer: REST exposure and data validation.
├── services/ # Business Layer: Orchestration, logic, and transactions.
├── dtos/ # Transfer Layer: Data objects decoupled from the database.
├── models/ # Domain Layer: JPA entities and relational mapping.
├── repositories/ # Data Layer: Spring Data JPA interfaces for PostgreSQL.
└──  repositories/ # Data Layer: Spring Data JPA interfaces for PostgreSQL. └── schedulers/ # Automation Layer: Scheduled Tasks (Cron Jobs).

```
---
## Flow of Responsibilities:

1. **Controller:** Receives the HTTP request from the frontend (Angular), intercepts initial errors, and validates the input data using native validation annotations (@Valid, @NotNull).

2. **DTO (Data Transfer Object):** Decouples the database entities from the public API. Prevents data overfetching and protects sensitive fields.

3. **Service:** Contains the business logic. Uses the @Transactional annotation to ensure that PostgreSQL operations are executed atomically (if something fails, an automatic rollback is applied).

4. **Model:** Defines the structure of the tables in PostgreSQL using Hibernate/JPA annotations.

5. **Repository:** Extends JpaRepository, abstracting complex SQL queries into object-oriented programming methods.

---

## Endpoints (REST API)

The API exposes distinct prefixes to separate public and administrative traffic, simplifying routing rules in Nginx:

### Public Endpoints (/api/v1/public/*)

Accessible by any user or search bot without authentication.

- `GET /api/v1/public/projects` - Returns the list of projects (excluding the binary file to optimize file size).

- `GET /api/v1/public/projects/{id}` - Returns the details of a specific project for SSR rendering in Angular.

- `GET /api/v1/public/experience` - List of work experience and academic background.

### Administrative Endpoints (/api/v1/admin/*)

These require the frontend interceptor to attach a valid JWT in the headers (Authorization: Bearer <token>).

- `POST /api/v1/admin/auth/login` - Validates credentials and issues the administrative JWT.

- `POST /api/v1/admin/projects` - Creates a new project and processes the upload of the Markdown file (BYTEA) in a PENDING state.

- `PUT /api/v1/admin/projects/{id}` - Modifies metadata or content of an existing project (resets the state to PENDING if the content has changed).

- `DELETE /api/v1/admin/projects/{id}` - Physically deletes the PostgreSQL registry entry and triggers a vector purge command.

---
## The Synchronization Mechanism: DocumentSyncScheduler

The fundamental component supporting the Eventual Consistency pattern in the monorepo is the **DocumentSyncScheduler**. It is an automated component (Cron Job) from Spring Boot that eliminates the need for blocking synchronous HTTP calls during content creation.
```
[Admin Angular] ──> (SQL Insert) ──> [PostgreSQL (Status: PENDING)]
                                              │
                                   [DocumentSyncScheduler] (Every X seconds)
                                              │
                                              ▼
[ChromaDB] <── (Vectorize) <── [FastAPI AI Core] <── (HTTP POST with X-Internal-Secret)
        │
    (Success) ──> [Spring Boot] ──> (SQL Update) ──> [PostgreSQL (Status: SYNCED)]
```

---

## Asynchronous Synchronization Flow:

- **Discovery:** The scheduler runs in the background at configurable intervals. Its first task is to query the ProjectRepository, searching for records with a PENDING synchronization status.

- **Lazy Load:** For each detected project, the service opens a transaction and invokes the method that extracts the binary Markdown file from PostgreSQL.

- **Secure Inter-Container Request:** Spring Boot acts as an HTTP client (RestTemplate or WebClient) and sends an asynchronous request to the AI ​​Core service (FastAPI), targeting the internal endpoint /internal/documents/upsert.

- **Secret Validation:** In the headers of this request, Spring Boot injects a symmetric secret key known only to our containers (X-Internal-Secret).

- **Status Resolution:**

- If FastAPI responds successfully (200 OK) after processing and indexing the document in ChromaDB, Spring Boot immediately updates the project status in PostgreSQL to SYNCED.

- If the AI ​​Core reports a failure or the Python microservice is unreachable, the scheduler logs the error and changes the status to FAILED, making it ready for an automatic retry in the next cycle.

---
# Spanish Version
---

# Backend / Web Core: Núcleo Transaccional y Fuente de la Verdad

Este componente es el corazón transaccional del sistema y actúa como la **Única Fuente de la Verdad (Source of Truth)** de todo el ecosistema. Mientras que el AI Core maneja la lógica cognitiva del Agente RAG, este microservicio en Java gestiona la integridad del contenido del portafolio, la seguridad del panel administrativo y el pipeline que alimenta la base de datos vectorial.

<img width="1024" height="559" alt="imagen" src="https://github.com/user-attachments/assets/00e0c763-aa1f-4cdc-801b-3958feb1a1bd" />

*Figura 1: Arquitectura interna en capas y flujo de persistencia del Web Core.*

---

## Tecnologías y Decisiones Arquitectónicas

El servicio está construido sobre la plataforma **Java** y el framework **Spring Boot**, aprovechando su robustez, madurez y ecosistema empresarial para garantizar la máxima estabilidad.

### Decisiones de Diseño Críticas:
* **Persistencia Avanzada:** Se utiliza **PostgreSQL 15+** como motor de base de datos relacional. Para evitar la dependencia de servicios de almacenamiento de terceros (como AWS S3), los archivos físicos Markdown de los proyectos se almacenan directamente en la base de datos utilizando bloques binarios (`BYTEA`).
* **Optimización de Memoria (Lazy Loading):** Para impedir que la lectura de listados de proyectos colapse la memoria RAM de la JVM, las entidades utilizan la anotación `@Lob` configurada explícitamente con *FetchType.LAZY*. El archivo físico solo se extrae de la base de datos cuando el scheduler de sincronización lo requiere expresamente.
* **Seguridad Stateless:** La autenticación del panel administrativo se basa en **Spring Security** y tokens **JWT (JSON Web Tokens)** auto-contenidos, garantizando un diseño sin estado (*Stateless*) que facilita el despliegue en contenedores Docker.

---

## Estructura del Código: Arquitectura de Capas Limpias

El código está organizado siguiendo un patrón de **Arquitectura en Capas**, aislando estrictamente las responsabilidades para facilitar el mantenimiento y la realización de pruebas unitarias/integración:

```text
src/main/java/com/portfolio/core/
│
├── controllers/   # Capa de Entrada: Exposición REST y validación de datos.
├── services/      # Capa de Negocio: Orquestación, lógica y transaccionalidad.
├── dtos/          # Capa de Transferencia: Objetos de datos desacoplados de la DB.
├── models/        # Capa de Dominio: Entidades JPA y mapeo relacional.
├── repositories/  # Capa de Datos: Interfaces Spring Data JPA para PostgreSQL.
└── schedulers/    # Capa de Automatización: Tareas programadas (Cron Jobs).
```

---

## Flujo de Responsabilidades:

1. **Controller:** Recibe la petición HTTP del frontend (Angular), intercepta errores iniciales y valida los datos de entrada usando las anotaciones nativas de validación (@Valid, @NotNull).
2. **DTO (Data Transfer Object):** Desacopla las entidades de la base de datos de la API pública. Evita el problema de sobre-exposición de datos (Over-fetching) y protege campos sensibles.
3. **Service:** Contiene la lógica del negocio. Utiliza la anotación @Transactional para asegurar que las operaciones en PostgreSQL se ejecuten de forma atómica (si algo falla, se aplica un Rollback automático).
4. **Model:** Define la estructura de las tablas en PostgreSQL a través de anotaciones Hibernate/JPA.
5. **Repository:** Extiende de JpaRepository, abstrayendo las consultas SQL complejas en métodos de programación orientada a objetos.

--- 

## Endpoints (API REST)

La API expone prefijos bien diferenciados para separar el tráfico público del administrativo, simplificando las reglas de enrutamiento en Nginx:

### Endpoints Públicos (/api/v1/public/*)

Accesibles por cualquier usuario o bot de búsqueda sin necesidad de autenticación.

 - `GET /api/v1/public/projects` - Devuelve la lista de proyectos (excluyendo el archivo binario binario para optimizar peso).
 - `GET /api/v1/public/projects/{id}` - Devuelve el detalle de un proyecto específico para el renderizado SSR en Angular.
 - `GET /api/v1/public/experience` - Listado de trayectoria laboral y formación académica.

### Endpoints Administrativos (/api/v1/admin/*)

Requieren que el interceptor del frontend adjunte un JWT válido en las cabeceras (Authorization: Bearer <token>).

- `POST /api/v1/admin/auth/login` - Valida credenciales y emite el JWT de administración.
- `POST /api/v1/admin/projects` - Crea un nuevo proyecto y procesa la carga del archivo Markdown (BYTEA) en estado PENDING.
- `PUT /api/v1/admin/projects/{id}` - Modifica metadatos o contenido de un proyecto existente (reinicia el estado a PENDING si el contenido varió).
- `DELETE /api/v1/admin/projects/{id}` - Eliminación física del registro de PostgreSQL y disparo de orden de purga vectorial.

---

## El Mecanismo de Sincronización: DocumentSyncScheduler

La pieza fundamental que sostiene el patrón de Consistencia Eventual en el monorepo es el **DocumentSyncScheduler**. Es un componente automatizado (Cron Job) de Spring Boot que elimina la necesidad de realizar llamadas HTTP síncronas bloqueantes durante la creación de contenidos.
```
[Admin Angular] ──> (SQL Insert) ──> [PostgreSQL (Status: PENDING)]
                                              │
                                   [DocumentSyncScheduler] (Every X seconds)
                                              │
                                              ▼
[ChromaDB] <── (Vectorize) <── [FastAPI AI Core] <── (HTTP POST with X-Internal-Secret)
        │
    (Success) ──> [Spring Boot] ──> (SQL Update) ──> [PostgreSQL (Status: SYNCED)]
```

---

## Flujo de Sincronización Asíncrona:

- **Detección:** El scheduler se ejecuta en segundo plano en intervalos de tiempo configurables. Su primera tarea es consultar al ProjectRepository buscando registros cuyo estado de sincronización sea estrictamente PENDING.
- **Carga Diferida (Lazy):** Para cada proyecto detectado, el servicio abre una transacción e invoca el método que extrae el archivo Markdown binario desde PostgreSQL.
- **Petición Segura Inter-Contenedor:** Spring Boot actúa como un cliente HTTP (RestTemplate o WebClient) y emite una petición asíncrona hacia el servicio AI Core (FastAPI) apuntando al endpoint interno /internal/documents/upsert.
- **Validación de Secreto:** En las cabeceras de esta petición, Spring Boot inyecta una clave secreta simétrica conocida únicamente por nuestros contenedores (X-Internal-Secret).
- **Resolución del Estado:**
        - Si FastAPI responde de forma exitosa (200 OK) tras haber procesado e indexado el documento en ChromaDB, Spring Boot actualiza inmediatamente el estado del proyecto en PostgreSQL a SYNCED.
        - Si el AI Core reporta un fallo o el microservicio de Python no es alcanzable, el scheduler registra el error en los logs y cambia el estado a FAILED, quedando listo para un proceso de reintento automático en el siguiente ciclo.
  
