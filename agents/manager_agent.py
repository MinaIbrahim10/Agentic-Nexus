from langsmith import traceable
from config import llm
from agents.lag_grammar import OrchestratorPlan

# Bind Pydantic schema for Language Agent Grammar (LAG) compliance
structured_llm = llm.with_structured_output(OrchestratorPlan)

@traceable(run_type="chain", name="Manager_Orchestrator_Agent")
def run_manager_agent(user_query: str) -> OrchestratorPlan:
    prompt = f"Deconstruct this complex user request into structured sub-tasks: {user_query}"
    plan = structured_llm.invoke(prompt)
    return plan
