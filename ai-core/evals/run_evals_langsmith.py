"""
run_evals_langsmith.py
Ejecuta el benchmark del Agente CV contra el Golden Dataset en LangSmith.

Flujo:
    1. Carga el dataset desde LangSmith por nombre
    2. Invoca el agente CV por cada ejemplo
    3. Evalúa con el evaluador LLM-as-a-Judge configurado en LangSmith (Gemini)
    4. Los resultados quedan visibles en la plataforma

Uso: python evals/run_evals_langsmith.py
"""

import os
import sys
import uuid
import asyncio
from dotenv import load_dotenv


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langsmith import Client, evaluate
from langsmith.evaluation import EvaluationResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.agent.Chain import build_cv_agent

# ── Configuración ─────────────────────────────────────────────────────────────
load_dotenv()


DATASET_NAME      = "golden_dataset_cv_bot"
EXPERIMENT_PREFIX = "cv-agent-sprint2"
EVAL_MODEL        = "gemini-2.5-flash-lite"

# ── Agente (singleton) ────────────────────────────────────────────────────────

print("── Inicializando agente CV ──")
agent = build_cv_agent()

# ── Función objetivo ──────────────────────────────────────────────────────────

def target(inputs: dict) -> dict:
    """
    Invocada por LangSmith por cada fila del dataset.
    Retorna answer y contexts para que los evaluadores puedan usarlos.
    """
    question   = inputs.get("question", "")
    session_id = f"eval-{uuid.uuid4().hex[:8]}"

    result = agent.invoke(
        {"input": question},
        config={"configurable": {"session_id": session_id}},
    )

    answer    = result.get("answer", "")
    contexts  = [
        doc.page_content
        for doc in result.get("context", [])
        if hasattr(doc, "page_content")
    ]

    return {
        "answer":   answer,
        "contexts": contexts,
    }

# ── Evaluador LLM-as-a-Judge (replica el prompt configurado en LangSmith) ─────

_eval_llm = ChatGoogleGenerativeAI(
    model=EVAL_MODEL,
    google_api_key=os.environ["GOOGLE_API_KEY"],
    temperature=0,
)

JUDGE_PROMPT = """You are an expert evaluator assessing the quality of an AI assistant's answer about a professional's CV.

<Rubric>
A perfect answer:
- Contains only the exact information requested.
- Uses the minimum number of words necessary to convey the complete answer.
When scoring, deduct points for:
- Redundant information or restatements.
- Polite filler phrases like "hope this helps".
- Information not grounded in the provided context.
Score range: 0.0 (completely wrong or hallucinated) to 1.0 (perfect).
</Rubric>

<Instructions>
- Carefully read the input, output and reference output.
- Check whether the answer is faithful to the reference.
- Check for any unnecessary elements mentioned in the Rubric.
- Return ONLY a JSON with two fields: "score" (float 0.0-1.0) and "comment" (one sentence explanation).
</Instructions>

<Reminder>
Reward responses that provide complete answers with no extraneous information.
Never reward hallucinated facts not present in the reference output.
</Reminder>

<input>{input}</input>
<output>{output}</output>
<referenceOutput>{reference}</referenceOutput>

Respond with valid JSON only, example: {{"score": 0.85, "comment": "Answer is accurate but slightly verbose."}}"""


def llm_judge_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> EvaluationResult:
    """
    Evaluador LLM-as-a-Judge usando Gemini.
    Replica la lógica del evaluador configurado en la plataforma LangSmith.
    """
    import json

    question  = inputs.get("question", "")
    answer    = outputs.get("answer", "")
    reference = reference_outputs.get("ground_truth", "")

    prompt = JUDGE_PROMPT.format(
        input=question,
        output=answer,
        reference=reference,
    )

    try:
        response  = _eval_llm.invoke([HumanMessage(content=prompt)])
        raw       = response.content.strip()
        # Limpiar posibles backticks de markdown
        raw       = raw.replace("```json", "").replace("```", "").strip()
        parsed    = json.loads(raw)
        score     = float(parsed.get("score", 0.0))
        comment   = parsed.get("comment", "")
    except Exception as e:
        score   = 0.0
        comment = f"Error en evaluación: {e}"

    return EvaluationResult(
        key="llm_judge",
        score=score,
        comment=comment,
    )


def faithfulness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> EvaluationResult:
    """
    Evalúa si la respuesta está basada en los contextos recuperados.
    Score 1.0 si no hay afirmaciones inventadas, 0.0 si hay alucinaciones claras.
    """
    import json

    answer   = outputs.get("answer", "")
    contexts = outputs.get("contexts", [])
    context_text = "\n---\n".join(contexts) if contexts else "No context available."

    prompt = f"""You are evaluating faithfulness: whether the answer is grounded in the provided context.

Context:
{context_text}

Answer:
{answer}

Score 1.0 if every claim in the answer is supported by the context.
Score 0.0 if the answer contains facts not present in the context (hallucinations).
Score between 0 and 1 for partial faithfulness.

Respond with valid JSON only: {{"score": 0.9, "comment": "brief explanation"}}"""

    try:
        response = _eval_llm.invoke([HumanMessage(content=prompt)])
        raw      = response.content.strip().replace("```json", "").replace("```", "").strip()
        parsed   = json.loads(raw)
        score    = float(parsed.get("score", 0.0))
        comment  = parsed.get("comment", "")
    except Exception as e:
        score   = 0.0
        comment = f"Error: {e}"

    return EvaluationResult(key="faithfulness", score=score, comment=comment)


def context_recall_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> EvaluationResult:
    """
    Evalúa si el contexto recuperado contiene la información necesaria
    para responder la pregunta según el ground truth.
    """
    import json

    question      = inputs.get("question", "")
    contexts      = outputs.get("contexts", [])
    reference     = reference_outputs.get("ground_truth", "")
    context_text  = "\n---\n".join(contexts) if contexts else "No context available."

    prompt = f"""You are evaluating context recall: whether the retrieved context contains the information needed to answer the question correctly.

Question: {question}
Ground Truth Answer: {reference}

Retrieved Context:
{context_text}

Score 1.0 if the context contains all the information needed to produce the ground truth answer.
Score 0.0 if the context is completely missing the relevant information.
Score between 0 and 1 for partial recall.

Respond with valid JSON only: {{"score": 0.8, "comment": "brief explanation"}}"""

    try:
        response = _eval_llm.invoke([HumanMessage(content=prompt)])
        raw      = response.content.strip().replace("```json", "").replace("```", "").strip()
        parsed   = json.loads(raw)
        score    = float(parsed.get("score", 0.0))
        comment  = parsed.get("comment", "")
    except Exception as e:
        score   = 0.0
        comment = f"Error: {e}"

    return EvaluationResult(key="context_recall", score=score, comment=comment)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n══ CV Agent Benchmark - Sprint 2 ══")
    print(f"   Dataset:    {DATASET_NAME}")
    print(f"   Evaluador:  {EVAL_MODEL}")
    print(f"   Experimento: {EXPERIMENT_PREFIX}\n")

    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[
            llm_judge_evaluator,
            faithfulness_evaluator,
            context_recall_evaluator,
        ],
        experiment_prefix=EXPERIMENT_PREFIX,
        metadata={
            "sprint":    "Sprint 2",
            "retriever": "SelfQuery + Diversify + ParentFetch + CohereRerank",
            "llm":       "llama-3.3-70b-versatile",
            "eval_llm":  EVAL_MODEL,
        },
        max_concurrency=1,  # Secuencial para evitar rate limits en Groq/Cohere
    )

    print(f"\n✓ Evaluación completada.")
    print(f"  Ver resultados en LangSmith: https://smith.langchain.com")


if __name__ == "__main__":
    main()