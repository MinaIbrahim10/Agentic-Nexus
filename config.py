import os
from langchain_ollama import ChatOllama, OllamaEmbeddings

# LangSmith Tracing & Observability Configuration
os.environ["LANGCHAIN_TRACING_V2"] = "false"
#os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
#os.environ["LANGCHAIN_API_KEY"] = ""
#os.environ["LANGCHAIN_PROJECT"] = "Enterprise-Agentic-Nexus"

# Initialize Local LLM with Context Keep-Alive (CAG optimization)
llm = ChatOllama(
    model="gemma4:e4b-it",
    temperature=0,
    keep_alive="15m",
    num_ctx=8192,
)

# Initialize Local Embedding Model
embeddings = OllamaEmbeddings(
    model="bge-m3:latest"
)
