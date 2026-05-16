# backend/app/agents/schema_registry_v7.py

from typing import Dict, List

try:
    from app.database.schema_global import ALL_TABLES as GLOBAL_TABLES
    from app.database.schema_tenants import ALL_TABLES as TENANT_TABLES
    from app.database.standards_v3 import (
        CRITICAL_COLUMNS,
        JOINS,
        TENANT_ALIASES,
        GLOBAL_DATABASE,
    )
except ImportError:
    from database.schema_global import ALL_TABLES as GLOBAL_TABLES
    from database.schema_tenants import ALL_TABLES as TENANT_TABLES
    from database.standards_v3 import (
        CRITICAL_COLUMNS,
        JOINS,
        TENANT_ALIASES,
        GLOBAL_DATABASE,
    )


class SchemaRegistryV7:
    def __init__(self):
        self.global_tables = GLOBAL_TABLES
        self.tenant_tables = TENANT_TABLES
        self.critical_columns = CRITICAL_COLUMNS
        self.joins = JOINS
        self.tenant_aliases = TENANT_ALIASES
        self.global_db = GLOBAL_DATABASE

    def get_tenant_db(self, tenant: str) -> str:
        return self.tenant_aliases.get(tenant.lower(), "v3_tenant_jln")

    def get_table_schema(self, table_name: str) -> Dict:
        if table_name in self.global_tables:
            return self.global_tables[table_name]
        if table_name in self.tenant_tables:
            return self.tenant_tables[table_name]
        return {}

    def is_global_table(self, table_name: str) -> bool:
        return table_name in self.global_tables

    def get_relevant_tables_from_intent(self, intent) -> List[str]:
        category = getattr(intent, "category", "unknown")
        entities = getattr(intent, "entities", {}) or {}
        tables = set()

        if category == "asset":
            tables.update(["assets", "asset_classes", "families"])
        elif category == "fault":
            tables.update(["assets", "asset_faults", "faults"])
        elif category == "alarm":
            tables.update(["assets", "alarms"])
        elif category == "measurement":
            tables.update(["assets", "measurements", "feature_measurement", "feature_group"])
        elif category == "recommendation":
            tables.update(["assets", "recommendations_v3", "recommendation_assets", "recommendation_faults"])
        elif category == "intervention":
            tables.update(["assets", "interventions"])
        elif category == "user":
            tables.update(["users", "user_company", "companies"])
        elif category == "company":
            tables.update(["companies", "abonnements", "devices", "user_company"])
        else:
            tables.update(["assets"])

        if entities.get("feature"):
            tables.update(["feature_measurement", "feature_group", "features"])
        if entities.get("fault_type"):
            tables.update(["faults", "asset_faults"])

        return list(tables)

    def get_compact_schema_for_tables(self, tables: List[str], tenant_db: str) -> str:
        sections = []
        for table in tables:
            schema = self.get_table_schema(table)
            if not schema:
                continue

            columns = schema.get("columns", {})
            critical = self.critical_columns.get(table, [])
            db_prefix = self.global_db if self.is_global_table(table) else tenant_db

            ordered_cols = []
            for c in critical:
                if c in columns:
                    ordered_cols.append(f"{c} ({columns[c].get('type', 'UNKNOWN')})")
            for c, meta in columns.items():
                if c not in critical:
                    ordered_cols.append(f"{c} ({meta.get('type', 'UNKNOWN')})")

            parts = [
                f"TABLE {db_prefix}.{table}",
                "COLUMNS: " + ", ".join(ordered_cols[:30]),
            ]

            rels = schema.get("relationships", [])[:5]
            if rels:
                rel_text = []
                for rel in rels:
                    rel_text.append(f"{rel.get('table', '')} ON {rel.get('on', '')}")
                parts.append("RELATIONSHIPS: " + " | ".join(rel_text))

            sections.append("\n".join(parts))

        return "\n\n".join(sections)

    def get_join_hints(self, tables: List[str], tenant_db: str) -> str:
        hints = []
        for _, join_sql in self.joins.items():
            for t in tables:
                if t in join_sql:
                    hints.append(join_sql.replace("{tenant_db}", tenant_db))
                    break
        return "\n".join(hints[:12])