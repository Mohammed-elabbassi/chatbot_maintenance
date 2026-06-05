#!/usr/bin/env python3
"""
run_benchmark.py
════════════════════════════════════════════════════════════════════════════════
Benchmark GÉNÉRATION SQL UNIQUEMENT (sans exécution, sans templates).

Source des questions  : les_questions.txt
Référence SQL         : DATASET_400_QUESTIONS (pour similarité Jaccard)
Pipeline              : LLM Groq + RAG Milvus hybride (pas de templates paramétriques)

Usage :
    python run_benchmark.py
    python run_benchmark.py --max 10
    python run_benchmark.py --tenant v3_tenant_Site_Safi
    python run_benchmark.py --no-rag
    python run_benchmark.py --timeout 60
    python run_benchmark.py --out mon_rapport
"""

import argparse
import csv
import json
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Chargement .env (GROQ_API_KEY)
# ─────────────────────────────────────────────────────────────────────────────

def _load_env():
    """Cherche et charge le .env dans les dossiers parents."""
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
        pass  # python-dotenv non installé, on continue

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
# ─────────────────────────────────────────────────────────────────────────────

def _load_questions_txt() -> List[Dict]:
    """
    Charge les questions depuis les_questions.txt.
    Cherche le fichier dans plusieurs emplacements.
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
        Path("chatbot_maintenance/backend/app/database/les_questions.txt"),
        Path("chatbot_maintenance/backend/app/agents/les_questions.txt"),
    ]

    for path in candidates:
        if path.exists():
            print(f"      📄 Fichier trouvé : {path}")
            lines = path.read_text(encoding="utf-8").splitlines()
            questions = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    questions.append({
                        "question": line,
                        "sql":      "",
                        "metadata": {"category": "unknown"}
                    })
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
    """
    Charge le dataset_400_questions comme dictionnaire question → SQL.
    Utilisé uniquement pour calculer la similarité Jaccard.
    """
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
# Chargement des composants LLM (sans templates, sans exécuteur)
# ─────────────────────────────────────────────────────────────────────────────

def _import_components(use_rag: bool = True) -> Dict:
    """
    Importe uniquement les composants nécessaires à la génération SQL.
    Exclus volontairement : SQLExecutorV7, ParametricTemplateEngineV6, SQLRepairV8.
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

    if errors:
        raise ImportError(f"Composants introuvables : {', '.join(errors)}")

    # RAG Milvus (optionnel)
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
        "classifier": IntentClassifierV7(),
        "registry":   SchemaRegistryV7(),
        "examples":   ExampleRetrieverV7(),
        "pb":         PromptBuilderV7(),
        "llm":        LLMAgentV8(),
        "rag":        rag,
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


# ─────────────────────────────────────────────────────────────────────────────
# Génération SQL — pipeline LLM + RAG (sans templates, sans exécution)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_sql(question: str, tenant_db: str, components: Dict) -> Dict:
    """
    Génère un SQL via LLM Groq + RAG Milvus hybride.
    Sans template paramétrique. Sans exécution SQL.
    Retourne : { sql, decision, reasoning, tables, tokens, category }
    """
    classifier = components["classifier"]
    registry   = components["registry"]
    examples   = components["examples"]
    pb         = components["pb"]
    llm        = components["llm"]
    rag        = components["rag"]

    # 1. Classification de l'intent
    intent = classifier.classify(question)

    # 2. Contexte schéma depuis SchemaRegistry
    rel_tables = registry.get_relevant_tables_from_intent(intent)
    schema_ctx = registry.get_compact_schema_for_tables(rel_tables, tenant_db)
    join_hints = registry.get_join_hints(rel_tables, tenant_db)

    # 3. Exemples BM25 depuis dataset_400_questions (comme référence seulement)
    close_ex = examples.retrieve_examples(question, intent=intent, top_k=2)
    cat_ex   = examples.retrieve_category_examples(intent=intent, top_k=2)
    merged   = examples.merge_examples(close_ex, cat_ex, max_total=4)
    ex_ctx   = examples.format_examples_for_prompt(merged, tenant_db, "EXEMPLES UTILES")

    # 4. Contexte RAG Milvus (Dense + BM25 + RRF + CrossEncoder)
    rag_ctx = ""
    if rag:
        try:
            rag_ctx = rag.build_prompt_context(
                question=question, tenant_db=tenant_db,
                intent=intent, max_chars=1600
            )
        except Exception:
            pass

    # 5. Construction du prompt et génération Groq
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

    if not gen.get("success"):
        return {
            "sql": "", "decision": "llm_error",
            "reasoning": gen.get("error", ""),
            "tables": [], "tokens": 0,
            "category": intent.category,
        }

    parsed = gen.get("parsed", {})
    return {
        "sql":       parsed.get("sql", ""),
        "decision":  parsed.get("decision", "unknown"),
        "reasoning": parsed.get("reasoning", ""),
        "tables":    parsed.get("tables", []),
        "tokens":    gen.get("tokens", 0),
        "category":  intent.category,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Comparaison SQL — Jaccard
# ─────────────────────────────────────────────────────────────────────────────

def _sql_ok(sql: str) -> bool:
    return bool(sql and sql.strip().upper().startswith("SELECT"))


def _jaccard(ref: str, gen: str) -> float:
    import re
    def tok(s): return set(re.findall(r"\w+", s.lower()))
    t1, t2 = tok(ref), tok(gen)
    if not t1 and not t2: return 1.0
    if not t1 or not t2:  return 0.0
    return round(len(t1 & t2) / len(t1 | t2), 4)


# ─────────────────────────────────────────────────────────────────────────────
# BenchmarkRunner
# ─────────────────────────────────────────────────────────────────────────────

class BenchmarkRunner:
    def __init__(
        self,
        components:    Dict,
        dataset:       List[Dict],      # questions depuis les_questions.txt
        ref_sql:       Dict[str, str],  # question (lowercase) → SQL de référence
        tenant_db:     str,
        max_questions: Optional[int] = None,
        timeout_s:     float = 60.0,
        verbose:       bool  = True,
    ):
        self.components  = components
        self.dataset     = dataset[:max_questions] if max_questions else dataset
        self.ref_sql     = ref_sql
        self.tenant_db   = tenant_db
        self.timeout_s   = timeout_s
        self.verbose     = verbose
        self.results:    List[Dict] = []
        self.started_at  = None
        self.finished_at = None

    def _find_ref_sql(self, question: str) -> str:
        """
        Cherche le SQL de référence le plus proche par similarité Jaccard.
        Retourne '' si aucune correspondance suffisante (seuil 0.3).
        """
        if not self.ref_sql:
            return ""
        q_norm = question.strip().lower()
        # Correspondance exacte
        if q_norm in self.ref_sql:
            return self.ref_sql[q_norm]
        # Meilleure similarité Jaccard
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
        print(f"  BENCHMARK — GÉNÉRATION SQL UNIQUEMENT")
        print(f"  Source questions  : les_questions.txt ({total} questions)")
        print(f"  Référence SQL     : dataset_400_questions ({len(self.ref_sql)} entrées)")
        print(f"  Tenant            : {self.tenant_db}")
        print(f"  Pipeline          : LLM Groq + RAG Milvus (sans templates, sans exécution)")
        print(f"  Démarré           : {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Timeout/question  : {self.timeout_s}s")
        print(f"{'═'*72}\n")

        for idx, entry in enumerate(self.dataset, start=1):
            question = entry.get("question", "").strip()
            if not question:
                continue

            # Cherche le SQL de référence le plus proche
            ref_sql  = self._find_ref_sql(question)
            category = entry.get("metadata", {}).get("category", "unknown")

            if self.verbose:
                print(f"  [{idx:3d}/{total}] {question[:68]:<68}", end=" ", flush=True)

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
                ok       = _sql_ok(gen_sql)
                sim      = _jaccard(ref_sql, gen_sql) if (ok and ref_sql) else 0.0
                has_ref  = bool(ref_sql)

                record = {
                    "index":        idx,
                    "question":     question,
                    "category":     gen.get("category", category),
                    "decision":     decision,
                    "sql_ok":       ok,
                    "similarity":   sim,
                    "has_ref":      has_ref,
                    "latency_ms":   round(elapsed_ms, 2),
                    "tokens":       gen.get("tokens", 0),
                    "timeout":      False,
                    "error":        "" if ok else gen.get("reasoning", "no SQL"),
                    "sql_ref":      ref_sql,
                    "sql_gen":      gen_sql,
                    "tables_gen":   gen.get("tables", []),
                    "gen_category": gen.get("category", ""),
                }

                if self.verbose:
                    icon    = "✅" if ok else "❌"
                    ref_tag = f"sim={sim:.2f}" if (ok and has_ref) else ("ok(no-ref)" if ok else "no-sql")
                    print(f"{icon}  {elapsed_ms:7.1f}ms  {ref_tag:<14}  [{decision}]")

            except _TimeoutError:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                record = {
                    "index": idx, "question": question,
                    "category": category, "decision": "timeout",
                    "sql_ok": False, "similarity": 0.0, "has_ref": False,
                    "latency_ms": round(elapsed_ms, 2), "tokens": 0,
                    "timeout": True, "error": f"Timeout >{self.timeout_s}s",
                    "sql_ref": ref_sql, "sql_gen": "",
                    "tables_gen": [], "gen_category": "",
                }
                if self.verbose:
                    print(f"⏱️   {elapsed_ms:7.1f}ms  TIMEOUT")

            except Exception as exc:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                record = {
                    "index": idx, "question": question,
                    "category": category, "decision": "exception",
                    "sql_ok": False, "similarity": 0.0, "has_ref": False,
                    "latency_ms": round(elapsed_ms, 2), "tokens": 0,
                    "timeout": False, "error": str(exc),
                    "sql_ref": ref_sql, "sql_gen": "",
                    "tables_gen": [], "gen_category": "",
                }
                if self.verbose:
                    print(f"💥  {elapsed_ms:7.1f}ms  {str(exc)[:60]}")

            self.results.append(record)

        self.finished_at = datetime.now()
        return self._compute_stats()

    def _compute_stats(self) -> Dict:
        total    = len(self.results)
        ok_count = sum(1 for r in self.results if r["sql_ok"])
        timeouts = sum(1 for r in self.results if r["timeout"])
        with_ref = sum(1 for r in self.results if r.get("has_ref"))

        lats = [r["latency_ms"] for r in self.results]
        srt  = sorted(lats)
        avg_ms = round(sum(lats) / len(lats), 2) if lats else 0
        min_ms = round(min(lats), 2)             if lats else 0
        max_ms = round(max(lats), 2)             if lats else 0
        p50    = round(srt[int(len(srt)*0.50)], 2) if srt else 0
        p95    = round(srt[int(len(srt)*0.95)], 2) if srt else 0

        sims    = [r["similarity"] for r in self.results if r["sql_ok"] and r.get("has_ref")]
        avg_sim = round(sum(sims)/len(sims), 4) if sims else 0
        tokens  = sum(r["tokens"] for r in self.results)
        duration= (self.finished_at - self.started_at).total_seconds()

        by_decision: Dict[str, int] = {}
        for r in self.results:
            d = r["decision"]
            by_decision[d] = by_decision.get(d, 0) + 1

        by_category: Dict[str, Dict] = {}
        for r in self.results:
            c = r["category"]
            if c not in by_category:
                by_category[c] = {"total": 0, "sql_ok": 0, "_sims": [], "avg_sim": 0.0}
            by_category[c]["total"]  += 1
            by_category[c]["sql_ok"] += int(r["sql_ok"])
            if r["sql_ok"] and r.get("has_ref"):
                by_category[c]["_sims"].append(r["similarity"])
        for c, d in by_category.items():
            d["avg_sim"] = round(sum(d["_sims"])/len(d["_sims"]), 4) if d["_sims"] else 0
            del d["_sims"]

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
            [r for r in self.results if r["sql_ok"] and r.get("has_ref")],
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
                "pipeline":          "LLM Groq + RAG Milvus (sans templates, sans exécution)",
            },
            "summary": {
                "total_questions":      total,
                "sql_generated":        ok_count,
                "sql_not_generated":    total - ok_count,
                "generation_rate_pct":  round(ok_count/total*100, 2) if total else 0,
                "questions_with_ref":   with_ref,
                "avg_similarity":       avg_sim,
                "avg_latency_ms":       avg_ms,
                "min_latency_ms":       min_ms,
                "max_latency_ms":       max_ms,
                "p50_latency_ms":       p50,
                "p95_latency_ms":       p95,
                "hard_timeouts":        timeouts,
                "total_tokens":         tokens,
                "total_duration_s":     round(duration, 2),
            },
            "by_decision":  by_decision,
            "by_category":  by_category,
            "failures":     failures,
            "slowest_5":    [{"q": r["question"][:70], "ms": r["latency_ms"]} for r in slowest],
            "best_sim_5":   [
                {"q": r["question"][:70], "sim": r["similarity"], "ms": r["latency_ms"]}
                for r in best_sim
            ],
            "results":      self.results,
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
        return f"  {label:<26}: {value}"

    lines = [
        "",
        dbl,
        "  RAPPORT BENCHMARK — GÉNÉRATION SQL",
        "  Source questions : les_questions.txt",
        "  Pipeline : LLM Groq + RAG Milvus (sans templates · sans exécution)",
        dbl,
        kv("Tenant",              m["tenant_db"]),
        kv("Début",               m["started_at"][:19]),
        kv("Fin",                 m["finished_at"][:19]),
        kv("Durée totale",        f"{m['total_duration_s']} s"),
        kv("Timeout / question",  f"{m['timeout_setting']} s"),
        sep,
        "  KPIs PRINCIPAUX",
        sep,
        kv("Total questions",     str(s["total_questions"])),
        kv("SQL générés",
           f"{s['generation_rate_pct']:.2f}%  ({s['sql_generated']}/{s['total_questions']})"),
        kv("Questions avec réf.", str(s["questions_with_ref"])),
        kv("Similarité moyenne",  f"{s['avg_similarity']:.4f}  (Jaccard)"),
        kv("Latence moyenne",     f"{s['avg_latency_ms']:.2f} ms"),
        kv("Timeouts",            str(s["hard_timeouts"])),
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
        "  PAR DÉCISION LLM",
        sep,
    ]

    for dec, cnt in sorted(stats["by_decision"].items(), key=lambda x: -x[1]):
        lines.append(f"  {dec:<32}  {cnt:4d} question(s)")

    lines += [sep, "  PAR CATÉGORIE (intent détecté)", sep]
    for cat, d in sorted(stats["by_category"].items(), key=lambda x: -x[1]["total"]):
        rate = (f"{d['sql_ok']/d['total']*100:.1f}%" if d["total"] else "0%")
        lines.append(
            f"  {cat:<20}  n={d['total']:3d}  ok={d['sql_ok']:3d}"
            f"  ({rate})  sim={d['avg_sim']:.3f}"
        )

    if stats["failures"]:
        lines += [sep, f"  ÉCHECS — SQL non généré ({len(stats['failures'])} questions)", sep]
        for f in stats["failures"][:30]:
            tag = " [TIMEOUT]" if f["timeout"] else ""
            lines.append(
                f"  [{f['index']:3d}] [{f['category']:<16}]"
                f"  {f['latency_ms']:8.1f}ms  {f['question'][:55]}{tag}"
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
# Sauvegarde CSV / JSON / TXT
# ─────────────────────────────────────────────────────────────────────────────

def save_csv(stats: Dict, path: Path):
    fields = [
        "index", "question", "category", "gen_category",
        "decision", "sql_ok", "has_ref", "similarity",
        "latency_ms", "tokens", "timeout", "error",
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
            "index", "question", "category", "decision",
            "sql_ok", "has_ref", "similarity",
            "latency_ms", "tokens", "timeout", "error", "sql_gen",
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
        description="Benchmark génération SQL — questions depuis les_questions.txt"
    )
    p.add_argument("--max",     type=int,   default=None,
                   help="Nombre max de questions (défaut: toutes)")
    p.add_argument("--tenant",  type=str,   default="v3_tenant_Site_Safi",
                   help="Tenant cible (défaut: v3_tenant_Site_Safi)")
    p.add_argument("--out",     type=str,   default="rapport_benchmark",
                   help="Préfixe des fichiers de sortie")
    p.add_argument("--timeout", type=float, default=60.0,
                   help="Timeout par question en secondes (défaut: 60)")
    p.add_argument("--no-rag",  action="store_true",
                   help="Désactiver le RAG Milvus")
    p.add_argument("--quiet",   action="store_true",
                   help="Masquer la progression question par question")
    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print(f"\n  Backend root détecté : {_backend_root}")

    # ── 1. Questions depuis les_questions.txt ────────────────────────────────
    print("\n[1/3] Chargement des questions depuis les_questions.txt...")
    try:
        dataset = _load_questions_txt()
        print(f"      ✅ {len(dataset)} questions chargées.")
    except FileNotFoundError as e:
        print(f"      ❌ {e}")
        sys.exit(1)

    # ── 1b. SQL de référence depuis dataset_400_questions ────────────────────
    print("[1b/3] Chargement des SQL de référence depuis dataset_400_questions...")
    ref_sql = _load_reference_sql()

    # ── 2. Composants LLM ────────────────────────────────────────────────────
    rag_label = "OFF" if args.no_rag else "ON"
    print(f"[2/3] Chargement des composants LLM (RAG={rag_label})...")
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
        max_questions=args.max,
        timeout_s=args.timeout,
        verbose=not args.quiet,
    )
    stats = runner.run()

    # ── Sauvegarde des rapports ──────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name  = args.out if isinstance(args.out, str) else "rapport_benchmark"
    base      = Path(out_name + f"_{timestamp}")

    report = generate_text_report(stats)
    print(report)

    try:
        save_csv(base.with_suffix(".csv"),   stats)
        save_json(base.with_suffix(".json"), stats)
        save_txt(report, base.with_suffix(".txt"))
        print(f"  📄 CSV  : {base.with_suffix('.csv')}")
        print(f"  📄 JSON : {base.with_suffix('.json')}")
        print(f"  📄 TXT  : {base.with_suffix('.txt')}")
    except Exception as e:
        print(f"  ⚠️  Sauvegarde échouée : {e}")
        # Sauvegarde de secours dans le répertoire courant
        fallback = Path(f"benchmark_result_{timestamp}.txt")
        fallback.write_text(report, encoding="utf-8")
        print(f"  📄 Rapport de secours : {fallback}")

    print("  ✅ Terminé.\n")


if __name__ == "__main__":
    main()