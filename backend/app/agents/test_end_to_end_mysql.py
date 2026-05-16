# test_end_to_end_mysql.py
# ============================================================
# TEST COMPLET AVEC EXÉCUTION MYSQL — 3 MODES
# Mode 1 : Toutes les questions automatiquement
# Mode 2 : Saisir une question manuelle
# Mode 3 : Questions une par une avec pause
# ============================================================

import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, "chatbot_maintenance/backend")

try:
    from app.agents.planner_agent_v8 import PlannerAgentV8
except ImportError:
    from agents.planner_agent_v8 import PlannerAgentV8

QUESTIONS = [
    "Combien d'équipements ?",
    "les équipements critiques ?",
    "Quels équipements ont une alarme critique à Safi ?",
    "Combien de pannes actives ce mois ?",
    "Top 5 assets avec le plus de défauts",
    "Quels sont les équipements présentant actuellement un problème de roulement ?",
    "Quelle est la mesure NGV la plus élevée aujourd'hui ?",
    "Combien d'équipements à NTN ?",
    "Top 5 assets avec le plus de défauts a Safi ?",
    "Bonjour, tu peux m'aider ?",
    "Supprime tous les assets",
]


def sep(char="─", width=70):
    print(char * width)


def afficher_resultat(question: str, r: dict, idx: int = None):
    titre = f"QUESTION {idx} : {question}" if idx else f"QUESTION : {question}"
    print(f"\n{'═'*70}")
    print(f"  {titre}")
    print(f"{'═'*70}")

    success   = r.get("success", False)
    method    = r.get("method", "?")
    tenant    = r.get("tenant", "?")
    category  = r.get("category", "?")
    rows      = r.get("row_count", 0)
    elapsed   = r.get("processing_time", "?")
    sql       = r.get("sql", "")
    response  = r.get("natural_response", "")
    error     = r.get("error", "")
    data_rows = r.get("rows", [])
    columns   = r.get("columns", [])

    icon = "✅" if success else "❌"
    print(f"\n{icon} success={success} | method={method} | tenant={tenant} | "
          f"category={category} | rows={rows} | time={elapsed}s")

    # ── SQL ──────────────────────────────────────────────────
    if sql:
        sep()
        print("📋 REQUÊTE SQL GÉNÉRÉE :")
        sep()
        sql_fmt = (sql
            .replace(" FROM ",       "\nFROM ")
            .replace(" INNER JOIN ", "\nINNER JOIN ")
            .replace(" LEFT JOIN ",  "\nLEFT JOIN ")
            .replace(" WHERE ",      "\nWHERE ")
            .replace(" AND ",        "\n  AND ")
            .replace(" GROUP BY ",   "\nGROUP BY ")
            .replace(" ORDER BY ",   "\nORDER BY ")
            .replace(" LIMIT ",      "\nLIMIT ")
        )
        for line in sql_fmt.split("\n"):
            print(f"  {line}")

    # ── Données MySQL ─────────────────────────────────────────
    if data_rows:
        sep()
        print(f"📊 DONNÉES RÉCUPÉRÉES DE MySQL ({rows} lignes) :")
        sep()
        if columns:
            widths = {}
            for col in columns:
                widths[col] = max(len(str(col)), 10)
                for row in data_rows[:20]:
                    widths[col] = min(max(widths[col], len(str(row.get(col, "")))), 35)

            header = " | ".join(str(c).ljust(widths[c]) for c in columns)
            print(f"  {header}")
            print(f"  {'-' * len(header)}")
            for row in data_rows[:10]:
                line = " | ".join(
                    str(row.get(c, ""))[:widths[c]].ljust(widths[c]) for c in columns
                )
                print(f"  {line}")
            if rows > 10:
                print(f"  ... ({rows - 10} lignes supplémentaires)")
        else:
            for i, row in enumerate(data_rows[:10]):
                print(f"  [{i+1}] {row}")
    elif success and method not in ("small_talk", "blocked_nl", "direct"):
        sep()
        print("📊 DONNÉES RÉCUPÉRÉES DE MySQL :")
        sep()
        print("  ⚠ Aucune donnée retournée (0 résultats)")

    # ── Réponse finale ────────────────────────────────────────
    if response:
        sep()
        print("💬 RÉPONSE FINALE (Groq) :")
        sep()
        for line in response.split("\n"):
            print(f"  {line}")

    if error and error != response:
        sep()
        print(f"❌ ERREUR : {error[:200]}")

    sep()
    print(f"  ⏱  Total : {elapsed}s | Méthode : {method} | DB : {tenant} | Lignes : {rows}")


def traiter(agent, question, idx=None):
    r = agent.process_question(question)
    afficher_resultat(question, r, idx)
    return {
        "question": question,
        "success":  r.get("success", False),
        "method":   r.get("method", "?"),
        "rows":     r.get("row_count", 0),
        "time":     r.get("processing_time", 0),
    }


def stats(results):
    total    = len(results)
    passed   = sum(1 for r in results if r["success"])
    avg_time = round(sum(r["time"] for r in results) / total, 2) if total else 0
    methods  = {}
    for r in results:
        methods[r["method"]] = methods.get(r["method"], 0) + 1

    print(f"\n{'='*70}")
    print("RÉSULTATS FINAUX")
    print(f"{'='*70}")
    print(f"\n  Tests passés : {passed}/{total}")
    print(f"  Temps moyen  : {avg_time}s")
    print(f"  Méthodes     : {methods}")
    print(f"\n  {'✅ TOUS OK' if passed == total else f'❌ {total-passed} ÉCHECS'}")
    sep()
    print("Détail :")
    sep()
    for r in results:
        icon = "✅" if r["success"] else "❌"
        print(f"  {icon} [{r['method']:<25}] {r['time']}s | rows={r['rows']} | {r['question'][:50]}")
    print(f"\n{'='*70}")


def main():
    print("=" * 70)
    print("TEST END-TO-END MYSQL — PlannerAgentV8")
    print("=" * 70)

    print("\n[INIT] Chargement des agents...")
    t0 = time.time()
    agent = PlannerAgentV8()
    print(f"[INIT] ✅ Prêt en {round(time.time()-t0, 1)}s")

    print("\nChoisir le mode :")
    print("  1 = Toutes les questions automatiquement")
    print("  2 = Saisir une question manuelle")
    print("  3 = Questions une par une avec pause")
    choix = input("\nChoix (1/2/3) : ").strip()

    results = []

    if choix == "1":
        for i, q in enumerate(QUESTIONS, 1):
            results.append(traiter(agent, q, i))
        stats(results)

    elif choix == "2":
        print("\nTape 'exit' pour quitter.\n")
        idx = 1
        while True:
            q = input("📝 Question > ").strip()
            if not q:
                continue
            if q.lower() in {"exit", "quit"}:
                break
            results.append(traiter(agent, q, idx))
            idx += 1
        if results:
            stats(results)

    elif choix == "3":
        for i, q in enumerate(QUESTIONS, 1):
            results.append(traiter(agent, q, i))
            if i < len(QUESTIONS):
                cont = input("\n  ⏎ Entrée pour continuer (ou 'stop') : ").strip()
                if cont.lower() == "stop":
                    break
        stats(results)

    else:
        traiter(agent, QUESTIONS[0], 1)


if __name__ == "__main__":
    main()