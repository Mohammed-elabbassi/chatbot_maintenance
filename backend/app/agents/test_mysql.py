# test_mysql.py
import sys
sys.path.insert(0, "chatbot_maintenance/backend")
from app.database.connection import DatabaseConnection

db = DatabaseConnection()
ok = db.connect("v3_tenant_jln")
if ok:
    rows = db.execute_query("SELECT COUNT(*) as total FROM assets LIMIT 1")
    print("MySQL OK — assets:", rows)
    db.close()
else:
    print("ERREUR connexion MySQL")