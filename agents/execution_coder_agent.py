from langsmith import traceable
from config import llm
from rag_pipeline.data_engine import CAGDataEngine

@traceable(run_type="chain", name="Coder_Execution_Agent")
def run_execution_coder_agent(
    query: str,
    context: list,
    data_engine: CAGDataEngine,
    chat_history: list = None,
    **kwargs
):
    # Run structured SQL query against DuckDB
    sql_records = data_engine.duck_con.execute("SELECT topic, sector FROM ai_market_research").fetchall()

    formatted_context = "\n".join(context) if context else "No additional context provided."

    # Format chat history if provided
    formatted_history = ""
    if chat_history:
        formatted_history = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in chat_history])

    prompt = f"""You are the Coder & Technical Execution Agent.

Chat History:
{formatted_history}

Context:
{formatted_context}

DuckDB Records Snapshot: {sql_records}

User Query: {query}
Generate a detailed technical response using the provided information."""

    response = llm.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)
