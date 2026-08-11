from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

from config import llm
from rag_pipeline.data_engine import CAGDataEngine
from rag_pipeline.graph_store import KnowledgeGraphStore
from agents.lag_grammar import OrchestratorPlan
from agents.manager_agent import run_manager_agent
from agents.hybrid_rag_agent import run_hybrid_rag_agent, web_search_tool
from agents.execution_coder_agent import run_execution_coder_agent
from agents.evaluator_agent import run_evaluator_agent
from evaluation.langsmith_eval import run_langsmith_evaluation

data_engine = CAGDataEngine()
graph_store = KnowledgeGraphStore()

MAX_EVAL_RETRIES = 1


class NexusState(TypedDict):
    user_query: str
    plan: Optional[OrchestratorPlan]
    next_action: str
    context: List[str]
    crag_status: str
    crag_score: float
    final_response: str
    evaluation: dict
    eval_retry_count: int
    chat_history: List[dict]


def manager_node(state: NexusState):
    plan = run_manager_agent(state["user_query"])
    agent_types = [getattr(task, "assigned_agent", "") for task in plan.sub_tasks]

    if not agent_types or all(a == "DirectAnswer" for a in agent_types):
        next_action = "direct_answer"
    elif all(a == "HybridRAG" for a in agent_types):
        next_action = "rag_only"
    elif all(a == "CoderExecution" for a in agent_types):
        next_action = "coder_only"
    else:
        next_action = "full_pipeline"

    print(f"-> [Manager Router]: Planned Route Strategy -> '{next_action}'")
    return {"plan": plan, "next_action": next_action, "context": []}


def direct_answer_node(state: NexusState):
    print("-> [Direct Answer Node]: Executing direct response (Bypassing RAG & Coder)...")
    history_text = "\n".join(
        [f"{m['role']}: {m['content']}" for m in state["chat_history"][-4:]]
    )
    prompt = f"""Previous conversation:
{history_text if history_text else "(no prior turns)"}

Answer the user's current query directly and concisely, using the conversation
above for context if the query refers back to it:
{state['user_query']}"""
    response = llm.invoke(prompt)
    res_text = response.content if hasattr(response, "content") else str(response)
    return {"final_response": res_text, "crag_status": "DIRECT_PASSTHROUGH", "crag_score": 1.0}


def hybrid_rag_node(state: NexusState):
    result = run_hybrid_rag_agent(state["user_query"], data_engine, graph_store)
    score = result.get("score") or result.get("confidence_score") or result.get("relevance_score") or 0.0
    status = result.get("status") or result.get("crag_status") or "UNKNOWN"
    return {
        "context": result.get("context", []),
        "crag_status": status,
        "crag_score": float(score),
    }


def web_fallback_node(state: NexusState):
    print("-> [CRAG Web Fallback Node]: Fetching external context...")
    try:
        web_results = web_search_tool.run(state["user_query"])
        if not web_results:
            web_results = "Web search returned no results."
    except Exception as e:
        print(f"[Web Fallback Warning]: {type(e).__name__} - {e}")
        web_results = f"Web search unavailable due to network/API restriction. Query context: {state['user_query']}"
    return {"context": [str(web_results)], "crag_status": "WEB_FALLBACK_EXECUTED"}


def coder_node(state: NexusState):
    feedback = state.get("evaluation", {}).get("reasoning", "") if state.get("eval_retry_count", 0) > 0 else ""
    response = run_execution_coder_agent(
        state["user_query"],
        state["context"],
        data_engine,
        state["chat_history"],
        crag_status=state.get("crag_status", ""),
        evaluator_feedback=feedback,
    )
    return {"final_response": response}


def evaluator_node(state: NexusState):
    evaluation = run_evaluator_agent(state["user_query"], state["final_response"])
    return {"evaluation": evaluation}


def bump_eval_retry(state: NexusState):
    return {"eval_retry_count": state.get("eval_retry_count", 0) + 1}


def route_from_manager(state: NexusState) -> str:
    action = state.get("next_action", "full_pipeline")
    if action == "direct_answer":
        return "direct_answer"
    elif action == "coder_only":
        return "coder"
    else:
        return "hybrid_rag"


def route_after_rag(state: NexusState) -> str:
    if state["crag_score"] < 0.4:
        print(f"-> [CRAG Decision]: Low Confidence ({state['crag_score']:.2f}). Triggering Fallback.")
        return "web_fallback"
    return "coder"


def route_after_evaluation(state: NexusState) -> str:
    if state["evaluation"]["score"] == 0 and state.get("eval_retry_count", 0) < MAX_EVAL_RETRIES:
        print("-> [Routing]: evaluation FAILED, retrying generation with feedback.")
        return "retry"
    return "end"


workflow = StateGraph(NexusState)

workflow.add_node("manager", manager_node)
workflow.add_node("direct_answer", direct_answer_node)
workflow.add_node("hybrid_rag", hybrid_rag_node)
workflow.add_node("web_fallback", web_fallback_node)
workflow.add_node("coder", coder_node)
workflow.add_node("bump_eval_retry", bump_eval_retry)
workflow.add_node("evaluator", evaluator_node)

workflow.set_entry_point("manager")

workflow.add_conditional_edges(
    "manager",
    route_from_manager,
    {"direct_answer": "direct_answer", "coder": "coder", "hybrid_rag": "hybrid_rag"},
)

workflow.add_conditional_edges(
    "hybrid_rag",
    route_after_rag,
    {"web_fallback": "web_fallback", "coder": "coder"},
)

workflow.add_edge("web_fallback", "coder")
workflow.add_edge("direct_answer", "evaluator")
workflow.add_edge("coder", "evaluator")

workflow.add_conditional_edges(
    "evaluator",
    route_after_evaluation,
    {"retry": "bump_eval_retry", "end": END},
)

workflow.add_edge("bump_eval_retry", "coder")

app = workflow.compile()


def fresh_state(user_query: str, chat_history: list) -> dict:
    return {
        "user_query": user_query,
        "plan": None,
        "next_action": "",
        "context": [],
        "crag_status": "",
        "crag_score": 0.0,
        "final_response": "",
        "evaluation": {},
        "eval_retry_count": 0,
        "chat_history": chat_history,
    }


def predict_for_evaluation(inputs: dict) -> dict:
    question = inputs.get("question", "")
    result = app.invoke(fresh_state(question, []))
    return {"final_response": result["final_response"]}


if __name__ == "__main__":
    chat_history = []

    print("Executing Enterprise-Agentic-Nexus Pipeline Test Runs...\n")

    q1 = "How do Language Agent Grammars (LAG) enforce structural outputs?"
    out1 = app.invoke(fresh_state(q1, chat_history))

    chat_history.append({"role": "user", "content": q1})
    chat_history.append({"role": "assistant", "content": out1["final_response"]})

    print(f"\nQuery 1 Response:\n{out1['final_response']}\n")
    print(f"CRAG Status: {out1['crag_status']} (Score: {out1['crag_score']:.2f})")
    print(f"Evaluator Score: {out1['evaluation'].get('score', 0)}/1\n")
    print("=" * 70)

    q2 = "Summarize what we discussed about it."
    out2 = app.invoke(fresh_state(q2, chat_history))

    print(f"\nQuery 2 Multi-Turn Response:\n{out2['final_response']}\n")
    print("=" * 70)

    run_langsmith_evaluation(predict_for_evaluation)
