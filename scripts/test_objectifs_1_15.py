# test_objectifs_1_15.py
"""
Test des Objectifs 1-15 : Équipements (Assets)
Version Corrigée - Détection réelle des erreurs
Basé sur la structure réelle des bases de données
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from app.database.connection import DatabaseConnection
from app.database.queries_assets import (
    get_query, 
    get_objectif_info, 
    list_all_objectifs,
    OBJECTIFS_METADATA
)

def test_all_objectifs():
    """Tester tous les objectifs 1-15"""
    
    db = DatabaseConnection()
    tenant_db = 'v3_tenant_jln'
    
    print("\n" + "="*80)
    print(" " * 20 + "🧪 TEST DES OBJECTIFS 1-15 : ÉQUIPEMENTS")
    print("="*80)
    
    # Trouver un asset de test
    print("\n📋 Asset de test...")
    db.connect(tenant_db)
    query = "SELECT id, name FROM assets WHERE deleted_at IS NULL LIMIT 1"
    result = db.execute_query(query)
    if result:
        asset_id = result[0]['id']
        asset_name = result[0]['name']
        print(f"   ✅ Asset: {asset_name} (ID: {asset_id})")
    else:
        print("   ❌ Aucun asset trouvé")
        return
    db.close()
    
    # Tester chaque objectif
    objectifs = list_all_objectifs()
    succes = 0
    echec = 0
    partiel = 0
    
    for objectif_key in objectifs:
        print(f"\n{'─'*80}")
        info = get_objectif_info(objectif_key)
        print(f"📊 {info['titre']}")
        print(f"   Description: {info['description']}")
        print(f"   Priorité: {info['priorite']}")
        print(f"   Statut: {info.get('statut', 'Inconnu')}")
        print(f"   Question: '{info['exemple_question']}'")
        
        try:
            db.connect(tenant_db)
            
            # Préparer les paramètres
            params = (20,) if 'limit' in info.get('params', []) else ()
            
            # Exécuter la requête
            query = get_query(objectif_key, tenant_db, params if params else None)
            results = db.execute_query(query)
            
            if results:
                print(f"   ✅ SUCCÈS: {len(results)} lignes retournées")
                if len(results) > 0:
                    print(f"   📊 Exemple: {results[0]}")
                
                # Vérifier si c'est un statut partiel
                if info.get('statut') == '✅ Validé':
                    succes += 1
                elif info.get('statut') == '⚠️ Partiel':
                    partiel += 1
                else:
                    succes += 1
            else:
                # 0 lignes mais pas d'erreur = succès (données inexistantes)
                if info.get('statut') == '❌ Non disponible':
                    print(f"   ⚠️ Non disponible dans cette base")
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
    
    # Afficher les objectifs validés
    print("🎯 Objectifs validés (✅) :")
    for key, info in OBJECTIFS_METADATA.items():
        if info.get('statut') == '✅ Validé':
            print(f"   - {info['titre']}")
    
    print("\n⚠️ Objectifs partiels (⚠️) :")
    for key, info in OBJECTIFS_METADATA.items():
        if info.get('statut') == '⚠️ Partiel':
            print(f"   - {info['titre']}")
    
    print("\n❌ Objectifs non disponibles (❌) :")
    for key, info in OBJECTIFS_METADATA.items():
        if info.get('statut') == '❌ Non disponible':
            print(f"   - {info['titre']}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_all_objectifs()