from __future__ import annotations
 
from datetime import datetime
from typing import Any, Dict, Literal, Optional, TypedDict
 
from langgraph.graph import END, START, StateGraph
 
# ── imports projet ────────────────────────────────────────────────────────────
try:
    from app.agents.intent_classifier_v7    import IntentClassifierV7
    from app.agents.schema_registry_v7      import SchemaRegistryV7
    from app.agents.example_retriever_v7    import ExampleRetrieverV7
    from app.agents.security_executor       import GuardrailsV7, SQLValidatorV7, SQLExecutorV7
    from app.agents.llm_pipeline            import PromptBuilderV7, LLMAgentV8, SQLRepairV8
    from app.agents.parametric_templates_v6 import ParametricTemplateEngineV6
    from app.agents.response_formatter_v6   import ResponseFormatterV6
    from app.agents.rag_agent_v8            import RAGAgentV8
except ImportError:
    from intent_classifier_v7    import IntentClassifierV7
    from schema_registry_v7      import SchemaRegistryV7
    from example_retriever_v7    import ExampleRetrieverV7
    from security_executor       import GuardrailsV7, SQLValidatorV7, SQLExecutorV7
    from llm_pipeline            import PromptBuilderV7, LLMAgentV8, SQLRepairV8
    from parametric_templates_v6 import ParametricTemplateEngineV6
    from response_formatter_v6   import ResponseFormatterV6
    from rag_agent_v8            import RAGAgentV8
 
 
# ─────────────────────────────────────────────────────────────────────────────
# État partagé LangGraph
# ─────────────────────────────────────────────────────────────────────────────
 
class AgentState(TypedDict):
    # Entrée
    question:          str
    t0:                Any
    forced_tenant_db:  Optional[str]   # ← NOUVEAU : tenant forcé par le frontend
    # Classification
    intent:            Optional[Any]
    route:             Optional[Literal["sql", "direct"]]
    tenant:            str
    tenant_db:         str
    # SQL
    sql:               Optional[str]
    rows:              Optional[list]
    columns:           Optional[list]
    row_count:         int
    # Résultat
    natural_response:  Optional[str]
    success:           bool
    method:            str
    error:             Optional[str]
    meta:              Optional[Dict]
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Orchestrateur
# ─────────────────────────────────────────────────────────────────────────────
 
class PlannerAgentV8:
    """
    Orchestrateur V8 basé sur LangGraph.
 
    Graphe :
        START → [classify] → routing → [sql_agent | direct] → [finalize] → END
    """
 
    def __init__(
        self,
        use_templates: bool = False,
        use_rag:       bool = True,
        milvus_uri:    str  = "http://localhost:19530",
    ):
        # ── Composants ──────────────────────────────────────────────
        self.classifier = IntentClassifierV7()
        self.registry   = SchemaRegistryV7()
        self.examples   = ExampleRetrieverV7()
        self.guardrails = GuardrailsV7()
        self.validator  = SQLValidatorV7()
        self.executor   = SQLExecutorV7()
        self.formatter  = ResponseFormatterV6(mode="markdown")
        self.templates  = ParametricTemplateEngineV6() if use_templates else None
 
        # LLM pipeline (prompt + génération + réparation)
        self.pb     = PromptBuilderV7()
        self.llm    = LLMAgentV8()
        self.repair = SQLRepairV8()
 
        # ── RAG Milvus ────────────────────────────────────────────
        self.rag: Optional[RAGAgentV8] = None
        if use_rag:
            try:
                self.rag = RAGAgentV8(milvus_uri=milvus_uri)
                print("[PlannerAgentV8]  RAG Milvus connecté.")
            except Exception as exc:
                print(f"[PlannerAgentV8]   Milvus indisponible, RAG désactivé : {exc}")
 
        # ── Graphe LangGraph ──────────────────────────────────────
        self.graph = self._build_graph()
 
    # ──────────────────────────────────────────────────────────────
    # Construction du graphe
    # ──────────────────────────────────────────────────────────────
    def _build_graph(self):
        builder = StateGraph(AgentState)
 
        builder.add_node("classify",        self._node_classify)
        builder.add_node("sql_agent",       self._node_sql_agent)
        builder.add_node("direct_response", self._node_direct_response)
        builder.add_node("finalize",        self._node_finalize)
 
        builder.add_edge(START,             "classify")
        builder.add_edge("sql_agent",       "finalize")
        builder.add_edge("direct_response", "finalize")
        builder.add_edge("finalize",         END)
 
        builder.add_conditional_edges(
            "classify",
            lambda s: s.get("route", "sql"),
            {"sql": "sql_agent", "direct": "direct_response"},
        )
 
        return builder.compile()
 
    # ──────────────────────────────────────────────────────────────
    # Nœud 1 : Classify
    # ──────────────────────────────────────────────────────────────
    def _node_classify(self, state: AgentState) -> AgentState:
        question = state["question"]
        intent   = self.classifier.classify(question)
 
        # Small talk / meta → réponse directe
        if intent.category == "chat":
            # ── Utiliser le tenant forcé si disponible ─────────────
            forced = state.get("forced_tenant_db")
            tenant_db = forced or self.registry.get_tenant_db("jln")
 
            if intent.action == "META":
                natural_response = (
                    "Je suis l'assistant de maintenance prédictive OCP i-sense. "
                    "Je n'ai pas accès à l'heure ou à la date système, et je ne peux "
                    "répondre qu'aux questions sur vos équipements, alarmes, pannes, "
                    "mesures, recommandations et interventions de maintenance."
                )
            else:  # GREETING
                natural_response = (
                    "Bonjour ! Je suis votre assistant de maintenance prédictive OCP i-sense. "
                    "Posez-moi une question sur les équipements, alarmes, pannes ou mesures."
                )
 
            return {
                **state,
                "intent":   intent,
                "route":    "direct",
                "tenant":   "jln",
                "tenant_db": tenant_db,
                "natural_response": natural_response,
                "method":  "small_talk",
                "success": True,
            }
 
        # ── TENANT : priorité au forced_tenant_db du frontend ──────
        forced = state.get("forced_tenant_db")
        if forced:
            # Le frontend a sélectionné un tenant explicitement
            tenant_db = forced
            # Extraire un nom court depuis le tenant_db pour l'affichage
            tenant = forced.replace("v3_tenant_", "").replace("_", " ").strip()
        else:
            # Fallback : détecter depuis l'intent (question contient "à Safi" etc.)
            tenant    = (intent.entities or {}).get("tenant", "jln")
            tenant_db = self.registry.get_tenant_db(tenant)
 
        # Guardrails NL
        nl_check = self.guardrails.check_nl(question)
        if not nl_check["safe"]:
            return {
                **state,
                "intent":           intent,
                "route":            "direct",
                "tenant":           tenant,
                "tenant_db":        tenant_db,
                "natural_response": nl_check["reason"],
                "method":           "blocked_nl",
                "success":          False,
                "error":            nl_check["reason"],
            }
 
        return {
            **state,
            "intent":    intent,
            "route":     "sql",
            "tenant":    tenant,
            "tenant_db": tenant_db,
        }
 
    # ──────────────────────────────────────────────────────────────
    # Nœud 2a : SQL Agent
    # ──────────────────────────────────────────────────────────────
    def _node_sql_agent(self, state: AgentState) -> AgentState:
        # intent    = state["intent"]
        # tenant_db = state["tenant_db"]
 
        # # ÉTAPE 1 : Templates déterministes
        # if self.templates:
        #     tmpl = self.templates.match(intent, tenant_db)
        #     if tmpl:
        #         val = self.validator.validate(tmpl.sql)
        #         if val["valid"]:
        #             exec_r = self.executor.execute(tmpl.sql, tenant_db)
        #             if exec_r["success"]:
        #                 return {
        #                     **state,
        #                     "sql":       tmpl.sql,
        #                     "rows":      exec_r["rows"],
        #                     "columns":   exec_r["columns"],
        #                     "row_count": exec_r["row_count"],
        #                     "success":   True,
        #                     "method":    f"template:{tmpl.template_name}",
        #                 }
 
        # ÉTAPE 2 : LLM Groq + RAG Milvus
        return self._llm_pipeline(state)
 
    def _llm_pipeline(self, state: AgentState) -> AgentState:
        question  = state["question"]
        intent    = state["intent"]
        tenant_db = state["tenant_db"]
 
        # Contexte schéma
        rel_tables = self.registry.get_relevant_tables_from_intent(intent)
        schema_ctx = self.registry.get_compact_schema_for_tables(rel_tables, tenant_db)
        join_hints = self.registry.get_join_hints(rel_tables, tenant_db)
 
        # Exemples BM25
        close_ex = self.examples.retrieve_examples(question, intent=intent, top_k=2)
        cat_ex   = self.examples.retrieve_category_examples(intent=intent, top_k=2)
        merged   = self.examples.merge_examples(close_ex, cat_ex, max_total=4)
        ex_ctx   = self.examples.format_examples_for_prompt(merged, tenant_db, "EXEMPLES UTILES")
 
        # Contexte RAG Milvus
        rag_ctx = ""
        if self.rag:
            try:
                rag_ctx = self.rag.build_prompt_context(
                    question=question, tenant_db=tenant_db, intent=intent, max_chars=1600
                )
            except Exception as exc:
                print(f"[PlannerAgentV8] RAG error: {exc}")
 
        # Prompt + génération
        system = self.pb.build_sql_system_prompt()
        user   = self.pb.build_sql_user_prompt(
            question=question, tenant_db=tenant_db, intent=intent,
            schema_context=schema_ctx, join_hints=join_hints,
            examples_context=ex_ctx, category_examples_context="",
            negative_examples_context="", rag_context=rag_ctx,
        )
 
        gen = self.llm.generate_json(
            prompt=user, system=system, temperature=0.05, max_tokens=1024
        )
 
        if not gen.get("success"):
            return {
                **state,
                "success": False,
                "method":  "llm_failed",
                "error":   gen.get("error"),
                "natural_response": f"❌ Génération SQL échouée : {gen.get('error')}",
            }
 
        parsed   = gen["parsed"]
        decision = parsed.get("decision", "sql")
        sql      = parsed.get("sql", "")
 
        if decision != "sql" or not sql:
            return {
                **state,
                "success": False,
                "method":  "clarify" if decision == "clarify" else "llm_refuse",
                "natural_response": parsed.get("reasoning", "Requête refusée ou insuffisante."),
            }
 
        # Guardrails SQL
        sql_check = self.guardrails.check_generated_sql(sql)
        if not sql_check["safe"]:
            return {
                **state,
                "success": False,
                "method":  "blocked_sql",
                "error":   sql_check["reason"],
                "natural_response": sql_check["reason"],
            }
 
        return self._validate_and_execute(
            state, sql, schema_ctx, join_hints, ex_ctx, tenant_db
        )
 
    def _validate_and_execute(
        self, state, sql, schema_ctx, join_hints, ex_ctx, tenant_db
    ) -> AgentState:
        question = state["question"]
 
        # Validation
        val = self.validator.validate(sql)
        if not val["valid"]:
            rep = self.repair.repair(
                question=question, failed_sql=sql,
                error_msg="; ".join(val["errors"]),
                schema_context=schema_ctx, join_hints=join_hints,
                examples_context=ex_ctx,
            )
            if rep.get("success"):
                sql  = rep["parsed"].get("sql", "")
                val2 = self.validator.validate(sql)
                if not val2["valid"]:
                    return {
                        **state, "success": False, "method": "validation_failed",
                        "error": str(val2["errors"]),
                        "natural_response": "❌ SQL invalide après réparation.",
                    }
            else:
                return {
                    **state, "success": False, "method": "repair_failed",
                    "error": rep.get("error"),
                    "natural_response": "❌ Réparation SQL échouée.",
                }
 
        # Exécution
        exec_r = self.executor.execute(sql, tenant_db)
        if not exec_r["success"]:
            rep = self.repair.repair(
                question=question, failed_sql=sql,
                error_msg=exec_r.get("error", "DB error"),
                schema_context=schema_ctx, join_hints=join_hints,
                examples_context=ex_ctx,
            )
            if rep.get("success"):
                sql2 = rep["parsed"].get("sql", "")
                val2 = self.validator.validate(sql2)
                if val2["valid"]:
                    exec_r = self.executor.execute(sql2, tenant_db)
                    if exec_r["success"]:
                        sql = sql2
                    else:
                        return {
                            **state, "success": False, "method": "exec_failed",
                            "error": exec_r.get("error"),
                            "natural_response": "❌ Exécution SQL échouée.",
                        }
                else:
                    return {
                        **state, "success": False, "method": "repair_invalid",
                        "natural_response": "❌ SQL réparé invalide.",
                    }
            else:
                return {
                    **state, "success": False, "method": "exec_failed",
                    "error": exec_r.get("error"),
                    "natural_response": "❌ Exécution SQL échouée.",
                }
 
        return {
            **state,
            "sql":       sql,
            "rows":      exec_r["rows"],
            "columns":   exec_r["columns"],
            "row_count": exec_r["row_count"],
            "success":   True,
            "method":    "llm_v8_milvus" if self.rag else "llm_v8",
            "meta": {
                "rag_used":    bool(self.rag),
                "tables_used": self.registry.get_relevant_tables_from_intent(state["intent"]),
                "tenant_db":   tenant_db,
            },
        }
 
    # ──────────────────────────────────────────────────────────────
    # Nœud 2b : Réponse directe
    # ──────────────────────────────────────────────────────────────
    def _node_direct_response(self, state: AgentState) -> AgentState:
        return state  # natural_response déjà renseignée dans classify
 
    # ──────────────────────────────────────────────────────────────
    # Nœud 3 : Finalize
    # ──────────────────────────────────────────────────────────────
    def _node_finalize(self, state: AgentState) -> AgentState:
        question = state["question"]
        tenant   = state["tenant"]
        intent   = state["intent"]
 
        if (
            state.get("success")
            and state.get("rows") is not None
            and not state.get("natural_response")
        ):
            natural = self.formatter.format(
                question, state["rows"], state["columns"], tenant, intent=intent
            )
            state = {**state, "natural_response": natural}
 
        return state
 
    # ──────────────────────────────────────────────────────────────
    # Interface publique
    # ──────────────────────────────────────────────────────────────
    def process_question(
        self,
        question: str,
        forced_tenant_db: Optional[str] = None   # ← NOUVEAU PARAMÈTRE
    ) -> Dict:
        """
        Traite une question utilisateur.
        
        Args:
            question:         La question posée par l'utilisateur.
            forced_tenant_db: Si fourni, ce tenant sera utilisé sans détecter
                              le tenant depuis la question. Permet au frontend
                              de forcer le tenant sélectionné dans l'UI.
        """
        t0 = datetime.now()
 
        initial: AgentState = {
            "question":          question,
            "t0":                t0,
            "forced_tenant_db":  forced_tenant_db,   # ← NOUVEAU
            "intent":            None,
            "route":             None,
            "tenant":            "jln",
            "tenant_db":         forced_tenant_db or "",  # ← pré-rempli
            "sql":               None,
            "rows":              None,
            "columns":           None,
            "row_count":         0,
            "natural_response":  None,
            "success":           False,
            "method":            "unknown",
            "error":             None,
            "meta":              None,
        }
 
        final           = self.graph.invoke(initial)
        processing_time = round((datetime.now() - t0).total_seconds(), 2)
        intent          = final.get("intent")
 
        result = {
            "success":          final.get("success", False),
            "tenant":           final.get("tenant_db", forced_tenant_db or "jln"),
            "method":           final.get("method", "unknown"),
            "natural_response": final.get("natural_response", ""),
            "processing_time":  processing_time,
            "timestamp":        datetime.now().isoformat(),
            "category":         getattr(intent, "category", "unknown") if intent else "unknown",
            "row_count":        final.get("row_count", 0),
        }
        if final.get("sql"):
            result["sql"] = final["sql"]
        if final.get("rows") is not None:
            result["rows"]    = final["rows"]
            result["columns"] = final.get("columns", [])
        if final.get("error"):
            result["error"] = final["error"]
        if final.get("meta"):
            result["meta"] = final["meta"]
 
        return result