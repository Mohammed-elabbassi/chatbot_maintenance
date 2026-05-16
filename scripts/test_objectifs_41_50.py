# test_objectifs_41_50.py
"""
Test des Objectifs 41-50 : Recommandations
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from app.database.connection import DatabaseConnection
from app.database.queries_recommendations import (
    get_query, 
    get_objectif_info, 
    list_all_objectifs,
    OBJECTIFS_METADATA
)

def test_all_objectifs():
    """Tester tous les objectifs 41-50"""
    
    db = DatabaseConnection()
    tenant_db = 'v3_tenant_Site_Safi'  # Toutes les requêtes sont sur Safi
    
    print("\n" + "="*80)
    print(" " * 20 + "🧪 TEST DES OBJECTIFS 41-50 : RECOMMANDATIONS")
    print("="*80)
    
    # Vérifier le nombre total de recommandations
    print("\n📋 Statistiques recommandations...")
    db.connect(tenant_db)
    query = "SELECT COUNT(*) as total FROM recommendations_v3 WHERE deleted_at IS NULL"
    result = db.execute_query(query)
    if result:
        total_reco = result[0]['total']
        print(f"   ✅ Total recommandations: {total_reco:,}")
    db.close()
    
    # Trouver un fault_id et asset_id de test
    print("\n📋 IDs de test...")
    db.connect(tenant_db)
    query = """
        SELECT f.id as fault_id, a.id as asset_id 
        FROM v3_tenant_Site_Safi.faults f
        CROSS JOIN v3_tenant_Site_Safi.assets a
        LIMIT 1
    """
    result = db.execute_query(query)
    if result:
        fault_id = result[0]['fault_id']
        asset_id = result[0]['asset_id']
        print(f"   ✅ fault_id: {fault_id}, asset_id: {asset_id}")
    else:
        fault_id = 1
        asset_id = 1
    db.close()
    
    # Tester chaque objectif
    objectifs = list_all_objectifs()
    succes = 0
    echec = 0
    partiel = 0
    
    for objectif_key in objectifs:
        print(f"\n{'─'*80}")
        
        info = get_objectif_info(objectif_key)
        
        if not isinstance(info, dict):
            print(f"📊 {objectif_key}")
            print(f"   ⚠️ Métadonnées non disponibles")
            info = {
                'titre': objectif_key,
                'description': 'Non disponible',
                'priorite': '⭐',
                'statut': '⚠️ À vérifier',
                'exemple_question': 'N/A'
            }
        
        print(f"📊 {info.get('titre', objectif_key)}")
        print(f"   Description: {info.get('description', 'N/A')}")
        print(f"   Priorité: {info.get('priorite', '⭐')}")
        print(f"   Statut: {info.get('statut', 'Inconnu')}")
        print(f"   Question: '{info.get('exemple_question', 'N/A')}'")
        
        try:
            db.connect(tenant_db)
            
            # Préparer les paramètres selon l'objectif
            if 'fault_id' in info.get('params', []):
                params = (fault_id, 20)
            elif 'asset_id' in info.get('params', []):
                params = (asset_id, 20)
            elif 'limit' in info.get('params', []):
                params = (20,)
            else:
                params = ()
            
            query = get_query(objectif_key, tenant_db, params if params else None)
            results = db.execute_query(query)
            
            if results:
                print(f"   ✅ SUCCÈS: {len(results)} lignes retournées")
                if len(results) > 0:
                    print(f"   📊 Exemple: {results[0]}")
                
                if info.get('statut') == '✅ Validé':
                    succes += 1
                elif info.get('statut') == '⚠️ À vérifier':
                    partiel += 1
                else:
                    succes += 1
            else:
                if info.get('statut') == '⚠️ À vérifier':
                    print(f"   ⚠️ 0 ligne retournée (données inexistantes)")
                    partiel += 1
                else:
                    print(f"   ⚠️ 0 ligne retournée (données inexistantes)")
                    succes += 1
            
            db.close()
            
        except Exception as e:
            print(f"   ❌ ÉCHEC: {e}")
            echec += 1
            db.close()
    
    # Résumé
    print("\n" + "="*80)
    print(" " * 30 + "📋 RÉSUMÉ")
    print("="*80)
    print(f"  ✅ Succès: {succes}/{len(objectifs)}")
    print(f"  ⚠️ Partiel: {partiel}/{len(objectifs)}")
    print(f"  ❌ Échecs: {echec}/{len(objectifs)}")
    print(f"  📊 Taux de réussite: {((succes + partiel)/len(objectifs))*100:.1f}%")
    print("="*80 + "\n")
    
    # Afficher par statut
    print("🎯 Objectifs validés (✅) :")
    for key, info in OBJECTIFS_METADATA.items():
        if isinstance(info, dict) and info.get('statut') == '✅ Validé':
            print(f"   - {info.get('titre', key)}")
    
    print("\n⚠️ Objectifs à vérifier (⚠️) :")
    for key, info in OBJECTIFS_METADATA.items():
        if isinstance(info, dict) and info.get('statut') == '⚠️ À vérifier':
            print(f"   - {info.get('titre', key)}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_all_objectifs()