"""
SMOKE TEST — Sprint 0
Verifica que el pipeline de evaluación con Ragas + Gemini funciona
ANTES de tener el agente real construido.

Funcionamiento:
  1. Carga datos sintéticos de smoke_data.json
  2. Configura Gemini como LLM juez para Ragas
  3. Ejecuta las 3 métricas definidas en el Sprint 0
  4. Compara resultados contra los umbrales establecidos
  5. Imprime un reporte PASS/FAIL por caso y por métrica

Variables de entorno necesarias en .env:
  GOOGLE_API_KEY=tu_api_key_aqui
  LANGCHAIN_TRACING_V2=true
  LANGCHAIN_API_KEY=tu_langsmith_key
  LANGCHAIN_PROJECT=personal-agent-cv
"""

import json
import os
import time
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# ── Configuración ──────────────────────────────────────────────────────────────

load_dotenv()

SMOKE_DATA_PATH = "evals/smoke_data.json"

# Umbrales definidos en el Sprint 0
THRESHOLDS = {
    "faithfulness":      0.85,
    "answer_relevancy":  0.85,
    "context_recall":    0.80,
}

# ── Inicialización del LLM juez (Gemini) ──────────────────────────────────────

def build_ragas_config():
    """
    Configura Gemini como LLM juez y como modelo de embeddings para Ragas.
    Ragas necesita ambos:
      - LLM: para razonar sobre faithfulness, relevancy y recall
      - Embeddings: para calcular similitud semántica en answer_relevancy
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No se encontró GOOGLE_API_KEY en las variables de entorno.\n"
            "Asegurate de tener un archivo .env con: GOOGLE_API_KEY=tu_key"
        )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite", 
        google_api_key=api_key,
        temperature=0,
    )

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview",
        google_api_key=api_key,
    )

    return LangchainLLMWrapper(llm), LangchainEmbeddingsWrapper(embeddings)

# ── Carga de datos ─────────────────────────────────────────────────────────────

def load_smoke_data(path: str) -> dict:
    """
    Lee smoke_data.json y lo convierte al formato que espera Ragas.
    Ragas espera un dict con listas paralelas:
      - question:    lista de preguntas
      - answer:      lista de respuestas del agente
      - contexts:    lista de listas (cada elemento es lista de strings)
      - ground_truth: lista de respuestas de referencia
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    dataset = {
        "question":     [],
        "answer":       [],
        "contexts":     [],
        "ground_truth": [],
        "_case":        [],   # Solo para el reporte, Ragas lo ignora
    }

    for item in raw:
        dataset["question"].append(item["question"])
        dataset["answer"].append(item["answer"])
        dataset["contexts"].append(item["contexts"])
        dataset["ground_truth"].append(item["ground_truth"])
        dataset["_case"].append(item.get("_case", "Sin descripción"))

    return dataset

# ── Evaluación ─────────────────────────────────────────────────────────────────

def run_smoke_test():
    print("\n" + "="*60)
    print("  SMOKE TEST — Pipeline de Evaluación Ragas + Gemini")
    print("="*60)

    # 1. Configurar juez
    print("\n[1/4] Inicializando Gemini como LLM juez...")
    ragas_llm, ragas_embeddings = build_ragas_config()

    # Asignar el juez a cada métrica
    metrics = [faithfulness, answer_relevancy, context_recall]
    for metric in metrics:
        metric.llm = ragas_llm
        if hasattr(metric, "embeddings"):
            metric.embeddings = ragas_embeddings

    # 2. Cargar datos
    print("[2/4] Cargando smoke_data.json...")
    raw_data = load_smoke_data(SMOKE_DATA_PATH)
    cases = raw_data.pop("_case")   # Separar antes de pasarlo a Dataset

    dataset = Dataset.from_dict(raw_data)
    print(f"      {len(dataset)} casos cargados correctamente.\n")

    # 3. Ejecutar evaluación
    print("[3/4] Ejecutando evaluación...")
    start = time.time()

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
    )

    elapsed = time.time() - start
    print(f"      Completado en {elapsed:.1f}s\n")

    # 4. Reporte
    print("[4/4] Resultados\n")
    print_report(result, cases)

    return result

# ── Reporte ────────────────────────────────────────────────────────────────────

def print_report(result, cases: list):
    df = result.to_pandas()

    metric_keys = ["faithfulness", "answer_relevancy", "context_recall"]

    # Reporte por caso
    print("-"*60)
    for i, row in df.iterrows():
        print(f"\nCASO {i+1}: {cases[i][:60]}...")
        for metric in metric_keys:
            score = row.get(metric, None)
            threshold = THRESHOLDS[metric]
            if score is None:
                status = "N/A"
                icon = "⚠️ "
            else:
                passed = score >= threshold
                icon = "✅" if passed else "❌"
                status = f"{score:.3f}  (umbral: {threshold})  {'PASS' if passed else 'FAIL'}"
            print(f"  {icon} {metric:<22} {status}")

    # Resumen global
    print("\n" + "="*60)
    print("RESUMEN GLOBAL")
    print("-"*60)
    all_passed = True
    for metric in metric_keys:
        avg_score = df[metric].mean()
        threshold = THRESHOLDS[metric]
        passed = avg_score >= threshold
        icon = "✅" if passed else "❌"
        print(f"  {icon} {metric:<22} avg={avg_score:.3f}  umbral={threshold}")
        if not passed:
            all_passed = False

    print("-"*60)
    if all_passed:
        print("  🟢 INFRAESTRUCTURA OK — El pipeline de evaluación funciona.")
        print("     Podés avanzar al Sprint 1 con confianza.")
    else:
        print("  🟡 INFRAESTRUCTURA OK con advertencias.")
        print("     Los FAILs en este smoke test son ESPERADOS (datos sintéticos).")
        print("     Lo importante: el script corrió sin errores de configuración.")
    print("="*60 + "\n")

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_smoke_test()