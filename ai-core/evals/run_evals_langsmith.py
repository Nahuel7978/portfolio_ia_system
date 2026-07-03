"""
run_evals_langsmith.py
Ejecuta el benchmark del Agente CV contra el Golden Dataset en LangSmith.

Flujo:
    1. Carga el dataset desde LangSmith por nombre
    2. Invoca el grafo LangGraph (cv_agent_app) por cada ejemplo
    3. Evalúa con el evaluador LLM-as-a-Judge configurado en LangSmith
    4. Los resultados quedan visibles en la plataforma

Uso: python evals/run_evals_langsmith.py
"""

import os
import sys
import json
from dotenv import load_dotenv
import uuid
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langsmith import Client, aevaluate
from langsmith.evaluation import EvaluationResult
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Importamos el Grafo global en lugar del antiguo chain
from src.agent.graph import cv_agent_app

# ── Configuración ─────────────────────────────────────────────────────────────
load_dotenv()

DATASET_NAME      = "golden_ds_portfolio"
EXPERIMENT_PREFIX = "cv-agent-sprint7-langgraph"

# Usamos Llama 3.3 70B vía OpenRouter como juez evaluador
EVAL_MODEL        = "meta-llama/llama-3.3-70b-instruct"

# ── Configuración del Evaluador OpenRouter ────────────────────────────────────
_eval_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model=EVAL_MODEL,
    temperature=0.0
)

# ── Función objetivo ──────────────────────────────────────────────────────────
async def target(inputs: dict) -> dict:
    """
    Invocada por LangSmith por cada fila del dataset.
    Retorna answer y contexts extrayéndolos del AgentState de LangGraph.
    """
    question = inputs["question"]
    # Generamos un ID de hilo simulado para aislar la memoria del Grafo
    session_id = "eval_" + str(os.urandom(4).hex())
    config = {"configurable": {"thread_id": session_id}}
    
    # Invocamos el Grafo de LangGraph
    result = await cv_agent_app.ainvoke(
        {"messages": [HumanMessage(content=question)]}, 
        config=config
    )

    # Extraemos la respuesta final y el contexto del estado
    final_answer = result["messages"][-1].content
    context_docs = result.get("context", [])

    return {
        "answer": final_answer,
        "contexts": [doc.page_content for doc in context_docs] if context_docs else []
    }

# ── Evaluadores Personalizados (LLM-as-a-Judge) ───────────────────────────────
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
    import json
    question  = inputs.get("question", "")
    answer    = outputs.get("answer", "")
    reference = reference_outputs.get("ground_truth", "")

    prompt = JUDGE_PROMPT.format(input=question, output=answer, reference=reference)

    try:
        response  = _eval_llm.invoke([HumanMessage(content=prompt)])
        raw       = response.content.strip()
        raw       = raw.replace("```json", "").replace("```", "").strip()
        parsed    = json.loads(raw)
        score     = float(parsed.get("score", 0.0))
        comment   = parsed.get("comment", "")
    except Exception as e:
        score   = 0.0
        comment = f"Error en evaluación: {e}"

    return EvaluationResult(key="llm_judge", score=score, comment=comment)

def faithfulness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> EvaluationResult:
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
async def main():
    print(f"\n══ CV Agent Benchmark - Integración LangGraph ══")
    print(f"   Dataset:    {DATASET_NAME}")
    print(f"   Evaluador:  {EVAL_MODEL}")
    print(f"   Experimento: {EXPERIMENT_PREFIX}\n")

    results = await aevaluate(
        target,
        data=DATASET_NAME,
        evaluators=[
            llm_judge_evaluator,
            faithfulness_evaluator,
            context_recall_evaluator,
        ],
        experiment_prefix=EXPERIMENT_PREFIX,
        metadata={
            "sprint":    "Sprint 7",
            "retriever": "LangGraph + Chroma HTTP",
            "llm":       "openrouter/agent",
            "eval_llm":  EVAL_MODEL,
        },
        max_concurrency=1,
    )

if __name__ == "__main__":
    asyncio.run(main())