from pydantic import BaseModel, Field
from typing import List, Literal

class SubTask(BaseModel):
    task_id: int
    assigned_agent: Literal["HybridRAG", "CoderExecution", "DirectAnswer"]
    description: str
    query: str

class OrchestratorPlan(BaseModel):
    reasoning: str = Field(description="Deterministic reasoning for task decomposition")
    sub_tasks: List[SubTask]
