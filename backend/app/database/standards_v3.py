# standards_v3.py
"""
Standards SQL V3.1 pour TOUT le dataset
Source de vérité unique pour le fine-tuning
Chatbot Maintenance Prédictive - i-sense / i-predict

V3.1 : SYSTEM_PROMPT compressé (~400 tokens au lieu de ~900)
        + 45 exemples négatifs
        Tout le reste est IDENTIQUE à V3
"""

import re
from typing import List, Set, Dict, Optional, Tuple

# ═══════════════════════════════════════════════════════════════
# BASES DE DONNÉES (IDENTIQUE)
# ═══════════════════════════════════════════════════════════════

GLOBAL_DATABASE = "i_sense_v3_devenv_db"

ALL_TENANT_DATABASES = [
    "v3_tenant_jln",
    "v3_tenant_Site_Safi",
    "v3_tenant_cmcp_ip",
    "v3_tenant_cobomi",
    "v3_tenant_jfc4",
    "v3_tenant_nomac",
    "v3_tenant_ntn",
    "v3_tenant_onee",
    "v3_tenant_lafarge_holcim_bouskoura",
]

TENANT_ALIASES = {
    "jln": "v3_tenant_jln",
    "jfc4": "v3_tenant_jfc4",
    "safi": "v3_tenant_Site_Safi",
    "ntn": "v3_tenant_ntn",
    "cmcp": "v3_tenant_cmcp_ip",
    "cobomi": "v3_tenant_cobomi",
    "nomac": "v3_tenant_nomac",
    "onee": "v3_tenant_onee",
    "lafarge_holcim_bouskoura": "v3_tenant_lafarge_holcim_bouskoura",
    "global": "i_sense_v3_devenv_db",
}

TENANT_DISPLAY_NAMES = {
    "jln": "Jorf Lasfar",
    "safi": "Safi",
    "cmcp": "CMCP Casablanca",
    "cobomi": "Cobomi",
    "jfc4": "JFC4",
    "nomac": "NOMAC",
    "ntn": "NTN",
    "onee": "ONEE",
    "bouskoura": "Lafarge Holcim Bouskoura",
}

SAMPLE_TENANTS = [
    ("jln", "Jorf Lasfar", "v3_tenant_jln"),
    ("safi", "Safi", "v3_tenant_Site_Safi"),
    ("ntn", "NTN", "v3_tenant_ntn"),
    ("cmcp", "CMCP", "v3_tenant_cmcp_ip"),
    ("cobomi", "COBOMI", "v3_tenant_cobomi"),
    ("nomac", "NOMAC", "v3_tenant_nomac"),
    ("onee", "ONEE", "v3_tenant_onee"),
    ("jfc4", "JFC4", "v3_tenant_jfc4"),
    ("bouskoura", "Lafarge Holcim Bouskoura", "v3_tenant_lafarge_holcim_bouskoura"),
]

# ═══════════════════════════════════════════════════════════════
# SYNONYMES (IDENTIQUE)
# ═══════════════════════════════════════════════════════════════

SYNONYMS = {
    "équipement": ["machine", "asset", "équipement", "matériel"],
    "panne": ["défaut", "problème", "dysfonctionnement", "incident", "failure"],
    "alarme": ["alerte", "alarme", "notification", "warning"],
    "intervention": ["maintenance", "réparation", "intervention", "action corrective"],
    "recommandation": ["suggestion", "préconisation", "recommandation", "advice"],
    "mesure": ["measurement", "relevé"],
    "utilisateur": ["user", "personne", "expert", "technicien"],
    "entreprise": ["company", "société", "tenant"],
}

# ═══════════════════════════════════════════════════════════════
# TEMPLATES DE REFORMULATION (IDENTIQUE)
# ═══════════════════════════════════════════════════════════════

REFORMULATION_TEMPLATES = [
    ("Quels sont", "Donne-moi"),
    ("Quels sont", "Liste"),
    ("Quel est", "Montre-moi"),
    ("Quel est", "Indique"),
    ("Combien", "Quel est le nombre de"),
    ("Combien", "Donne le total de"),
    ("Quels sont", "Peux-tu me donner"),
    ("Quel est", "Peux-tu indiquer"),
    ("Affiche", "Montre"),
    ("Donne", "Fournis"),
]

# ═══════════════════════════════════════════════════════════════
# STATUTS STANDARD (IDENTIQUE)
# ═══════════════════════════════════════════════════════════════

ASSET_STATUS = {
    -1: "Unassigned",
    0: "Shut down",
    1: "Normal",
    2: "MID",
    3: "Moderate",
    4: "Undefined",
    5: "Critical",
}

ASSET_STATUS_CASE = """
    CASE
        WHEN a.status = -1 THEN 'Unassigned'
        WHEN a.status = 0 THEN 'Shut down'
        WHEN a.status = 1 THEN 'Normal'
        WHEN a.status = 2 THEN 'MID'
        WHEN a.status = 3 THEN 'Moderate'
        WHEN a.status = 4 THEN 'Undefined'
        WHEN a.status = 5 THEN 'Critical'
        ELSE 'Unknown'
    END AS status_label
"""

# ═══════════════════════════════════════════════════════════════
# FILTRES STANDARD (IDENTIQUE)
# ═══════════════════════════════════════════════════════════════

FILTERS = {
    "soft_delete": "deleted_at IS NULL",
    "pannes_actives": "af.end_date IS NULL AND af.deleted_at IS NULL",
    "alarmes_actives": "al.ended_at IS NULL AND al.deleted_at IS NULL",
    "alarmes_critiques": "al.ended_at IS NULL AND al.deleted_at IS NULL AND al.status = 5",
    "assets_actifs": "a.deleted_at IS NULL AND a.status != 0 AND a.status != -1",
    "users_actifs": "u.deleted_at IS NULL AND u.active = 1",
    "interventions_actives": "i.deleted_at IS NULL",
    "recommandations_actives": "r.deleted_at IS NULL",
}

# ═══════════════════════════════════════════════════════════════
# JOINTURES STANDARD (IDENTIQUE)
# ═══════════════════════════════════════════════════════════════

JOINS = {
    "asset_faults": "INNER JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id",
    "faults": "INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id",
    "alarms": "INNER JOIN {tenant_db}.alarms al ON a.id = al.asset_id",
    "measurements": "INNER JOIN {tenant_db}.measurements m ON a.id = m.asset_id",
    "interventions": "INNER JOIN {tenant_db}.interventions i ON a.id = i.asset_id",
    "recommendations": "INNER JOIN {tenant_db}.recommendation_assets ra ON a.id = ra.asset_id",
    "recommendations_v3": "INNER JOIN {tenant_db}.recommendations_v3 r ON ra.recommendation_id = r.id",
    "families": "LEFT JOIN {tenant_db}.families fam ON a.family_id = fam.id",
    "asset_classes": "LEFT JOIN {tenant_db}.asset_classes ac ON a.class_id = ac.id",
    "devices_global": "LEFT JOIN i_sense_v3_devenv_db.devices d ON al.device_id = d.id",
    "users_global": "INNER JOIN i_sense_v3_devenv_db.users u ON 1=1",
    "companies_global": "INNER JOIN i_sense_v3_devenv_db.companies c ON 1=1",
    "user_company": "INNER JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id",
    "family_fault": "INNER JOIN {tenant_db}.family_fault ff ON f.id = ff.fault_id",
    "operations": "INNER JOIN {tenant_db}.operations o ON 1=1",
    "feature_measurement": "INNER JOIN {tenant_db}.feature_measurement fm ON fm.asset_parent_id = a.id",
    "feature_group": "INNER JOIN {tenant_db}.feature_group fg ON fm.feature_id = fg.feature_id AND fm.group_id = fg.group_id",
    "pdm_detection": "INNER JOIN {tenant_db}.pdm_detection pd ON a.id = pd.parent_id",
    "groups": "LEFT JOIN {tenant_db}.groups g ON a.group_id = g.id",
    "point_position": "LEFT JOIN {tenant_db}.point_position pp ON a.id = pp.asset_id",
    "fault_operation": "INNER JOIN {tenant_db}.fault_operation fo ON f.id = fo.fault_id",
}

# ═══════════════════════════════════════════════════════════════
# ★★★ SYSTEM PROMPT V3.1 - COMPRESSÉ ★★★
# ★★★ SEULE CHOSE QUI CHANGE PAR RAPPORT À V3 ★★★
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Expert SQL MySQL maintenance industrielle OCP (i-sense/i-predict). Génère 1 requête SELECT uniquement, terminée par ;

TENANTS:{tenant_db} = v3_tenant_jln|v3_tenant_Site_Safi|v3_tenant_cmcp_ip|v3_tenant_cobomi|v3_tenant_jfc4|v3_tenant_nomac|v3_tenant_ntn|v3_tenant_onee|v3_tenant_lafarge_holcim_bouskoura
GLOBAL:i_sense_v3_devenv_db

TABLES TENANT:
assets(id,name,ref,status,family_id,class_id,parent_id,rpm,brand,group_id,diagram_id,is_manual,created_at,deleted_at)
asset_faults(id,asset_id,sub_asset_id,fault_id,start_date,end_date,status,percentage,duration,point_id,treated_by,deleted_at)
alarms(id,asset_id,device_id,status,created_at,ended_at,duration,point_id,asset_parent_id,deleted_at)
faults(id,name,description,locked,is_asset,require_rpm,deleted_at)
families(id,name,for_asset,family_type,deleted_at)
measurements(id,asset_id,status,is_online,device_id,point_id,created_at,deleted_at)
measurement_points(id,name,asset_id,deleted_at)
interventions(id,asset_id,description,date_intervention,status,expert_id,validator_id,operation_id,deleted_at)
recommendations_v3(id,severity,fault_date,asset_id,asset_parent_id,created_by,validated_by,measure_id,point_id,diagnostic_details,recommendation_details,deleted_at)
recommendation_assets(id,fault,cause,notes,started_at,ended_at,asset_id,point_id,expert,status,deleted_at)
recommendation_faults(id,recommendation_id,fault_id,probability,deleted_at)
recommendation_operations(id,recommendation_id,operation_id)
feature_measurement(id,asset_parent_id,feature_id,group_id,value,point_id,measurement_id,created_at,deleted_at)
feature_group(id,feature_id,group_id,warning,alarm,deleted_at)
pdm_detection(id,parent_id,point_id,rpm,max_amplitude_vel,Seuil_Alarm_Vitesse,created_at,deleted_at)
groups(id,name,entity_id,deleted_at)
operations(id,name,deleted_at)
asset_classes(id,name)
diagrams(id,name,family_id,deleted_at)
checklists(id,name,ref,family_id,schema,deleted_at)
assignment_checklist(id,user_id,checklist_id,asset_id,responses,status,start_date,duration,deleted_at)
actions(id,name,deleted_at)
actions_fault(id,action_id,fault_id,deleted_at)
activity_log(id,log_name,description,user_id,event,created_at)
measurements_faults(id,measurement_id,fault_id,deleted_at)
entity_user(id,entity_id,user_id,deleted_at)
tarifs(id,name,price,deleted_at)
tarif_measures(id,tarif_id,measure_id,deleted_at)
family_fault_operations(id,family_id,fault_id,operation_id,deleted_at)
point_position(id,asset_id,point_id,diagram_id,xAxis,yAxis)
fault_operation(id,operation_id,fault_id,deleted_at)
email_histories(id,asset_id,user_id,subject,created_at)
automated_emails(id,name,entity_id,deleted_at)

TABLES GLOBAL (i_sense_v3_devenv_db):
users(id,first_name,last_name,email,phone,active,last_connection,start_date,end_date,parent_id,deleted_at)
companies(id,name,reference,alias,created_by,deleted_at)
user_company(id,user_id,company_id,is_default,deleted_at)
devices(id,ref,mac,company_id,status,product_id,config_id,deleted_at)
features(id,name,label,unit,grandeur_id,data_type,priority,deleted_at)
features_device(id,feature_id,device_id,deleted_at)
predictions(id,asset_id,measurement_id,model,failure,cause,failures_probability,causes_probability,deleted_at)
pdm_features(id,feature,label,type,unit,deleted_at)
grandeurs(id,name,type,grandeur_category_id,deleted_at)
grandeur_categories(id,name,deleted_at)
notifications(id,type,notifiable_type,notifiable_id,data,read_at,created_at)
abonnements(id,package_id,company_id,max_sms,max_email,max_users,max_devices,start_date,end_date,status,deleted_at)
tenants(id,data,deleted_at)

JOINS:assets.id=asset_faults.asset_id|asset_faults.fault_id=faults.id|assets.id=alarms.asset_id|assets.id=measurements.asset_id|assets.id=interventions.asset_id|assets.family_id=families.id|assets.class_id=asset_classes.id|assets.group_id=groups.id|feature_measurement.asset_parent_id=assets.id|feature_measurement.feature_id=i_sense_v3_devenv_db.features.id|feature_group.feature_id=features.id AND feature_group.group_id=groups.id|alarms.device_id=i_sense_v3_devenv_db.devices.id|recommendations_v3.asset_id=assets.id|recommendation_faults.recommendation_id=recommendations_v3.id|user_company.user_id=users.id|user_company.company_id=companies.id

STATUTS:-1=Unassigned,0=Shut down,1=Normal,2=MID,3=Moderate,4=Undefined,5=Critical
REGLES:TOUJOURS deleted_at IS NULL|Pannes actives=end_date IS NULL|Alarmes actives=ended_at IS NULL|SELECT uniquement|1 requête terminée par ;|Pas de SELECT *|Cross-DB=i_sense_v3_devenv_db.table"""

# ═══════════════════════════════════════════════════════════════
# TABLES CONNUES (IDENTIQUE)
# ═══════════════════════════════════════════════════════════════

KNOWN_TENANT_TABLES = {
    "assets", "asset_faults", "alarms", "faults", "families",
    "recommendations_v3", "recommendation_assets", "recommendation_faults",
    "recommendation_operations", "interventions", "checklists",
    "assignment_checklist", "actions", "actions_fault", "activity_log",
    "measurements", "measurement_points", "measurement_signal",
    "measurements_faults", "vibox_diagnosis", "vibox_diagnosis_item",
    "vibox_diagnosis_recommended_action", "pdm_detection",
    "email_histories", "email_notif_config", "sms_notif_config",
    "user_notif_config", "automated_emails", "entity_user",
    "tarifs", "tarif_measures", "operations", "family_fault_operations",
    "diagrams", "asset_classes", "point_position", "feature_measurement",
    "groups", "feature_group", "fault_operation", "generic_assets",
    "asset_components", "couplings", "daily_asset_status",
    "faults_percentage", "fault_prerequis", "cause_fault", "causes",
    "family_fault", "clients", "factures", "fournisseurs", "burden_details",
    "measures", "bon_de_livraison", "brands", "cache", "cache_locks",
    "categories", "failed_jobs", "jobs", "jobs_batches",
}

KNOWN_GLOBAL_TABLES = {
    "users", "companies", "user_company", "notifications", "devices",
    "features", "features_device", "predictions", "pdm_features",
    "power_values", "transmission_values", "manual_features",
    "grandeurs", "grandeur_categories", "abonnements", "tenants",
    "packages", "acquisition_configurations", "products",
    "product_grandeurs", "shapes", "models_3d", "entities",
}

ALL_KNOWN_TABLES = KNOWN_TENANT_TABLES | KNOWN_GLOBAL_TABLES

# ═══════════════════════════════════════════════════════════════
# COLONNES CRITIQUES PAR TABLE (IDENTIQUE)
# ═══════════════════════════════════════════════════════════════

CRITICAL_COLUMNS = {
    "assets": ["id", "name", "ref", "status", "family_id", "class_id", "parent_id", "rpm", "brand", "deleted_at", "created_at"],
    "asset_faults": ["id", "asset_id", "fault_id", "start_date", "end_date", "status", "percentage", "duration", "deleted_at"],
    "alarms": ["id", "asset_id", "device_id", "status", "created_at", "ended_at", "duration", "deleted_at"],
    "faults": ["id", "name", "deleted_at"],
    "families": ["id", "name", "deleted_at"],
    "measurements": ["id", "asset_id", "status", "is_online", "created_at", "deleted_at"],
    "interventions": ["id", "asset_id", "description", "date_intervention", "status", "expert_id", "deleted_at"],
    "recommendations_v3": ["id", "severity", "fault_date", "asset_id", "created_by", "validated_by", "deleted_at"],
    "recommendation_assets": ["id", "fault", "cause", "notes", "asset_id", "expert", "status", "deleted_at"],
    "pdm_detection": ["id", "parent_id", "rpm", "max_amplitude_vel", "created_at", "deleted_at"],
    "feature_measurement": ["id", "asset_parent_id", "feature_id", "group_id", "value", "created_at", "deleted_at"],
    "feature_group": ["id", "feature_id", "group_id", "warning", "alarm", "deleted_at"],
    "users": ["id", "first_name", "last_name", "email", "active", "last_connection", "deleted_at"],
    "companies": ["id", "name", "reference", "alias", "deleted_at"],
    "user_company": ["id", "user_id", "company_id", "is_default", "deleted_at"],
    "devices": ["id", "ref", "mac", "status", "company_id", "deleted_at"],
}

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES (TOUTES IDENTIQUES)
# ═══════════════════════════════════════════════════════════════

def get_status_label(status_code: int) -> str:
    return ASSET_STATUS.get(status_code, "Unknown")


def get_tenant_db(alias: str) -> str:
    return TENANT_ALIASES.get(alias.lower(), "v3_tenant_jln")


def get_tenant_display(alias: str) -> str:
    return TENANT_DISPLAY_NAMES.get(alias.lower(), alias)


def is_known_table(table_name: str) -> bool:
    return table_name.lower() in ALL_KNOWN_TABLES


def validate_sql_tables(sql: str) -> List[str]:
    """Retourne les tables inconnues dans une requête SQL"""
    pattern = r'(?:FROM|JOIN)\s+(?:\w+\.)?(\w+)'
    tables = re.findall(pattern, sql, re.IGNORECASE)
    return list(set(t.lower() for t in tables if not is_known_table(t)))


def validate_sql_has_deleted_filter(sql: str) -> bool:
    return 'deleted_at is null' in sql.lower()


def validate_sql_safety(sql: str) -> Tuple[bool, str]:
    """Vérifie qu'une requête SQL est sûre (SELECT only)"""
    sql_upper = sql.strip().upper()
    dangerous = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE']
    for keyword in dangerous:
        if sql_upper.startswith(keyword) or f' {keyword} ' in sql_upper:
            if sql.strip().startswith('--'):
                return True, "Negative example (comment)"
            return False, f"Dangerous keyword: {keyword}"
    return True, "OK"


def get_synonyms(word: str) -> List[str]:
    """Retourne les synonymes d'un mot clé"""
    return SYNONYMS.get(word.lower(), [])


def reformulate_question(question: str) -> List[str]:
    """Génère des reformulations d'une question à partir des templates"""
    variations = []
    for old, new in REFORMULATION_TEMPLATES:
        if question.startswith(old):
            variations.append(question.replace(old, new, 1))
        elif question.lower().startswith(old.lower()):
            variations.append(new + question[len(old):])
    return variations


def synonym_augment(question: str) -> List[str]:
    """Génère des variantes en remplaçant par des synonymes"""
    variants = []
    q_lower = question.lower()
    for word, syns in SYNONYMS.items():
        if word in q_lower:
            for syn in syns:
                if syn != word:
                    new_q = question.replace(word, syn).replace(word.capitalize(), syn.capitalize())
                    if new_q != question:
                        variants.append(new_q)
                        break
    return variants[:2]


def get_sample_tenants() -> List[Tuple[str, str, str]]:
    return SAMPLE_TENANTS


def format_query_for_tenant(sql_template: str, tenant_db: str) -> str:
    return sql_template.format(tenant_db=tenant_db)


def generate_asset_status_case(alias: str = "a") -> str:
    return ASSET_STATUS_CASE.replace("a.status", f"{alias}.status")


def get_required_columns(table_name: str) -> List[str]:
    return CRITICAL_COLUMNS.get(table_name, [])


def get_table_categories() -> Dict[str, Set[str]]:
    return {
        "equipements": {"assets", "asset_classes", "diagrams", "generic_assets", "asset_components", "couplings"},
        "defauts": {"faults", "asset_faults", "family_fault", "cause_fault", "causes", "faults_percentage"},
        "alarmes": {"alarms"},
        "mesures": {"measurements", "measurement_points", "measurement_signal", "feature_measurement", "pdm_detection"},
        "predictions": {"predictions", "pdm_features", "vibox_diagnosis"},
        "maintenance": {"interventions", "checklists", "assignment_checklist", "actions", "operations"},
        "recommandations": {"recommendations_v3", "recommendation_assets", "recommendation_faults"},
        "utilisateurs": {"users", "user_company", "notifications"},
        "entreprises": {"companies", "abonnements", "devices"},
    }


# ═══════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 80)
    print(" " * 20 + "★ STANDARDS SQL V3.1 - VÉRIFICATION ★")
    print("=" * 80)

    print(f"\n Bases tenant: {len(ALL_TENANT_DATABASES)}")
    print(f" Aliases tenant: {len(TENANT_ALIASES)}")
    print(f" Display names: {len(TENANT_DISPLAY_NAMES)}")
    print(f" Échantillons tenants: {len(SAMPLE_TENANTS)}")
    print(f" Synonymes: {len(SYNONYMS)} catégories")
    print(f" Templates reformulation: {len(REFORMULATION_TEMPLATES)}")
    print(f" Statuts définis: {len(ASSET_STATUS)}")
    print(f" Filtres standard: {len(FILTERS)}")
    print(f" Jointures standard: {len(JOINS)}")
    print(f" Tables tenant connues: {len(KNOWN_TENANT_TABLES)}")
    print(f" Tables globales connues: {len(KNOWN_GLOBAL_TABLES)}")
    print(f" Colonnes critiques: {len(CRITICAL_COLUMNS)} tables")
    print(f"\n★ SYSTEM_PROMPT: {len(SYSTEM_PROMPT)} caractères (~{len(SYSTEM_PROMPT.split())} mots)")

    if len(SYSTEM_PROMPT) < 3500:
        print(f"   ✅ Prompt compact OK (< 3500 chars)")
    else:
        print(f"   ⚠️ Prompt encore trop long ! ({len(SYSTEM_PROMPT)} chars)")

    # Test reformulation
    sample_q = "Quels sont les équipements critiques ?"
    print(f"\n Test reformulation : '{sample_q}'")
    for v in reformulate_question(sample_q):
        print(f"   → {v}")

    # Test synonymes
    sample_q2 = "Quels sont les équipements en panne ?"
    print(f"\n Test synonymes : '{sample_q2}'")
    for v in synonym_augment(sample_q2):
        print(f"   → {v}")

    # Test validation SQL
    test_sql = "SELECT a.id FROM assets a WHERE a.deleted_at IS NULL"
    safe, msg = validate_sql_safety(test_sql)
    print(f"\n Test sécurité SQL: safe={safe}, msg={msg}")

    print("\n" + "=" * 80)
    print(" " * 25 + "★ STANDARDS V3.1 VALIDÉS ★")
    print("=" * 80 + "\n")