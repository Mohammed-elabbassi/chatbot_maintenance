# backend/app/agents/sql_validator_v7.py

import re
from typing import Dict, List


class SQLValidatorV7:
    FORBIDDEN_OPERATIONS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE",
        "ALTER", "CREATE", "REPLACE", "GRANT", "REVOKE",
        "EXEC", "EXECUTE", "CALL", "LOAD_FILE"
    ]

    DANGEROUS_PATTERNS = [
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
        self.stats = {
            "total_validations": 0,
            "passed": 0,
            "failed": 0,
        }

    def validate(self, query: str) -> Dict:
        self.stats["total_validations"] += 1
        errors = []

        if not query or not query.strip():
            errors.append("Requête vide")
            return self._result(False, errors, "")

        query_stripped = query.strip()
        query_upper = query_stripped.upper()

        if ";" in query_stripped:
            parts = [p.strip() for p in query_stripped.split(";") if p.strip()]
            if len(parts) > 1:
                errors.append("Multiples requêtes détectées")

        if not query_upper.startswith("SELECT"):
            errors.append("Seules les requêtes SELECT sont autorisées")

        for op in self.FORBIDDEN_OPERATIONS:
            if re.search(rf"\b{op}\b", query_upper):
                errors.append(f"Mot-clé interdit: {op}")
                break

        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE | re.DOTALL):
                errors.append("Pattern SQL dangereux détecté")
                break

        if re.search(r"SELECT\s+\*", query, re.IGNORECASE):
            errors.append("SELECT * interdit")

        valid = len(errors) == 0
        if valid:
            self.stats["passed"] += 1
        else:
            self.stats["failed"] += 1

        return self._result(valid, errors, query_stripped)

    def _result(self, valid: bool, errors: List[str], query: str) -> Dict:
        return {
            "valid": valid,
            "errors": errors,
            "sanitized_query": query.rstrip(";").strip(),
        }

    def get_stats(self) -> Dict:
        total = self.stats["total_validations"]
        out = self.stats.copy()
        out["pass_rate"] = round((out["passed"] / total) * 100, 2) if total else 0
        return out