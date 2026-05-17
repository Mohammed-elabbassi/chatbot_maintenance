# backend/app/agents/security_executor.py
"""
Fusion de :
  - guardrails_v7.py   → GuardrailsV7
  - sql_validator_v7.py → SQLValidatorV7
  - sql_executor_v7.py  → SQLExecutorV7

Aucune dépendance circulaire. Importer ce seul module à la place des trois anciens.
"""

from __future__ import annotations

import re
from typing import Dict, List

try:
    from app.database.connection import DatabaseConnection
except ImportError:
    from database.connection import DatabaseConnection


# ─────────────────────────────────────────────────────────────────────────────
# GUARDRAILS
# ─────────────────────────────────────────────────────────────────────────────

class GuardrailsV7:
    """Bloque les requêtes NL et SQL dangereuses (écriture, DDL, injections)."""

    DANGER_NL: Dict[str, str] = {
        "supprime":     "Suppression",
        "supprimer":    "Suppression",
        "efface":       "Suppression",
        "effacer":      "Suppression",
        "modifie":      "Modification",
        "modifier":     "Modification",
        "mets à jour":  "Modification",
        "ajoute":       "Insertion",
        "insère":       "Insertion",
        "drop":         "DDL",
        "truncate":     "TRUNCATE",
        "alter":        "DDL",
        "create table": "DDL",
    }

    _DANGER_SQL = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
        re.IGNORECASE,
    )

    def check_nl(self, question: str) -> Dict:
        q = question.lower()
        for kw, reason in self.DANGER_NL.items():
            if kw in q:
                return {
                    "safe": False,
                    "reason": (
                        f"🔒 Requête interdite : {reason}. "
                        "Seules les lectures sont autorisées."
                    ),
                }
        return {"safe": True, "reason": None}

    def check_generated_sql(self, sql: str) -> Dict:
        if not sql or not sql.strip():
            return {"safe": False, "reason": "SQL vide"}
        if self._DANGER_SQL.search(sql):
            return {"safe": False, "reason": "SQL dangereux détecté"}
        if not sql.strip().upper().startswith("SELECT"):
            return {"safe": False, "reason": "Seules les requêtes SELECT sont autorisées"}
        return {"safe": True, "reason": None}

    def check_tables_exist(self, tables: List[str], registry) -> Dict:
        unknown = [t for t in tables if not registry.get_table_schema(t)]
        return {"valid": len(unknown) == 0, "unknown_tables": unknown}


# ─────────────────────────────────────────────────────────────────────────────
# SQL VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class SQLValidatorV7:
    """Validation structurelle d'une requête SQL (SELECT uniquement, pas de SELECT *)."""

    _FORBIDDEN = [
        "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE",
        "ALTER", "CREATE", "REPLACE", "GRANT", "REVOKE",
        "EXEC", "EXECUTE", "CALL", "LOAD_FILE",
    ]

    _DANGEROUS_PATTERNS = [
        r";\s*(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE)",
        r"\bOR\b\s+\d+\s*=\s*\d+",
        r"\bAND\b\s+\d+\s*=\s*\d+",
        r"\bUNION\b.*\bSELECT\b.*\bFROM\b",
        r"\bSLEEP\s*\(",
        r"\bBENCHMARK\s*\(",
        r"\bINTO\s+OUTFILE\b",
        r"\bINTO\s+DUMPFILE\b",
    ]

    def __init__(self):
        self.stats = {"total_validations": 0, "passed": 0, "failed": 0}

    def validate(self, query: str) -> Dict:
        self.stats["total_validations"] += 1
        errors: List[str] = []

        if not query or not query.strip():
            errors.append("Requête vide")
            return self._result(False, errors, "")

        stripped = query.strip()
        upper    = stripped.upper()

        # Multi-statements
        parts = [p.strip() for p in stripped.split(";") if p.strip()]
        if len(parts) > 1:
            errors.append("Multiples requêtes détectées")

        # Must start with SELECT
        if not upper.startswith("SELECT"):
            errors.append("Seules les requêtes SELECT sont autorisées")

        # Forbidden keywords
        for op in self._FORBIDDEN:
            if re.search(rf"\b{op}\b", upper):
                errors.append(f"Mot-clé interdit: {op}")
                break

        # Dangerous patterns
        for pattern in self._DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE | re.DOTALL):
                errors.append("Pattern SQL dangereux détecté")
                break

        # No SELECT *
        if re.search(r"SELECT\s+\*", query, re.IGNORECASE):
            errors.append("SELECT * interdit")

        valid = len(errors) == 0
        self.stats["passed" if valid else "failed"] += 1
        return self._result(valid, errors, stripped)

    def _result(self, valid: bool, errors: List[str], query: str) -> Dict:
        return {
            "valid":            valid,
            "errors":           errors,
            "sanitized_query":  query.rstrip(";").strip(),
        }

    def get_stats(self) -> Dict:
        total = self.stats["total_validations"]
        out   = self.stats.copy()
        out["pass_rate"] = round((out["passed"] / total) * 100, 2) if total else 0
        return out


# ─────────────────────────────────────────────────────────────────────────────
# SQL EXECUTOR
# ─────────────────────────────────────────────────────────────────────────────

class SQLExecutorV7:
    """Exécute une requête SELECT validée sur la base tenant cible."""

    def execute(self, sql: str, db_name: str) -> Dict:
        db = DatabaseConnection()
        try:
            if not db.connect(db_name):
                return {
                    "success":   False,
                    "error":     f"Connexion impossible à {db_name}",
                    "rows":      [],
                    "columns":   [],
                    "row_count": 0,
                }

            rows    = db.execute_query(sql) or []
            columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []

            return {
                "success":   True,
                "rows":      rows,
                "columns":   columns,
                "row_count": len(rows),
                "sql":       sql,
            }

        except Exception as exc:
            return {
                "success":   False,
                "error":     str(exc),
                "rows":      [],
                "columns":   [],
                "row_count": 0,
                "sql":       sql,
            }
        finally:
            db.close()
