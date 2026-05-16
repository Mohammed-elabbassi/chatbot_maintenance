# test_rag_basic.py
import sys
sys.path.insert(0, "chatbot_maintenance/backend")
from app.agents.rag_agent_v8 import RAGAgentV8

print("Chargement RAG (30-60s première fois)...")
rag = RAGAgentV8()

stats = rag.get_collection_stats()
print("Stats collections:", stats)
# Si tout est 0 → normal, pas encore indexé