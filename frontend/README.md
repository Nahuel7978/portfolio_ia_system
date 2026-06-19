# Frontend App: Hybrid Presentation Layer (SSR & SPA)

This layer is the visible face of the entire platform. Its primary responsibility is to orchestrate the end-user experience, consume the APIs of our microservices (Web Core and AI Core), and ensure that the content is perfectly indexable by search engines.

This is not a traditional web application. It's a dual-purpose system: it acts as an SEO-optimized Public Portfolio and, simultaneously, as a highly secure Reactive Admin Panel.

---

## Technologies and Architectural Decisions

The project is developed using Angular 17/18, taking full advantage of its new reactive engine and Standalone Components architecture. This decision allowed us to completely eliminate traditional modules (`NgModules`), resulting in cleaner code, more efficient lazy loading, and superior tree shaking.

For styling, we migrated to Tailwind CSS v4. By using its new native CSS-based engine, we eliminated the need for complex preprocessors, keeping the final package extremely lightweight.

---

## Server-Side Rendering (SSR) and the SEO Challenge

One of the biggest problems with traditional Single Page Applications (SPAs) is that search engines (like Googlebot) often have difficulty reading content rendered by JavaScript, ruining SEO.

To solve this in a portfolio where visibility is critical, we implemented **Angular Universal (SSR)**.

* **The Public Flow:** When a visitor or search bot requests a public page (e.g., a portfolio article), Angular's Node.js server compiles the HTML with the actual data on the backend before sending it to the browser.

* **Hydration Management:** SSR introduces the challenge of hydration (synchronizing the server-side DOM with the client-side DOM). To avoid critical mismatch errors and memory leaks, we strictly encapsulate the use of browser-specific APIs (such as `window` or `localStorage`) using the `PLATFORM_ID` token and the `isPlatformBrowser` function.

---

## Administration Panel: Security and Interceptors

While the public-facing portion is SSR, the `/admin` route operates strictly as a client-side SPA. All state and security management is handled robustly:

1. **Route Protection (Guards):** Administrative routes are protected by `CanActivate` Guards. If a user does not possess a valid token in their session, they are immediately redirected.

2. **HTTP Interceptors:** We implemented an `HttpInterceptor` system that captures all outgoing requests to our *Web Core* (Spring Boot). This interceptor automatically injects the **JWT Token** into the authorization headers (`Bearer`) and handles errors globally (such as expired tokens, forcing a clean logout).

---

## Backend Integration: BFF (Backend for Frontend) Architecture

To avoid rigid coupling and optimize network calls, the frontend doesn't consume a single monolithic API. Instead, it communicates intelligently with our two microservices, operating under a **Backend for Frontend (BFF)** strategy:

1. **Content and Administration Flow (Web Core):** Requests related to the portfolio, blogs, project uploads, and administrator authentication are directed to the **Spring Boot** service. Communication is handled through Angular services (`HttpClient`) that encapsulate standard CRUD methods. Security here is strict: an interceptor appends the administrative JWT to each header and monitors responses to transparently handle `401 Unauthorized` errors (forcing a redirect to the login page) or `403 Forbidden` errors.

1. **Content and Administration Flow (Web Core):** 2. **Direct Conversational Flow (AI Core):** Connects directly to FastAPI for RAG Agent operations.

3. **Domain Isolation and CORS:** Web Core and AI Core run on different ports/subdomains. The integration was meticulously configured at the HTTP header level. Spring Boot and FastAPI restrict their Cross-Origin Resource Sharing (CORS) policies to accept only requests originating from the frontend domain, protecting the system against malicious third-party requests.

---

## AI Chat Integration (Streaming and Markdown)

1. **Ephemeral Token Management:** When the chat is opened, Angular transparently requests an ephemeral JWT from the AI ​​Core. This token is used exclusively for the chat session, isolating this layer from administrative authentication.

2. **Server-Sent Events (SSE):** Angular establishes a reactive connection with FastAPI, consuming the streaming endpoint. As the LLM generates the response, the frontend renders it to the screen, token by token. All of this occurs outside the main change detection cycle using `NgZone` to avoid blocking the UI thread.

3. **Secure Rendering:** Agent responses often include code or Markdown formatting. We use the `marked` library along with Angular's `DomSanitizer` to parse the text to HTML in real time, ensuring protection against Cross-Site Scripting (XSS) attacks.

---

## Compilation and Deployment

Thanks to orchestration in the monorepo, the frontend is compiled within its own Docker container (`app-frontend`). The resulting image contains the optimized Node.js server that serves the application. All public exposure of this interface is handled by the **Reverse Proxy (Nginx)** in the root of our VPS, guaranteeing secure connections via HTTPS.

---
# Spanish Version
---

# Frontend App: Capa de Presentación Híbrida (SSR & SPA)

 Esta capa es la cara visible de toda la plataforma. Su responsabilidad principal es orquestar la experiencia del usuario final, consumir las APIs de nuestros microservicios (Web Core y AI Core) y garantizar que el contenido sea perfectamente indexable por los motores de búsqueda.

No se trata de una aplicación web tradicional. Es un sistema de doble propósito: actúa como un **Portafolio Público optimizado para SEO** y, simultáneamente, como un **Panel de Administración Reactivo** altamente seguro.

---

## Tecnologías y Decisiones Arquitectónicas

El proyecto está desarrollado utilizando **Angular 17/18** aprovechando al máximo su nuevo motor reactivo y la arquitectura de **Standalone Components**. Esta decisión nos permitió eliminar por completo los módulos tradicionales (`NgModules`), logrando un código más limpio, una carga diferida (*Lazy Loading*) más eficiente y un *Tree-Shaking* superior.

Para los estilos, hemos migrado a **Tailwind CSS v4**. Al utilizar su nuevo motor basado en CSS nativo, eliminamos la necesidad de preprocesadores complejos, manteniendo el paquete final extremadamente ligero.

---

## Server-Side Rendering (SSR) y el Desafío del SEO

Uno de los mayores problemas de las Single Page Applications (SPA) tradicionales es que los motores de búsqueda (como Googlebot) a menudo tienen dificultades para leer el contenido renderizado por JavaScript, arruinando el SEO. 

Para solucionar esto en un portafolio donde la visibilidad es crítica, implementamos **Angular Universal (SSR)**.

* **El Flujo Público:** Cuando un visitante o un bot de búsqueda solicita una página pública (ej. un artículo del portafolio), el servidor Node.js de Angular compila el HTML con los datos reales en el backend antes de enviarlo al navegador.
* **Manejo de Hidratación:** SSR introduce el desafío de la hidratación (sincronizar el DOM del servidor con el del cliente). Para evitar errores críticos de desajuste y fugas de memoria (*Memory Leaks*), encapsulamos estrictamente el uso de APIs exclusivas del navegador (como `window` o `localStorage`) utilizando el token `PLATFORM_ID` y la función `isPlatformBrowser`.

---

## Panel de Administración: Seguridad e Interceptores

Mientras que la parte pública es SSR, la ruta `/admin` opera estrictamente como una SPA del lado del cliente. Toda la gestión de estado y seguridad se maneja de forma robusta:

1. **Protección de Rutas (Guards):** Las rutas administrativas están protegidas por `CanActivate` Guards. Si el usuario no posee un token válido en su sesión, es redirigido inmediatamente.
2. **Interceptores HTTP:** Implementamos un sistema de `HttpInterceptor` que atrapa todas las peticiones salientes hacia nuestro *Web Core* (Spring Boot). Este interceptor inyecta automáticamente el **Token JWT** en las cabeceras de autorización (`Bearer`) y maneja globalmente los errores (como tokens expirados, forzando un cierre de sesión limpio).

---

## Integración con el Backend: Arquitectura BFF (Backend for Frontend)

Para evitar acoplamientos rígidos y optimizar las llamadas de red, el frontend no consume una única API monolítica, sino que se comunica de forma inteligente con nuestros dos microservicios, actuando bajo una estrategia de **Backend for Frontend (BFF)**:

1. **Flujo de Contenidos y Administración (Web Core):** Las peticiones relacionadas con el portafolio, blogs, carga de proyectos y la autenticación del administrador se dirigen hacia el servicio de **Spring Boot**. La comunicación se realiza mediante servicios de Angular (`HttpClient`) que encapsulan los métodos CRUD estándar. La seguridad aquí es estricta: un interceptor adjunta el JWT administrativo en cada cabecera y monitoriza las respuestas para manejar de forma transparente errores `401 Unauthorized` (forzando la redirección al login) o `403 Forbidden`.
2. **Flujo Conversacional Directo (AI Core):** Se conecta directamente con FastAPI** para las operaciones del Agente RAG. 
3. **Aislamiento de Dominios y CORS:** El Web Core y el AI Core corren en puertos/subdominios distintos, la integración se configuró meticulosamente a nivel de cabeceras HTTP. Spring Boot y FastAPI restringen sus políticas de *Cross-Origin Resource Sharing (CORS)* para aceptar únicamente peticiones originadas por el dominio del frontend, blindando al sistema contra solicitudes maliciosas de terceros.

---

## Integración del Chat de IA (Streaming y Markdown)

1. **Gestión del Token Efímero:** Al abrir el chat, Angular solicita de forma transparente un JWT efímero al AI Core. Este token se usa exclusivamente para la sesión del chat, aislando esta capa de la autenticación administrativa.
2. **Server-Sent Events (SSE):** Angular establece una conexión reactiva con FastAPI consumiendo el endpoint de streaming. A medida que el LLM genera la respuesta, el frontend la pinta en la pantalla **token por token**. Todo esto ocurre fuera del ciclo de detección de cambios principal usando `NgZone` para no bloquear el hilo de la interfaz de usuario.
3. **Renderizado Seguro:** Las respuestas del agente suelen incluir código o formato Markdown. Utilizamos la librería `marked` junto con el `DomSanitizer` de Angular para parsear el texto a HTML en tiempo real, garantizando protección contra ataques de Cross-Site Scripting (XSS).

---

## Compilación y Despliegue

Gracias a la orquestación en el monorepo, el frontend se compila dentro de su propio contenedor Docker (`app-frontend`). La imagen resultante contiene el servidor Node.js optimizado que sirve la aplicación. Toda la exposición pública de esta interfaz es manejada por el **Reverse Proxy (Nginx)** en la raíz de nuestro VPS, garantizando conexiones seguras vía HTTPS.
