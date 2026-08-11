import networkx as nx

class KnowledgeGraphStore:
    """
    NetworkX Knowledge Graph engine for multi-hop entity-relation assertions.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self):
        self.graph.add_edge("Local RAG Optimization", "Ollama", relation="powered_by")
        self.graph.add_edge("Local RAG Optimization", "FAISS", relation="uses")
        self.graph.add_edge("GraphRAG & Knowledge Graphs", "NetworkX", relation="built_with")
        self.graph.add_edge("Corrective RAG (CRAG)", "Cross-Encoder", relation="evaluated_by")
        self.graph.add_edge("Hardware Quantization & Acceleration", "CUDA", relation="runs_on")
        self.graph.add_edge("Language Agent Grammars (LAG)", "Pydantic DFA", relation="enforced_by")

    def query_graph(self, query: str) -> list:
        kg_results = []
        for node in self.graph.nodes:
            if node.lower() in query.lower():
                for neighbor in self.graph.neighbors(node):
                    edge_data = self.graph.get_edge_data(node, neighbor)
                    kg_results.append(f"KG Assertion: {node} --[{edge_data['relation']}]--> {neighbor}")
        return kg_results
