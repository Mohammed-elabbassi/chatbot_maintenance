# backend/app/agents/llm_pipeline.py
"""
Fusion de :
  - prompt_builder_v7.py  → PromptBuilderV7
  - llm_agent_v8.py       → LLMAgentV8
  - sql_repair_v8.py      → SQLRepairV8

Importer ce seul module à la place des trois anciens.
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# TENANT NAME FIXES (anciennement dans llm_agent_v8)
# ─────────────────────────────────────────────────────────────────────────────

_TENANT_NAME_FIXES: Dict[str, str] = {
    "v3_tenant_Safi":  "v3_tenant_Site_Safi",
    "v3_tenant_safi":  "v3_tenant_Site_Safi",
    "v3_tenant_SAFI":  "v3_tenant_Site_Safi",
    "v3_tenant_Nomac": "v3_tenant_nomac",
    "v3_tenant_NOMAC": "v3_tenant_nomac",
    "v3_tenant_JLN":   "v3_tenant_jln",
    "v3_tenant_NTN":   "v3_tenant_ntn",
}


def _fix_tenant_name(sql: str) -> str:
    for wrong, correct in _TENANT_NAME_FIXES.items():
        sql = sql.replace(wrong, correct)
    return sql


def _normalize_sql(sql: str) -> str:
    sql = sql.strip()
    sql = re.sub(r"\s+", " ", sql)
    if sql and not sql.endswith(";"):
        sql += ";"
    return _fix_tenant_name(sql)


# ─────────────────────────────────────────────────────────────────────────────
# LLM AGENT  (Groq LLaMA 3.1 8B)
# ─────────────────────────────────────────────────────────────────────────────

class LLMAgentV8:
    """
    Wrapper Groq LLaMA 3.1 8B.

    Corrections intégrées :
      V8.2-fix1 : _parse_free_text_format() parse « Decision: sql\\nSQL: SELECT… »
      V8.2-fix2 : max_tokens auto-adaptatif (2048 si prompt > 8000 chars)
      V8.2-fix3 : _clean_json_strings() pour SQL multiligne dans JSON
      V8.2-fix4 : fix_tenant_name() corrige v3_tenant_Safi → v3_tenant_Site_Safi
    """

    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        from groq import Groq  # import lazy pour ne pas bloquer si groq absent
        self.model  = model or self.DEFAULT_MODEL
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        self.stats  = {"calls": 0, "success": 0, "failed": 0}

    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        return len(os.getenv("GROQ_API_KEY", "")) > 10

    # ------------------------------------------------------------------
    def generate(
        self,
        prompt:      str,
        system:      Optional[str] = None,
        temperature: float = 0.05,
        max_tokens:  int   = 2048,
        timeout:     int   = 60,
    ) -> Dict:
        self.stats["calls"] += 1
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            self.stats["success"] += 1
            return {
                "success":  True,
                "response": (resp.choices[0].message.content or "").strip(),
                "tokens":   resp.usage.total_tokens if resp.usage else 0,
            }
        except Exception as exc:
            self.stats["failed"] += 1
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    def generate_json(
        self,
        prompt:      str,
        system:      Optional[str] = None,
        temperature: float = 0.05,
        max_tokens:  int | None = None,
        timeout:     int   = 60,
    ) -> Dict:
        # Auto-adapter max_tokens selon taille du prompt
        if max_tokens is None:
            max_tokens = 2048 if (len(prompt) + len(system or "")) > 8000 else 1024

        result = self.generate(prompt, system, temperature, max_tokens, timeout)
        if not result.get("success"):
            return result

        raw    = result["response"].strip()
        parsed = self._extract_json(raw)
        if parsed is None:
            return {"success": False, "error": "JSON parsing failed", "raw_response": raw}

        if parsed.get("sql"):
            parsed["sql"] = _fix_tenant_name(parsed["sql"])

        return {
            "success":      True,
            "parsed":       parsed,
            "raw_response": raw,
            "tokens":       result.get("tokens", 0),
        }

    # ------------------------------------------------------------------
    # JSON extraction (4 stratégies en cascade)
    # ------------------------------------------------------------------
    def _extract_json(self, raw: str):
        # Stratégie 1 & 2 : JSON brut ou avec backticks markdown
        cleaned = raw
        if cleaned.startswith("```"):
            parts   = cleaned.split("```")
            cleaned = parts[1].lstrip("json").strip() if len(parts) > 1 else cleaned

        s = cleaned.find("{")
        e = cleaned.rfind("}")
        if s != -1 and e > s:
            bloc = cleaned[s : e + 1]
            try:
                return json.loads(bloc)
            except json.JSONDecodeError:
                pass
            try:
                return json.loads(self._clean_json_strings(bloc))
            except json.JSONDecodeError:
                pass

        # Stratégie 3 : format texte libre Groq (« Decision: sql\nSQL: SELECT… »)
        result = self._parse_free_text_format(raw)
        if result:
            return result

        # Stratégie 4 : regex champ par champ
        return self._regex_extract(raw)

    def _parse_free_text_format(self, raw: str) -> dict | None:
        if not re.search(r"(?i)^\s*decision\s*:", raw, re.MULTILINE):
            return None
        result: Dict = {}

        m = re.search(r"(?i)^\s*decision\s*:\s*(\w+)", raw, re.MULTILINE)
        if m:
            result["decision"] = m.group(1).lower().strip()

        m = re.search(
            r"(?i)^\s*reasoning\s*:\s*(.+?)(?=\n\s*(?:tables|sql)\s*:|$)",
            raw, re.MULTILINE | re.DOTALL,
        )
        if m:
            result["reasoning"] = m.group(1).strip()

        m = re.search(
            r"(?i)^\s*tables\s*:\s*(.+?)(?=\n\s*sql\s*:|$)",
            raw, re.MULTILINE | re.DOTALL,
        )
        if m:
            tables_raw = m.group(1).strip()
            try:
                tables = json.loads(tables_raw)
                result["tables"] = tables if isinstance(tables, list) else [tables_raw]
            except Exception:
                tokens = re.findall(r"[\w\.]+", tables_raw)
                result["tables"] = [t for t in tokens if "." in t or len(t) > 4]

        m = re.search(r"(?i)^\s*sql\s*:\s*\n?(SELECT\s.+)", raw, re.MULTILINE | re.DOTALL)
        if m:
            sql = m.group(1).strip()
            semi = sql.find(";")
            if semi != -1:
                sql = sql[: semi + 1]
            result["sql"] = _normalize_sql(sql)
        else:
            m = re.search(r"(?i)sql\s*:\s*(SELECT\s.+?;)", raw, re.DOTALL)
            if m:
                result["sql"] = _normalize_sql(m.group(1))

        return result if result.get("decision") and result.get("sql") else None

    def _clean_json_strings(self, raw: str) -> str:
        """Remplace les newlines/tabs bruts dans les strings JSON par des espaces."""
        out, in_string, escape_next = [], False, False
        for c in raw:
            if escape_next:
                out.append(c); escape_next = False
            elif c == "\\" and in_string:
                out.append(c); escape_next = True
            elif c == '"':
                in_string = not in_string; out.append(c)
            elif in_string and c in ("\n", "\r", "\t"):
                out.append(" ")
            else:
                out.append(c)
        return "".join(out)

    def _regex_extract(self, raw: str) -> dict | None:
        result: Dict = {}
        m = re.search(r'"decision"\s*:\s*"(\w+)"', raw)
        if m: result["decision"] = m.group(1)
        m = re.search(r'"reasoning"\s*:\s*"([^"]*)"', raw)
        if m: result["reasoning"] = m.group(1)
        m = re.search(r'"tables"\s*:\s*\[([^\]]*)\]', raw, re.DOTALL)
        if m: result["tables"] = re.findall(r'"([^"]+)"', m.group(1))
        m = re.search(r'"sql"\s*:\s*"(.*?)"\s*[,}]', raw, re.DOTALL)
        if m:
            sql = m.group(1).replace("\\n", " ").replace("\n", " ")
            result["sql"] = _normalize_sql(sql)
        return result if result else None

    def get_stats(self) -> Dict:
        return self.stats.copy()


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

class PromptBuilderV7:
    """
    Construit les prompts système/utilisateur pour la génération SQL
    et la réparation de requêtes échouées.

    Corrections intégrées :
      fix3 : rappel anti-tenant dans le system prompt
      fix4 : hint dynamique top-assets vs top-faults
      fix5 : règle OR avec parenthèses obligatoires
      fix6 : SQL sur une seule ligne dans le JSON
    """

    # ------------------------------------------------------------------
    def build_sql_system_prompt(self) -> str:
        return (
            "Tu es un expert senior SQL MySQL spécialisé en maintenance prédictive industrielle "
            "pour i-sense / i-predict.\n\n"
            "Tu dois générer une unique requête SQL SELECT correcte, sûre et exécutable.\n\n"
            "Règles strictes :\n"
            "- Utilise uniquement les tables et colonnes fournies dans le schéma.\n"
            "- N'invente jamais de table, colonne ou jointure absente du schéma.\n"
            "- ended_at appartient UNIQUEMENT à alarms et à recommendation_assets.\n"
            "- (start_date, end_date) appartient UNIQUEMENT à users et à asset_faults.\n"
            "- RÈGLE CRITIQUE — pannes actives : 'actif/actuellement/en cours' → ajouter af.end_date IS NULL.\n"
            "- RÈGLE CRITIQUE — alarmes actives : 'actif/actuellement/en cours' → ajouter al.ended_at IS NULL.\n"
            "- Génère uniquement une requête SELECT.\n"
            "- Interdiction absolue : INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE.\n"
            "- Utilise deleted_at IS NULL lorsque pertinent.\n"
            "- Jamais de SELECT *.\n"
            "- Si le contexte est insuffisant ou ambigu, réponds decision=\"clarify\".\n"
            "- Termine toujours la requête par ;\n\n"
            "RÈGLE STATUS : Pour chercher un équipement par nom ou ref, utiliser UNIQUEMENT\n"
            "FROM assets a WHERE (a.name = 'X' OR a.ref = 'X') AND a.deleted_at IS NULL.\n"
            "Ne pas joindre recommendation_assets ni asset_classes sauf si explicitement demandé.\n\n"
            "RÈGLE CRITIQUE — TENANT :\n"
            "Le tenant est défini par le préfixe de la base de données fourni dans le schéma.\n"
            "N'ajoute JAMAIS de filtre WHERE sur tenant, tenant_id, site, ou site_id.\n"
            "Ces colonnes N'EXISTENT PAS dans les tables.\n"
            "EXEMPLES INTERDITS : WHERE a.tenant = 'safi' | WHERE a.site = 'jln'\n\n"
            "RÈGLE CRITIQUE — TOP ASSETS vs TOP FAULTS :\n"
            "- 'top N ASSETS/équipements avec le plus de X' → GROUP BY a.id, a.name\n"
            "- 'top N FAULTS/types de défauts les plus fréquents' → GROUP BY f.id, f.name\n\n"
            "RÈGLE CRITIQUE — WHERE avec OR :\n"
            "  CORRECT   : WHERE (a.name = 'X' OR a.ref = 'X') AND a.deleted_at IS NULL\n"
            "  INTERDIT  : WHERE a.name = 'X' OR a.ref = 'X' AND a.deleted_at IS NULL\n\n"
            "RÈGLE CRITIQUE — FORMAT JSON :\n"
            "- Réponds UNIQUEMENT en JSON valide sur une seule ligne.\n"
            "- Le champ \"sql\" doit tenir sur UNE SEULE LIGNE, sans retour à la ligne.\n"
            '- Format obligatoire :\n{"decision":"sql|refuse|clarify","reasoning":"résumé bref",'
            '"tables":["table1"],"sql":"SELECT ...;"}'
        )

    # ------------------------------------------------------------------
    def build_sql_user_prompt(
        self,
        question:                  str,
        tenant_db:                 str,
        intent,
        schema_context:            str,
        join_hints:                str,
        examples_context:          str,
        category_examples_context: str = "",
        negative_examples_context: str = "",
        rag_context:               str = "",
    ) -> str:
        q_lower = question.lower()

        # Hint grouping dynamique (fix4)
        mots_assets = ["asset", "équipement", "equipement", "appareil", "machine"]
        mots_top    = ["top", "plus de", "plus d'", "maximum", "max", "les plus"]
        grouping_hint = ""
        if any(w in q_lower for w in mots_assets) and any(w in q_lower for w in mots_top):
            grouping_hint = (
                "\n⚠ GROUPING : La question porte sur les ÉQUIPEMENTS (assets). "
                "Utilise GROUP BY a.id, a.name — PAS GROUP BY f.id ou f.name."
            )

        tenant_hint = (
            f"\n⚠ TENANT : Le site est défini par le préfixe '{tenant_db}'. "
            "N'ajoute JAMAIS de filtre WHERE tenant= ou tenant_id= (colonne inexistante)."
        )

        return (
            f"Question utilisateur:\n{question}\n\n"
            f"Tenant cible:\n{tenant_db}{tenant_hint}{grouping_hint}\n\n"
            f"Intent détecté:\n"
            f"- name: {getattr(intent, 'name', 'unknown')}\n"
            f"- action: {getattr(intent, 'action', 'unknown')}\n"
            f"- category: {getattr(intent, 'category', 'unknown')}\n"
            f"- entities: {getattr(intent, 'entities', {})}\n"
            f"- modifiers: {getattr(intent, 'modifiers', [])}\n\n"
            f"Schéma pertinent:\n{schema_context or 'Aucun schéma compact disponible'}\n\n"
            f"Hints de jointure:\n{join_hints or 'Aucun hint déterministe'}\n\n"
            f"Exemples proches:\n{examples_context or 'Aucun exemple proche'}\n\n"
            f"Exemples de même catégorie:\n{category_examples_context or 'Aucun exemple de catégorie'}\n\n"
            f"Exemples négatifs:\n{negative_examples_context or 'Aucun'}\n\n"
            f"Contexte RAG:\n{rag_context or 'Aucun contexte RAG pertinent'}\n\n"
            "Instructions supplémentaires importantes:\n"
            "- Les exemples fournis sont des modèles transférables : adapte les JOINs, filtres "
            "et calculs à la nouvelle question.\n"
            "- Si aucun exemple très proche n'existe, appuie-toi sur le schéma + hints + RAG.\n"
            "- N'invente jamais une colonne absente du schéma fourni.\n"
            "- Si les informations sont ambiguës ou insuffisantes : decision=\"clarify\".\n"
            "- Le champ \"sql\" du JSON doit être sur UNE SEULE LIGNE (pas de \\n dans le JSON).\n"
        )

    # ------------------------------------------------------------------
    def build_repair_prompt(
        self,
        question:         str,
        failed_sql:       str,
        error_msg:        str,
        schema_context:   str,
        join_hints:       str,
        examples_context: str,
    ) -> str:
        return (
            f"La requête précédente a échoué.\n\n"
            f"Question:\n{question}\n\n"
            f"SQL précédent:\n{failed_sql}\n\n"
            f"Erreur SQL:\n{error_msg}\n\n"
            f"Schéma pertinent:\n{schema_context}\n\n"
            f"Hints de jointure:\n{join_hints}\n\n"
            f"Exemples similaires:\n{examples_context}\n\n"
            "Règles de correction :\n"
            "- N'invente pas de colonne absente du schéma.\n"
            "- N'ajoute PAS de filtre WHERE tenant= ou tenant_id= (colonne inexistante).\n"
            "- WHERE avec OR → parenthèses obligatoires : (a.name='X' OR a.ref='X').\n"
            "- SQL sur une seule ligne dans le champ \"sql\" du JSON.\n\n"
            "Retourne uniquement un JSON valide sur une ligne :\n"
            '{"decision":"sql|refuse|clarify","reasoning":"résumé bref",'
            '"tables":["table1"],"sql":"SELECT ...;"}'
        )

    # ------------------------------------------------------------------
    def build_rewrite_prompt(
        self,
        question: str,
        tenant:   str,
        columns:  List[str],
        rows:     List[Dict],
    ) -> str:
        return (
            "Tu es un assistant analytique métier.\n"
            "Réponds en français clair, précis et professionnel.\n"
            "N'invente aucun chiffre.\n\n"
            f"Question:\n{question}\n\n"
            f"Tenant:\n{tenant}\n\n"
            f"Colonnes:\n{columns}\n\n"
            f"Résultats:\n{rows}\n\n"
            "Règles:\n"
            "- Si aucun résultat: indique qu'aucune donnée ne correspond.\n"
            "- Si une seule ligne: réponds directement.\n"
            "- Si plusieurs lignes: fais une synthèse concise puis mentionne les principaux éléments.\n"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SQL REPAIR
# ─────────────────────────────────────────────────────────────────────────────

class SQLRepairV8:
    """Tente de réparer une requête SQL échouée via Groq."""

    def __init__(self):
        self._pb  = PromptBuilderV7()
        self._llm = LLMAgentV8()

    def repair(
        self,
        question:         str,
        failed_sql:       str,
        error_msg:        str,
        schema_context:   str,
        join_hints:       str,
        examples_context: str,
        timeout:          int = 60,
    ) -> Dict:
        system = self._pb.build_sql_system_prompt()
        prompt = self._pb.build_repair_prompt(
            question=question,
            failed_sql=failed_sql,
            error_msg=error_msg,
            schema_context=schema_context,
            join_hints=join_hints,
            examples_context=examples_context,
        )
        result = self._llm.generate_json(
            prompt=prompt,
            system=system,
            temperature=0.05,
            max_tokens=1024,
            timeout=timeout,
        )
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "repair failed")}
        return {
            "success":      True,
            "parsed":       result.get("parsed", {}),
            "raw_response": result.get("raw_response", ""),
        }
