# test_objectifs_16_30.py
"""
Test des Objectifs 16-30 : Défauts (Faults)
Version Corrigée - Gestion des erreurs améliorée
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from app.database.connection import DatabaseConnection
from app.database.queries_faults import (
    get_query, 
    get_objectif_info, 
    list_all_objectifs,
    OBJECTIFS_METADATA
)

def test_all_objectifs():
    """Tester tous les objectifs 16-30"""
    
    db = DatabaseConnection()
    tenant_db = 'v3_tenant_jln'
    
    print("\n" + "="*80)
    print(" " * 20 + "🧪 TEST DES OBJECTIFS 16-30 : DÉFAUTS")
    print("="*80)
    
    # Trouver un asset avec des défauts
    print("\n📋 Asset de test...")
    db.connect(tenant_db)
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
        asset_name = result[0]['name']
        nb_defauts = result[0]['nb_defauts']
        print(f"   ✅ Asset: {asset_name} (ID: {asset_id}, Défauts: {nb_defauts})")
    else:
        print("   ❌ Aucun asset avec défauts trouvé")
        return
    db.close()
    
    # Tester chaque objectif
    objectifs = list_all_objectifs()
    succes = 0
    echec = 0
    partiel = 0
    
    for objectif_key in objectifs:
        print(f"\n{'─'*80}")
        
        # ✅ CORRECTION: Vérifier que info est un dictionnaire
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
            
            # Préparer les paramètres
            params = (asset_id,) if 'asset_id' in info.get('params', []) else ()
            
            # Exécuter la requête
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