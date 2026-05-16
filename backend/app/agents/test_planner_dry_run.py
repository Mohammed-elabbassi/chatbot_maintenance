# test_planner_dry_run.py
# ============================================================
# TEST PLANNER V8 — MODE DRY RUN (sans exécution MySQL)
# On voit :
#   1. L'INTENT détecté (category, action, tenant, entities)
#   2. Les TABLES sélectionnées par SchemaRegistry
#   3. Le CONTEXTE RAG récupéré depuis Milvus (exemples similaires)
#   4. Le PROMPT complet envoyé à Groq
#   5. La REQUÊTE SQL générée par Groq (sans l'exécuter)
#   6. La VALIDATION (guardrails + validator)
# ============================================================

import sys
import time
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, "chatbot_maintenance/backend")

# ── Imports agents ──────────────────────────────────────────
try:
    from app.agents.intent_classifier_v7  import IntentClassifierV7
    from app.agents.guardrails_v7         import GuardrailsV7
    from app.agents.schema_registry_v7    import SchemaRegistryV7
    from app.agents.example_retriever_v7  import ExampleRetrieverV7
    from app.agents.rag_agent_v8          import RAGAgentV8
    from app.agents.prompt_builder_v7     import PromptBuilderV7
    from app.agents.llm_agent_v8          import LLMAgentV8
    from app.agents.sql_validator_v7      import SQLValidatorV7
except ImportError:
    from agents.intent_classifier_v7  import IntentClassifierV7
    from agents.guardrails_v7         import GuardrailsV7
    from agents.schema_registry_v7    import SchemaRegistryV7
    from agents.example_retriever_v7  import ExampleRetrieverV7
    from agents.rag_agent_v8          import RAGAgentV8
    from agents.prompt_builder_v7     import PromptBuilderV7
    from agents.llm_agent_v8          import LLMAgentV8
    from agents.sql_validator_v7      import SQLValidatorV7

# ── Questions à tester ──────────────────────────────────────
QUESTIONS = [
    "Quels équipements ont une alarme critique ?",
     "Quel est le statut actuel de l'équipement 'Pompe 03XYP23'?",
    "Combien de pannes actives ce mois ?",
    "Top 5 assets avec le plus de défauts ",
    "les équipements critiques  ?",
    "Quelle est la mesure NGV la plus élevée aujourd'hui ?",
    "Combien d'équipements ?",
    "Quel est le statut actuel de l'équipement 'Pompe 03XYP23'?",
    "Quels sont les équipements présentant actuellement un problème de roulement ?",
    "Quels équipements ont une alarme critique a Safi?",
     "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' a Safi?",
    "Combien de pannes actives ce mois a Safi ?",
    "Top 5 assets avec le plus de défauts a Safi?",
    "les équipements critiques a NTN? ",
    "Quelle est la mesure NGV la plus élevée aujourd'hui a Safi?",
    "Combien d'équipements a NOMAC?",
    "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' a NTN?",
    "Quels sont les équipements présentant actuellement un problème de roulement a Safi?",


]

# ── Initialisation des agents ────────────────────────────────
print("=" * 70)
print("TEST PLANNER DRY RUN — Groq + RAG Milvus (sans exécution MySQL)")
print("=" * 70)

print("\n[INIT] Chargement des agents (30-60s pour les modèles ML)...")
t_init = time.time()

clf       = IntentClassifierV7()
guard     = GuardrailsV7()
registry  = SchemaRegistryV7()
retriever = ExampleRetrieverV7()
pb        = PromptBuilderV7()
llm       = LLMAgentV8()
validator = SQLValidatorV7()

print("[INIT] Chargement RAG (MiniLM + CrossEncoder)...")
rag = RAGAgentV8()

print(f"[INIT] ✅ Tous les agents prêts en {round(time.time()-t_init, 1)}s\n")

# ── Séparateur visuel ────────────────────────────────────────
def sep(title="", char="─", width=70):
    if title:
        side = (width - len(title) - 2) // 2
        print(f"\n{'─'*side} {title} {'─'*side}")
    else:
        print("─" * width)

# ── Traitement d'une question ────────────────────────────────
def analyse_question(question: str, idx: int):
    print(f"\n{'═'*70}")
    print(f"  QUESTION {idx} : {question}")
    print(f"{'═'*70}")

    total_start = time.time()

    # ── ÉTAPE 1 : Guardrails NL ──────────────────────────────
    sep("ÉTAPE 1 — Guardrails NL")
    guard_result = guard.check_nl(question)
    if not guard_result["safe"]:
        print(f"  🔒 BLOQUÉ : {guard_result['reason']}")
        print(f"  ⏱  Temps total : {round(time.time()-total_start, 3)}s")
        return
    print(f"  ✅ Sécurité NL : OK (question autorisée)")

    # ── ÉTAPE 2 : Intent Classification ─────────────────────
    sep("ÉTAPE 2 — Intent Classification")
    t0 = time.time()
    intent = clf.classify(question)
    print(f"  category   : {intent.category}")
    print(f"  action     : {intent.action}")
    print(f"  confidence : {intent.confidence:.2f}")
    print(f"  entities   : {intent.entities}")
    print(f"  modifiers  : {getattr(intent, 'modifiers', [])}")
    print(f"  ⏱  {round(time.time()-t0, 3)}s")

    # Récupérer tenant
    tenant_raw = (intent.entities or {}).get("tenant") or "jln"
    tenant_db  = registry.get_tenant_db(tenant_raw)
    print(f"\n  tenant raw : '{tenant_raw}' → DB : '{tenant_db}'")

    # ── ÉTAPE 3 : Tables sélectionnées ──────────────────────
    sep("ÉTAPE 3 — Tables sélectionnées (SchemaRegistry)")
    t0 = time.time()
    tables = registry.get_relevant_tables_from_intent(intent)
    print(f"  Tables retenues : {tables}")

    schema_context = registry.get_compact_schema_for_tables(tables, tenant_db)
    join_hints     = registry.get_join_hints(tables, tenant_db)

    print(f"\n  ── Schéma compact ──")
    for line in schema_context.split("\n")[:20]:   # 20 premières lignes
        print(f"  {line}")
    if schema_context.count("\n") > 20:
        print(f"  ... ({schema_context.count(chr(10))} lignes total)")

    print(f"\n  ── Join hints ──")
    for line in join_hints.split("\n")[:8]:
        print(f"  {line}")
    print(f"  ⏱  {round(time.time()-t0, 3)}s")

    # ── ÉTAPE 4 : Exemples BM25 (ExampleRetriever) ──────────
    sep("ÉTAPE 4 — Exemples BM25 (ExampleRetriever)")
    t0 = time.time()
    examples_primary  = retriever.retrieve_examples(question, intent, top_k=4)
    examples_category = retriever.retrieve_category_examples(intent, top_k=2)
    examples_merged   = retriever.merge_examples(examples_primary, examples_category, max_total=5)
    examples_context  = retriever.format_examples_for_prompt(examples_merged, tenant_db)
    print(f"  {len(examples_merged)} exemples récupérés par BM25 :")
    for i, ex in enumerate(examples_merged, 1):
        print(f"  [{i}] {ex['question'][:65]}")
    print(f"  ⏱  {round(time.time()-t0, 3)}s")

    # ── ÉTAPE 5 : Contexte RAG Milvus ───────────────────────
    sep("ÉTAPE 5 — Contexte RAG Milvus (Dense+BM25+RRF+CrossEncoder)")
    t0 = time.time()
    rag_context = rag.build_prompt_context(
        question=question,
        tenant_db=tenant_db,
        intent=intent,
        max_chars=2000,
    )
    print(f"  Contexte RAG ({len(rag_context)} chars) :")
    print()
    # Affichage structuré du contexte RAG
    for line in rag_context.split("\n")[:30]:
        print(f"  {line}")
    if rag_context.count("\n") > 30:
        print(f"  ... ({rag_context.count(chr(10))} lignes total)")
    print(f"\n  ⏱  RAG : {round(time.time()-t0, 3)}s")

    # ── ÉTAPE 6 : Construction du Prompt complet ─────────────
    sep("ÉTAPE 6 — Prompt complet envoyé à Groq")
    system_prompt = pb.build_sql_system_prompt()
    user_prompt   = pb.build_sql_user_prompt(
        question=question,
        tenant_db=tenant_db,
        intent=intent,
        schema_context=schema_context,
        join_hints=join_hints,
        examples_context=examples_context,
        category_examples_context="",
        negative_examples_context="",
        rag_context=rag_context,
    )
    print(f"\n  ── SYSTEM PROMPT ({len(system_prompt)} chars) ──")
    for line in system_prompt.split("\n")[:10]:
        print(f"  {line}")

    print(f"\n  ── USER PROMPT ({len(user_prompt)} chars) ──")
    for line in user_prompt.split("\n")[:30]:
        print(f"  {line}")
    if user_prompt.count("\n") > 30:
        print(f"  ... ({user_prompt.count(chr(10))} lignes total)")

    total_prompt_chars = len(system_prompt) + len(user_prompt)
    print(f"\n  📊 Taille totale prompt : {total_prompt_chars} chars")

    # ── ÉTAPE 7 : Génération SQL par Groq ───────────────────
    sep("ÉTAPE 7 — Génération SQL par Groq LLaMA 3.1 8B")
    t0 = time.time()
    result = llm.generate_json(
        prompt=user_prompt,
        system=system_prompt,
        temperature=0.05,
        max_tokens=2048,
    )
    groq_time = round(time.time()-t0, 3)

    if not result.get("success"):
        print(f"  ❌ Groq erreur : {result.get('error')}")
        print(f"  Raw : {result.get('raw_response', '')[:3000]}")
        return

    parsed = result.get("parsed", {})
    decision = parsed.get("decision", "?")
    sql_generated = parsed.get("sql", "")
    reasoning = parsed.get("reasoning", "")
    tables_used = parsed.get("tables", [])

    print(f"\n  decision  : {decision}")
    print(f"  reasoning : {reasoning}")
    print(f"  tables    : {tables_used}")
    print(f"  tokens    : {result.get('tokens', '?')}")
    print(f"  ⏱  Groq   : {groq_time}s")

    print(f"\n  ── SQL GÉNÉRÉ PAR GROQ ──────────────────────────────")
    print()
    if sql_generated:
        for line in sql_generated.split("\n"):
            print(f"  {line}")
    else:
        print(f"  (aucun SQL — decision={decision})")

    # ── ÉTAPE 8 : Validation du SQL ─────────────────────────
    sep("ÉTAPE 8 — Validation SQL (GuardrailsV7 + SQLValidatorV7)")
    if sql_generated:
        guard_sql = guard.check_generated_sql(sql_generated)
        val_result = validator.validate(sql_generated)

        print(f"  Guardrails SQL : {'✅ OK' if guard_sql['safe'] else '❌ ' + guard_sql['reason']}")
        print(f"  SQLValidator   : {'✅ Valide' if val_result['valid'] else '❌ ' + str(val_result['errors'])}")

        if val_result["valid"] and guard_sql["safe"]:
            print(f"\n  ✅ REQUÊTE PRÊTE POUR EXÉCUTION MySQL")
            print(f"  (MySQL actuellement en panne — exécution désactivée)")
            print(f"\n  ── Requête finale nettoyée ──────────────────────────")
            print(f"  {val_result['sanitized_query'][:300]}")
        else:
            print(f"\n  ❌ REQUÊTE REJETÉE — ne sera pas envoyée à MySQL")
    else:
        print(f"  Pas de SQL à valider (decision={decision})")

    # ── Résumé ───────────────────────────────────────────────
    sep("RÉSUMÉ")
    print(f"  Question    : {question}")
    print(f"  Tenant DB   : {tenant_db}")
    print(f"  Catégorie   : {intent.category}")
    print(f"  Decision    : {decision}")
    print(f"  SQL valide  : {'✅' if sql_generated and val_result.get('valid') else '❌'}")
    print(f"  ⏱  Total    : {round(time.time()-total_start, 2)}s")
    print()


# ── Lancement ────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nChoisir le mode :")
    print("  1 = Toutes les questions automatiquement")
    print("  2 = Saisir une question manuelle")
    print("  3 = Questions une par une avec pause")
    choix = input("\nChoix (1/2/3) : ").strip()

    if choix == "1":
        for i, q in enumerate(QUESTIONS, 1):
            analyse_question(q, i)
        print("\n" + "="*70)
        print(f"  TERMINÉ — {len(QUESTIONS)} questions analysées")
        print("="*70)

    elif choix == "2":
        while True:
            q = input("\n📝 Ta question (ou 'exit') : ").strip()
            if q.lower() in {"exit", "quit", ""}:
                break
            analyse_question(q, 1)

    elif choix == "3":
        for i, q in enumerate(QUESTIONS, 1):
            analyse_question(q, i)
            if i < len(QUESTIONS):
                cont = input("\n  ⏎ Appuie sur Entrée pour la question suivante (ou 'stop') : ")
                if cont.strip().lower() == "stop":
                    break
    else:
        # Par défaut : première question seulement
        analyse_question(QUESTIONS[0], 1)