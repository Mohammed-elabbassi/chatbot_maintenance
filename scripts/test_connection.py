# test_connection.py
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le backend au path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from app.database.connection import DatabaseConnection

def test_all_databases():
    """Tester TOUTES les bases de données disponibles"""
    
    db = DatabaseConnection()
    results = {}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ═══════════════════════════════════════════════════════════════
    # LISTE COMPLÈTE DE TOUTES LES BASES
    # ═══════════════════════════════════════════════════════════════
    all_databases = {
        # Bases Globales
        'i_sense_v3_devenv_db': {
            'label': 'Globale (Production)',
            'tables': ['tenants', 'users', 'companies', 'devices', 'predictions', 'pdm_features']
        },
        'i_sense_v3_devenv_db3': {
            'label': 'Globale (Backup)',
            'tables': ['tenants', 'users', 'companies', 'devices', 'predictions']
        },
        'test_company_db': {
            'label': 'Test Company',
            'tables': ['assets', 'asset_faults', 'users']
        },
        
        # Bases Tenant (Clients)
        'v3_tenant_Site_Safi': {
            'label': 'Tenant: Site Safi ⭐',
            'tables': ['faults', 'recommendations_v3', 'interventions', 'daily_asset_status', 'family_fault', 'causes']
        },
        'v3_tenant_jln': {
            'label': 'Tenant: JLN ⭐',
            'tables': ['asset_faults', 'assets', 'alarms', 'asset_components', 'actions_fault']
        },
        'v3_tenant_cmcp_ip': {
            'label': 'Tenant: CMCP IP',
            'tables': ['asset_faults', 'assets', 'alarms']
        },
        'v3_tenant_cobomi': {
            'label': 'Tenant: Cobomi',
            'tables': ['asset_faults', 'assets', 'alarms']
        },
        'v3_tenant_jfc4': {
            'label': 'Tenant: JFC4',
            'tables': ['asset_faults', 'assets', 'alarms']
        },
        'v3_tenant_lafarge_holcim_bouskoura': {
            'label': 'Tenant: Lafarge Holcim',
            'tables': ['asset_faults', 'assets', 'alarms']
        },
        'v3_tenant_nomac': {
            'label': 'Tenant: Nomac',
            'tables': ['asset_faults', 'assets', 'alarms']
        },
        'v3_tenant_ntn': {
            'label': 'Tenant: NTN',
            'tables': ['asset_faults', 'assets', 'alarms']
        },
        'v3_tenant_onee': {
            'label': 'Tenant: ONEE',
            'tables': ['asset_faults', 'assets', 'alarms']
        },
        'v3_tenant_test': {
            'label': 'Tenant: Test',
            'tables': ['asset_faults', 'assets', 'alarms']
        },
    }
    
    # ═══════════════════════════════════════════════════════════════
    # EN-TÊTE DU RAPPORT
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*80)
    print(" " * 20 + "📊 RAPPORT DE CONNEXION AUX BASES DE DONNÉES")
    print("="*80)
    print(f"  🕐 Date: {timestamp}")
    print(f"  📁 Total bases à tester: {len(all_databases)}")
    print("="*80 + "\n")
    
    successful_connections = 0
    failed_connections = 0
    
    # ═══════════════════════════════════════════════════════════════
    # TEST DE CHAQUE BASE
    # ═══════════════════════════════════════════════════════════════
    for db_name, db_info in all_databases.items():
        print("\n" + "─"*80)
        print(f"📊 TEST: {db_name}")
        print(f"   Description: {db_info['label']}")
        print("─"*80)
        
        if db.connect(db_name):
            successful_connections += 1
            print(f"  ✅ Connexion: SUCCÈS")
            
            # Compter les lignes par table
            for table in db_info['tables']:
                try:
                    query = f"SELECT COUNT(*) as total FROM {table}"
                    result = db.execute_query(query)
                    count = result[0]['total'] if result else 0
                    results[f'{db_name}_{table}'] = count
                    
                    # Afficher avec formatage
                    status = "⭐" if count > 1000 else "✅" if count > 0 else "⚠️"
                    print(f"    {status} {table}: {count:,} lignes")
                except Exception as e:
                    print(f"    ❌ {table}: Table n'existe pas ou erreur")
                    results[f'{db_name}_{table}'] = 0
        else:
            failed_connections += 1
            print(f"  ❌ Connexion: ÉCHEC")
            for table in db_info['tables']:
                results[f'{db_name}_{table}'] = -1
        
        db.close()
    
    # ═══════════════════════════════════════════════════════════════
    # RÉSUMÉ GÉNÉRAL
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*80)
    print(" " * 30 + "📋 RÉSUMÉ GÉNÉRAL")
    print("="*80)
    print(f"  ✅ Bases connectées: {successful_connections}/{len(all_databases)}")
    print(f"  ❌ Bases échouées: {failed_connections}/{len(all_databases)}")
    print(f"  📊 Tables vérifiées: {len(results)}")
    
    # Calculer le total des enregistrements
    total_records = sum(v for v in results.values() if v > 0)
    print(f"  📈 Total enregistrements: {total_records:,}")
    
    # Taux de succès
    success_rate = (successful_connections / len(all_databases)) * 100
    print(f"  📊 Taux de succès: {success_rate:.1f}%")
    print("="*80 + "\n")
    
    # ═══════════════════════════════════════════════════════════════
    # TABLEAU RÉCAPITULATIF PAR TYPE
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*80)
    print(" " * 25 + "📊 RÉPARTITION PAR TYPE DE BASE")
    print("="*80)
    
    # Bases globales
    global_bases = [k for k in all_databases.keys() if 'i_sense' in k or 'test_company' in k]
    print(f"\n  🌐 BASES GLOBALES ({len(global_bases)}):")
    for db_name in global_bases:
        status = "✅" if any(v > 0 for k, v in results.items() if db_name in k) else "❌"
        print(f"    {status} {db_name}")
    
    # Bases tenant
    tenant_bases = [k for k in all_databases.keys() if 'v3_tenant' in k and 'test' not in k]
    print(f"\n  🏢 BASES TENANT/CLIENTS ({len(tenant_bases)}):")
    for db_name in tenant_bases:
        status = "✅" if any(v > 0 for k, v in results.items() if db_name in k) else "❌"
        print(f"    {status} {db_name}")
    
    # Bases test
    test_bases = [k for k in all_databases.keys() if 'test' in k]
    print(f"\n  🧪 BASES DE TEST ({len(test_bases)}):")
    for db_name in test_bases:
        status = "✅" if any(v > 0 for k, v in results.items() if db_name in k) else "❌"
        print(f"    {status} {db_name}")
    
    print("\n" + "="*80 + "\n")
    
    # ═══════════════════════════════════════════════════════════════
    # SAUVEGARDER LE RAPPORT DANS UN FICHIER
    # ═══════════════════════════════════════════════════════════════
    report_path = Path(__file__).parent.parent / 'data' / 'connection_report.txt'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"RAPPORT DE CONNEXION - {timestamp}\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total bases: {len(all_databases)}\n")
        f.write(f"Connectées: {successful_connections}\n")
        f.write(f"Échouées: {failed_connections}\n\n")
        
        for db_name, db_info in all_databases.items():
            f.write(f"\n{db_name} ({db_info['label']}):\n")
            f.write("-"*40 + "\n")
            for table in db_info['tables']:
                count = results.get(f'{db_name}_{table}', 0)
                f.write(f"  {table}: {count:,} lignes\n")
    
    print(f"💾 Rapport sauvegardé: {report_path}\n")
    
    return results

if __name__ == "__main__":
    print("🚀 Test de TOUTES les bases de données...\n")
    test_all_databases()
    print("✅ Tests terminés !\n")