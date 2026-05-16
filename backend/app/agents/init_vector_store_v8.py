# backend/app/agents/init_vector_store_v8.py
"""
Init Vector Store V8 — Indexation Milvus
Indexe dans les 3 collections Milvus :
  1. ocp_sql_examples   ← dataset_400_questions + dataset_enrichment
  2. ocp_table_schemas  ← schema_global + schema_tenants
  3. ocp_join_patterns  ← standards_v3.JOINS

Usage :
    python init_vector_store_v8.py
    python init_vector_store_v8.py --reset      # supprime et recrée les collections
    python init_vector_store_v8.py --check      # affiche les stats sans indexer
"""

import argparse
import sys
from pathlib import Path

# Fix imports robustes
for p in [str(Path(__file__).parents[1]), str(Path(__file__).parents[2]), str(Path(__file__).parents[3])]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.database.dataset_400_questions import DATASET_400_QUESTIONS
    from app.database.dataset_enrichment    import NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES
    from app.database.schema_global         import ALL_TABLES as GLOBAL_TABLES
    from app.database.schema_tenants        import ALL_TABLES as TENANT_TABLES
    from app.database.standards_v3          import JOINS
    from app.agents.rag_agent_v8            import RAGAgentV8
except ImportError:
    from database.dataset_400_questions import DATASET_400_QUESTIONS
    from database.dataset_enrichment    import NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES
    from database.schema_global         import ALL_TABLES as GLOBAL_TABLES
    from database.schema_tenants        import ALL_TABLES as TENANT_TABLES
    from database.standards_v3          import JOINS
    from rag_agent_v8                   import RAGAgentV8

from pymilvus import MilvusClient

# Mapping normalisation catégories (identique à example_retriever_v7)
CATEGORY_MAP = {
    "equipements": "asset", "equipment": "asset",
    "alarmes": "alarm", "mesures": "measurement",
    "utilisateurs": "user", "entreprises": "company",
    "defauts": "fault", "défauts": "fault", "faults": "fault",
    "predictions": "prediction", "recommandations": "recommendation",
    "maintenance": "intervention",
}


def normalize_cat(raw: str) -> str:
    return CATEGORY_MAP.get((raw or "").lower(), (raw or "").lower())


# ─────────────────────────────────────────────────────────────────────────────
# Constructeurs de données
# ─────────────────────────────────────────────────────────────────────────────

def build_sql_examples() -> list:
    seen, examples = set(), []
    for source in [DATASET_400_QUESTIONS, NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES]:
        for ex in source:
            q   = (ex.get("question") or "").strip()
            sql = (ex.get("sql") or "").strip()
            if not q or not sql or q in seen:
                continue
            seen.add(q)
            meta = ex.get("metadata", {})
            examples.append({
                "question": q,
                "sql":      sql,
                "category": normalize_cat(meta.get("category", "")),
                "tables":   meta.get("tables", []),
            })
    print(f"  → {len(examples)} exemples SQL préparés.")
    return examples


def build_table_schemas() -> list:
    schemas = []
    for tname, schema in {**GLOBAL_TABLES, **TENANT_TABLES}.items():
        cols = schema.get("columns", {})
        if not cols:
            continue
        col_lines = [f"  {c} ({m.get('type','?')})" for c, m in list(cols.items())[:30]]
        rel_lines = [
            f"  JOIN {r.get('table','')} ON {r.get('on','')}"
            for r in schema.get("relationships", [])[:5]
        ]
        desc = schema.get("description", f"Table {tname}")
        text = f"TABLE {tname}\nDescription: {desc}\nColonnes:\n" + "\n".join(col_lines)
        if rel_lines:
            text += "\nJointures:\n" + "\n".join(rel_lines)
        schemas.append({"table_name": tname, "text": text, "description": desc})
    print(f"  → {len(schemas)} schémas préparés.")
    return schemas


def build_join_patterns() -> list:
    patterns = []
    for name, sql_pattern in JOINS.items():
        patterns.append({
            "text":        f"{name}: {sql_pattern[:200]}",
            "description": name,
            "sql_pattern": sql_pattern,
        })
    print(f"  → {len(patterns)} patterns de jointure préparés.")
    return patterns


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main(reset: bool = False, check: bool = False, milvus_uri: str = "http://localhost:19530"):
    print("\n" + "=" * 65)
    print("INIT VECTOR STORE V8 — MILVUS")
    print("=" * 65)
    print(f"URI Milvus : {milvus_uri}")

    # Mode check uniquement
    if check:
        rag = RAGAgentV8(milvus_uri=milvus_uri)
        stats = rag.get_collection_stats()
        print("\n📊 Stats collections :")
        for k, v in stats.items():
            print(f"  {k} : {v} documents")
        return

    # Reset optionnel
    if reset:
        print("\n⚠️  --reset : suppression des collections...")
        client = MilvusClient(uri=milvus_uri)
        for name in ["ocp_sql_examples", "ocp_table_schemas", "ocp_join_patterns"]:
            if client.has_collection(name):
                client.drop_collection(name)
                print(f"  Supprimé : {name}")

    # Instanciation RAG (crée les collections vides si besoin)
    print("\n[1/4] Connexion Milvus + chargement modèles ML...")
    rag = RAGAgentV8(milvus_uri=milvus_uri)

    print("\n[2/4] Indexation exemples SQL (dataset_400_questions + enrichments)...")
    rag.index_sql_examples(build_sql_examples())

    print("\n[3/4] Indexation schémas de tables...")
    rag.index_table_schemas(build_table_schemas())

    print("\n[4/4] Indexation patterns de jointure...")
    rag.index_join_patterns(build_join_patterns())

    stats = rag.get_collection_stats()
    print("\n" + "=" * 65)
    print("✅ INDEXATION TERMINÉE")
    print("=" * 65)
    for k, v in stats.items():
        print(f"  {k} : {v} documents")
    print("=" * 65)
    print("\nProchaine étape : python chat_cli_v8.py\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indexation Milvus V8")
    parser.add_argument("--reset",       action="store_true", help="Supprime et recrée les collections")
    parser.add_argument("--check",       action="store_true", help="Affiche les stats sans indexer")
    parser.add_argument("--milvus-uri",  default="http://localhost:19530", help="URI Milvus")
    args = parser.parse_args()
    main(reset=args.reset, check=args.check, milvus_uri=args.milvus_uri)
