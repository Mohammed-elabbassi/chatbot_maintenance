# backend/app/agents/sql_executor_v7.py

from typing import Dict

try:
    from app.database.connection import DatabaseConnection
except ImportError:
    from database.connection import DatabaseConnection


class SQLExecutorV7:
    def __init__(self):
        pass

    def execute(self, sql: str, db_name: str) -> Dict:
        db = DatabaseConnection()
        try:
            if not db.connect(db_name):
                return {
                    "success": False,
                    "error": f"Connexion impossible à {db_name}",
                    "rows": [],
                    "columns": [],
                    "row_count": 0,
                }

            rows = db.execute_query(sql) or []
            columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []

            return {
                "success": True,
                "rows": rows,
                "columns": columns,
                "row_count": len(rows),
                "sql": sql,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rows": [],
                "columns": [],
                "row_count": 0,
                "sql": sql,
            }
        finally:
            db.close()