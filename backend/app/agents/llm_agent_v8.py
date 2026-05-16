# # backend/app/agents/llm_agent_v8.py
# """
# LLM Agent V8 — Groq LLaMA 3.1 8B
# Remplace Ollama (llm_agent_v7.py). Interface identique : generate() / generate_json().
# Nécessite : pip install groq  +  GROQ_API_KEY dans .env
# """

# import json
# import os
# from typing import Dict, Optional

# from groq import Groq


# class LLMAgentV8:
#     DEFAULT_MODEL = "llama-3.1-8b-instant"

#     def __init__(self, model: str = None, api_key: str = None):
#         self.model  = model or self.DEFAULT_MODEL
#         self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
#         self.stats  = {"calls": 0, "success": 0, "failed": 0}

#     def is_available(self) -> bool:
#         key = os.getenv("GROQ_API_KEY", "")
#         return len(key) > 10

#     def generate(
#         self,
#         prompt:      str,
#         system:      Optional[str] = None,
#         temperature: float = 0.05,
#         max_tokens:  int   = 1024,
#         timeout:     int   = 60,
#     ) -> Dict:
#         self.stats["calls"] += 1
#         messages = []
#         if system:
#             messages.append({"role": "system", "content": system})
#         messages.append({"role": "user", "content": prompt})
#         try:
#             resp = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 timeout=timeout,
#             )
#             self.stats["success"] += 1
#             return {
#                 "success":  True,
#                 "response": (resp.choices[0].message.content or "").strip(),
#                 "tokens":   resp.usage.total_tokens if resp.usage else 0,
#             }
#         except Exception as e:
#             self.stats["failed"] += 1
#             return {"success": False, "error": str(e)}

#     def generate_json(
#         self,
#         prompt:      str,
#         system:      Optional[str] = None,
#         temperature: float = 0.05,
#         max_tokens:  int   = 1024,
#         timeout:     int   = 60,
#     ) -> Dict:
#         result = self.generate(prompt, system, temperature, max_tokens, timeout)
#         if not result.get("success"):
#             return result
#         raw    = result["response"].strip()
#         parsed = self._extract_json(raw)
#         if parsed is None:
#             return {"success": False, "error": "JSON parsing failed", "raw_response": raw}
#         return {"success": True, "parsed": parsed, "raw_response": raw}

#     def _extract_json(self, raw: str):
#         # Retire les balises ```json ... ```
#         if raw.startswith("```"):
#             parts = raw.split("```")
#             raw   = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
#         try:
#             return json.loads(raw)
#         except Exception:
#             s, e = raw.find("{"), raw.rfind("}")
#             if s != -1 and e > s:
#                 try:
#                     return json.loads(raw[s:e + 1])
#                 except Exception:
#                     pass
#         return None

#     def get_stats(self) -> Dict:
#         return self.stats.copy()





# -------------------------------------------------2----------------------------------------------

# # backend/app/agents/llm_agent_v8.py
# """
# LLM Agent V8 — Groq LLaMA 3.1 8B
# Remplace Ollama (llm_agent_v7.py). Interface identique : generate() / generate_json().
# Nécessite : pip install groq  +  GROQ_API_KEY dans .env

# CORRECTIONS V8.1 :
# - Fix 1 : _extract_json() robuste — parse SQL multiligne (newlines bruts dans JSON)
# - Fix 2 : max_tokens auto-adaptatif selon taille du prompt (2048 si > 8000 chars)
# - Fix 3 : _manual_extract() fallback si json.loads échoue totalement
# """

# import json
# import os
# import re
# from typing import Dict, Optional

# from groq import Groq


# class LLMAgentV8:
#     DEFAULT_MODEL = "llama-3.1-8b-instant"

#     def __init__(self, model: str = None, api_key: str = None):
#         self.model  = model or self.DEFAULT_MODEL
#         self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
#         self.stats  = {"calls": 0, "success": 0, "failed": 0}

#     def is_available(self) -> bool:
#         key = os.getenv("GROQ_API_KEY", "")
#         return len(key) > 10

#     def generate(
#         self,
#         prompt:      str,
#         system:      Optional[str] = None,
#         temperature: float = 0.05,
#         max_tokens:  int   = 2048,
#         timeout:     int   = 60,
#     ) -> Dict:
#         self.stats["calls"] += 1
#         messages = []
#         if system:
#             messages.append({"role": "system", "content": system})
#         messages.append({"role": "user", "content": prompt})
#         try:
#             resp = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 timeout=timeout,
#             )
#             self.stats["success"] += 1
#             return {
#                 "success":  True,
#                 "response": (resp.choices[0].message.content or "").strip(),
#                 "tokens":   resp.usage.total_tokens if resp.usage else 0,
#             }
#         except Exception as e:
#             self.stats["failed"] += 1
#             return {"success": False, "error": str(e)}

#     def generate_json(
#         self,
#         prompt:      str,
#         system:      Optional[str] = None,
#         temperature: float = 0.05,
#         max_tokens:  int   = None,   # FIX 2 : None = auto-adapté
#         timeout:     int   = 60,
#     ) -> Dict:
#         # FIX 2 : augmenter max_tokens automatiquement si prompt grand
#         if max_tokens is None:
#             total_chars = len(prompt) + len(system or "")
#             max_tokens = 2048 if total_chars > 8000 else 1024

#         result = self.generate(prompt, system, temperature, max_tokens, timeout)
#         if not result.get("success"):
#             return result
#         raw    = result["response"].strip()
#         parsed = self._extract_json(raw)
#         if parsed is None:
#             return {"success": False, "error": "JSON parsing failed", "raw_response": raw}
#         return {
#             "success":      True,
#             "parsed":       parsed,
#             "raw_response": raw,
#             "tokens":       result.get("tokens", 0),
#         }

#     def _extract_json(self, raw: str):
#         """
#         FIX 1 — Parsing robuste avec SQL multiligne.

#         Problème : Groq génère parfois :
#           { "sql": "SELECT a.id
#                     FROM table a
#                     WHERE a.status = 5" }
#         Les newlines bruts dans une string JSON sont invalides → json.loads() échoue.

#         Solution : nettoyer les newlines DANS les strings JSON avant parsing.
#         """
#         # Étape 1 : retirer les balises markdown ```json ... ```
#         if raw.startswith("```"):
#             parts = raw.split("```")
#             raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

#         # Étape 2 : isoler le bloc JSON { ... }
#         s = raw.find("{")
#         e = raw.rfind("}")
#         if s != -1 and e > s:
#             raw = raw[s:e + 1]

#         # Étape 3 : tentative directe
#         try:
#             return json.loads(raw)
#         except json.JSONDecodeError:
#             pass

#         # Étape 4 : nettoyer les newlines bruts dans les strings JSON
#         cleaned = self._clean_json_strings(raw)
#         try:
#             return json.loads(cleaned)
#         except json.JSONDecodeError:
#             pass

#         # Étape 5 : extraction manuelle champ par champ (fallback final)
#         return self._manual_extract(raw)

#     def _clean_json_strings(self, raw: str) -> str:
#         """
#         Remplace les newlines/tabs bruts à l'intérieur des valeurs
#         string JSON par des espaces. Ne touche pas à la structure JSON.
#         """
#         result      = []
#         in_string   = False
#         escape_next = False

#         for c in raw:
#             if escape_next:
#                 result.append(c)
#                 escape_next = False
#             elif c == '\\' and in_string:
#                 result.append(c)
#                 escape_next = True
#             elif c == '"':
#                 in_string = not in_string
#                 result.append(c)
#             elif in_string and c in ('\n', '\r'):
#                 result.append(' ')   # newline brut → espace
#             elif in_string and c == '\t':
#                 result.append(' ')   # tab brut → espace
#             else:
#                 result.append(c)

#         return ''.join(result)

#     def _manual_extract(self, raw: str) -> dict:
#         """
#         Extraction manuelle si json.loads échoue totalement.
#         Retourne un dict partiel plutôt que None.
#         """
#         result = {}

#         # decision
#         m = re.search(r'"decision"\s*:\s*"(\w+)"', raw)
#         if m:
#             result["decision"] = m.group(1)

#         # reasoning
#         m = re.search(r'"reasoning"\s*:\s*"([^"]*)"', raw)
#         if m:
#             result["reasoning"] = m.group(1)

#         # tables
#         m = re.search(r'"tables"\s*:\s*\[([^\]]*)\]', raw, re.DOTALL)
#         if m:
#             result["tables"] = re.findall(r'"([^"]+)"', m.group(1))

#         # sql — prendre tout entre "sql": " et le dernier ;
#         m = re.search(r'"sql"\s*:\s*"(.*?)"\s*[,}]', raw, re.DOTALL)
#         if m:
#             sql = m.group(1).strip()
#             sql = sql.replace('\\n', ' ').replace('\n', ' ').replace('\r', '')
#             sql = re.sub(r'\s+', ' ', sql).strip()
#             result["sql"] = sql

#         return result if result else None

#     def get_stats(self) -> Dict:
#         return self.stats.copy()




# -------------------------------------------------3----------------------------------------------

# backend/app/agents/llm_agent_v8.py
"""
LLM Agent V8 — Groq LLaMA 3.1 8B
CORRECTIONS V8.2 :
- Fix CRITIQUE : _parse_free_text_format() parse "Decision: sql\nSQL: SELECT..."
- Fix 2 : max_tokens auto-adaptatif (2048 si prompt > 8000 chars)
- Fix 3 : _clean_json_strings() pour SQL multiligne dans JSON
- Fix 4 : fix_tenant_name() corrige v3_tenant_Safi → v3_tenant_Site_Safi
"""

import json
import os
import re
from typing import Dict, Optional

from groq import Groq


# Corrections des noms de tenant mal générés par Groq
TENANT_NAME_FIXES = {
    "v3_tenant_Safi":  "v3_tenant_Site_Safi",
    "v3_tenant_safi":  "v3_tenant_Site_Safi",
    "v3_tenant_SAFI":  "v3_tenant_Site_Safi",
    "v3_tenant_Nomac": "v3_tenant_nomac",
    "v3_tenant_NOMAC": "v3_tenant_nomac",
    "v3_tenant_JLN":   "v3_tenant_jln",
    "v3_tenant_NTN":   "v3_tenant_ntn",
}


def fix_tenant_name(sql: str) -> str:
    for wrong, correct in TENANT_NAME_FIXES.items():
        sql = sql.replace(wrong, correct)
    return sql


def normalize_sql(sql: str) -> str:
    sql = sql.strip()
    sql = re.sub(r'\s+', ' ', sql)
    if sql and not sql.endswith(';'):
        sql += ';'
    return fix_tenant_name(sql)


class LLMAgentV8:
    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def __init__(self, model: str = None, api_key: str = None):
        self.model  = model or self.DEFAULT_MODEL
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        self.stats  = {"calls": 0, "success": 0, "failed": 0}

    def is_available(self) -> bool:
        key = os.getenv("GROQ_API_KEY", "")
        return len(key) > 10

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
        except Exception as e:
            self.stats["failed"] += 1
            return {"success": False, "error": str(e)}

    def generate_json(
        self,
        prompt:      str,
        system:      Optional[str] = None,
        temperature: float = 0.05,
        max_tokens:  int   = None,
        timeout:     int   = 60,
    ) -> Dict:
        # Auto-adapter max_tokens selon taille du prompt
        if max_tokens is None:
            total_chars = len(prompt) + len(system or "")
            max_tokens = 2048 if total_chars > 8000 else 1024

        result = self.generate(prompt, system, temperature, max_tokens, timeout)
        if not result.get("success"):
            return result

        raw    = result["response"].strip()
        parsed = self._extract_json(raw)

        if parsed is None:
            return {"success": False, "error": "JSON parsing failed", "raw_response": raw}

        # Corriger le nom du tenant dans le SQL
        if parsed.get("sql"):
            parsed["sql"] = fix_tenant_name(parsed["sql"])

        return {
            "success":      True,
            "parsed":       parsed,
            "raw_response": raw,
            "tokens":       result.get("tokens", 0),
        }

    def _extract_json(self, raw: str):
        """
        4 stratégies en cascade :
        1. JSON brut ou avec balises markdown
        2. JSON avec newlines nettoyés dans les strings
        3. Format texte libre "Decision: sql / SQL: SELECT..."  ← CAS PRINCIPAL GROQ
        4. Regex champ par champ (fallback final)
        """
        # ── Stratégie 1 & 2 : tentative JSON ───────────────────────
        cleaned = raw
        if cleaned.startswith("```"):
            parts   = cleaned.split("```")
            cleaned = parts[1].lstrip("json").strip() if len(parts) > 1 else cleaned

        s = cleaned.find("{")
        e = cleaned.rfind("}")
        if s != -1 and e > s:
            bloc = cleaned[s:e + 1]
            try:
                return json.loads(bloc)
            except json.JSONDecodeError:
                pass
            try:
                return json.loads(self._clean_json_strings(bloc))
            except json.JSONDecodeError:
                pass

        # ── Stratégie 3 : format texte libre Groq ───────────────────
        result = self._parse_free_text_format(raw)
        if result:
            return result

        # ── Stratégie 4 : regex champ par champ ─────────────────────
        return self._regex_extract(raw)

    def _parse_free_text_format(self, raw: str) -> dict:
        """
        Parse le format que Groq génère systématiquement :

          Decision: sql
          Reasoning: La question demande...
          Tables: ["v3_tenant_jln.assets"]
          SQL: SELECT a.id, a.name
               FROM v3_tenant_jln.assets a
               WHERE a.status = 5;

        Ce format apparaît quand Groq ignore la règle JSON du system prompt.
        """
        # Vérifier si c'est ce format (présence de "Decision:")
        if not re.search(r'(?i)^\s*decision\s*:', raw, re.MULTILINE):
            return None

        result = {}

        # decision
        m = re.search(r'(?i)^\s*decision\s*:\s*(\w+)', raw, re.MULTILINE)
        if m:
            result["decision"] = m.group(1).lower().strip()

        # reasoning
        m = re.search(
            r'(?i)^\s*reasoning\s*:\s*(.+?)(?=\n\s*(?:tables|sql)\s*:|$)',
            raw, re.MULTILINE | re.DOTALL
        )
        if m:
            result["reasoning"] = m.group(1).strip()

        # tables
        m = re.search(
            r'(?i)^\s*tables\s*:\s*(.+?)(?=\n\s*sql\s*:|$)',
            raw, re.MULTILINE | re.DOTALL
        )
        if m:
            tables_raw = m.group(1).strip()
            try:
                tables = json.loads(tables_raw)
                result["tables"] = tables if isinstance(tables, list) else [tables_raw]
            except Exception:
                # Extraire noms de tables (contenant un point ou >3 chars)
                tokens = re.findall(r'[\w\.]+', tables_raw)
                result["tables"] = [t for t in tokens if '.' in t or len(t) > 4]

        # SQL — tout ce qui suit "SQL:" jusqu'à la fin (multiligne supporté)
        m = re.search(
            r'(?i)^\s*sql\s*:\s*\n?(SELECT\s.+)',
            raw, re.MULTILINE | re.DOTALL
        )
        if m:
            sql = m.group(1).strip()
            # Couper au premier ";" (fin de requête)
            semi = sql.find(';')
            if semi != -1:
                sql = sql[:semi + 1]
            result["sql"] = normalize_sql(sql)
        else:
            # SQL sur une ligne sans retour à la ligne
            m = re.search(r'(?i)sql\s*:\s*(SELECT\s.+?;)', raw, re.DOTALL)
            if m:
                result["sql"] = normalize_sql(m.group(1))

        return result if result.get("decision") and result.get("sql") else None

    def _clean_json_strings(self, raw: str) -> str:
        """Remplace les newlines bruts dans les strings JSON par des espaces."""
        result, in_string, escape_next = [], False, False
        for c in raw:
            if escape_next:
                result.append(c); escape_next = False
            elif c == '\\' and in_string:
                result.append(c); escape_next = True
            elif c == '"':
                in_string = not in_string; result.append(c)
            elif in_string and c in ('\n', '\r', '\t'):
                result.append(' ')
            else:
                result.append(c)
        return ''.join(result)

    def _regex_extract(self, raw: str) -> dict:
        """Fallback final : extraction regex champ par champ."""
        result = {}

        m = re.search(r'"decision"\s*:\s*"(\w+)"', raw)
        if m: result["decision"] = m.group(1)

        m = re.search(r'"reasoning"\s*:\s*"([^"]*)"', raw)
        if m: result["reasoning"] = m.group(1)

        m = re.search(r'"tables"\s*:\s*\[([^\]]*)\]', raw, re.DOTALL)
        if m: result["tables"] = re.findall(r'"([^"]+)"', m.group(1))

        m = re.search(r'"sql"\s*:\s*"(.*?)"\s*[,}]', raw, re.DOTALL)
        if m:
            sql = m.group(1).replace('\\n', ' ').replace('\n', ' ')
            result["sql"] = normalize_sql(sql)

        return result if result else None

    def get_stats(self) -> Dict:
        return self.stats.copy()