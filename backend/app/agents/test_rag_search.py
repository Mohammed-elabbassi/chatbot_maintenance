# test_rag_search.py
import sys
sys.path.insert(0, "chatbot_maintenance/backend")

from app.agents.rag_agent_v8 import RAGAgentV8

print("Initialisation du RAG Agent...")
rag = RAGAgentV8()

print("\nRecherche dans Milvus en cours...")
ctx = rag.build_prompt_context(
    question="Quels équipements ont une alarme critique à Safi ?",
    tenant_db="v3_tenant_safi",
    intent=None,
    max_chars=1500,
)

print("\n✅ Contexte RAG récupéré (premiers 500 caractères) :\n")
print(ctx[:1000])