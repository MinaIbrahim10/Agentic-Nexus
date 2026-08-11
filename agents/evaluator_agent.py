from langsmith import traceable
from config import llm

@traceable(run_type="chain", name="Observer_Evaluator_Agent")
def run_evaluator_agent(query: str, final_response: str) -> dict:
    prompt = f"""Evaluate whether the response properly answers the user query without hallucination.
Query: {query}
Response: {final_response}

Answer with '1' for pass or '0' for fail followed by a concise reason."""

    eval_result = llm.invoke(prompt).content
    score = 1 if "1" in eval_result[:3] else 0
    return {"score": score, "reasoning": eval_result}
