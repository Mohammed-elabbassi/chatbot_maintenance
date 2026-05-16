# backend/app/agents/chat_cli_v8.py
"""Chat CLI V8 — Test interactif du PlannerAgentV8."""

import sys
from pathlib import Path

for p in [str(Path(__file__).parents[1]), str(Path(__file__).parents[2]), str(Path(__file__).parents[3])]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.agents.planner_agent_v8 import PlannerAgentV8
except ImportError:
    from planner_agent_v8 import PlannerAgentV8


def blk(title, value):
    print(f"\n{'-'*70}\n{title}\n{'-'*70}")
    print(value if value is not None else "None")


def main():
    agent = PlannerAgentV8()
    print("\n" + "="*70)
    print("CHAT CLI V8 — LangGraph + Groq LLaMA 3.1 8B + Milvus RAG Hybride")
    print("="*70)
    print("Commandes : 'exit' | 'sql on/off' | 'meta on/off'")
    print("="*70)

    show_sql = show_meta = True

    while True:
        q = input("\n🧑 Question > ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break
        if q.lower() in {"sql off", "sql on"}:
            show_sql = q.lower() == "sql on"
            print(f"SQL {'activé' if show_sql else 'désactivé'}.")
            continue
        if q.lower() in {"meta off", "meta on"}:
            show_meta = q.lower() == "meta on"
            print(f"Meta {'activé' if show_meta else 'désactivé'}.")
            continue

        r = agent.process_question(q)
        blk("RÉPONSE", r.get("natural_response"))
        print(
            f"\n✅ success={r.get('success')} | method={r.get('method')} | "
            f"tenant={r.get('tenant')} | category={r.get('category')} | "
            f"time={r.get('processing_time')}s | rows={r.get('row_count', 0)}"
        )
        if r.get("error"):        blk("ERREUR", r["error"])
        if show_sql  and r.get("sql"):   blk("SQL", r["sql"])
        if show_meta and r.get("meta"):  blk("META", r["meta"])
        if r.get("rows"):                blk("APERÇU (5 max)", r["rows"][:5])


if __name__ == "__main__":
    main()
