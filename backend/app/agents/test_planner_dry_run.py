# # test_planner_dry_run.py
# # ============================================================
# # TEST PLANNER V8 — MODE DRY RUN
# #   ✅ Sans exécution MySQL
# #   ✅ Sans ParametricTemplateEngineV6 (templates désactivés)
# #   ✅ Pipeline complet : Intent → Schema → BM25 → RAG → Groq → Validation
# #
# # Ce qu'on voit à chaque question :
# #   1. Guardrails NL
# #   2. Intent détecté (category, action, tenant, entities, modifiers)
# #   3. Tables sélectionnées + schéma compact + join hints
# #   4. Exemples BM25 (ExampleRetrieverV7)
# #   5. Contexte RAG Milvus (Dense + BM25 + RRF + CrossEncoder)
# #   6. Prompt complet envoyé à Groq
# #   7. SQL généré par Groq
# #   8. Validation du SQL (GuardrailsV7 + SQLValidatorV7)
# #   9. Résumé
# # ============================================================

# import sys
# import time
# import os
# from dotenv import load_dotenv

# load_dotenv()
# sys.path.insert(0, "chatbot_maintenance/backend")

# # ── Imports agents ──────────────────────────────────────────
# try:
#     from app.agents.intent_classifier_v7 import IntentClassifierV7
#     from app.agents.schema_registry_v7   import SchemaRegistryV7
#     from app.agents.example_retriever_v7 import ExampleRetrieverV7
#     from app.agents.rag_agent_v8         import RAGAgentV8
#     from app.agents.security_executor    import GuardrailsV7, SQLValidatorV7
#     from app.agents.llm_pipeline         import PromptBuilderV7, LLMAgentV8
# except ImportError:
#     from agents.intent_classifier_v7 import IntentClassifierV7
#     from agents.schema_registry_v7   import SchemaRegistryV7
#     from agents.example_retriever_v7 import ExampleRetrieverV7
#     from agents.rag_agent_v8         import RAGAgentV8
#     from agents.security_executor    import GuardrailsV7, SQLValidatorV7
#     from agents.llm_pipeline         import PromptBuilderV7, LLMAgentV8

# # NOTE : ParametricTemplateEngineV6 volontairement absent —
# #        on force le pipeline LLM+RAG pour toutes les questions.

# # ── Questions à tester ──────────────────────────────────────
# QUESTIONS = [
#     # Sans tenant explicite (fallback jln)
#     "Quels équipements ont une alarme critique ?",
#     "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' ?",
#     "Combien de pannes actives ce mois ?",
#     "Top 5 assets avec le plus de défauts",
#     "Les équipements critiques ?",
#     "Quelle est la mesure NGV la plus élevée aujourd'hui ?",
#     "Combien d'équipements ?",
#     "Quels sont les équipements présentant actuellement un problème de roulement ?",
#     # Avec tenant explicite
#     "Quels équipements ont une alarme critique à Safi ?",
#     "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' à Safi ?",
#     "Combien de pannes actives ce mois à Safi ?",
#     "Top 5 assets avec le plus de défauts à Safi ?",
#     "Les équipements critiques à NTN ?",
#     "Quelle est la mesure NGV la plus élevée aujourd'hui à Safi ?",
#     "Combien d'équipements à NOMAC ?",
#     "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' à NTN ?",
#     "Quels sont les équipements présentant actuellement un problème de roulement à Safi ?",
# ]

# # ─────────────────────────────────────────────────────────────
# # INITIALISATION
# # ─────────────────────────────────────────────────────────────
# print("=" * 70)
# print("  TEST DRY RUN — LLM+RAG UNIQUEMENT (sans templates, sans MySQL)")
# print("=" * 70)

# print("\n[INIT] Chargement des agents...")
# t_init = time.time()

# clf       = IntentClassifierV7()
# guard     = GuardrailsV7()
# registry  = SchemaRegistryV7()
# retriever = ExampleRetrieverV7()
# pb        = PromptBuilderV7()
# llm       = LLMAgentV8()
# validator = SQLValidatorV7()

# print("[INIT] Chargement RAG Milvus (MiniLM + CrossEncoder)...")
# rag = RAGAgentV8()

# print(f"[INIT] ✅ Prêt en {round(time.time() - t_init, 1)}s\n")
# print("  ⚠️  ParametricTemplateEngineV6 : DÉSACTIVÉ — pipeline LLM pur\n")


# # ─────────────────────────────────────────────────────────────
# # HELPERS
# # ─────────────────────────────────────────────────────────────
# def sep(title="", width=70):
#     if title:
#         side = (width - len(title) - 2) // 2
#         print(f"\n{'─' * side} {title} {'─' * side}")
#     else:
#         print("─" * width)


# def print_block(lines_str: str, max_lines: int = 25, indent: str = "  "):
#     """Affiche un bloc de texte avec une limite de lignes."""
#     lines = lines_str.split("\n")
#     for line in lines[:max_lines]:
#         print(f"{indent}{line}")
#     if len(lines) > max_lines:
#         print(f"{indent}... ({len(lines)} lignes total, {len(lines) - max_lines} cachées)")


# # ─────────────────────────────────────────────────────────────
# # ANALYSE D'UNE QUESTION
# # ─────────────────────────────────────────────────────────────
# def analyse_question(question: str, idx: int):
#     print(f"\n{'═' * 70}")
#     print(f"  QUESTION {idx} : {question}")
#     print(f"{'═' * 70}")

#     total_start = time.time()
#     val_result  = {"valid": False}   # défaut pour le résumé final

#     # ── ÉTAPE 1 : Guardrails NL ──────────────────────────────
#     sep("ÉTAPE 1 — Guardrails NL")
#     guard_result = guard.check_nl(question)
#     if not guard_result["safe"]:
#         print(f"  🔒 BLOQUÉ : {guard_result['reason']}")
#         print(f"  ⏱  Total : {round(time.time() - total_start, 3)}s")
#         return
#     print("  ✅ Question autorisée")

#     # ── ÉTAPE 2 : Intent Classification ─────────────────────
#     sep("ÉTAPE 2 — Intent Classification")
#     t0     = time.time()
#     intent = clf.classify(question)
#     print(f"  category   : {intent.category}")
#     print(f"  action     : {intent.action}")
#     print(f"  confidence : {intent.confidence:.2f}")
#     print(f"  entities   : {intent.entities}")
#     print(f"  modifiers  : {getattr(intent, 'modifiers', [])}")
#     print(f"  ⏱  {round(time.time() - t0, 3)}s")

#     # Résolution du tenant
#     tenant_raw = (intent.entities or {}).get("tenant") or "jln"
#     tenant_db  = registry.get_tenant_db(tenant_raw)
#     print(f"\n  tenant raw : '{tenant_raw}' → DB : '{tenant_db}'")

#     # ── ÉTAPE 3 : Tables + Schéma + Join hints ───────────────
#     sep("ÉTAPE 3 — SchemaRegistry (tables, schéma, jointures)")
#     t0             = time.time()
#     tables         = registry.get_relevant_tables_from_intent(intent)
#     schema_context = registry.get_compact_schema_for_tables(tables, tenant_db)
#     join_hints     = registry.get_join_hints(tables, tenant_db)

#     print(f"  Tables retenues : {tables}\n")
#     print("  ── Schéma compact ──")
#     print_block(schema_context, max_lines=20)
#     print("\n  ── Join hints ──")
#     print_block(join_hints, max_lines=8)
#     print(f"\n  ⏱  {round(time.time() - t0, 3)}s")

#     # ── ÉTAPE 4 : Exemples BM25 ──────────────────────────────
#     sep("ÉTAPE 4 — Exemples BM25 (ExampleRetrieverV7)")
#     t0                = time.time()
#     ex_primary        = retriever.retrieve_examples(question, intent, top_k=4)
#     ex_category       = retriever.retrieve_category_examples(intent, top_k=2)
#     ex_merged         = retriever.merge_examples(ex_primary, ex_category, max_total=5)
#     examples_context  = retriever.format_examples_for_prompt(ex_merged, tenant_db)

#     print(f"  {len(ex_merged)} exemple(s) récupéré(s) :")
#     for i, ex in enumerate(ex_merged, 1):
#         print(f"  [{i}] {ex['question'][:70]}")
#     print(f"  ⏱  {round(time.time() - t0, 3)}s")

#     # ── ÉTAPE 5 : RAG Milvus ─────────────────────────────────
#     sep("ÉTAPE 5 — RAG Milvus (Dense + BM25 + RRF + CrossEncoder)")
#     t0          = time.time()
#     rag_context = rag.build_prompt_context(
#         question=question,
#         tenant_db=tenant_db,
#         intent=intent,
#         max_chars=2000,
#     )
#     print(f"  Contexte RAG : {len(rag_context)} chars\n")
#     print_block(rag_context, max_lines=30)
#     print(f"\n  ⏱  {round(time.time() - t0, 3)}s")

#     # ── ÉTAPE 6 : Prompt complet ─────────────────────────────
#     sep("ÉTAPE 6 — Prompt envoyé à Groq")
#     system_prompt = pb.build_sql_system_prompt()
#     user_prompt   = pb.build_sql_user_prompt(
#         question=question,
#         tenant_db=tenant_db,
#         intent=intent,
#         schema_context=schema_context,
#         join_hints=join_hints,
#         examples_context=examples_context,
#         category_examples_context="",
#         negative_examples_context="",
#         rag_context=rag_context,
#     )

#     print(f"\n  ── SYSTEM PROMPT ({len(system_prompt)} chars) ──")
#     print_block(system_prompt, max_lines=8)
#     print(f"\n  ── USER PROMPT ({len(user_prompt)} chars) ──")
#     print_block(user_prompt, max_lines=30)
#     print(f"\n  📊 Taille totale : {len(system_prompt) + len(user_prompt)} chars")

#     # ── ÉTAPE 7 : Groq — génération SQL ──────────────────────
#     sep("ÉTAPE 7 — Génération SQL par Groq LLaMA 3.1 8B")
#     t0     = time.time()
#     result = llm.generate_json(
#         prompt=user_prompt,
#         system=system_prompt,
#         temperature=0.05,
#         max_tokens=2048,
#     )
#     groq_time = round(time.time() - t0, 3)

#     if not result.get("success"):
#         print(f"  ❌ Groq erreur : {result.get('error')}")
#         raw = result.get("raw_response", "")
#         if raw:
#             print(f"\n  Raw response :\n")
#             print_block(raw, max_lines=20)
#         print(f"  ⏱  Groq : {groq_time}s")
#         sep("RÉSUMÉ")
#         print(f"  Question  : {question}")
#         print(f"  Tenant DB : {tenant_db}")
#         print(f"  Catégorie : {intent.category}")
#         print(f"  Decision  : ❌ groq_error")
#         print(f"  ⏱  Total  : {round(time.time() - total_start, 2)}s\n")
#         return

#     parsed        = result.get("parsed", {})
#     decision      = parsed.get("decision", "?")
#     sql_generated = parsed.get("sql", "")
#     reasoning     = parsed.get("reasoning", "")
#     tables_used   = parsed.get("tables", [])

#     print(f"\n  decision  : {decision}")
#     print(f"  reasoning : {reasoning}")
#     print(f"  tables    : {tables_used}")
#     print(f"  tokens    : {result.get('tokens', '?')}")
#     print(f"  ⏱  Groq   : {groq_time}s")

#     print(f"\n  ── SQL GÉNÉRÉ ───────────────────────────────────────")
#     if sql_generated:
#         print()
#         print_block(sql_generated, max_lines=40)
#     else:
#         print(f"\n  (aucun SQL — decision='{decision}')")

#     # ── ÉTAPE 8 : Validation SQL ─────────────────────────────
#     sep("ÉTAPE 8 — Validation (GuardrailsV7 + SQLValidatorV7)")

#     if sql_generated:
#         guard_sql  = guard.check_generated_sql(sql_generated)
#         val_result = validator.validate(sql_generated)

#         status_g = "✅ OK" if guard_sql["safe"] else f"❌ {guard_sql['reason']}"
#         status_v = "✅ Valide" if val_result["valid"] else f"❌ {val_result['errors']}"

#         print(f"  Guardrails SQL : {status_g}")
#         print(f"  SQLValidator   : {status_v}")

#         if val_result["valid"] and guard_sql["safe"]:
#             print("\n  ✅ REQUÊTE PRÊTE — MySQL désactivé, exécution sautée")
#             print("\n  ── Requête nettoyée ──────────────────────────────────")
#             print(f"  {val_result['sanitized_query'][:400]}")
#         else:
#             print("\n  ❌ REQUÊTE REJETÉE")
#     else:
#         val_result = {"valid": False}
#         print(f"  Pas de SQL à valider (decision='{decision}')")

#     # ── RÉSUMÉ ───────────────────────────────────────────────
#     sep("RÉSUMÉ")
#     sql_ok = bool(sql_generated) and val_result.get("valid", False)
#     print(f"  Question    : {question}")
#     print(f"  Tenant DB   : {tenant_db}")
#     print(f"  Catégorie   : {intent.category}")
#     print(f"  Action      : {intent.action}")
#     print(f"  Decision    : {decision}")
#     print(f"  Templates   : ⛔ désactivés (DRY RUN LLM pur)")
#     print(f"  MySQL       : ⛔ désactivé (DRY RUN)")
#     print(f"  SQL valide  : {'✅' if sql_ok else '❌'}")
#     print(f"  ⏱  Total    : {round(time.time() - total_start, 2)}s\n")


# # ─────────────────────────────────────────────────────────────
# # POINT D'ENTRÉE
# # ─────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     print("\nChoisir le mode :")
#     print("  1 = Toutes les questions automatiquement")
#     print("  2 = Saisir une question manuelle")
#     print("  3 = Questions une par une avec pause")
#     choix = input("\nChoix (1/2/3) : ").strip()

#     if choix == "1":
#         for i, q in enumerate(QUESTIONS, 1):
#             analyse_question(q, i)
#         print("\n" + "=" * 70)
#         print(f"  TERMINÉ — {len(QUESTIONS)} questions analysées")
#         print("=" * 70)

#     elif choix == "2":
#         while True:
#             q = input("\nTa question (ou 'exit') : ").strip()
#             if q.lower() in {"exit", "quit", ""}:
#                 break
#             analyse_question(q, 1)

#     elif choix == "3":
#         for i, q in enumerate(QUESTIONS, 1):
#             analyse_question(q, i)
#             if i < len(QUESTIONS):
#                 cont = input("\n  ⏎ Entrée pour continuer (ou 'stop') : ").strip()
#                 if cont.lower() == "stop":
#                     break

#     else:
#         # Par défaut : première question
#         analyse_question(QUESTIONS[0], 1)

# --------------------------------------------------------------------................-----------------------------------------------------

# # test_planner_dry_run.py
# # ============================================================
# # TEST PLANNER V8 — MODE DRY RUN
# #   ✅ Sans exécution MySQL
# #   ✅ Sans ParametricTemplateEngineV6 (templates désactivés)
# #   ✅ Pipeline complet : Intent → Schema → BM25 → RAG → Groq → Validation
# #
# # Ce qu'on voit à chaque question :
# #   1. Guardrails NL
# #   2. Intent détecté (category, action, tenant, entities, modifiers)
# #   3. Tables sélectionnées + schéma compact + join hints
# #   4. Exemples BM25 (ExampleRetrieverV7)
# #   5. Contexte RAG Milvus (Dense + BM25 + RRF + CrossEncoder)
# #   6. Prompt complet envoyé à Groq
# #   7. SQL généré par Groq
# #   8. Validation du SQL (GuardrailsV7 + SQLValidatorV7)
# #   9. Résumé
# # ============================================================

# import sys
# import time
# import os
# from dotenv import load_dotenv

# load_dotenv()
# sys.path.insert(0, "chatbot_maintenance/backend")

# try:
#     from app.agents.intent_classifier_v7 import IntentClassifierV7
#     from app.agents.schema_registry_v7   import SchemaRegistryV7
#     from app.agents.example_retriever_v7 import ExampleRetrieverV7
#     from app.agents.rag_agent_v8         import RAGAgentV8
#     from app.agents.security_executor    import GuardrailsV7, SQLValidatorV7
#     from app.agents.llm_pipeline         import PromptBuilderV7, LLMAgentV8
# except ImportError:
#     from agents.intent_classifier_v7 import IntentClassifierV7
#     from agents.schema_registry_v7   import SchemaRegistryV7
#     from agents.example_retriever_v7 import ExampleRetrieverV7
#     from agents.rag_agent_v8         import RAGAgentV8
#     from agents.security_executor    import GuardrailsV7, SQLValidatorV7
#     from agents.llm_pipeline         import PromptBuilderV7, LLMAgentV8

# # NOTE : ParametricTemplateEngineV6 volontairement absent —
# #        on force le pipeline LLM+RAG pour toutes les questions.

# # ── Questions à tester ──────────────────────────────────────
# QUESTIONS = [
#     # Sans tenant explicite (fallback jln)
#     "Quels équipements ont une alarme critique ?",
#     "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' ?",
#     "Combien de pannes actives ce mois ?",
#     "Top 5 assets avec le plus de défauts",
#     "Les équipements critiques ?",
#     "Quelle est la mesure NGV la plus élevée aujourd'hui ?",
#     "Combien d'équipements ?",
#     "Quels sont les équipements présentant actuellement un problème de roulement ?",
#     # Avec tenant explicite
#     "Quels équipements ont une alarme critique à Safi ?",
#     "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' à Safi ?",
#     "Combien de pannes actives ce mois à Safi ?",
#     "Top 5 assets avec le plus de défauts à Safi ?",
#     "Les équipements critiques à NTN ?",
#     "Quelle est la mesure NGV la plus élevée aujourd'hui à Safi ?",
#     "Combien d'équipements à NOMAC ?",
#     "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' à NTN ?",
#     "Quels sont les équipements présentant actuellement un problème de roulement à Safi ?",
# ]

# # ─────────────────────────────────────────────────────────────
# # INITIALISATION
# # ─────────────────────────────────────────────────────────────
# print("=" * 70)
# print("  TEST DRY RUN — LLM+RAG UNIQUEMENT (sans templates, sans MySQL)")
# print("=" * 70)

# print("\n[INIT] Chargement des agents...")
# t_init = time.time()

# clf       = IntentClassifierV7()
# guard     = GuardrailsV7()
# registry  = SchemaRegistryV7()
# retriever = ExampleRetrieverV7()
# pb        = PromptBuilderV7()
# llm       = LLMAgentV8()
# validator = SQLValidatorV7()

# print("[INIT] Chargement RAG Milvus (MiniLM + CrossEncoder)...")
# rag = RAGAgentV8()

# print(f"[INIT] ✅ Prêt en {round(time.time() - t_init, 1)}s\n")
# print("  ⚠️  ParametricTemplateEngineV6 : DÉSACTIVÉ — pipeline LLM pur\n")


# # ─────────────────────────────────────────────────────────────
# # HELPERS
# # ─────────────────────────────────────────────────────────────
# def sep(title="", width=70):
#     if title:
#         side = (width - len(title) - 2) // 2
#         print(f"\n{'─' * side} {title} {'─' * side}")
#     else:
#         print("─" * width)


# def print_block(lines_str: str, max_lines: int = 25, indent: str = "  "):
#     """Affiche un bloc de texte avec une limite de lignes."""
#     lines = lines_str.split("\n")
#     for line in lines[:max_lines]:
#         print(f"{indent}{line}")
#     if len(lines) > max_lines:
#         print(f"{indent}... ({len(lines)} lignes total, {len(lines) - max_lines} cachées)")


# # ─────────────────────────────────────────────────────────────
# # ANALYSE D'UNE QUESTION
# # ─────────────────────────────────────────────────────────────
# def analyse_question(question: str, idx: int):
#     print(f"\n{'═' * 70}")
#     print(f"  QUESTION {idx} : {question}")
#     print(f"{'═' * 70}")

#     total_start = time.time()
#     val_result  = {"valid": False}   # défaut pour le résumé final

#     # ── ÉTAPE 1 : Guardrails NL ──────────────────────────────
#     sep("ÉTAPE 1 — Guardrails NL")
#     guard_result = guard.check_nl(question)
#     if not guard_result["safe"]:
#         print(f"  🔒 BLOQUÉ : {guard_result['reason']}")
#         print(f"  ⏱  Total : {round(time.time() - total_start, 3)}s")
#         return
#     print("  ✅ Question autorisée")

#     # ── ÉTAPE 2 : Intent Classification ─────────────────────
#     sep("ÉTAPE 2 — Intent Classification")
#     t0     = time.time()
#     intent = clf.classify(question)
#     print(f"  category   : {intent.category}")
#     print(f"  action     : {intent.action}")
#     print(f"  confidence : {intent.confidence:.2f}")
#     print(f"  entities   : {intent.entities}")
#     print(f"  modifiers  : {getattr(intent, 'modifiers', [])}")
#     print(f"  ⏱  {round(time.time() - t0, 3)}s")

#     # Résolution du tenant
#     tenant_raw = (intent.entities or {}).get("tenant") or "jln"
#     tenant_db  = registry.get_tenant_db(tenant_raw)
#     print(f"\n  tenant raw : '{tenant_raw}' → DB : '{tenant_db}'")

#     # ── ÉTAPE 3 : Tables + Schéma + Join hints ───────────────
#     sep("ÉTAPE 3 — SchemaRegistry (tables, schéma, jointures)")
#     t0             = time.time()
#     tables         = registry.get_relevant_tables_from_intent(intent)
#     schema_context = registry.get_compact_schema_for_tables(tables, tenant_db)
#     join_hints     = registry.get_join_hints(tables, tenant_db)

#     print(f"  Tables retenues : {tables}\n")
#     print("  ── Schéma compact ──")
#     print_block(schema_context, max_lines=20)
#     print("\n  ── Join hints ──")
#     print_block(join_hints, max_lines=8)
#     print(f"\n  ⏱  {round(time.time() - t0, 3)}s")

#     # ── ÉTAPE 4 : Exemples BM25 ──────────────────────────────
#     sep("ÉTAPE 4 — Exemples BM25 (ExampleRetrieverV7)")
#     t0                = time.time()
#     ex_primary        = retriever.retrieve_examples(question, intent, top_k=4)
#     ex_category       = retriever.retrieve_category_examples(intent, top_k=2)
#     ex_merged         = retriever.merge_examples(ex_primary, ex_category, max_total=5)
#     examples_context  = retriever.format_examples_for_prompt(ex_merged, tenant_db)

#     print(f"  {len(ex_merged)} exemple(s) récupéré(s) :")
#     for i, ex in enumerate(ex_merged, 1):
#         print(f"  [{i}] {ex['question'][:70]}")
#     print(f"  ⏱  {round(time.time() - t0, 3)}s")

#     # ── ÉTAPE 5 : RAG Milvus ─────────────────────────────────
#     sep("ÉTAPE 5 — RAG Milvus (Dense + BM25 + RRF + CrossEncoder)")
#     t0          = time.time()
#     rag_context = rag.build_prompt_context(
#         question=question,
#         tenant_db=tenant_db,
#         intent=intent,
#         max_chars=2000,
#     )
#     print(f"  Contexte RAG : {len(rag_context)} chars\n")
#     print_block(rag_context, max_lines=30)
#     print(f"\n  ⏱  {round(time.time() - t0, 3)}s")

#     # ── ÉTAPE 6 : Prompt complet ─────────────────────────────
#     sep("ÉTAPE 6 — Prompt envoyé à Groq")
#     system_prompt = pb.build_sql_system_prompt()
#     user_prompt   = pb.build_sql_user_prompt(
#         question=question,
#         tenant_db=tenant_db,
#         intent=intent,
#         schema_context=schema_context,
#         join_hints=join_hints,
#         examples_context=examples_context,
#         category_examples_context="",
#         negative_examples_context="",
#         rag_context=rag_context,
#     )

#     print(f"\n  ── SYSTEM PROMPT ({len(system_prompt)} chars) ──")
#     print_block(system_prompt, max_lines=8)
#     print(f"\n  ── USER PROMPT ({len(user_prompt)} chars) ──")
#     print_block(user_prompt, max_lines=30)
#     print(f"\n  📊 Taille totale : {len(system_prompt) + len(user_prompt)} chars")

#     # ── ÉTAPE 7 : Groq — génération SQL ──────────────────────
#     sep("ÉTAPE 7 — Génération SQL par Groq LLaMA 3.1 8B")
#     t0     = time.time()
#     result = llm.generate_json(
#         prompt=user_prompt,
#         system=system_prompt,
#         temperature=0.05,
#         max_tokens=2048,
#     )
#     groq_time = round(time.time() - t0, 3)

#     if not result.get("success"):
#         print(f"  ❌ Groq erreur : {result.get('error')}")
#         raw = result.get("raw_response", "")
#         if raw:
#             print(f"\n  Raw response :\n")
#             print_block(raw, max_lines=20)
#         print(f"  ⏱  Groq : {groq_time}s")
#         sep("RÉSUMÉ")
#         print(f"  Question  : {question}")
#         print(f"  Tenant DB : {tenant_db}")
#         print(f"  Catégorie : {intent.category}")
#         print(f"  Decision  : ❌ groq_error")
#         print(f"  ⏱  Total  : {round(time.time() - total_start, 2)}s\n")
#         return

#     parsed        = result.get("parsed", {})
#     decision      = parsed.get("decision", "?")
#     sql_generated = parsed.get("sql", "")
#     reasoning     = parsed.get("reasoning", "")
#     tables_used   = parsed.get("tables", [])

#     print(f"\n  decision  : {decision}")
#     print(f"  reasoning : {reasoning}")
#     print(f"  tables    : {tables_used}")
#     print(f"  tokens    : {result.get('tokens', '?')}")
#     print(f"  ⏱  Groq   : {groq_time}s")

#     print(f"\n  ── SQL GÉNÉRÉ ───────────────────────────────────────")
#     if sql_generated:
#         print()
#         print_block(sql_generated, max_lines=999)  # pas de troncature
#     else:
#         print(f"\n  (aucun SQL — decision='{decision}')")

#     # ── ÉTAPE 8 : Validation SQL ─────────────────────────────
#     sep("ÉTAPE 8 — Validation (GuardrailsV7 + SQLValidatorV7)")

#     if sql_generated:
#         guard_sql  = guard.check_generated_sql(sql_generated)
#         val_result = validator.validate(sql_generated)

#         status_g = "✅ OK" if guard_sql["safe"] else f"❌ {guard_sql['reason']}"
#         status_v = "✅ Valide" if val_result["valid"] else f"❌ {val_result['errors']}"

#         print(f"  Guardrails SQL : {status_g}")
#         print(f"  SQLValidator   : {status_v}")

#         if val_result["valid"] and guard_sql["safe"]:
#             print("\n  ✅ REQUÊTE PRÊTE — MySQL désactivé, exécution sautée")
#             print("\n  ── Requête nettoyée ──────────────────────────────────")
#             # Affichage complet sans troncature
#             for line in val_result['sanitized_query'].split("\n"):
#                 print(f"  {line}")
#         else:
#             print("\n  ❌ REQUÊTE REJETÉE")
#     else:
#         val_result = {"valid": False}
#         print(f"  Pas de SQL à valider (decision='{decision}')")

#     # ── RÉSUMÉ ───────────────────────────────────────────────
#     sep("RÉSUMÉ")
#     sql_ok = bool(sql_generated) and val_result.get("valid", False)
#     print(f"  Question    : {question}")
#     print(f"  Tenant DB   : {tenant_db}")
#     print(f"  Catégorie   : {intent.category}")
#     print(f"  Action      : {intent.action}")
#     print(f"  Decision    : {decision}")
#     print(f"  Templates   : ⛔ désactivés (DRY RUN LLM pur)")
#     print(f"  MySQL       : ⛔ désactivé (DRY RUN)")
#     print(f"  SQL valide  : {'✅' if sql_ok else '❌'}")
#     print(f"  ⏱  Total    : {round(time.time() - total_start, 2)}s\n")


# # ─────────────────────────────────────────────────────────────
# # POINT D'ENTRÉE
# # ─────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     print("\nChoisir le mode :")
#     print("  1 = Toutes les questions automatiquement")
#     print("  2 = Saisir une question manuelle")
#     print("  3 = Questions une par une avec pause")
#     choix = input("\nChoix (1/2/3) : ").strip()

#     if choix == "1":
#         for i, q in enumerate(QUESTIONS, 1):
#             analyse_question(q, i)
#         print("\n" + "=" * 70)
#         print(f"  TERMINÉ — {len(QUESTIONS)} questions analysées")
#         print("=" * 70)

#     elif choix == "2":
#         while True:
#             q = input("\nTa question (ou 'exit') : ").strip()
#             if q.lower() in {"exit", "quit", ""}:
#                 break
#             analyse_question(q, 1)

#     elif choix == "3":
#         for i, q in enumerate(QUESTIONS, 1):
#             analyse_question(q, i)
#             if i < len(QUESTIONS):
#                 cont = input("\n  ⏎ Entrée pour continuer (ou 'stop') : ").strip()
#                 if cont.lower() == "stop":
#                     break

#     else:
#         # Par défaut : première question
#         analyse_question(QUESTIONS[0], 1)


# test_planner_dry_run.py
# ============================================================
# TEST PLANNER V8 — MODE DRY RUN
#   ✅ Sans exécution MySQL
#   ✅ Sans ParametricTemplateEngineV6 (templates désactivés)
#   ✅ Pipeline complet : Intent → Schema → BM25 → RAG → Groq → Validation
#
# Ce qu'on voit à chaque question :
#   1. Guardrails NL
#   2. Intent détecté (category, action, tenant, entities, modifiers)
#   3. Tables sélectionnées + schéma compact + join hints
#   4. Exemples BM25 (ExampleRetrieverV7)
#   5. Contexte RAG Milvus (Dense + BM25 + RRF + CrossEncoder)
#   6. Prompt complet envoyé à Groq
#   7. SQL généré par Groq
#   8. Validation du SQL (GuardrailsV7 + SQLValidatorV7)
#   9. Résumé
# ============================================================
 
import sys
import time
from pathlib import Path
 
# ─────────────────────────────────────────────────────────────────────────────
# FIX PYTHONPATH — fonctionne quel que soit le répertoire de lancement
# ─────────────────────────────────────────────────────────────────────────────
 
def _fix_pythonpath():
    here = Path(__file__).resolve()
    # Remonte jusqu'à trouver le dossier contenant app/agents/llm_pipeline.py
    for candidate in [here.parent] + list(here.parents):
        if (candidate / "app" / "agents" / "llm_pipeline.py").exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return candidate
        # Cherche aussi chatbot_maintenance/backend/
        deep = candidate / "chatbot_maintenance" / "backend"
        if (deep / "app" / "agents" / "llm_pipeline.py").exists():
            if str(deep) not in sys.path:
                sys.path.insert(0, str(deep))
            return deep
    return None
 
_backend_root = _fix_pythonpath()
print(f"  Backend root : {_backend_root}")
 
# ─────────────────────────────────────────────────────────────────────────────
# Chargement .env (GROQ_API_KEY)
# ─────────────────────────────────────────────────────────────────────────────
 
try:
    from dotenv import load_dotenv
    for _candidate in [Path(__file__).parents[0], Path(__file__).parents[1],
                       Path(__file__).parents[2], Path(__file__).parents[3]]:
        _env = _candidate / ".env"
        if _env.exists():
            load_dotenv(_env)
            print(f"  .env chargé depuis : {_env}")
            break
except ImportError:
    pass  # python-dotenv non installé
 
# ─────────────────────────────────────────────────────────────────────────────
# Imports agents
# ─────────────────────────────────────────────────────────────────────────────
 
try:
    from app.agents.intent_classifier_v7 import IntentClassifierV7
    from app.agents.schema_registry_v7   import SchemaRegistryV7
    from app.agents.example_retriever_v7 import ExampleRetrieverV7
    from app.agents.rag_agent_v8         import RAGAgentV8
    from app.agents.security_executor    import GuardrailsV7, SQLValidatorV7
    from app.agents.llm_pipeline         import PromptBuilderV7, LLMAgentV8
except ImportError:
    from agents.intent_classifier_v7 import IntentClassifierV7
    from agents.schema_registry_v7   import SchemaRegistryV7
    from agents.example_retriever_v7 import ExampleRetrieverV7
    from agents.rag_agent_v8         import RAGAgentV8
    from agents.security_executor    import GuardrailsV7, SQLValidatorV7
    from agents.llm_pipeline         import PromptBuilderV7, LLMAgentV8
 
# NOTE : ParametricTemplateEngineV6 volontairement absent —
#        on force le pipeline LLM+RAG pour toutes les questions.
 
# ─────────────────────────────────────────────────────────────────────────────
# Questions à tester
# ─────────────────────────────────────────────────────────────────────────────
 
QUESTIONS = [
    # Sans tenant explicite (fallback jln)
    "Quels équipements ont une alarme critique ?",
    "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' ?",
    "Combien de pannes actives ce mois ?",
    "Top 5 assets avec le plus de défauts",
    "Les équipements critiques ?",
    "Quelle est la mesure NGV la plus élevée aujourd'hui ?",
    "Combien d'équipements ?",
    "Quels sont les équipements présentant actuellement un problème de roulement ?",
    # Avec tenant explicite
    "Quels équipements ont une alarme critique à Safi ?",
    "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' à Safi ?",
    "Combien de pannes actives ce mois à Safi ?",
    "Top 5 assets avec le plus de défauts à Safi ?",
    "Les équipements critiques à NTN ?",
    "Quelle est la mesure NGV la plus élevée aujourd'hui à Safi ?",
    "Combien d'équipements à NOMAC ?",
    "Quel est le statut actuel de l'équipement 'Pompe 03XYP23' à NTN ?",
    "Quels sont les équipements présentant actuellement un problème de roulement à Safi ?",
]
 
# ─────────────────────────────────────────────────────────────────────────────
# INITIALISATION
# ─────────────────────────────────────────────────────────────────────────────
 
print("=" * 70)
print("  TEST DRY RUN — LLM+RAG UNIQUEMENT (sans templates, sans MySQL)")
print("=" * 70)
 
print("\n[INIT] Chargement des agents...")
t_init = time.time()
 
clf       = IntentClassifierV7()
guard     = GuardrailsV7()
registry  = SchemaRegistryV7()
retriever = ExampleRetrieverV7()
pb        = PromptBuilderV7()
llm       = LLMAgentV8()
validator = SQLValidatorV7()
 
print("[INIT] Chargement RAG Milvus (MiniLM + CrossEncoder)...")
try:
    rag = RAGAgentV8()
    print("[INIT] ✅ RAG Milvus connecté.")
except Exception as e:
    rag = None
    print(f"[INIT] ⚠️  RAG désactivé (Milvus indisponible) : {e}")
 
print(f"[INIT] ✅ Prêt en {round(time.time() - t_init, 1)}s\n")
print("  ⚠️  ParametricTemplateEngineV6 : DÉSACTIVÉ — pipeline LLM pur\n")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
 
def sep(title="", width=70):
    if title:
        side = (width - len(title) - 2) // 2
        print(f"\n{'─' * side} {title} {'─' * side}")
    else:
        print("─" * width)
 
 
def print_block(lines_str: str, max_lines: int = 25, indent: str = "  "):
    """Affiche un bloc de texte avec une limite de lignes."""
    lines = lines_str.split("\n")
    for line in lines[:max_lines]:
        print(f"{indent}{line}")
    if len(lines) > max_lines:
        print(f"{indent}... ({len(lines)} lignes total, "
              f"{len(lines) - max_lines} cachées)")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ANALYSE D'UNE QUESTION
# ─────────────────────────────────────────────────────────────────────────────
 
def analyse_question(question: str, idx: int):
    print(f"\n{'═' * 70}")
    print(f"  QUESTION {idx} : {question}")
    print(f"{'═' * 70}")
 
    total_start = time.time()
    val_result  = {"valid": False}   # défaut pour le résumé final
 
    # ── ÉTAPE 1 : Guardrails NL ──────────────────────────────────────────────
    sep("ÉTAPE 1 — Guardrails NL")
    guard_result = guard.check_nl(question)
    if not guard_result["safe"]:
        print(f"  🔒 BLOQUÉ : {guard_result['reason']}")
        print(f"  ⏱  Total : {round(time.time() - total_start, 3)}s")
        return
    print("  ✅ Question autorisée")
 
    # ── ÉTAPE 2 : Intent Classification ─────────────────────────────────────
    sep("ÉTAPE 2 — Intent Classification")
    t0     = time.time()
    intent = clf.classify(question)
    print(f"  category   : {intent.category}")
    print(f"  action     : {intent.action}")
    print(f"  confidence : {intent.confidence:.2f}")
    print(f"  entities   : {intent.entities}")
    print(f"  modifiers  : {getattr(intent, 'modifiers', [])}")
    print(f"  ⏱  {round(time.time() - t0, 3)}s")
 
    # Résolution du tenant
    tenant_raw = (intent.entities or {}).get("tenant") or "jln"
    tenant_db  = registry.get_tenant_db(tenant_raw)
    print(f"\n  tenant raw : '{tenant_raw}' → DB : '{tenant_db}'")
 
    # ── ÉTAPE 3 : Tables + Schéma + Join hints ───────────────────────────────
    sep("ÉTAPE 3 — SchemaRegistry (tables, schéma, jointures)")
    t0             = time.time()
    tables         = registry.get_relevant_tables_from_intent(intent)
    schema_context = registry.get_compact_schema_for_tables(tables, tenant_db)
    join_hints     = registry.get_join_hints(tables, tenant_db)
 
    print(f"  Tables retenues : {tables}\n")
    print("  ── Schéma compact ──")
    print_block(schema_context, max_lines=20)
    print("\n  ── Join hints ──")
    print_block(join_hints, max_lines=8)
    print(f"\n  ⏱  {round(time.time() - t0, 3)}s")
 
    # ── ÉTAPE 4 : Exemples BM25 ──────────────────────────────────────────────
    sep("ÉTAPE 4 — Exemples BM25 (ExampleRetrieverV7)")
    t0               = time.time()
    ex_primary       = retriever.retrieve_examples(question, intent, top_k=4)
    ex_category      = retriever.retrieve_category_examples(intent, top_k=2)
    ex_merged        = retriever.merge_examples(ex_primary, ex_category, max_total=5)
    examples_context = retriever.format_examples_for_prompt(ex_merged, tenant_db)
 
    print(f"  {len(ex_merged)} exemple(s) récupéré(s) :")
    for i, ex in enumerate(ex_merged, 1):
        print(f"  [{i}] {ex['question'][:70]}")
    print(f"  ⏱  {round(time.time() - t0, 3)}s")
 
    # ── ÉTAPE 5 : RAG Milvus ─────────────────────────────────────────────────
    sep("ÉTAPE 5 — RAG Milvus (Dense + BM25 + RRF + CrossEncoder)")
    t0          = time.time()
    rag_context = ""
    if rag:
        try:
            rag_context = rag.build_prompt_context(
                question=question,
                tenant_db=tenant_db,
                intent=intent,
                max_chars=2000,
            )
            print(f"  Contexte RAG : {len(rag_context)} chars\n")
            print_block(rag_context, max_lines=30)
        except Exception as e:
            print(f"  ⚠️  RAG erreur : {e}")
    else:
        print("  ⚠️  RAG non disponible (Milvus désactivé)")
    print(f"\n  ⏱  {round(time.time() - t0, 3)}s")
 
    # ── ÉTAPE 6 : Prompt complet ─────────────────────────────────────────────
    sep("ÉTAPE 6 — Prompt envoyé à Groq")
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
    print_block(system_prompt, max_lines=8)
    print(f"\n  ── USER PROMPT ({len(user_prompt)} chars) ──")
    print_block(user_prompt, max_lines=30)
    print(f"\n  📊 Taille totale prompt : {len(system_prompt) + len(user_prompt)} chars")
 
    # ── ÉTAPE 7 : Groq — génération SQL ──────────────────────────────────────
    sep("ÉTAPE 7 — Génération SQL par Groq LLaMA 3.1 8B")
    t0     = time.time()
    result = llm.generate_json(
        prompt=user_prompt,
        system=system_prompt,
        temperature=0.05,
        max_tokens=2048,
    )
    groq_time = round(time.time() - t0, 3)
 
    if not result.get("success"):
        print(f"  ❌ Groq erreur : {result.get('error')}")
        raw = result.get("raw_response", "")
        if raw:
            print(f"\n  Raw response :")
            print_block(raw, max_lines=20)
        print(f"  ⏱  Groq : {groq_time}s")
        sep("RÉSUMÉ")
        print(f"  Question  : {question}")
        print(f"  Tenant DB : {tenant_db}")
        print(f"  Catégorie : {intent.category}")
        print(f"  Decision  : ❌ groq_error")
        print(f"  ⏱  Total  : {round(time.time() - total_start, 2)}s\n")
        return
 
    parsed        = result.get("parsed", {})
    decision      = parsed.get("decision", "?")
    sql_generated = parsed.get("sql", "")
    reasoning     = parsed.get("reasoning", "")
    tables_used   = parsed.get("tables", [])
 
    print(f"\n  decision  : {decision}")
    print(f"  reasoning : {reasoning}")
    print(f"  tables    : {tables_used}")
    print(f"  tokens    : {result.get('tokens', '?')}")
    print(f"  ⏱  Groq   : {groq_time}s")
 
    print(f"\n  ── SQL GÉNÉRÉ ──────────────────────────────────────────────")
    if sql_generated:
        print()
        print_block(sql_generated, max_lines=999)  # affichage complet
    else:
        print(f"\n  (aucun SQL — decision='{decision}')")
 
    # ── ÉTAPE 8 : Validation SQL ─────────────────────────────────────────────
    sep("ÉTAPE 8 — Validation (GuardrailsV7 + SQLValidatorV7)")
 
    if sql_generated:
        guard_sql  = guard.check_generated_sql(sql_generated)
        val_result = validator.validate(sql_generated)
 
        status_g = "✅ OK"          if guard_sql["safe"]   else f"❌ {guard_sql['reason']}"
        status_v = "✅ Valide"      if val_result["valid"] else f"❌ {val_result['errors']}"
 
        print(f"  Guardrails SQL : {status_g}")
        print(f"  SQLValidator   : {status_v}")
 
        if val_result["valid"] and guard_sql["safe"]:
            print("\n  ✅ REQUÊTE PRÊTE — MySQL désactivé, exécution sautée")
            print("\n  ── Requête nettoyée ────────────────────────────────────")
            for line in val_result["sanitized_query"].split("\n"):
                print(f"  {line}")
        else:
            print("\n  ❌ REQUÊTE REJETÉE")
    else:
        val_result = {"valid": False}
        print(f"  Pas de SQL à valider (decision='{decision}')")
 
    # ── RÉSUMÉ FINAL ─────────────────────────────────────────────────────────
    sep("RÉSUMÉ")
    sql_ok = bool(sql_generated) and val_result.get("valid", False)
    print(f"  Question    : {question}")
    print(f"  Tenant DB   : {tenant_db}")
    print(f"  Catégorie   : {intent.category}")
    print(f"  Action      : {intent.action}")
    print(f"  Decision    : {decision}")
    print(f"  Templates   : ⛔ désactivés (DRY RUN LLM pur)")
    print(f"  MySQL       : ⛔ désactivé (DRY RUN)")
    print(f"  SQL valide  : {'✅' if sql_ok else '❌'}")
    print(f"  ⏱  Total    : {round(time.time() - total_start, 2)}s\n")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    print("\nChoisir le mode :")
    print("  1 = Toutes les questions automatiquement")
    print("  2 = Saisir une question manuelle")
    print("  3 = Questions une par une avec pause")
    choix = input("\nChoix (1/2/3) : ").strip()
 
    if choix == "1":
        for i, q in enumerate(QUESTIONS, 1):
            analyse_question(q, i)
        print("\n" + "=" * 70)
        print(f"  TERMINÉ — {len(QUESTIONS)} questions analysées")
        print("=" * 70)
 
    elif choix == "2":
        while True:
            q = input("\nTa question (ou 'exit') : ").strip()
            if q.lower() in {"exit", "quit", ""}:
                break
            analyse_question(q, 1)
 
    elif choix == "3":
        for i, q in enumerate(QUESTIONS, 1):
            analyse_question(q, i)
            if i < len(QUESTIONS):
                cont = input("\n  ⏎ Entrée pour continuer (ou 'stop') : ").strip()
                if cont.lower() == "stop":
                    break
 
    else:
        # Par défaut : première question
        analyse_question(QUESTIONS[0], 1)