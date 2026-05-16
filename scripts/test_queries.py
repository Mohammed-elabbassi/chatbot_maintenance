# test_queries.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from app.database.connection import DatabaseConnection
from app.database.queries import QUERIES, DATABASES

def test_all_queries():
    """Tester toutes les requêtes SQL"""
    
    db = DatabaseConnection()
    
    print("\n" + "="*60)
    print("🧪 TEST DES REQUÊTES SQL")
    print("="*60)
    
    # Trouver un asset avec des défauts
    print("\n1️⃣ Trouver un asset avec des défauts...")
    db.connect(DATABASES['tenant'])
    query = """
        SELECT a.id, a.name, COUNT(af.id) as nb_defauts
        FROM v3_tenant_jln.assets a
        LEFT JOIN v3_tenant_jln.asset_faults af ON a.id = af.asset_id
        GROUP BY a.id, a.name
        HAVING nb_defauts > 0
        ORDER BY nb_defauts DESC
        LIMIT 1
    """
    result = db.execute_query(query)
    if result:
        asset_id = result[0]['id']
        asset_name = result[0]['name']  # ← CORRECTION: 'name' au lieu de 'equipment_name'
        print(f"   ✅ Asset trouvé: {asset_name} (ID: {asset_id})")
    else:
        print("   ❌ Aucun asset avec défauts trouvé")
        return
    
    db.close()
    
    # Tester chaque requête
    for query_name, query_template in QUERIES.items():
        print(f"\n{query_name.upper()}...")
        
        try:
            db.connect(DATABASES['tenant'])
            
            # Remplacer les paramètres
            if '%s' in query_template:
                query = query_template % asset_id
            else:
                query = query_template
            
            results = db.execute_query(query)
            
            if results:
                print(f"   ✅ {len(results)} lignes retournées")
                # Afficher un exemple
                if len(results) > 0:
                    print(f"   📊 Exemple: {results[0]}")
            else:
                print(f"   ⚠️ 0 ligne retournée")
            
            db.close()
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            db.close()
    
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_all_queries()