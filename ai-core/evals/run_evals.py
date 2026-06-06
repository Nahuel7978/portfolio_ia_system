"""
run_evals.py
Ejecuta el benchmark Ragas contra el Golden Dataset.

Flujo:
    1. Carga el golden dataset (excluye categoría 'agendamiento')
    2. Invoca el agente CV por cada pregunta
    3. Evalúa con Ragas usando Gemini como juez
    4. Imprime métricas y análisis de fallos

Uso: python evals/run_evals.py
"""

import json
import os
import sys
import uuid
from dotenv import load_dotenv

load_dotenv()

# Asegurar que el root del proyecto esté en el path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datasets import Dataset
from ragas import evaluate
from ragas.metrics.collections import Faithfulness, AnswerRelevancy, ContextRecall
from ragas.llms import llm_factory
from ragas.embeddings import GoogleEmbeddings

from google import genai

from src.agent.Chain import build_cv_agent

# ── Configuración ─────────────────────────────────────────────────────────────

GOLDEN_DATASET_PATH = "./data/golden_dataset.json"
EXCLUDED_CATEGORIES = {"agendamiento"}
EVAL_MODEL          = "gemini-2.0-flash"
SESSION_PREFIX      = "eval"
EMBEDDING_MODEL = "models/text-embedding-004"

# ── Carga del dataset ─────────────────────────────────────────────────────────

def load_golden_dataset(path: str, exclude: set) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    filtered = [item for item in data if item.get("category") not in exclude]
    print(f"✓ Golden dataset cargado: {len(filtered)} preguntas "
          f"(excluidas {len(data) - len(filtered)} de categorías {exclude})")
    return filtered

# ── Invocación del agente ─────────────────────────────────────────────────────

def run_agent_on_dataset(agent, dataset: list[dict]) -> tuple[list, list, list, list]:
    questions, answers, contexts, ground_truths = [], [], [], []

    for i, item in enumerate(dataset):
        question     = item["question"]
        ground_truth = item["ground_truth"]
        session_id   = f"{SESSION_PREFIX}-{uuid.uuid4().hex[:8]}"

        print(f"\n[{i+1}/{len(dataset)}] Q: {question[:80]}...")

        try:
            result = agent.invoke(
                {"input": question},
                config={"configurable": {"session_id": session_id}},
            )
            answer = result.get("answer", "")

            # Extraer textos de los documentos de contexto recuperados
            source_docs = result.get("context", [])
            context_texts = [doc.page_content for doc in source_docs if hasattr(doc, "page_content")]

            print(f"   ✓ Respuesta generada | {len(context_texts)} fragmentos de contexto")

        except Exception as e:
            print(f"   ✗ Error en pregunta {i+1}: {e}")
            answer        = ""
            context_texts = []

        questions.append(question)
        answers.append(answer)
        contexts.append(context_texts)
        ground_truths.append(ground_truth)

    return questions, answers, contexts, ground_truths

# ── Evaluación Ragas ──────────────────────────────────────────────────────────

def run_evaluation(questions, answers, contexts, ground_truths) -> dict:
    data = {
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(data)

    # Gemini como juez evaluador
    print("\n── Ejecutando evaluación Ragas ──")
    evaluator_llm = llm_factory(
            EVAL_MODEL,
            provider = "google",
            client=genai.Client(api_key=os.environ["GOOGLE_API_KEY"]),
        )

    
    embeddings = GoogleEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=os.environ["GOOGLE_API_KEY"],
    )

    faithfulness_metric    = Faithfulness(llm=evaluator_llm)
    answer_relevancy_metric = AnswerRelevancy(llm=evaluator_llm, embeddings=embeddings)
    context_recall_metric  = ContextRecall(llm=evaluator_llm)

    result = evaluate(
            dataset,
            metrics=[faithfulness_metric, answer_relevancy_metric, context_recall_metric],
        )
    return result

# ── Análisis de fallos ────────────────────────────────────────────────────────

def analyze_failures(dataset: list[dict], results: dict, threshold: float = 0.7):
    print("\n── Análisis de fallos (score < {}) ──".format(threshold))

    scores_df = results.to_pandas()
    hard_cases = []

    for i, row in scores_df.iterrows():
        item_scores = {
            "faithfulness":     row.get("faithfulness", None),
            "answer_relevancy": row.get("answer_relevancy", None),
            "context_recall":   row.get("context_recall", None),
        }

        # Detectar si alguna métrica está bajo el umbral
        failures = {k: v for k, v in item_scores.items() if v is not None and v < threshold}
        if failures:
            hard_cases.append({
                "index":    i,
                "question": dataset[i]["question"],
                "category": dataset[i]["category"],
                "scores":   item_scores,
                "failures": failures,
            })

    if not hard_cases:
        print("✓ No se detectaron hard cases. Todas las métricas superan el umbral.")
    else:
        print(f"✗ {len(hard_cases)} hard cases detectados:\n")
        for case in hard_cases:
            print(f"  [{case['index']+1}] ({case['category']}) {case['question'][:70]}...")
            for metric, score in case["failures"].items():
                print(f"       {metric}: {score:.3f}")

    return hard_cases

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("══ Baseline Benchmark - Sprint 2 ══\n")

    # 1. Cargar dataset
    dataset = load_golden_dataset(GOLDEN_DATASET_PATH, EXCLUDED_CATEGORIES)

    # 2. Construir agente
    print("\n── Inicializando agente CV ──")
    agent = build_cv_agent()

    # 3. Generar respuestas
    print("\n── Generando respuestas del agente ──")
    questions, answers, contexts, ground_truths = run_agent_on_dataset(agent, dataset)

    # 4. Evaluar
    results = run_evaluation(questions, answers, contexts, ground_truths)

    # 5. Imprimir métricas globales
    print("\n══ Métricas Ragas (Sprint 2 - Baseline) ══")
    print(f"  Faithfulness:     {results['faithfulness']:.3f}")
    print(f"  Answer Relevancy: {results['answer_relevancy']:.3f}")
    print(f"  Context Recall:   {results['context_recall']:.3f}")

    # 6. Análisis de fallos
    analyze_failures(dataset, results)

    print("\n══ Benchmark completado ══")


if __name__ == "__main__":
    main()