import argparse
import csv
import json
import re
import sys
import threading
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Chargement .env (GROQ_API_KEY)
# ─────────────────────────────────────────────────────────────────────────────

def _load_env():
    try:
        from dotenv import load_dotenv
        for candidate in [Path(__file__).parents[0], Path(__file__).parents[1],
                          Path(__file__).parents[2], Path(__file__).parents[3]]:
            env_file = candidate / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                print(f"  .env chargé depuis : {env_file}")
                return
    except ImportError:
        pass

_load_env()


# ─────────────────────────────────────────────────────────────────────────────
# FIX PYTHONPATH
# ─────────────────────────────────────────────────────────────────────────────

def _fix_pythonpath():
    anchor = "app/agents/planner_agent_v8.py"
    candidates = [Path(__file__).resolve().parent]
    for _ in range(6):
        candidates.append(candidates[-1].parent)

    for base in candidates:
        if (base / anchor).exists():
            if str(base) not in sys.path:
                sys.path.insert(0, str(base))
            return base

    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "app").is_dir():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return parent
    return None

_backend_root = _fix_pythonpath()


# ─────────────────────────────────────────────────────────────────────────────
# Imports projet
# ─────────────────────────────────────────────────────────────────────────────

def _try_import(dotted_path: str, attr: str):
    try:
        mod = __import__(dotted_path, fromlist=[attr])
        return getattr(mod, attr)
    except (ImportError, AttributeError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Chargement des QUESTIONS depuis les_questions.txt
# MODIFIÉ : extraction automatique de la catégorie depuis les en-têtes
#           "# ── N. NOM (...) ── (start-end)"
# ─────────────────────────────────────────────────────────────────────────────

_SECTION_RGX = re.compile(
    r"^#\s*[─_\-—]*\s*(\d+)\.\s*([^─_\-—(]+)"
)


def _load_questions_txt() -> List[Dict]:
    """
    Charge les questions depuis les_questions.txt.
    - Chaque ligne `# ── N. NOM ... ──` ouvre une nouvelle catégorie.
    - Toutes les questions qui suivent (jusqu'à la prochaine section ou la fin)
      héritent de cette catégorie.
    - Les lignes vides sont ignorées.
    """
    candidates = []
    if _backend_root:
        candidates += [
            _backend_root / "app" / "database" / "les_questions.txt",
            _backend_root / "app" / "agents"   / "les_questions.txt",
            _backend_root / "les_questions.txt",
        ]
    candidates += [
        Path("les_questions.txt"),
        Path(__file__).resolve().parent / "les_questions.txt",
        Path("chatbot_maintenance/backend/app/database/les_questions.txt"),
        Path("chatbot_maintenance/backend/app/agents/les_questions.txt"),
    ]

    for path in candidates:
        if path.exists():
            print(f"      📄 Fichier trouvé : {path}")
            lines = path.read_text(encoding="utf-8").splitlines()
            questions = []
            current_category = "unknown"

            for line in lines:
                raw = line.strip()
                if not raw:
                    continue

                if raw.startswith("#"):
                    m = _SECTION_RGX.match(raw)
                    if m:
                        name = m.group(2).strip()
                        # Coupe au premier '(' restant éventuel et nettoie
                        name = name.split("(")[0].strip()
                        current_category = name
                    continue  # ligne de commentaire, jamais une question

                questions.append({
                    "question": raw,
                    "sql":      "",
                    "metadata": {"category": current_category},
                })

            print(f"      ✅ {len(questions)} questions chargées "
                  f"({len(set(q['metadata']['category'] for q in questions))} catégories détectées).")
            return questions

    raise FileNotFoundError(
        "Fichier les_questions.txt introuvable.\n"
        "  Emplacements cherchés :\n" +
        "\n".join(f"    - {p}" for p in candidates)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chargement des SQL de RÉFÉRENCE depuis dataset_400_questions
# ─────────────────────────────────────────────────────────────────────────────

def _load_reference_sql() -> Dict[str, str]:
    DATASET_400_QUESTIONS = None
    for mod in [
        "app.database.dataset_400_questions",
        "database.dataset_400_questions",
        "dataset_400_questions",
    ]:
        DATASET_400_QUESTIONS = _try_import(mod, "DATASET_400_QUESTIONS")
        if DATASET_400_QUESTIONS is not None:
            break

    if DATASET_400_QUESTIONS is None:
        print("      ⚠️  dataset_400_questions introuvable, similarité désactivée.")
        return {}

    ref = {}
    for entry in DATASET_400_QUESTIONS:
        q   = entry.get("question", "").strip().lower()
        sql = entry.get("sql", "").strip()
        if q and sql:
            ref[q] = sql

    print(f"      📚 {len(ref)} SQL de référence chargés depuis dataset_400_questions.")
    return ref


# ─────────────────────────────────────────────────────────────────────────────
# Chargement des composants LLM
# ─────────────────────────────────────────────────────────────────────────────

def _import_components(use_rag: bool = True) -> Dict:
    """
    ❌ ParametricTemplateEngineV6 : volontairement NON importé
    ❌ SQLExecutorV7              : volontairement NON importé (génération only)
    ❌ SQLRepairV8                : volontairement NON importé
    ✅ GuardrailsV7 (security_executor) : utilisé pour le pré-filtre NL
    """
    errors = []

    IntentClassifierV7 = None
    for mod in ["app.agents.intent_classifier_v7", "intent_classifier_v7"]:
        IntentClassifierV7 = _try_import(mod, "IntentClassifierV7")
        if IntentClassifierV7:
            break
    if not IntentClassifierV7:
        errors.append("IntentClassifierV7")

    SchemaRegistryV7 = None
    for mod in ["app.agents.schema_registry_v7", "schema_registry_v7"]:
        SchemaRegistryV7 = _try_import(mod, "SchemaRegistryV7")
        if SchemaRegistryV7:
            break
    if not SchemaRegistryV7:
        errors.append("SchemaRegistryV7")

    ExampleRetrieverV7 = None
    for mod in ["app.agents.example_retriever_v7", "example_retriever_v7"]:
        ExampleRetrieverV7 = _try_import(mod, "ExampleRetrieverV7")
        if ExampleRetrieverV7:
            break
    if not ExampleRetrieverV7:
        errors.append("ExampleRetrieverV7")

    PromptBuilderV7 = LLMAgentV8 = None
    for mod in ["app.agents.llm_pipeline", "llm_pipeline"]:
        PromptBuilderV7 = _try_import(mod, "PromptBuilderV7")
        LLMAgentV8      = _try_import(mod, "LLMAgentV8")
        if PromptBuilderV7 and LLMAgentV8:
            break
    if not PromptBuilderV7:
        errors.append("PromptBuilderV7")
    if not LLMAgentV8:
        errors.append("LLMAgentV8")

    # GuardrailsV7 — pré-filtre NL dangereux (fusionné dans security_executor.py)
    GuardrailsV7 = None
    for mod in ["app.agents.security_executor", "security_executor"]:
        GuardrailsV7 = _try_import(mod, "GuardrailsV7")
        if GuardrailsV7:
            break
    if not GuardrailsV7:
        errors.append("GuardrailsV7")

    if errors:
        raise ImportError(f"Composants introuvables : {', '.join(errors)}")

    rag = None
    if use_rag:
        RAGAgentV8 = None
        for mod in ["app.agents.rag_agent_v8", "rag_agent_v8"]:
            RAGAgentV8 = _try_import(mod, "RAGAgentV8")
            if RAGAgentV8:
                break
        if RAGAgentV8:
            try:
                rag = RAGAgentV8()
                print("      ✅ RAG Milvus connecté.")
            except Exception as e:
                print(f"      ⚠️  RAG désactivé (Milvus indisponible) : {e}")
        else:
            print("      ⚠️  RAGAgentV8 introuvable, RAG désactivé.")

    return {
        "classifier":  IntentClassifierV7(),
        "registry":    SchemaRegistryV7(),
        "examples":    ExampleRetrieverV7(),
        "pb":          PromptBuilderV7(),
        "llm":         LLMAgentV8(),
        "rag":         rag,
        "guardrails":  GuardrailsV7(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Timeout helper (cross-platform Windows/Linux)
# ─────────────────────────────────────────────────────────────────────────────

class _TimeoutError(Exception):
    pass


def _run_with_timeout(fn, timeout_s: float):
    result_box = [None]
    error_box  = [None]

    def target():
        try:
            result_box[0] = fn()
        except Exception as exc:
            error_box[0] = exc

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=timeout_s)

    if t.is_alive():
        raise _TimeoutError(f"Timeout après {timeout_s}s")
    if error_box[0]:
        raise error_box[0]
    return result_box[0]




GREETING_RESPONSE = (
    "Bonjour ! Je suis votre assistant de maintenance prédictive OCP i-sense. "
    "Posez-moi une question sur les équipements, alarmes, pannes ou mesures."
)

META_RESPONSE = (
    "Je suis l'assistant de maintenance prédictive OCP i-sense. "
    "Je n'ai pas accès à l'heure ou à la date système, et je ne peux répondre "
    "qu'aux questions sur vos équipements, alarmes, pannes, mesures, "
    "recommandations et interventions de maintenance."
)

# NOTE : depuis l'ajout de META_TALK_RGX dans IntentClassifierV7 (identité du
# bot, date/heure, capacités), ces questions sont déjà classées category=="chat"
# par le classifieur lui-même. _OFF_TOPIC_RGX ci-dessous n'est conservé que
# comme filet de sécurité si une ancienne version de IntentClassifierV7 (sans
# META_TALK_RGX) est utilisée — il ne devrait normalement plus jamais matcher.
_OFF_TOPIC_RGX = re.compile(
    r"\b(vous êtes qui|qui êtes[\s-]vous|qui es[\s-]tu|"
    r"quelle est la date|quel jour sommes[\s-]nous|date d'aujourd'hui)\b",
    re.IGNORECASE,
)

# Demandes explicites de données personnelles d'un utilisateur nommé.
# GuardrailsV7.check_nl() ne couvre que les verbes d'action DML/DDL
# (supprime/modifie/ajoute) ; il ne bloque pas en amont une simple demande
# de lecture comme "numéro de téléphone d'Ahmed" ou "mot de passe de
# l'administrateur" — ces questions ne contiennent ni colonne ni nom de
# table, donc GuardrailsV7.check_generated_sql() ne peut les attraper que
# *après* coup, une fois que le LLM a déjà halluciné un SELECT phone/...
# On les bloque donc nous-mêmes, ici, avant le LLM.
_PERSONAL_DATA_RGX = re.compile(
    r"\b(numéro de téléphone|téléphone de|mobile de|"
    r"adresse email|email de|mot de passe|password)\b",
    re.IGNORECASE,
)
_OWNERSHIP_RGX = re.compile(
    r"\b(appartient à quelle entreprise|quelle entreprise|"
    r"quelle société|de quelle entreprise)\b",
    re.IGNORECASE,
)


def _normalize_for_match(text: str) -> str:
    t = text.lower().strip()
    t = unicodedata.normalize("NFC", t)
    return t


def _direct_response_check(question: str, components: Dict, intent) -> Optional[Dict]:
    """
    Retourne un dict {decision, sql, reasoning, category} si la question doit
    être court-circuitée AVANT le LLM, sinon None (→ on continue vers _generate_sql).
    """
    norm = _normalize_for_match(question)

    # 1) Small talk / meta détecté par le classifieur d'intent
    if intent.category == "chat":
        is_meta = (getattr(intent, "action", "") == "META")
        return {
            "sql": "", "decision": "direct_response",
            "reasoning": META_RESPONSE if is_meta else GREETING_RESPONSE,
            "tables": [], "tokens": 0,
            "category": "chat_meta" if is_meta else "chat_greeting",
        }

    # 2) Filet de sécurité hors-sujet (ne devrait plus matcher si
    #    IntentClassifierV7 contient déjà META_TALK_RGX)
    if _OFF_TOPIC_RGX.search(norm):
        return {
            "sql": "", "decision": "direct_response",
            "reasoning": META_RESPONSE,
            "tables": [], "tokens": 0, "category": "off_topic",
        }

    # 3) Actions interdites (DDL/DML) → GuardrailsV7.check_nl()
    #    (fusionné dans security_executor.py)
    guardrails = components.get("guardrails")
    if guardrails:
        check = guardrails.check_nl(question)
        if not check["safe"]:
            return {
                "sql": "", "decision": "blocked_nl",
                "reasoning": check["reason"],
                "tables": [], "tokens": 0, "category": "blocked",
            }

    # 4) Demandes de données personnelles (téléphone, email, mot de passe,
    #    entreprise d'un utilisateur nommé) — bloquées avant le LLM, car
    #    une fois le SQL généré il est déjà trop tard pour éviter la fuite
    #    d'intention même si check_generated_sql() bloquerait l'exécution.
    if _PERSONAL_DATA_RGX.search(norm) or (
        _OWNERSHIP_RGX.search(norm) and intent.category in ("user", "company", "asset")
    ):
        return {
            "sql": "", "decision": "blocked_nl",
            "reasoning": (
                "🔒 Accès interdit : cette question porte sur des données "
                "personnelles d'utilisateur (téléphone, email, mot de passe, "
                "entreprise). Seules les données de maintenance sont accessibles."
            ),
            "tables": [], "tokens": 0, "category": "blocked",
        }

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Génération SQL — pipeline LLM + RAG, avec pré-filtre direct-response
# + décomposition de la latence par composant
# ─────────────────────────────────────────────────────────────────────────────

def _generate_sql(question: str, tenant_db: str, components: Dict) -> Dict:
    """
    Retourne :
      { sql, decision, reasoning, tables, tokens, category,
        timings: {classify, direct_filter, schema, examples, rag, llm} (ms) }
    """
    classifier = components["classifier"]
    registry   = components["registry"]
    examples   = components["examples"]
    pb         = components["pb"]
    llm        = components["llm"]
    rag        = components["rag"]

    timings = {}

    # 1. Classification de l'intent
    t0 = time.perf_counter()
    intent = classifier.classify(question)
    timings["classify"] = (time.perf_counter() - t0) * 1000

    # 1b. Pré-filtre direct-response (small talk / hors-sujet / interdit)
    t0 = time.perf_counter()
    direct = _direct_response_check(question, components, intent)
    timings["direct_filter"] = (time.perf_counter() - t0) * 1000

    if direct is not None:
        timings["schema"] = 0.0
        timings["examples"] = 0.0
        timings["rag"] = 0.0
        timings["llm"] = 0.0
        direct["timings"] = timings
        return direct

    # 2. Contexte schéma depuis SchemaRegistry
    t0 = time.perf_counter()
    rel_tables = registry.get_relevant_tables_from_intent(intent)
    schema_ctx = registry.get_compact_schema_for_tables(rel_tables, tenant_db)
    join_hints = registry.get_join_hints(rel_tables, tenant_db)
    timings["schema"] = (time.perf_counter() - t0) * 1000

    # 3. Exemples BM25 depuis dataset_400_questions
    t0 = time.perf_counter()
    close_ex = examples.retrieve_examples(question, intent=intent, top_k=1)
    cat_ex   = examples.retrieve_category_examples(intent=intent, top_k=2)
    merged   = examples.merge_examples(close_ex, cat_ex, max_total=2)
    ex_ctx   = examples.format_examples_for_prompt(merged, tenant_db, "EXEMPLES UTILES")
    timings["examples"] = (time.perf_counter() - t0) * 1000

    # 4. Contexte RAG Milvus (Dense + BM25 + RRF + CrossEncoder)
    t0 = time.perf_counter()
    rag_ctx = ""
    if rag:
        try:
            rag_ctx = rag.build_prompt_context(
                question=question, tenant_db=tenant_db,
                intent=intent, max_chars=1000
            )
        except Exception:
            pass
    timings["rag"] = (time.perf_counter() - t0) * 1000

    # 5. Prompt + génération Groq
    t0 = time.perf_counter()
    system = pb.build_sql_system_prompt()
    user   = pb.build_sql_user_prompt(
        question=question, tenant_db=tenant_db, intent=intent,
        schema_context=schema_ctx, join_hints=join_hints,
        examples_context=ex_ctx, category_examples_context="",
        negative_examples_context="", rag_context=rag_ctx,
    )

    gen = llm.generate_json(
        prompt=user, system=system, temperature=0.05, max_tokens=1024
    )
    timings["llm"] = (time.perf_counter() - t0) * 1000

    if not gen.get("success"):
        return {
            "sql": "", "decision": "llm_error",
            "reasoning": gen.get("error", ""),
            "tables": [], "tokens": 0,
            "category": intent.category,
            "timings": timings,
        }

    parsed = gen.get("parsed", {})
    return {
        "sql":       parsed.get("sql", ""),
        "decision":  parsed.get("decision", "unknown"),
        "reasoning": parsed.get("reasoning", ""),
        "tables":    parsed.get("tables", []),
        "tokens":    gen.get("tokens", 0),
        "category":  intent.category,
        "timings":   timings,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Comparaison SQL — Jaccard + hallucination de tables
# ─────────────────────────────────────────────────────────────────────────────

def _sql_ok(sql: str) -> bool:
    return bool(sql and sql.strip().upper().startswith("SELECT"))


def _is_direct_decision(decision: str) -> bool:
    """Une réponse directe (chat/off_topic/blocked) est un succès si elle a
    bien été interceptée — elle n'a pas vocation à produire du SQL."""
    return decision in ("direct_response", "blocked_nl")


def _jaccard(ref: str, gen: str) -> float:
    def tok(s):
        return set(re.findall(r"\w+", s.lower()))
    t1, t2 = tok(ref), tok(gen)
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    return round(len(t1 & t2) / len(t1 | t2), 4)


_TABLE_RGX = re.compile(r"\b(?:FROM|JOIN)\s+([a-zA-Z0-9_.]+)", re.IGNORECASE)


def _extract_tables(sql: str) -> List[str]:
    return [t.split(".")[-1].lower() for t in _TABLE_RGX.findall(sql or "")]


def _has_hallucinated_table(sql: str, registry) -> bool:
    """
    Proxy d'hallucination : le SQL référence une table qui n'existe ni dans
    le schéma global ni dans le schéma tenant connus du SchemaRegistry.
    """
    if not sql or registry is None:
        return False
    tables = _extract_tables(sql)
    if not tables:
        return False
    for t in tables:
        if not registry.get_table_schema(t):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# BenchmarkRunner
# ─────────────────────────────────────────────────────────────────────────────

class BenchmarkRunner:
    def __init__(
        self,
        components:    Dict,
        dataset:       List[Dict],
        ref_sql:       Dict[str, str],
        tenant_db:     str,
        max_questions: Optional[int] = None,
        timeout_s:     float = 60.0,
        verbose:       bool  = True,
        pause_s:       float = 10.0,
    ):
        self.components  = components
        self.dataset     = dataset[:max_questions] if max_questions else dataset
        self.ref_sql     = ref_sql
        self.tenant_db   = tenant_db
        self.timeout_s   = timeout_s
        self.verbose     = verbose
        self.pause_s     = pause_s
        self.results:    List[Dict] = []
        self.started_at  = None
        self.finished_at = None

    def _find_ref_sql(self, question: str) -> str:
        if not self.ref_sql:
            return ""
        q_norm = question.strip().lower()
        if q_norm in self.ref_sql:
            return self.ref_sql[q_norm]
        best_score, best_sql = 0.0, ""
        for ref_q, ref_s in self.ref_sql.items():
            score = _jaccard(q_norm, ref_q)
            if score > best_score:
                best_score, best_sql = score, ref_s
        return best_sql if best_score >= 0.3 else ""

    def run(self) -> Dict:
        self.started_at = datetime.now()
        total = len(self.dataset)

        print(f"\n{'═'*72}")
        print(f"  BENCHMARK V9 — GÉNÉRATION SQL (+ pré-filtre direct-response)")
        print(f"  Source questions  : les_questions.txt ({total} questions)")
        print(f"  Référence SQL     : dataset_400_questions ({len(self.ref_sql)} entrées)")
        print(f"  Tenant            : {self.tenant_db}")
        print(f"  Pipeline          : Guardrails NL → IntentClassifier → LLM Groq + RAG Milvus")
        print(f"  Démarré           : {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Timeout/question  : {self.timeout_s}s")
        print(f"{'═'*72}\n")

        for idx, entry in enumerate(self.dataset, start=1):
            question = entry.get("question", "").strip()
            if not question:
                continue

            ref_sql  = self._find_ref_sql(question)
            category = entry.get("metadata", {}).get("category", "unknown")

            if self.verbose:
                print(f"  [{idx:3d}/{total}] {question[:60]:<60}", end=" ", flush=True)

            t0 = time.perf_counter()

            try:
                comps     = self.components
                tenant_db = self.tenant_db

                gen = _run_with_timeout(
                    fn=lambda: _generate_sql(question, tenant_db, comps),
                    timeout_s=self.timeout_s,
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000

                gen_sql  = gen.get("sql", "")
                decision = gen.get("decision", "unknown")
                is_direct = _is_direct_decision(decision)
                ok       = _sql_ok(gen_sql) or is_direct
                sim      = _jaccard(ref_sql, gen_sql) if (_sql_ok(gen_sql) and ref_sql) else 0.0
                has_ref  = bool(ref_sql)
                halluc   = _has_hallucinated_table(gen_sql, comps.get("registry"))

                record = {
                    "index":        idx,
                    "question":     question,
                    "category":     category,
                    "gen_category": gen.get("category", ""),
                    "decision":     decision,
                    "is_direct":    is_direct,
                    "sql_ok":       ok,
                    "similarity":   sim,
                    "has_ref":      has_ref,
                    "hallucination": halluc,
                    "latency_ms":   round(elapsed_ms, 2),
                    "tokens":       gen.get("tokens", 0),
                    "timeout":      False,
                    "error":        "" if ok else gen.get("reasoning", "no SQL"),
                    "sql_ref":      ref_sql,
                    "sql_gen":      gen_sql,
                    "tables_gen":   gen.get("tables", []),
                    "timings":      gen.get("timings", {}),
                }

                if self.verbose:
                    if is_direct:
                        icon, tag = "🟦", f"[{decision}]"
                    elif ok:
                        icon, tag = "✅", (f"sim={sim:.2f}" if has_ref else "ok(no-ref)")
                    else:
                        icon, tag = "❌", "no-sql"
                    h_tag = " ⚠HALLUC" if halluc else ""
                    print(f"{icon}  {elapsed_ms:7.1f}ms  {tag:<14}  [{decision}]{h_tag}")

            except _TimeoutError:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                record = {
                    "index": idx, "question": question,
                    "category": category, "gen_category": "",
                    "decision": "timeout", "is_direct": False,
                    "sql_ok": False, "similarity": 0.0, "has_ref": False,
                    "hallucination": False,
                    "latency_ms": round(elapsed_ms, 2), "tokens": 0,
                    "timeout": True, "error": f"Timeout >{self.timeout_s}s",
                    "sql_ref": ref_sql, "sql_gen": "",
                    "tables_gen": [], "timings": {},
                }
                if self.verbose:
                    print(f"⏱️   {elapsed_ms:7.1f}ms  TIMEOUT")

            except Exception as exc:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                record = {
                    "index": idx, "question": question,
                    "category": category, "gen_category": "",
                    "decision": "exception", "is_direct": False,
                    "sql_ok": False, "similarity": 0.0, "has_ref": False,
                    "hallucination": False,
                    "latency_ms": round(elapsed_ms, 2), "tokens": 0,
                    "timeout": False, "error": str(exc),
                    "sql_ref": ref_sql, "sql_gen": "",
                    "tables_gen": [], "timings": {},
                }
                if self.verbose:
                    print(f"💥  {elapsed_ms:7.1f}ms  {str(exc)[:60]}")

            self.results.append(record)
            if self.pause_s > 0:
                time.sleep(self.pause_s)  # ⏳ pause anti-rate-limit Groq (429)

        self.finished_at = datetime.now()
        return self._compute_stats()

    # ──────────────────────────────────────────────────────────────────────
    def _compute_stats(self) -> Dict:
        total    = len(self.results)
        ok_count = sum(1 for r in self.results if r["sql_ok"])
        sql_generated_count = sum(
            1 for r in self.results if _sql_ok(r["sql_gen"])
        )
        timeouts = sum(1 for r in self.results if r["timeout"])
        with_ref = sum(1 for r in self.results if r.get("has_ref"))
        halluc_count = sum(1 for r in self.results if r.get("hallucination"))

        lats = [r["latency_ms"] for r in self.results]
        srt  = sorted(lats)
        avg_ms = round(sum(lats) / len(lats), 2) if lats else 0
        min_ms = round(min(lats), 2)             if lats else 0
        max_ms = round(max(lats), 2)             if lats else 0
        p50    = round(srt[int(len(srt)*0.50)], 2) if srt else 0
        p95    = round(srt[int(len(srt)*0.95)], 2) if srt else 0

        sims    = [r["similarity"] for r in self.results if _sql_ok(r["sql_gen"]) and r.get("has_ref")]
        avg_sim = round(sum(sims)/len(sims), 4) if sims else 0
        tokens  = sum(r["tokens"] for r in self.results)
        duration = (self.finished_at - self.started_at).total_seconds()

        # Accuracy globale = (SQL valides sur questions SQL) + (bonnes interceptions
        # sur questions directes/bloquées) / total
        accuracy = round(ok_count / total * 100, 2) if total else 0
        hallucination_rate = round(halluc_count / total * 100, 2) if total else 0
        timeout_rate = round(timeouts / total * 100, 2) if total else 0

        by_decision: Dict[str, int] = {}
        for r in self.results:
            d = r["decision"]
            by_decision[d] = by_decision.get(d, 0) + 1

        by_category: Dict[str, Dict] = {}
        for r in self.results:
            c = r["category"]
            if c not in by_category:
                by_category[c] = {"total": 0, "success": 0, "_sims": [], "avg_sim": 0.0}
            by_category[c]["total"]   += 1
            by_category[c]["success"] += int(r["sql_ok"])
            if _sql_ok(r["sql_gen"]) and r.get("has_ref"):
                by_category[c]["_sims"].append(r["similarity"])
        for c, d in by_category.items():
            d["avg_sim"] = round(sum(d["_sims"])/len(d["_sims"]), 4) if d["_sims"] else 0
            d["success_rate_pct"] = round(d["success"]/d["total"]*100, 2) if d["total"] else 0
            del d["_sims"]

        # Décomposition de la latence par composant (moyenne sur les questions
        # routées LLM, càd hors direct-response où ces composants valent 0)
        component_keys = ["classify", "direct_filter", "schema", "examples", "rag", "llm"]
        comp_totals = {k: [] for k in component_keys}
        for r in self.results:
            t = r.get("timings") or {}
            for k in component_keys:
                if k in t:
                    comp_totals[k].append(t[k])
        latency_breakdown = {
            k: round(sum(v)/len(v), 2) if v else 0.0
            for k, v in comp_totals.items()
        }

        failures = [
            {
                "index":      r["index"],
                "question":   r["question"],
                "category":   r["category"],
                "decision":   r["decision"],
                "error":      r["error"],
                "latency_ms": r["latency_ms"],
                "timeout":    r["timeout"],
            }
            for r in self.results if not r["sql_ok"]
        ]

        slowest  = sorted(self.results, key=lambda r: r["latency_ms"], reverse=True)[:5]
        best_sim = sorted(
            [r for r in self.results if _sql_ok(r["sql_gen"]) and r.get("has_ref")],
            key=lambda r: r["similarity"], reverse=True
        )[:5]

        return {
            "meta": {
                "started_at":        self.started_at.isoformat(),
                "finished_at":       self.finished_at.isoformat(),
                "total_duration_s":  round(duration, 2),
                "tenant_db":         self.tenant_db,
                "timeout_setting":   self.timeout_s,
                "source_questions":  "les_questions.txt",
                "source_reference":  "dataset_400_questions",
                "pipeline":          "Guardrails NL → IntentClassifier → LLM Groq + RAG Milvus (sans templates · sans exécution)",
            },
            "summary": {
                "total_questions":      total,
                "sql_generated":        sql_generated_count,
                "sql_not_generated":    total - sql_generated_count,
                "generation_rate_pct":  round(sql_generated_count/total*100, 2) if total else 0,
                "questions_with_ref":   with_ref,
                "avg_similarity":       avg_sim,
                "avg_latency_ms":       avg_ms,
                "min_latency_ms":       min_ms,
                "max_latency_ms":       max_ms,
                "p50_latency_ms":       p50,
                "p95_latency_ms":       p95,
                "hard_timeouts":        timeouts,
                "timeout_rate_pct":     timeout_rate,
                "total_tokens":         tokens,
                "total_duration_s":     round(duration, 2),
                "accuracy_pct":         accuracy,
                "hallucination_count":  halluc_count,
                "hallucination_rate_pct": hallucination_rate,
            },
            "by_decision":        by_decision,
            "by_category":        by_category,
            "latency_breakdown":  latency_breakdown,
            "failures":           failures,
            "slowest_5":          [{"q": r["question"][:70], "ms": r["latency_ms"]} for r in slowest],
            "best_sim_5": [
                {"q": r["question"][:70], "sim": r["similarity"], "ms": r["latency_ms"]}
                for r in best_sim
            ],
            "results": self.results,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Rapport texte
# ─────────────────────────────────────────────────────────────────────────────

def _bar(ratio, width=30):
    f = int(round(ratio * width))
    return "█" * f + "░" * (width - f)


def generate_text_report(stats: Dict) -> str:
    s = stats["summary"]
    m = stats["meta"]
    W = 72
    sep = "─" * W
    dbl = "═" * W

    def kv(label, value):
        return f"  {label:<28}: {value}"

    lines = [
        "",
        dbl,
        "  RAPPORT BENCHMARK V9 — GÉNÉRATION SQL",
        "  Source questions : les_questions.txt",
        "  Pipeline : Guardrails NL → IntentClassifier → LLM Groq + RAG Milvus",
        dbl,
        kv("Tenant",              m["tenant_db"]),
        kv("Début",               m["started_at"][:19]),
        kv("Fin",                 m["finished_at"][:19]),
        kv("Durée totale benchmark", f"{m['total_duration_s']} s"),
        kv("Timeout / question",  f"{m['timeout_setting']} s"),
        sep,
        "  KPIs PRINCIPAUX",
        sep,
        kv("Total questions",     str(s["total_questions"])),
        kv("SQL générés avec succès",
           f"{s['generation_rate_pct']:.2f}%  ({s['sql_generated']}/{s['total_questions']})"),
        kv("Accuracy globale",    f"{s['accuracy_pct']:.2f}%"),
        kv("Questions avec réf.", str(s["questions_with_ref"])),
        kv("Similarité Jaccard moy.", f"{s['avg_similarity']:.4f}"),
        kv("Hallucination (tables inconnues)",
           f"{s['hallucination_rate_pct']:.2f}%  ({s['hallucination_count']}/{s['total_questions']})"),
        kv("Latence minimale",    f"{s['min_latency_ms']:.2f} ms"),
        kv("Latence moyenne",     f"{s['avg_latency_ms']:.2f} ms"),
        kv("Latence maximale",    f"{s['max_latency_ms']:.2f} ms"),
        kv("Latence P50 / P95",   f"{s['p50_latency_ms']:.2f} ms / {s['p95_latency_ms']:.2f} ms"),
        kv("Timeouts (> {:.0f}s)".format(m["timeout_setting"]),
           f"{s['hard_timeouts']}  ({s['timeout_rate_pct']:.2f}%)"),
        kv("Tokens totaux",       str(s["total_tokens"])),
        "",
        f"  SQL OK  [{_bar(s['sql_generated']/s['total_questions'] if s['total_questions'] else 0)}]"
        f"  {s['generation_rate_pct']:.1f}%",
        sep,
        "  LATENCE DÉTAILLÉE",
        sep,
        kv("Min",  f"{s['min_latency_ms']:.2f} ms"),
        kv("Moy",  f"{s['avg_latency_ms']:.2f} ms"),
        kv("Max",  f"{s['max_latency_ms']:.2f} ms"),
        kv("P50",  f"{s['p50_latency_ms']:.2f} ms"),
        kv("P95",  f"{s['p95_latency_ms']:.2f} ms"),
        sep,
        "  DÉCOMPOSITION LATENCE PAR COMPOSANT (moyenne)",
        sep,
    ]

    labels = {
        "classify": "Classification intent", "direct_filter": "Filtre direct-response",
        "schema": "Schema registry", "examples": "Exemples BM25",
        "rag": "RAG Milvus", "llm": "Appel LLM Groq",
    }
    for k, v in stats["latency_breakdown"].items():
        lines.append(f"  {labels.get(k, k):<28}: {v:8.2f} ms")

    lines += [sep, "  PAR DÉCISION", sep]
    for dec, cnt in sorted(stats["by_decision"].items(), key=lambda x: -x[1]):
        lines.append(f"  {dec:<32}  {cnt:4d} question(s)")

    lines += [sep, "  TAUX DE SUCCÈS PAR CATÉGORIE", sep]
    for cat, d in sorted(stats["by_category"].items(), key=lambda x: -x[1]["total"]):
        lines.append(
            f"  {cat:<45}  n={d['total']:3d}  ok={d['success']:3d}"
            f"  ({d['success_rate_pct']:.1f}%)  sim={d['avg_sim']:.3f}"
        )

    if stats["failures"]:
        lines += [sep, f"  ÉCHECS — SQL non généré ({len(stats['failures'])} questions)", sep]
        for f in stats["failures"][:30]:
            tag = " [TIMEOUT]" if f["timeout"] else ""
            lines.append(
                f"  [{f['index']:3d}] [{f['category']:<25}]"
                f"  {f['latency_ms']:8.1f}ms  {f['question'][:50]}{tag}"
            )
            if f["error"]:
                lines.append(f"        ↳ {f['error'][:100]}")
        if len(stats["failures"]) > 30:
            lines.append(f"  ... et {len(stats['failures'])-30} autres (voir CSV/JSON).")

    lines += [sep, "  TOP 5 QUESTIONS LES PLUS LENTES", sep]
    for item in stats["slowest_5"]:
        lines.append(f"  {item['ms']:9.1f}ms  {item['q']}")

    if stats["best_sim_5"]:
        lines += [sep, "  TOP 5 MEILLEURES SIMILARITÉS JACCARD", sep]
        for item in stats["best_sim_5"]:
            lines.append(f"  sim={item['sim']:.4f}  {item['ms']:8.1f}ms  {item['q']}")

    lines += [dbl, ""]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Graphiques (matplotlib)
# ─────────────────────────────────────────────────────────────────────────────

def generate_charts(stats: Dict, base: Path) -> List[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    paths = []

    # ── 1. Taux de succès par catégorie ─────────────────────────────────────
    by_cat = stats["by_category"]
    cats = sorted(by_cat.keys(), key=lambda c: -by_cat[c]["total"])
    rates = [by_cat[c]["success_rate_pct"] for c in cats]
    ns    = [by_cat[c]["total"] for c in cats]

    fig, ax = plt.subplots(figsize=(11, max(4, 0.45 * len(cats))))
    colors = ["#2ecc71" if r >= 80 else ("#f39c12" if r >= 50 else "#e74c3c") for r in rates]
    bars = ax.barh(cats, rates, color=colors)
    ax.set_xlabel("Taux de succès (%)")
    ax.set_xlim(0, 100)
    ax.set_title("Taux de succès par catégorie de question")
    ax.invert_yaxis()
    for bar, n, r in zip(bars, ns, rates):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                 f"{r:.0f}%  (n={n})", va="center", fontsize=8)
    fig.tight_layout()
    p1 = base.parent / f"{base.name}_success_by_category.png"
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    paths.append(p1)

    # ── 2. Distribution des types de question ───────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 8))
    sizes = ns
    explode = [0.03] * len(cats)
    ax.pie(
        sizes, labels=cats, autopct="%1.1f%%", startangle=90,
        explode=explode, pctdistance=0.8,
        textprops={"fontsize": 8},
    )
    ax.set_title("Distribution des types de question (par catégorie)")
    fig.tight_layout()
    p2 = base.parent / f"{base.name}_distribution_categories.png"
    fig.savefig(p2, dpi=150)
    plt.close(fig)
    paths.append(p2)

    # ── 3. Décomposition de la latence par composant ────────────────────────
    breakdown = stats["latency_breakdown"]
    labels = {
        "classify": "Classification\nintent", "direct_filter": "Filtre\ndirect-response",
        "schema": "Schema\nregistry", "examples": "Exemples\nBM25",
        "rag": "RAG\nMilvus", "llm": "Appel LLM\nGroq",
    }
    keys = list(breakdown.keys())
    vals = [breakdown[k] for k in keys]
    names = [labels.get(k, k) for k in keys]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(names, vals, color="#3498db")
    ax.set_ylabel("Latence moyenne (ms)")
    ax.set_title("Décomposition de la latence par composant")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 f"{v:.0f}ms", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    p3 = base.parent / f"{base.name}_latency_breakdown.png"
    fig.savefig(p3, dpi=150)
    plt.close(fig)
    paths.append(p3)

    return paths


# ─────────────────────────────────────────────────────────────────────────────
# Sauvegarde CSV / JSON / TXT
# ─────────────────────────────────────────────────────────────────────────────

def save_csv(stats: Dict, path: Path):
    fields = [
        "index", "question", "category", "gen_category",
        "decision", "is_direct", "sql_ok", "has_ref", "similarity",
        "hallucination", "latency_ms", "tokens", "timeout", "error",
        "sql_ref", "sql_gen",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in stats["results"]:
            row = {}
            for k in fields:
                v = r.get(k, "")
                row[k] = (
                    str(v).replace("\n", " ").strip()
                    if k in ("question", "sql_ref", "sql_gen", "error")
                    else v
                )
            w.writerow(row)


def save_json(stats: Dict, path: Path):
    export = {k: v for k, v in stats.items() if k != "results"}
    export["results_detail"] = [
        {k: r.get(k) for k in [
            "index", "question", "category", "decision", "is_direct",
            "sql_ok", "has_ref", "similarity", "hallucination",
            "latency_ms", "tokens", "timeout", "error", "sql_gen", "timings",
        ]}
        for r in stats["results"]
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2, default=str)


def save_txt(report: str, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description=(
            "Benchmark V9 — questions depuis les_questions.txt\n"
            "Pipeline : Guardrails NL → IntentClassifier → LLM Groq + RAG Milvus\n"
            "❌ sans templates  |  ❌ sans exécution SQL\n"
            "✅ pré-filtre direct-response (small talk / hors-sujet / interdit)\n"
            "✅ catégories auto-extraites de les_questions.txt\n"
            "✅ décomposition latence par composant + 3 graphiques PNG"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--max",     type=int,   default=None,
                   help="Nombre max de questions (défaut: toutes)")
    p.add_argument("--tenant",  type=str,   default="v3_tenant_Site_Safi",
                   help=(
                       "Tenant cible (défaut: v3_tenant_Site_Safi)\n"
                       "Autres options : v3_tenant_jln  v3_tenant_ntn  "
                       "v3_tenant_jfc4  v3_tenant_cmcp"
                   ))
    p.add_argument("--out",     type=str,   default="rapport_benchmark_v9",
                   help="Préfixe des fichiers de sortie")
    p.add_argument("--timeout", type=float, default=60.0,
                   help="Timeout par question en secondes (défaut: 60)")
    p.add_argument("--pause",   type=float, default=10.0,
                   help="Pause entre questions en secondes, anti rate-limit Groq (défaut: 10)")
    p.add_argument("--no-rag",  action="store_true",
                   help="Désactiver le RAG Milvus")
    p.add_argument("--no-charts", action="store_true",
                   help="Ne pas générer les graphiques PNG")
    p.add_argument("--quiet",   action="store_true",
                   help="Masquer la progression question par question")
    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print(f"\n  Backend root détecté : {_backend_root}")
    print(f"  ⚙️  Mode : sans templates paramétriques · sans exécution SQL")
    print(f"  ⚙️  Pré-filtre direct-response activé (small talk / hors-sujet / interdit)\n")

    # ── 1. Questions depuis les_questions.txt ────────────────────────────────
    print("[1/3] Chargement des questions depuis les_questions.txt...")
    try:
        dataset = _load_questions_txt()
        if args.max:
            dataset = dataset[:args.max]
            print(f"      ✂️  Limité à {len(dataset)} questions (--max {args.max}).")
    except FileNotFoundError as e:
        print(f"      ❌ {e}")
        sys.exit(1)

    # ── 1b. SQL de référence depuis dataset_400_questions ────────────────────
    print("[1b/3] Chargement des SQL de référence depuis dataset_400_questions...")
    ref_sql = _load_reference_sql()

    # ── 2. Composants LLM ────────────────────────────────────────────────────
    rag_label = "OFF (--no-rag)" if args.no_rag else "ON"
    print(f"[2/3] Chargement des composants (RAG={rag_label})...")
    try:
        components = _import_components(use_rag=not args.no_rag)
        print("      ✅ Composants prêts.")
    except Exception as e:
        print(f"      ❌ {e}")
        sys.exit(1)

    # ── 3. Lancement du benchmark ────────────────────────────────────────────
    print("[3/3] Lancement du benchmark...\n")
    runner = BenchmarkRunner(
        components=components,
        dataset=dataset,
        ref_sql=ref_sql,
        tenant_db=args.tenant,
        max_questions=None,
        timeout_s=args.timeout,
        verbose=not args.quiet,
        pause_s=args.pause,
    )
    stats = runner.run()

    # ── Sauvegarde des rapports ──────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name  = args.out if isinstance(args.out, str) else "rapport_benchmark_v9"
    base      = Path(out_name + f"_{timestamp}")

    report = generate_text_report(stats)
    print(report)

    try:
        save_csv(stats,  base.with_suffix(".csv"))
        save_json(stats, base.with_suffix(".json"))
        save_txt(report, base.with_suffix(".txt"))
        print(f"  📄 CSV  : {base.with_suffix('.csv')}")
        print(f"  📄 JSON : {base.with_suffix('.json')}")
        print(f"  📄 TXT  : {base.with_suffix('.txt')}")
    except Exception as e:
        print(f"  ⚠️  Sauvegarde échouée : {e}")
        fallback = Path(f"benchmark_result_{timestamp}.txt")
        fallback.write_text(report, encoding="utf-8")
        print(f"  📄 Rapport de secours : {fallback}")

    if not args.no_charts:
        try:
            chart_paths = generate_charts(stats, base)
            for cp in chart_paths:
                print(f"  📊 Graphique : {cp}")
        except Exception as e:
            print(f"  ⚠️  Génération graphiques échouée : {e}")

    print("  ✅ Terminé.\n")


if __name__ == "__main__":
    main()