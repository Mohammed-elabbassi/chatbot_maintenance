# backend/app/agents/guardrails_v7.py

import re
from typing import Dict, List


class GuardrailsV7:
    DANGER_NL = {
        "supprime": "Suppression",
        "supprimer": "Suppression",
        "efface": "Suppression",
        "effacer": "Suppression",
        "modifie": "Modification",
        "modifier": "Modification",
        "mets à jour": "Modification",
        "ajoute": "Insertion",
        "insère": "Insertion",
        "drop": "DDL",
        "truncate": "TRUNCATE",
        "alter": "DDL",
        "create table": "DDL",
    }

    DANGER_SQL = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
        re.IGNORECASE,
    )

    def check_nl(self, question: str) -> Dict:
        q = question.lower()
        for kw, reason in self.DANGER_NL.items():
            if kw in q:
                return {
                    "safe": False,
                    "reason": f"🔒 Requête interdite : {reason}. Seules les lectures sont autorisées."
                }
        return {"safe": True, "reason": None}

    def check_generated_sql(self, sql: str) -> Dict:
        if not sql or not sql.strip():
            return {"safe": False, "reason": "SQL vide"}
        if self.DANGER_SQL.search(sql):
            return {"safe": False, "reason": "SQL dangereux détecté"}
        if not sql.strip().upper().startswith("SELECT"):
            return {"safe": False, "reason": "Seules les requêtes SELECT sont autorisées"}
        return {"safe": True, "reason": None}

    def check_tables_exist(self, tables: List[str], registry) -> Dict:
        unknown = []
        for t in tables:
            if not registry.get_table_schema(t):
                unknown.append(t)
        return {"valid": len(unknown) == 0, "unknown_tables": unknown}