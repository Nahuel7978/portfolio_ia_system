# CV_Bot
An agent capable of answering questions about me based on my personal information and can also schedule meetings. My information corresponds to the information in my CV, which includes projects, career path, education, and objectives.
Agente capaz de responder preguntas sobre mi en base a información personal mía y a su vez puede agendar reuniones. La información mía se corresponde con la información de mi CV que incluye proyectos, trayectoria, educación y objetivos.

[IMAGEN]

# Etapas

[IMAGEN]

Evaluación y monitoreo no son etapas que ocurren al final, son capas transversales que acompañan cada etapa.

## Sprint 0: Infraestructura de Evaluación y Monitoreo

### Tarea 1: Configuración de LangSmith (Tracing)

LangSmith nos permitirá ver qué pasa "bajo el capó" (instancias de cadenas, recuperación de documentos, llamadas al LLM).

1. **Registro:** Crea una cuenta en [smith.langchain.com](https://smith.langchain.com/).
2. **Variables de Entorno:** Crea un archivo `.env` en la raíz de tu proyecto:

```python
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="tu_api_key_aqui"
LANGCHAIN_PROJECT="personal-agent-cv" # Nombre del proyecto
```

1. **Verificación:** Al iniciar tu código de LangChain, las trazas se enviarán automáticamente sin código adicional.

---

### Tarea 2: Creación del Golden Dataset

Necesitamos un estándar de verdad para comparar los resultados del agente. Crearemos un archivo `evals/golden_dataset.json`.

**Estructura sugerida para los 20 pares Q&A:**
Dividiremos las preguntas en categorías para probar diferentes capacidades:

- **Experiencia (6):** "Explica tu rol en el proyecto [X]".
- **Técnico/Proyectos (6):** "¿Cómo implementaste el algoritmo de RL en tu tesis?".
- **Objetivos (4):** "¿Qué tipo de desafíos buscas en tu próximo rol?".
- **Agendamiento (4):** "¿Tienes disponibilidad para una entrevista mañana?".

**Ejemplo de entrada en `golden_dataset.json`:**

```json
[
  {
    "question": "¿Qué tecnologías usaste en el desarrollo del simulador de robótica?",
    "ground_truth": "Utilicé Python, ROS2 y algoritmos de Deep Reinforcement Learning como PPO.",
    "category": "tecnico"
  }
]
```

---

### Tarea 3: Setup de Ragas y DeepEval

Instalaremos las librerías y prepararemos el script base de evaluación.

1. **Instalación:**

```bash
pip install ragas deepeval langchain-openai # Usaremos wrappers de OpenAI para conectar con Groq/Gemini
```

1. **Script `run_evals.py` (Esqueleto):**

Para usar modelos gratuitos en la evaluación (como juez), configuraremos Ragas para que use

**Groq (Llama 3)** o **Gemini**.

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from datasets import Dataset

def run_evaluation(questions, answers, contexts, ground_truths):
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    dataset = Dataset.from_dict(data)
    # Aquí configuramos el LLM de evaluación (ej: ChatGroq o ChatGemini)
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall])
    return result
```

---

### Tarea 4: Definición de Umbrales (Quality Gates)

Establecemos los criterios de aceptación para movernos al siguiente sprint. Si el pipeline no cumple esto, debemos iterar en la Etapa 1 o 2.

| **Métrica** | **Definición** | **Umbral Mínimo** |
| --- | --- | --- |
| **Faithfulness** | ¿La respuesta se deriva estrictamente del CV? (Evita alucinaciones). | **0.85** |
| **Context Recall** | ¿El retriever encontró la sección correcta del CV para responder? | **0.80** |
| **Answer Relevancy** | ¿La respuesta es directa y resuelve la duda del usuario? | **0.85** |
| **Latency (p95)** | Tiempo de respuesta del agente. | **< 3 segundos** |

---

### Entregables del Sprint 0:

1. **Repositorio inicial** con estructura de carpetas (`/data`, `/evals`, `/src`).
2. **Dashboard de LangSmith** recibiendo trazas de prueba.
3. **`golden_dataset.json`** con las 20 preguntas clave validadas por ti.
4. **Script de evaluación** capaz de generar un reporte de métricas inicial.
