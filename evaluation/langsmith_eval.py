from langsmith import Client
from langchain_ollama import ChatOllama

client = Client()
eval_llm = ChatOllama(model="gemma4:e4b-it", temperature=0)

DATASET_NAME = "enterprise-crag-eval-dataset"


def _ensure_dataset() -> str:
    # 1. Create dataset if it doesn't exist
    if not client.has_dataset(dataset_name=DATASET_NAME):
        ds = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Evaluation dataset for Enterprise Agentic Nexus pipeline",
        )
        client.create_examples(
            inputs=[
                {"question": "How does Corrective RAG (CRAG) handle context failures?"},
                {"question": "What is the main benefit of Language Agent Grammars (LAG)?"},
                {"question": "How does GraphRAG improve complex technical domains?"},
            ],
            outputs=[
                {
                    "answer": "CRAG dynamically evaluates retrieval scores using Cross-Encoders, triggering web search fallbacks when local context fails."
                },
                {
                    "answer": "Enforcing strict DFA JSON schemas on agent outputs eliminates parsing errors and ensures deterministic multi-agent communication."
                },
                {
                    "answer": "Combining NetworkX Knowledge Graphs with Vector Stores improves multi-hop reasoning."
                },
            ],
            dataset_id=ds.id,  # Fix: Use the created dataset object's id
        )

    # 2. Return dataset name expected by evaluate()
    return DATASET_NAME


def _correctness_evaluator(run, example):
    student_output = run.outputs.get("final_response", "") if run.outputs else ""
    reference_output = example.outputs.get("answer", "") if example.outputs else ""

    eval_prompt = f"""You are an expert evaluator. Compare the Student Answer to the Reference Answer.
Reference Answer: {reference_output}
Student Answer: {student_output}

Is the student answer correct and aligned with the reference?
Answer with '1' for Yes or '0' for No, followed by a short explanation."""

    score_response = eval_llm.invoke(eval_prompt).content
    res_text = score_response.content if hasattr(score_response, "content") else str(score_response)
    is_correct = 1 if "1" in res_text[:5] else 0
    return {"key": "correctness", "score": is_correct}


def run_langsmith_evaluation(predict_fn):
    """Runs the LangSmith dataset evaluation against predict_fn."""
    try:
        dataset_name = _ensure_dataset()
        from langsmith.evaluation import evaluate

        results = evaluate(
            predict_fn,
            data=dataset_name,
            evaluators=[_correctness_evaluator],
            experiment_prefix="enterprise-nexus-eval",
        )
        print("-> [LangSmith Eval]: Completed. Check your LangSmith project for results.")
        return results
    except Exception as e:
        print(f"-> [LangSmith Eval Skipped]: {type(e).__name__} - {e}")
        return None
