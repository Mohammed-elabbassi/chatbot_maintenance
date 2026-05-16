


# schema_tenants.py
"""
Schéma complet des bases de données tenant (v3_tenant_*)
40+ tables essentielles avec TOUTES les colonnes, relations et métadonnées
Pour l'Agent NLP - Génération de requêtes SQL exactes

ARCHITECTURE MULTI-TENANT :
- 27 tables COMMUNES → Tous les tenants (9 bases)
- 13 tables UNIQUES → v3_tenant_Site_Safi SEULEMENT

Bases concernées :
- v3_tenant_jln
- v3_tenant_Site_Safi
- v3_tenant_cmcp_ip
- v3_tenant_cobomi
- v3_tenant_jfc4
- v3_tenant_nomac
- v3_tenant_ntn
- v3_tenant_onee
- v3_tenant_lafarge_holcim_bouskoura

Version : 3.0 - Schéma Complet 40+ Tables
Total tables : 40+
Total colonnes : ~600+
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION DES BASES TENANT
# ═══════════════════════════════════════════════════════════════

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

COMMON_TABLES = [
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
    "diagrams", "asset_classes","point_position","feature_measurement","groups", "feature_group","fault_operation",
]

UNIQUE_TABLES_SAFI = [
    "clients", "factures", "fournisseurs", "burden_details",
    "family_fault", "bon_de_livraison", "brands", "cache",
    "cache_locks", "categories", "failed_jobs", "jobs",
    "jobs_batches", "measures",
]

DATABASE_INFO = {
    "name": "v3_tenant_*",
    "type": "tenant",
    "description": "Bases de données tenant - Données opérationnelles par client",
    "total_tenants": 9,
    "tenants": ALL_TENANT_DATABASES,
    "total_tables": 40,
    "common_tables": 27,
    "unique_tables_safi": 13,
    "total_columns": "~600+",
    "used_in_objectifs": list(range(1, 101)),
}

# ═══════════════════════════════════════════════════════════════
# TABLE 1: assets (TOUS TENANTS) - 36 colonnes
# ═══════════════════════════════════════════════════════════════


TABLE_ASSETS = {
    "name": "assets",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Équipements/Actifs industriels",
    "category": "equipements",
    "used_in_objectifs": list(range(1, 16)) + list(range(16, 31)) + list(range(31, 41)) + list(range(51, 61)) + list(range(61, 71)),
    "total_columns": 36,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de l'équipement"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom de l'équipement"},
        "ref": {"type": "VARCHAR", "nullable": True, "description": "Référence"},
        "illustration": {"type": "VARCHAR", "nullable": True, "description": "Illustration/URL image"},
        "diagram_id": {"type": "INT", "nullable": True, "foreign_key": "diagrams.id", "description": "Diagramme associé"},
        "class_id": {"type": "BIGINT", "nullable": True, "foreign_key": "asset_classes.id", "description": "Classe de criticité"},
        "type": {"type": "SMALLINT", "nullable": True, "description": "Type d'équipement"},
        "brand": {"type": "VARCHAR", "nullable": True, "description": "Marque"},
        "structure": {"type": "VARCHAR", "nullable": True, "description": "Structure"},
        "latitude": {"type": "DECIMAL", "nullable": True, "description": "Latitude"},
        "longitude": {"type": "DECIMAL", "nullable": True, "description": "Longitude"},
        "SpeedPerimeter": {"type": "VARCHAR", "nullable": True, "description": "Périmètre de vitesse"},
        "powerRange": {"type": "VARCHAR", "nullable": True, "description": "Plage de puissance"},
        "rpm": {"type": "DOUBLE", "nullable": True, "description": "RPM (tours/minute)"},
        "entity_id": {"type": "INT", "nullable": True, "foreign_key": "entities.id", "description": "Entité associée"},
        "group_id": {"type": "INT", "nullable": True, "foreign_key": "groups.id", "description": "Groupe associé"},
        "family_id": {"type": "INT", "nullable": True, "foreign_key": "families.id", "description": "Famille d'équipement"},
        "parent_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement parent (hiérarchie)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "status": {"type": "TINYINT", "nullable": True, "description": "Statut (0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned')"},
        "last_measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Dernière mesure"},
        "transition_duration": {"type": "INT", "nullable": True, "description": "Durée de transition"},
        "is_manual": {"type": "TINYINT", "nullable": True, "description": "Manuel est 0 et en ligne (online) est 1"},
        "last_measure_created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date dernière mesure"},
        "old_id": {"type": "INT", "nullable": True, "description": "Ancien ID (migration)"},
        "outlier_detection": {"type": "DOUBLE", "nullable": True, "description": "Détection d'anomalies"},
        "rul": {"type": "DOUBLE", "nullable": True, "description": "RUL (Remaining Useful Life)"},
        "shape_id": {"type": "BIGINT", "nullable": True, "foreign_key": "shapes.id", "description": "Forme associée"},
        "number_of_bearings": {"type": "INT", "nullable": True, "description": "Nombre de roulements"},
        "3d_model_id": {"type": "BIGINT", "nullable": True, "foreign_key": "models_3d.id", "description": "Modèle 3D"},
        "has_pdm": {"type": "TINYINT", "nullable": True, "description": "A PDM (0/1)"},
        "pdm_enabled": {"type": "TINYINT", "nullable": True, "description": "PDM activé (0/1)"},
        "created_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Créateur (user_id)"},
        "assets_scores": {"type": "DOUBLE", "nullable": True, "description": "Score de l'équipement"},
    },
    "relationships": [
        {"table": "asset_faults", "type": "one-to-many", "on": "assets.id = asset_faults.asset_id"},
        {"table": "alarms", "type": "one-to-many", "on": "assets.id = alarms.asset_id"},
        {"table": "interventions", "type": "one-to-many", "on": "assets.id = interventions.asset_id"},
        {"table": "measurements", "type": "one-to-many", "on": "assets.id = measurements.asset_id"},
        {"table": "recommendation_assets", "type": "one-to-many", "on": "assets.id = recommendation_assets.asset_id"},
        {"table": "families", "type": "many-to-one", "on": "assets.family_id = families.id"},
        {"table": "asset_classes", "type": "many-to-one", "on": "assets.class_id = asset_classes.id"},
        {"table": "diagrams", "type": "many-to-one", "on": "assets.diagram_id = diagrams.id"},
        {"table": "users", "type": "many-to-one", "on": "assets.created_by = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 2: asset_faults (TOUS TENANTS) - 15 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_ASSET_FAULTS = {
    "name": "asset_faults",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Défauts/Pannes des équipements",
    "category": "defauts",
    "used_in_objectifs": list(range(16, 31)) + [55],
    "total_columns": 15,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique du défaut"},
        "asset_id": {"type": "INT", "nullable": False, "foreign_key": "assets.id", "description": "Équipement concerné"},
        "sub_asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Sous-équipement"},
        "fault_id": {"type": "INT", "nullable": False, "foreign_key": "faults.id", "description": "Type de défaut"},
        "start_date": {"type": "TIMESTAMP", "nullable": True, "description": "Date de début"},
        "status": {"type": "INT", "nullable": True, "description": "Statut (0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned')"},
        "end_date": {"type": "DATETIME", "nullable": True, "description": "Date de fin"},
        "point_id": {"type": "INT", "nullable": True, "foreign_key": "measurement_points.id", "description": "Point de mesure"},
        "start_measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure de début"},
        "end_measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure de fin"},
        "percentage": {"type": "DOUBLE", "nullable": True, "description": "Pourcentage de probabilité"},
        "etats": {"type": "INT", "nullable": True, "description": "États"},
        "treated_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Traité par (user_id)"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "duration": {"type": "INT", "nullable": True, "description": "Durée (heures)"},
    },
    "relationships": [
        {"table": "assets", "type": "many-to-one", "on": "asset_faults.asset_id = assets.id"},
        {"table": "faults", "type": "many-to-one", "on": "asset_faults.fault_id = faults.id"},
        {"table": "measurements_faults", "type": "one-to-many", "on": "asset_faults.id = measurements_faults.fault_id"},
        {"table": "actions_fault", "type": "one-to-many", "on": "asset_faults.id = actions_fault.fault_id"},
        {"table": "users", "type": "many-to-one", "on": "asset_faults.treated_by = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 3: alarms (TOUS TENANTS) - 13 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_ALARMS = {
    "name": "alarms",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Alarmes des équipements",
    "category": "alarmes",
    "used_in_objectifs": list(range(31, 41)),
    "total_columns": 13,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de l'alarme"},
        "status": {"type": "INT", "nullable": True, "description": "Statut (0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned')"},
        "ended_at": {"type": "DATETIME", "nullable": True, "description": "Date de fin"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "asset_id": {"type": "INT", "nullable": False, "foreign_key": "assets.id", "description": "Équipement concerné"},
        "device_id": {"type": "INT", "nullable": True, "foreign_key": "devices.id", "description": "Device de mesure"},
        "measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure associée"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "point_id": {"type": "INT", "nullable": True, "foreign_key": "measurement_points.id", "description": "Point de mesure"},
        "end_measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure de fin"},
        "asset_parent_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement parent"},
        "duration": {"type": "INT", "nullable": True, "description": "Durée (heures)"},
    },
    "relationships": [
        {"table": "assets", "type": "many-to-one", "on": "alarms.asset_id = assets.id"},
        {"table": "devices", "type": "many-to-one", "on": "alarms.device_id = devices.id", "database": "i_sense_v3_devenv_db"},
        {"table": "measurements", "type": "many-to-one", "on": "alarms.measure_id = measurements.id"},
        {"table": "measurement_points", "type": "many-to-one", "on": "alarms.point_id = measurement_points.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 4: faults (TOUS TENANTS) - 10 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_FAULTS = {
    "name": "faults",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Types de défauts (référence)",
    "category": "defauts",
    "used_in_objectifs": list(range(16, 31)) + list(range(41, 51)),
    "total_columns": 10,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique du type de défaut"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom du défaut (ex: Bearing Wear)"},
        "description": {"type": "VARCHAR", "nullable": True, "description": "Description"},
        "locked": {"type": "TINYINT", "nullable": True, "description": "Verrouillé (0/1)"},
        "image_path": {"type": "VARCHAR", "nullable": True, "description": "Chemin de l'image"},
        "is_asset": {"type": "TINYINT", "nullable": True, "description": "Est un équipement (0/1)"},
        "require_rpm": {"type": "TINYINT", "nullable": True, "description": "Requiert RPM (0/1)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    "relationships": [
        {"table": "asset_faults", "type": "one-to-many", "on": "faults.id = asset_faults.fault_id"},
        {"table": "family_fault", "type": "one-to-many", "on": "faults.id = family_fault.fault_id", "database": "v3_tenant_Site_Safi"},
        {"table": "recommendation_faults", "type": "one-to-many", "on": "faults.id = recommendation_faults.fault_id"},
        {"table": "measurements_faults", "type": "one-to-many", "on": "faults.id = measurements_faults.fault_id"},
        {"table": "actions_fault", "type": "one-to-many", "on": "faults.id = actions_fault.fault_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 5: families (TOUS TENANTS) - 9 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_FAMILIES = {
    "name": "families",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Familles d'équipements/défauts",
    "category": "defauts",
    "used_in_objectifs": list(range(16, 31)) + list(range(41, 51)),
    "total_columns": 9,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la famille"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom de la famille (ex: AC Motor)"},
        "image_url": {"type": "VARCHAR", "nullable": True, "description": "URL de l'image"},
        "locked": {"type": "TINYINT", "nullable": True, "description": "Verrouillé (0= 'non', 1= 'oui')"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "for_asset": {"type": "TINYINT", "nullable": True, "description": "Pour équipement (0= 'non', 1= 'oui')"},
        "family_type": {"type": "INT", "nullable": True, "description": "Type (0= 'non', 1= 'oui')"},
    },
    "relationships": [
        {"table": "assets", "type": "one-to-many", "on": "families.id = assets.family_id"},
        {"table": "family_fault", "type": "one-to-many", "on": "families.id = family_fault.family_id", "database": "v3_tenant_Site_Safi"},
        {"table": "checklists", "type": "one-to-many", "on": "families.id = checklists.family_id"},
        {"table": "diagrams", "type": "one-to-many", "on": "families.id = diagrams.family_id"},
    ],
}


# ═══════════════════════════════════════════════════════════════
# TABLE 6: recommendations_v3 (TOUS TENANTS) - 15 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_RECOMMENDATIONS_V3 = {
    "name": "recommendations_v3",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Recommandations de maintenance",
    "category": "recommandations",
    "used_in_objectifs": list(range(41, 51)),
    "total_columns": 15,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la recommandation"},
        "severity": {"type": "TINYINT", "nullable": True, "description": "Sévérité (1=Critique, 2=Haute, 3=Moyenne)"},
        "fault_date": {"type": "TIMESTAMP", "nullable": True, "description": "Date de la panne"},
        "asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement concerné"},
        "asset_parent_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement parent"},
        "created_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Créateur (user_id)"},
        "validated_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Validateur (user_id)"},
        "measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure associée"},
        "point_id": {"type": "INT", "nullable": True, "foreign_key": "measurement_points.id", "description": "Point de mesure"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "diagnostic_details": {"type": "VARCHAR", "nullable": True, "description": "Détails du diagnostic"},
        "recommendation_details": {"type": "VARCHAR", "nullable": True, "description": "Détails de la recommandation"},
        "actions_taken": {"type": "VARCHAR", "nullable": True, "description": "Actions entreprises"},
    },
    "relationships": [
        {"table": "assets", "type": "many-to-one", "on": "recommendations_v3.asset_id = assets.id"},
        {"table": "measurements", "type": "many-to-one", "on": "recommendations_v3.measure_id = measurements.id"},
        {"table": "measurement_points", "type": "many-to-one", "on": "recommendations_v3.point_id = measurement_points.id"},
        {"table": "recommendation_faults", "type": "one-to-many", "on": "recommendations_v3.id = recommendation_faults.recommendation_id"},
        {"table": "users", "type": "many-to-one", "on": "recommendations_v3.created_by = users.id", "database": "i_sense_v3_devenv_db"},
        {"table": "users", "type": "many-to-one", "on": "recommendations_v3.validated_by = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 7: recommendation_assets (TOUS TENANTS) - 13 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_RECOMMENDATION_ASSETS = {
    "name": "recommendation_assets",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Recommandations par équipement",
    "category": "recommandations",
    "used_in_objectifs": [42, 45, 47],
    "total_columns": 13,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la recommandation"},
        "fault": {"type": "VARCHAR", "nullable": True, "description": "Défaut identifié"},
        "cause": {"type": "VARCHAR", "nullable": True, "description": "Cause identifiée"},
        "notes": {"type": "VARCHAR", "nullable": True, "description": "Notes/Diagnostic"},
        "started_at": {"type": "DATE", "nullable": True, "description": "Date de début"},
        "ended_at": {"type": "DATE", "nullable": True, "description": "Date de fin"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement concerné"},
        "point_id": {"type": "INT", "nullable": True, "foreign_key": "measurement_points.id", "description": "Point de mesure"},
        "expert": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Expert assigné"},
        "status": {"type": "TINYINT", "nullable": True, "description": "Statut ((0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned'))"},
    },
    "relationships": [
        {"table": "assets", "type": "many-to-one", "on": "recommendation_assets.asset_id = assets.id"},
        {"table": "measurement_points", "type": "many-to-one", "on": "recommendation_assets.point_id = measurement_points.id"},
        {"table": "users", "type": "many-to-one", "on": "recommendation_assets.expert = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 8: recommendation_faults (TOUS TENANTS) - 5 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_RECOMMENDATION_FAULTS = {
    "name": "recommendation_faults",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Liaison recommandations-défauts",
    "category": "recommandations",
    "used_in_objectifs": [41, 46],
    "total_columns": 5,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la liaison"},
        "recommendation_id": {"type": "BIGINT", "nullable": True, "foreign_key": "recommendations_v3.id", "description": "Recommandation associée"},
        "fault_id": {"type": "INT", "nullable": True, "foreign_key": "faults.id", "description": "Défaut concerné"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "probability": {"type": "DOUBLE", "nullable": True, "description": "Probabilité de défaillance"},
    },
    "relationships": [
        {"table": "recommendations_v3", "type": "many-to-one", "on": "recommendation_faults.recommendation_id = recommendations_v3.id"},
        {"table": "faults", "type": "many-to-one", "on": "recommendation_faults.fault_id = faults.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 9: recommendation_operations (TOUS TENANTS) - 3 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_RECOMMENDATION_OPERATIONS = {
    "name": "recommendation_operations",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Liaison recommandations-opérations",
    "category": "recommandations",
    "used_in_objectifs": [49],
    "total_columns": 3,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la liaison"},
        "recommendation_id": {"type": "BIGINT", "nullable": True, "foreign_key": "recommendations_v3.id", "description": "Recommandation associée"},
        "operation_id": {"type": "INT", "nullable": True, "foreign_key": "operations.id", "description": "Opération concernée"},
    },
    "relationships": [
        {"table": "recommendations_v3", "type": "many-to-one", "on": "recommendation_operations.recommendation_id = recommendations_v3.id"},
        {"table": "operations", "type": "many-to-one", "on": "recommendation_operations.operation_id = operations.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 10: interventions (TOUS TENANTS) - 11 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_INTERVENTIONS = {
    "name": "interventions",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Interventions de maintenance",
    "category": "maintenance",
    "used_in_objectifs": list(range(51, 61)),
    "total_columns": 11,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de l'intervention"},
        "asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement concerné"},
        "description": {"type": "TEXT", "nullable": True, "description": "Description"},
        "date_intervention": {"type": "DATETIME", "nullable": True, "description": "Date"},
        "status": {"type": "VARCHAR", "nullable": True, "description": "Statut (0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned')"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "expert_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Expert"},
        "validator_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Validateur"},
        "operation_id": {"type": "INT", "nullable": True, "foreign_key": "operations.id", "description": "Opération associée"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "assets", "type": "many-to-one", "on": "interventions.asset_id = assets.id"},
        {"table": "operations", "type": "many-to-one", "on": "interventions.operation_id = operations.id"},
        {"table": "users", "type": "many-to-one", "on": "interventions.expert_id = users.id", "database": "i_sense_v3_devenv_db"},
        {"table": "users", "type": "many-to-one", "on": "interventions.validator_id = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 11: checklists (TOUS TENANTS) - 8 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_CHECKLISTS = {
    "name": "checklists",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Checklists de maintenance",
    "category": "maintenance",
    "used_in_objectifs": [52, 60],
    "total_columns": 8,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "ref": {"type": "VARCHAR", "nullable": True, "description": "Référence"},
        "family_id": {"type": "INT", "nullable": True, "foreign_key": "families.id", "description": "Famille associée"},
        "schema": {"type": "JSON", "nullable": True, "description": "Schéma (JSON)"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
    },
    "relationships": [
        {"table": "families", "type": "many-to-one", "on": "checklists.family_id = families.id"},
        {"table": "assignment_checklist", "type": "one-to-many", "on": "checklists.id = assignment_checklist.checklist_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 12: assignment_checklist (TOUS TENANTS) - 13 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_ASSIGNMENT_CHECKLIST = {
    "name": "assignment_checklist",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Assignation des checklists aux équipements",
    "category": "maintenance",
    "used_in_objectifs": [60],
    "total_columns": 13,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "user_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Utilisateur assigné"},
        "checklist_id": {"type": "BIGINT", "nullable": True, "foreign_key": "checklists.id", "description": "Checklist assignée"},
        "asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement concerné"},
        "responses": {"type": "JSON", "nullable": True, "description": "Réponses (JSON)"},
        "result": {"type": "VARCHAR", "nullable": True, "description": "Résultat"},
        "start_date": {"type": "DATE", "nullable": True, "description": "Date de début"},
        "status": {"type": "ENUM", "nullable": True, "description": "Statut (To do, Done, Overdue, Draft)"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "duration": {"type": "INT", "nullable": True, "description": "Durée (minutes)"},
        "workstation": {"type": "VARCHAR", "nullable": True, "description": "Poste de travail"},
    },
    "relationships": [
        {"table": "users", "type": "many-to-one", "on": "assignment_checklist.user_id = users.id", "database": "i_sense_v3_devenv_db"},
        {"table": "checklists", "type": "many-to-one", "on": "assignment_checklist.checklist_id = checklists.id"},
        {"table": "assets", "type": "many-to-one", "on": "assignment_checklist.asset_id = assets.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 13: actions (TOUS TENANTS) - 5 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_ACTIONS = {
    "name": "actions",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Actions de maintenance",
    "category": "maintenance",
    "used_in_objectifs": [55],
    "total_columns": 5,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "actions_fault", "type": "one-to-many", "on": "actions.id = actions_fault.action_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 14: actions_fault (TOUS TENANTS) - 6 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_ACTIONS_FAULT = {
    "name": "actions_fault",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Liaison actions-défauts",
    "category": "maintenance",
    "used_in_objectifs": [55],
    "total_columns": 6,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "action_id": {"type": "BIGINT", "nullable": True, "foreign_key": "actions.id", "description": "Action associée"},
        "fault_id": {"type": "INT", "nullable": True, "foreign_key": "asset_faults.id", "description": "Défaut concerné"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "actions", "type": "many-to-one", "on": "actions_fault.action_id = actions.id"},
        {"table": "asset_faults", "type": "many-to-one", "on": "actions_fault.fault_id = asset_faults.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 15: activity_log (TOUS TENANTS) - 17 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_ACTIVITY_LOG = {
    "name": "activity_log",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Journal d'activité (logs)",
    "category": "maintenance",
    "used_in_objectifs": [56, 57],
    "total_columns": 17,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "log_name": {"type": "VARCHAR", "nullable": True, "description": "Nom du log"},
        "description": {"type": "TEXT", "nullable": True, "description": "Description"},
        "user_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Utilisateur concerné"},
        "ip": {"type": "VARCHAR", "nullable": True, "description": "Adresse IP"},
        "browser": {"type": "VARCHAR", "nullable": True, "description": "Navigateur"},
        "country": {"type": "VARCHAR", "nullable": True, "description": "Pays"},
        "subject_type": {"type": "VARCHAR", "nullable": True, "description": "Type d'entité"},
        "subject_id": {"type": "BIGINT", "nullable": True, "description": "ID de l'entité"},
        "causer_type": {"type": "VARCHAR", "nullable": True, "description": "Type de cause"},
        "causer_id": {"type": "BIGINT", "nullable": True, "description": "ID de la cause"},
        "event": {"type": "VARCHAR", "nullable": True, "description": "Événement"},
        "properties": {"type": "JSON", "nullable": True, "description": "Propriétés (JSON)"},
        "batch_uuid": {"type": "CHAR", "nullable": True, "description": "UUID de batch"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "users", "type": "many-to-one", "on": "activity_log.user_id = users.id", "database": "i_sense_v3_devenv_db"},
        {"table": "assets", "type": "many-to-one", "on": "activity_log.subject_id = assets.id", "condition": "subject_type = 'App\\Models\\Asset'"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 16: measurements (TOUS TENANTS) - 20 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_MEASUREMENTS = {
    "name": "measurements",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Mesures des capteurs",
    "category": "mesures",
    "used_in_objectifs": list(range(61, 71)),
    "total_columns": 20,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement"},
        "device_id": {"type": "INT", "nullable": True, "foreign_key": "devices.id", "description": "Device"},
        "point_id": {"type": "INT", "nullable": True, "description": "Point de mesure"},
        "status": {"type": "INT", "nullable": True, "description": "Statut (0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned')"},
        "is_online": {"type": "TINYINT", "nullable": True, "description": "En ligne"},
        "treated": {"type": "TINYINT", "nullable": True, "description": "Traité"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "generic_asset_id": {"type": "BIGINT", "nullable": True, "description": "Asset générique"},
        "generic_point_id": {"type": "BIGINT", "nullable": True, "description": "Point générique"},
        "entity_id": {"type": "INT", "nullable": True, "description": "Entité"},
        "old_measure_id": {"type": "INT", "nullable": True, "description": "Ancienne mesure"},
        "is_generic": {"type": "TINYINT", "nullable": True, "description": "Est générique"},
        "is_oil": {"type": "TINYINT", "nullable": True, "description": "Est huile"},
        "has_signals": {"type": "TINYINT", "nullable": True, "description": "A des signaux"},
        "is_manual": {"type": "TINYINT", "nullable": True, "description": "Manuel"},
        "last_measure_created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date dernière mesure"},
        "outlier_detection": {"type": "DOUBLE", "nullable": True, "description": "Détection anomalies"},
        "assets_scores": {"type": "DOUBLE", "nullable": True, "description": "Score"},
    },
    "relationships": [
        {"table": "assets", "type": "many-to-one", "on": "measurements.asset_id = assets.id"},
        {"table": "devices", "type": "many-to-one", "on": "measurements.device_id = devices.id", "database": "i_sense_v3_devenv_db"},
        {"table": "measurement_points", "type": "many-to-one", "on": "measurements.point_id = measurement_points.id"},
        {"table": "measurement_signal", "type": "one-to-many", "on": "measurements.id = measurement_signal.measure_id"},
        {"table": "measurements_faults", "type": "one-to-many", "on": "measurements.id = measurements_faults.measure_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 17: measurement_points (TOUS TENANTS) - 21 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_MEASUREMENT_POINTS = {
    "name": "measurement_points",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Points de mesure des capteurs",
    "category": "mesures",
    "used_in_objectifs": list(range(61, 71)),
    "total_columns": 21,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "type": {"type": "VARCHAR", "nullable": True, "description": "Type"},
        "external": {"type": "VARCHAR", "nullable": True, "description": "Externe"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "parent_asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Asset parent"},
        "asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement"},
        "device_id": {"type": "INT", "nullable": True, "foreign_key": "devices.id", "description": "Device"},
        "component_id": {"type": "INT", "nullable": True, "description": "Composant"},
        "config_id": {"type": "INT", "nullable": True, "description": "Configuration"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "generic_asset_id": {"type": "BIGINT", "nullable": True, "description": "Asset générique"},
        "status": {"type": "INT", "nullable": True, "description": "Statut (0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned')"},
        "last_measure_created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date dernière mesure"},
        "last_measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Dernière mesure"},
        "old_id": {"type": "INT", "nullable": True, "description": "Ancien ID"},
        "old_component_id": {"type": "INT", "nullable": True, "description": "Ancien composant"},
        "is_oil": {"type": "INT", "nullable": True, "description": "Est huile (0 ou 1)"},
        "is_out": {"type": "TINYINT", "nullable": True, "description": "Est dehors"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "is_tachy": {"type": "TINYINT", "nullable": True, "description": "Est tachymètre"},
    },
    "relationships": [
        {"table": "assets", "type": "many-to-one", "on": "measurement_points.asset_id = assets.id"},
        {"table": "devices", "type": "many-to-one", "on": "measurement_points.device_id = devices.id", "database": "i_sense_v3_devenv_db"},
        {"table": "measurements", "type": "one-to-many", "on": "measurement_points.id = measurements.point_id"},
        {"table": "measurement_signal", "type": "one-to-many", "on": "measurement_points.id = measurement_signal.point_id"},
        {"table": "alarms", "type": "one-to-many", "on": "measurement_points.id = alarms.point_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 18: measurement_signal (TOUS TENANTS) - 9 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_MEASUREMENT_SIGNAL = {
    "name": "measurement_signal",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Signaux de mesure (données brutes)",
    "category": "mesures",
    "used_in_objectifs": [63],
    "total_columns": 9,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "value": {"type": "MEDIUMTEXT", "nullable": True, "description": "Valeur (données brutes)"},
        "signal_id": {"type": "INT", "nullable": True, "description": "ID du signal"},
        "measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure associée"},
        "point_id": {"type": "INT", "nullable": True, "foreign_key": "measurement_points.id", "description": "Point de mesure"},
        "treated": {"type": "TINYINT", "nullable": True, "description": "Traité"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "measurements", "type": "many-to-one", "on": "measurement_signal.measure_id = measurements.id"},
        {"table": "measurement_points", "type": "many-to-one", "on": "measurement_signal.point_id = measurement_points.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 19: measurements_faults (TOUS TENANTS) - 12 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_MEASUREMENTS_FAULTS = {
    "name": "measurements_faults",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Liaison mesures-défauts",
    "category": "mesures",
    "used_in_objectifs": [64],
    "total_columns": 12,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure associée"},
        "fault_id": {"type": "INT", "nullable": True, "foreign_key": "asset_faults.id", "description": "Défaut concerné"},
        "percentage": {"type": "INT", "nullable": True, "description": "Pourcentage"},
        "type": {"type": "INT", "nullable": True, "description": "Type"},
        "status": {"type": "INT", "nullable": True, "description": "Statut (0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned')"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "validator_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Validateur"},
        "asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement"},
        "parent_asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement parent"},
    },
    "relationships": [
        {"table": "measurements", "type": "many-to-one", "on": "measurements_faults.measure_id = measurements.id"},
        {"table": "asset_faults", "type": "many-to-one", "on": "measurements_faults.fault_id = asset_faults.id"},
        {"table": "assets", "type": "many-to-one", "on": "measurements_faults.asset_id = assets.id"},
        {"table": "users", "type": "many-to-one", "on": "measurements_faults.validator_id = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 20: vibox_diagnosis (TOUS TENANTS) - 12 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_VIBOX_DIAGNOSIS = {
    "name": "vibox_diagnosis",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Diagnostics Vibox",
    "category": "predictions",
    "used_in_objectifs": [77, 78, 79],
    "total_columns": 12,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "device_id": {"type": "INT", "nullable": True, "foreign_key": "devices.id", "description": "Device concerné"},
        "diagnosis_id": {"type": "INT", "nullable": True, "description": "Type de diagnostic"},
        "diagnosis": {"type": "TEXT", "nullable": True, "description": "Diagnostic"},
        "recommended_action_id": {"type": "INT", "nullable": True, "description": "Action recommandée"},
        "recommended_action": {"type": "TEXT", "nullable": True, "description": "Action recommandée"},
        "lead": {"type": "ENUM", "nullable": True, "description": "Lead/Priorité"},
        "start_date": {"type": "DATETIME", "nullable": True, "description": "Date de début"},
        "end_date": {"type": "DATETIME", "nullable": True, "description": "Date de fin"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "devices", "type": "many-to-one", "on": "vibox_diagnosis.device_id = devices.id", "database": "i_sense_v3_devenv_db"},
        {"table": "vibox_diagnosis_item", "type": "many-to-one", "on": "vibox_diagnosis.diagnosis_id = vibox_diagnosis_item.id"},
        {"table": "vibox_diagnosis_recommended_action", "type": "many-to-one", "on": "vibox_diagnosis.recommended_action_id = vibox_diagnosis_recommended_action.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 21: vibox_diagnosis_item (TOUS TENANTS) - 7 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_VIBOX_DIAGNOSIS_ITEM = {
    "name": "vibox_diagnosis_item",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Items de diagnostic Vibox",
    "category": "predictions",
    "used_in_objectifs": [78],
    "total_columns": 7,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "description": {"type": "VARCHAR", "nullable": True, "description": "Description"},
        "product_id": {"type": "INT", "nullable": True, "description": "Produit"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "vibox_diagnosis", "type": "one-to-many", "on": "vibox_diagnosis_item.id = vibox_diagnosis.diagnosis_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 22: vibox_diagnosis_recommended_action (TOUS TENANTS) - 7 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_VIBOX_DIAGNOSIS_RECOMMENDED_ACTION = {
    "name": "vibox_diagnosis_recommended_action",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Actions recommandées Vibox",
    "category": "predictions",
    "used_in_objectifs": [79],
    "total_columns": 7,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "description": {"type": "VARCHAR", "nullable": True, "description": "Description"},
        "product_id": {"type": "INT", "nullable": True, "description": "Produit"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "vibox_diagnosis", "type": "one-to-many", "on": "vibox_diagnosis_recommended_action.id = vibox_diagnosis.recommended_action_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 23: pdm_detection (TOUS TENANTS) - 211 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_PDM_DETECTION = {
    "name": "pdm_detection",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Détections PDM (Predictive Maintenance) - Features ML",
    "category": "predictions",
    "used_in_objectifs": [74, 75, 76],
    "total_columns": 211,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure associée"},
        "config_id": {"type": "INT", "nullable": True, "description": "Configuration"},
        "point_id": {"type": "INT", "nullable": True, "foreign_key": "measurement_points.id", "description": "Point de mesure"},
        "subAsset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Sous-équipement"},
        "parent_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement parent"},
        "parent_family_id": {"type": "INT", "nullable": True, "description": "Famille parent"},
        "sub_asset_family_id": {"type": "INT", "nullable": True, "description": "Famille sous-équipement"},
        "point_name": {"type": "VARCHAR", "nullable": True, "description": "Nom du point"},
        "type": {"type": "VARCHAR", "nullable": True, "description": "Type"},
        "family": {"type": "VARCHAR", "nullable": True, "description": "Famille"},
        "faults": {"type": "VARCHAR", "nullable": True, "description": "Défauts"},
        "NGA": {"type": "DOUBLE", "nullable": True, "description": "NGA"},
        "NGV": {"type": "DOUBLE", "nullable": True, "description": "NGV"},
        "VC_g": {"type": "DOUBLE", "nullable": True, "description": "VC_g"},
        "VCC_g": {"type": "DOUBLE", "nullable": True, "description": "VCC_g"},
        "K": {"type": "DOUBLE", "nullable": True, "description": "K"},
        "FC": {"type": "DOUBLE", "nullable": True, "description": "FC"},
        "RPM": {"type": "DOUBLE", "nullable": True, "description": "RPM"},
        "vel_Fds": {"type": "DOUBLE", "nullable": True, "description": "vel_Fds"},
        "f0": {"type": "DOUBLE", "nullable": True, "description": "f0"},
        "Seuil_Alert_Vitesse": {"type": "DOUBLE", "nullable": True, "description": "Seuil alerte vitesse"},
        "Seuil_Alarm_Vitesse": {"type": "DOUBLE", "nullable": True, "description": "Seuil alarme vitesse"},
        "Seuil_Alert_Acceleration": {"type": "DOUBLE", "nullable": True, "description": "Seuil alerte accélération"},
        "Seuil_Alarm_Acceleration": {"type": "DOUBLE", "nullable": True, "description": "Seuil alarme accélération"},
        "max_amplitude_vel": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude vitesse"},
        "max_amplitude_freq_vel": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude freq vitesse"},
        "max_amplitude_acc": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude accélération"},
        "max_amplitude_freq_acc": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude freq accélération"},
        "rms_vel": {"type": "DOUBLE", "nullable": True, "description": "RMS vitesse"},
        "rms_acc": {"type": "DOUBLE", "nullable": True, "description": "RMS accélération"},
        "rms_vel_010": {"type": "DOUBLE", "nullable": True, "description": "RMS vitesse 0-10"},
        "rms_acc_010": {"type": "DOUBLE", "nullable": True, "description": "RMS accélération 0-10"},
        "rms_10_vel": {"type": "DOUBLE", "nullable": True, "description": "RMS 10 vitesse"},
        "rms_10_acc": {"type": "DOUBLE", "nullable": True, "description": "RMS 10 accélération"},
        "rms_g": {"type": "DOUBLE", "nullable": True, "description": "RMS g"},
        "rms_global": {"type": "DOUBLE", "nullable": True, "description": "RMS global"},
        "max_percent_Saturation": {"type": "DOUBLE", "nullable": True, "description": "Max % saturation"},
        "min_percent_Saturation": {"type": "DOUBLE", "nullable": True, "description": "Min % saturation"},
        "V2C": {"type": "DOUBLE", "nullable": True, "description": "V2C"},
        "VFDS_NGV": {"type": "DOUBLE", "nullable": True, "description": "VFDS NGV"},
        "V2C_VCC": {"type": "DOUBLE", "nullable": True, "description": "V2C VCC"},
        "NGE_DC": {"type": "DOUBLE", "nullable": True, "description": "NGE DC"},
        "NGE": {"type": "DOUBLE", "nullable": True, "description": "NGE"},
        "NGV_m": {"type": "DOUBLE", "nullable": True, "description": "NGV m"},
        "NGA_rm": {"type": "DOUBLE", "nullable": True, "description": "NGA rm"},
        "NGV_rv": {"type": "DOUBLE", "nullable": True, "description": "NGV rv"},
        "NGA_rv": {"type": "DOUBLE", "nullable": True, "description": "NGA rv"},
        "NGV_ewm": {"type": "DOUBLE", "nullable": True, "description": "NGV ewm"},
        "NGA_ewm": {"type": "DOUBLE", "nullable": True, "description": "NGA ewm"},
        "A1F0_DC": {"type": "DOUBLE", "nullable": True, "description": "A1F0 DC"},
        "A1F0_freq_DC": {"type": "DOUBLE", "nullable": True, "description": "A1F0 freq DC"},
        "A2F0_DC": {"type": "DOUBLE", "nullable": True, "description": "A2F0 DC"},
        "A2F0_freq_DC": {"type": "DOUBLE", "nullable": True, "description": "A2F0 freq DC"},
        "A3F0_DC": {"type": "DOUBLE", "nullable": True, "description": "A3F0 DC"},
        "A3F0_freq_DC": {"type": "DOUBLE", "nullable": True, "description": "A3F0 freq DC"},
        "Energy_DS_Sum": {"type": "DOUBLE", "nullable": True, "description": "Energy DS Sum"},
        "JR_Energy": {"type": "DOUBLE", "nullable": True, "description": "JR Energy"},
        "A1F0_Energy": {"type": "DOUBLE", "nullable": True, "description": "A1F0 Energy"},
        "A2F0_energy": {"type": "DOUBLE", "nullable": True, "description": "A2F0 energy"},
        "A3F0_energy": {"type": "DOUBLE", "nullable": True, "description": "A3F0 energy"},
        "Fric_energy": {"type": "DOUBLE", "nullable": True, "description": "Fric energy"},
        "EnergyFFT": {"type": "DOUBLE", "nullable": True, "description": "Energy FFT"},
        "EnergyFFTv": {"type": "DOUBLE", "nullable": True, "description": "Energy FFTv"},
        "EnergyWPD1": {"type": "DOUBLE", "nullable": True, "description": "Energy WPD1"},
        "EnergyWPD2": {"type": "DOUBLE", "nullable": True, "description": "Energy WPD2"},
        "EnergyWPD3": {"type": "DOUBLE", "nullable": True, "description": "Energy WPD3"},
        "EnergyWPDApprox3": {"type": "DOUBLE", "nullable": True, "description": "Energy WPD Approx3"},
        "harmonics_energy_rms_DC": {"type": "DOUBLE", "nullable": True, "description": "Harmonics energy rms DC"},
        "harmonics_energy_rms_ngv": {"type": "DOUBLE", "nullable": True, "description": "Harmonics energy rms NGV"},
        "harmonics_amplitudes": {"type": "JSON", "nullable": True, "description": "Harmonics amplitudes (JSON)"},
        "harmonics_amplitudes_freq": {"type": "JSON", "nullable": True, "description": "Harmonics amplitudes freq (JSON)"},
        "percentage_lubrification": {"type": "DOUBLE", "nullable": True, "description": "% lubrification"},
        "percentage_Desalignement": {"type": "DOUBLE", "nullable": True, "description": "% désalignement"},
        "percentage_gear": {"type": "DOUBLE", "nullable": True, "description": "% engrenage"},
        "percentage_gear_8": {"type": "DOUBLE", "nullable": True, "description": "% engrenage 8"},
        "percentage_gear_23": {"type": "DOUBLE", "nullable": True, "description": "% engrenage 23"},
        "percentage_Turbulance_threshold": {"type": "DOUBLE", "nullable": True, "description": "% turbulence"},
        "V_Fds_percent": {"type": "DOUBLE", "nullable": True, "description": "V Fds %"},
        "A_Fds_percent": {"type": "DOUBLE", "nullable": True, "description": "A Fds %"},
        "Rolement_percentage": {"type": "DOUBLE", "nullable": True, "description": "% roulement"},
        "fault_1": {"type": "TINYINT", "nullable": True, "description": "Fault 1"},
        "fault_2": {"type": "TINYINT", "nullable": True, "description": "Fault 2"},
        "fault_3": {"type": "TINYINT", "nullable": True, "description": "Fault 3"},
        "fault_4": {"type": "TINYINT", "nullable": True, "description": "Fault 4"},
        "fault_5": {"type": "TINYINT", "nullable": True, "description": "Fault 5"},
        "fault_6": {"type": "TINYINT", "nullable": True, "description": "Fault 6"},
        "fault_8": {"type": "TINYINT", "nullable": True, "description": "Fault 8"},
        "fault_9": {"type": "TINYINT", "nullable": True, "description": "Fault 9"},
        "fault_10": {"type": "TINYINT", "nullable": True, "description": "Fault 10"},
        "fault_11": {"type": "TINYINT", "nullable": True, "description": "Fault 11"},
        "fault_14": {"type": "TINYINT", "nullable": True, "description": "Fault 14"},
        "fault_16": {"type": "TINYINT", "nullable": True, "description": "Fault 16"},
        "fault_17": {"type": "TINYINT", "nullable": True, "description": "Fault 17"},
        "fault_18": {"type": "TINYINT", "nullable": True, "description": "Fault 18"},
        "fault_19": {"type": "TINYINT", "nullable": True, "description": "Fault 19"},
        "fault_20": {"type": "TINYINT", "nullable": True, "description": "Fault 20"},
        "fault_21": {"type": "TINYINT", "nullable": True, "description": "Fault 21"},
        "fault_22": {"type": "TINYINT", "nullable": True, "description": "Fault 22"},
        "fault_23": {"type": "TINYINT", "nullable": True, "description": "Fault 23"},
        "fault_24": {"type": "TINYINT", "nullable": True, "description": "Fault 24"},
        "point_HI": {"type": "DOUBLE", "nullable": True, "description": "Point Health Index"},
        "sub_asset_HI": {"type": "DOUBLE", "nullable": True, "description": "Sub-asset Health Index"},
        "asset_HI": {"type": "DOUBLE", "nullable": True, "description": "Asset Health Index"},
        "severity_imbalance": {"type": "DOUBLE", "nullable": True, "description": "Sévérité déséquilibre"},
        "severity_misalignment": {"type": "DOUBLE", "nullable": True, "description": "Sévérité désalignement"},
        "severity_looseness": {"type": "DOUBLE", "nullable": True, "description": "Sévérité desserrage"},
        "severity_bearing": {"type": "DOUBLE", "nullable": True, "description": "Sévérité roulement"},
        "severity_gear": {"type": "DOUBLE", "nullable": True, "description": "Sévérité engrenage"},
        "Variance": {"type": "DOUBLE", "nullable": True, "description": "Variance"},
        "ClearanceFactor": {"type": "DOUBLE", "nullable": True, "description": "Clearance Factor"},
        "ImpulseFactor": {"type": "DOUBLE", "nullable": True, "description": "Impulse Factor"},
        "ShapeFactor": {"type": "DOUBLE", "nullable": True, "description": "Shape Factor"},
        "Skewness": {"type": "DOUBLE", "nullable": True, "description": "Skewness"},
        "Kurtosis_g": {"type": "DOUBLE", "nullable": True, "description": "Kurtosis g"},
        "CrestFactor_g": {"type": "DOUBLE", "nullable": True, "description": "Crest Factor g"},
        "Mean_g": {"type": "DOUBLE", "nullable": True, "description": "Mean g"},
        "Std_g": {"type": "DOUBLE", "nullable": True, "description": "Std g"},
        "LineIntegral": {"type": "DOUBLE", "nullable": True, "description": "Line Integral"},
        "shannon_entropy": {"type": "DOUBLE", "nullable": True, "description": "Shannon Entropy"},
        "PeakValueFFT": {"type": "DOUBLE", "nullable": True, "description": "Peak Value FFT"},
        "PeakValueFFTv": {"type": "DOUBLE", "nullable": True, "description": "Peak Value FFTv"},
        "Freq_defaut_Roulement": {"type": "DOUBLE", "nullable": True, "description": "Freq défaut roulement"},
        "frequency_spread_harmonics": {"type": "DOUBLE", "nullable": True, "description": "Frequency spread harmonics"},
        "mean_harmonics": {"type": "DOUBLE", "nullable": True, "description": "Mean harmonics"},
        "med_harmonics": {"type": "DOUBLE", "nullable": True, "description": "Median harmonics"},
        "zero_crossings": {"type": "DOUBLE", "nullable": True, "description": "Zero crossings"},
        "Fbw": {"type": "DOUBLE", "nullable": True, "description": "Fbw"},
        "real_fbw": {"type": "DOUBLE", "nullable": True, "description": "Real Fbw"},
        "real_amp_fbw": {"type": "DOUBLE", "nullable": True, "description": "Real amp Fbw"},
        "meanSpect_vel": {"type": "DOUBLE", "nullable": True, "description": "Mean Spectre vitesse"},
        "varSpect_vel": {"type": "DOUBLE", "nullable": True, "description": "Var Spectre vitesse"},
        "SkewnessSpect_vel": {"type": "DOUBLE", "nullable": True, "description": "Skewness Spectre vitesse"},
        "KurtosisSpect_vel": {"type": "DOUBLE", "nullable": True, "description": "Kurtosis Spectre vitesse"},
        "frequencyCenter_vel": {"type": "DOUBLE", "nullable": True, "description": "Frequency Center vitesse"},
        "FreqDeviation_vel": {"type": "DOUBLE", "nullable": True, "description": "Freq Deviation vitesse"},
        "RmsFreq_vel": {"type": "DOUBLE", "nullable": True, "description": "RMS Freq vitesse"},
        "FreqSpread_vel": {"type": "DOUBLE", "nullable": True, "description": "Freq Spread vitesse"},
        "FreqVar_vel": {"type": "DOUBLE", "nullable": True, "description": "Freq Var vitesse"},
        "FreqStd_vel": {"type": "DOUBLE", "nullable": True, "description": "Freq Std vitesse"},
        "FreqSkewness_vel": {"type": "DOUBLE", "nullable": True, "description": "Freq Skewness vitesse"},
        "FreqKurtosis_vel": {"type": "DOUBLE", "nullable": True, "description": "Freq Kurtosis vitesse"},
        "meanSpect_acc": {"type": "DOUBLE", "nullable": True, "description": "Mean Spectre accélération"},
        "varSpect_acc": {"type": "DOUBLE", "nullable": True, "description": "Var Spectre accélération"},
        "SkewnessSpect_acc": {"type": "DOUBLE", "nullable": True, "description": "Skewness Spectre accélération"},
        "KurtosisSpect_acc": {"type": "DOUBLE", "nullable": True, "description": "Kurtosis Spectre accélération"},
        "frequencyCenter_acc": {"type": "DOUBLE", "nullable": True, "description": "Frequency Center accélération"},
        "FreqDeviation_acc": {"type": "DOUBLE", "nullable": True, "description": "Freq Deviation accélération"},
        "RmsFreq_acc": {"type": "DOUBLE", "nullable": True, "description": "RMS Freq accélération"},
        "FreqSpread_acc": {"type": "DOUBLE", "nullable": True, "description": "Freq Spread accélération"},
        "FreqVar_acc": {"type": "DOUBLE", "nullable": True, "description": "Freq Var accélération"},
        "FreqStd_acc": {"type": "DOUBLE", "nullable": True, "description": "Freq Std accélération"},
        "FreqSkewness_acc": {"type": "DOUBLE", "nullable": True, "description": "Freq Skewness accélération"},
        "FreqKurtosis_acc": {"type": "DOUBLE", "nullable": True, "description": "Freq Kurtosis accélération"},
        "A_Fds": {"type": "DOUBLE", "nullable": True, "description": "A Fds"},
        "AF0": {"type": "DOUBLE", "nullable": True, "description": "AF0"},
        "AF0_energy": {"type": "DOUBLE", "nullable": True, "description": "AF0 energy"},
        "FF0": {"type": "DOUBLE", "nullable": True, "description": "FF0"},
        "CF0": {"type": "DOUBLE", "nullable": True, "description": "CF0"},
        "CF0_energy": {"type": "DOUBLE", "nullable": True, "description": "CF0 energy"},
        "Amps_pics_Turbulance_threshold": {"type": "JSON", "nullable": True, "description": "Amps pics turbulence (JSON)"},
        "Freqs_pics_Turbulance_threshold": {"type": "JSON", "nullable": True, "description": "Freqs pics turbulence (JSON)"},
        "pic_fault_energy_BW": {"type": "DOUBLE", "nullable": True, "description": "Pic fault energy BW"},
        "harmonics_fp_freq_BW": {"type": "JSON", "nullable": True, "description": "Harmonics fp freq BW (JSON)"},
        "harmonics_fp_amp_BW": {"type": "JSON", "nullable": True, "description": "Harmonics fp amp BW (JSON)"},
        "sum_10_harmonics_BW": {"type": "DOUBLE", "nullable": True, "description": "Sum 10 harmonics BW"},
        "sum_10_harmonics_percentage_BW": {"type": "DOUBLE", "nullable": True, "description": "Sum 10 harmonics % BW"},
        "rms_10_harmonic_percentage_BW": {"type": "DOUBLE", "nullable": True, "description": "RMS 10 harmonic % BW"},
        "RMS_totalHarmonics_sumMax_percentage_BW": {"type": "DOUBLE", "nullable": True, "description": "RMS total harmonics sum max % BW"},
        "top_4_harmonics_rms_percent_BW": {"type": "DOUBLE", "nullable": True, "description": "Top 4 harmonics RMS % BW"},
        "first_3_harmonics_rms_percent_BW": {"type": "DOUBLE", "nullable": True, "description": "First 3 harmonics RMS % BW"},
        "total_harmonix_percent_BW": {"type": "DOUBLE", "nullable": True, "description": "Total harmonics % BW"},
        "max_amplitude_is_harmonic_BW": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude is harmonic BW"},
        "rms_10_harmonic": {"type": "DOUBLE", "nullable": True, "description": "RMS 10 harmonic"},
        "rms_10_harmonic_new_ngv": {"type": "DOUBLE", "nullable": True, "description": "RMS 10 harmonic new NGV"},
        "rms_combined_method1": {"type": "DOUBLE", "nullable": True, "description": "RMS combined method 1"},
        "rms_combined_method2": {"type": "DOUBLE", "nullable": True, "description": "RMS combined method 2"},
        "peaks_indices": {"type": "JSON", "nullable": True, "description": "Peaks indices (JSON)"},
        "properties": {"type": "JSON", "nullable": True, "description": "Properties (JSON)"},
        "Count": {"type": "DOUBLE", "nullable": True, "description": "Count"},
        "Friction": {"type": "DOUBLE", "nullable": True, "description": "Friction"},
        "rpm_in": {"type": "DOUBLE", "nullable": True, "description": "RPM in"},
        "max_amplitude_10_vel": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude 10 vel"},
        "max_amplitude_freq_10_vel": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude freq 10 vel"},
        "max_amplitude_vel_energy": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude vel energy"},
        "max_amplitude_vel_energy_DC": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude vel energy DC"},
        "max_amplitude_accx_DC": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude accx DC"},
        "max_amplitude_is_harmonic": {"type": "TINYINT", "nullable": True, "description": "Max amplitude is harmonic"},
        "max_amplitude_acc_ener": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude acc energy"},
        "max_amplitude_vel_ener": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude vel energy"},
        "max_amplitude_env_freq": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude env freq"},
        "second_harmonics_peak_freq": {"type": "DOUBLE", "nullable": True, "description": "Second highest peak freq"},
        "harmonics_amplitudes_fr": {"type": "JSON", "nullable": True, "description": "Harmonics amplitudes freq (JSON)"},
        "rms_PBJO_F": {"type": "DOUBLE", "nullable": True, "description": "RMS PBJO F"},
        "date_acquisition": {"type": "TIMESTAMP", "nullable": True, "description": "Date acquisition"},
        "frequence_acquisition_m": {"type": "DOUBLE", "nullable": True, "description": "Fréquence acquisition"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "NGV_rv": {"type": "DOUBLE", "nullable": True, "description": "NGV rv"},
        "NGA_rv": {"type": "DOUBLE", "nullable": True, "description": "NGA rv"},
        "NGV_ewm": {"type": "DOUBLE", "nullable": True, "description": "NGV ewm"},
        "NGA_ewm": {"type": "DOUBLE", "nullable": True, "description": "NGA ewm"},
        "max_amplitude_acc_ener_DC": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude acc energy DC"},
        "harmonics_amplitudes_freq_DC": {"type": "JSON", "nullable": True, "description": "Harmonics amplitudes freq DC (JSON)"},
        "percentage_gear_8": {"type": "DOUBLE", "nullable": True, "description": "% engrenage 8"},
        "percentage_gear_23": {"type": "DOUBLE", "nullable": True, "description": "% engrenage 23"},
        "AF0": {"type": "DOUBLE", "nullable": True, "description": "AF0"},
        "AF0_energy": {"type": "DOUBLE", "nullable": True, "description": "AF0 energy"},
        "CF0": {"type": "DOUBLE", "nullable": True, "description": "CF0"},
        "CF0_energy": {"type": "DOUBLE", "nullable": True, "description": "CF0 energy"},
        "percentage_Turbulance_threshold": {"type": "DOUBLE", "nullable": True, "description": "% turbulence threshold"},
        "Amps_pics_Turbulance_threshold": {"type": "JSON", "nullable": True, "description": "Amps pics turbulence threshold (JSON)"},
        "Freqs_pics_Turbulance_threshold": {"type": "JSON", "nullable": True, "description": "Freqs pics turbulence threshold (JSON)"},
        "Fbw": {"type": "DOUBLE", "nullable": True, "description": "Fbw"},
        "real_fbw": {"type": "DOUBLE", "nullable": True, "description": "Real Fbw"},
        "real_amp_fbw": {"type": "DOUBLE", "nullable": True, "description": "Real amp Fbw"},
        "pic_fault_energy_BW": {"type": "DOUBLE", "nullable": True, "description": "Pic fault energy BW"},
        "harmonics_fp_freq_BW": {"type": "JSON", "nullable": True, "description": "Harmonics fp freq BW (JSON)"},
        "harmonics_fp_amp_BW": {"type": "JSON", "nullable": True, "description": "Harmonics fp amp BW (JSON)"},
        "sum_10_harmonics_BW": {"type": "DOUBLE", "nullable": True, "description": "Sum 10 harmonics BW"},
        "sum_10_harmonics_percentage_BW": {"type": "DOUBLE", "nullable": True, "description": "Sum 10 harmonics percentage BW"},
        "rms_10_harmonic_percentage_BW": {"type": "DOUBLE", "nullable": True, "description": "RMS 10 harmonic percentage BW"},
        "RMS_totalHarmonics_sumMax_percentage_BW": {"type": "DOUBLE", "nullable": True, "description": "RMS total Harmonics sumMax percentage BW"},
        "top_4_harmonics_rms_percent_BW": {"type": "DOUBLE", "nullable": True, "description": "Top 4 harmonics RMS percent BW"},
        "first_3_harmonics_rms_percent_BW": {"type": "DOUBLE", "nullable": True, "description": "First 3 harmonics RMS percent BW"},
        "total_harmonix_percent_BW": {"type": "DOUBLE", "nullable": True, "description": "Total harmonix percent BW"},
        "max_amplitude_is_harmonic_BW": {"type": "DOUBLE", "nullable": True, "description": "Max amplitude is harmonic BW"},
        "Mean_g": {"type": "DOUBLE", "nullable": True, "description": "Mean g"},
        "Std_g": {"type": "DOUBLE", "nullable": True, "description": "Std g"},
        "Kurtosis_g": {"type": "DOUBLE", "nullable": True, "description": "Kurtosis g"},
        "CrestFactor_g": {"type": "DOUBLE", "nullable": True, "description": "CrestFactor g"},
        "meanSpect_vel": {"type": "DOUBLE", "nullable": True, "description": "meanSpect vel"},
        "varSpect_vel": {"type": "DOUBLE", "nullable": True, "description": "varSpect vel"},
        "SkewnessSpect_vel": {"type": "DOUBLE", "nullable": True, "description": "SkewnessSpect vel"},
        "KurtosisSpect_vel": {"type": "DOUBLE", "nullable": True, "description": "KurtosisSpect vel"},
        "frequencyCenter_vel": {"type": "DOUBLE", "nullable": True, "description": "frequencyCenter vel"},
        "FreqDeviation_vel": {"type": "DOUBLE", "nullable": True, "description": "FreqDeviation vel"},
        "RmsFreq_vel": {"type": "DOUBLE", "nullable": True, "description": "RmsFreq vel"},
        "FreqSpread_vel": {"type": "DOUBLE", "nullable": True, "description": "FreqSpread vel"},
        "FreqVar_vel": {"type": "DOUBLE", "nullable": True, "description": "FreqVar vel"},
        "FreqStd_vel": {"type": "DOUBLE", "nullable": True, "description": "FreqStd vel"},
        "FreqSkewness_vel": {"type": "DOUBLE", "nullable": True, "description": "FreqSkewness vel"},
        "FreqKurtosis_vel": {"type": "DOUBLE", "nullable": True, "description": "FreqKurtosis vel"},
        "meanSpect_acc": {"type": "DOUBLE", "nullable": True, "description": "meanSpect acc"},
        "varSpect_acc": {"type": "DOUBLE", "nullable": True, "description": "varSpect acc"},
        "SkewnessSpect_acc": {"type": "DOUBLE", "nullable": True, "description": "SkewnessSpect acc"},
        "KurtosisSpect_acc": {"type": "DOUBLE", "nullable": True, "description": "KurtosisSpect acc"},
        "frequencyCenter_acc": {"type": "DOUBLE", "nullable": True, "description": "frequencyCenter acc"},
        "FreqDeviation_acc": {"type": "DOUBLE", "nullable": True, "description": "FreqDeviation acc"},
        "RmsFreq_acc": {"type": "DOUBLE", "nullable": True, "description": "RmsFreq acc"},
        "FreqSpread_acc": {"type": "DOUBLE", "nullable": True, "description": "FreqSpread acc"},
        "FreqVar_acc": {"type": "DOUBLE", "nullable": True, "description": "FreqVar acc"},
        "FreqStd_acc": {"type": "DOUBLE", "nullable": True, "description": "FreqStd acc"},
        "FreqSkewness_acc": {"type": "DOUBLE", "nullable": True, "description": "FreqSkewness acc"},
        "FreqKurtosis_acc": {"type": "DOUBLE", "nullable": True, "description": "FreqKurtosis acc"},
        "NGV_m": {"type": "DOUBLE", "nullable": True, "description": "NGV m"},
        "NGA_rm": {"type": "DOUBLE", "nullable": True, "description": "NGA rm"},
        "NGV_rv": {"type": "DOUBLE", "nullable": True, "description": "NGV rv"},
        "NGA_rv": {"type": "DOUBLE", "nullable": True, "description": "NGA rv"},
        "NGV_ewm": {"type": "DOUBLE", "nullable": True, "description": "NGV ewm"},
        "NGA_ewm": {"type": "DOUBLE", "nullable": True, "description": "NGA ewm"},
        "Count": {"type": "DOUBLE", "nullable": True, "description": "Count"},
        "point_HI": {"type": "DOUBLE", "nullable": True, "description": "point HI"},
        "sub_asset_HI": {"type": "DOUBLE", "nullable": True, "description": "sub_asset HI"},
        "asset_HI": {"type": "DOUBLE", "nullable": True, "description": "asset HI"},
        "fault_1": {"type": "TINYINT", "nullable": True, "description": "fault 1"},
        "fault_2": {"type": "TINYINT", "nullable": True, "description": "fault 2"},
        "fault_5": {"type": "TINYINT", "nullable": True, "description": "fault 5"},
        "fault_6": {"type": "TINYINT", "nullable": True, "description": "fault 6"},
        "fault_10": {"type": "TINYINT", "nullable": True, "description": "fault 10"},
        "fault_23": {"type": "TINYINT", "nullable": True, "description": "fault 23"},
        "fault_22": {"type": "TINYINT", "nullable": True, "description": "fault 22"},
        "fault_24": {"type": "TINYINT", "nullable": True, "description": "fault 24"},
        "Friction": {"type": "DOUBLE", "nullable": True, "description": "Friction"},
        "FF0": {"type": "DOUBLE", "nullable": True, "description": "FF0"},
        "Fric_energy": {"type": "DOUBLE", "nullable": True, "description": "Fric energy"},
        "rpm_in": {"type": "DOUBLE", "nullable": True, "description": "rpm in"},
        "severity_imbalance": {"type": "DOUBLE", "nullable": True, "description": "severity imbalance"},
        "severity_misalignment": {"type": "DOUBLE", "nullable": True, "description": "severity misalignment"},
        "severity_looseness": {"type": "DOUBLE", "nullable": True, "description": "severity looseness"},
        "severity_bearing": {"type": "DOUBLE", "nullable": True, "description": "severity bearing"},
        "severity_gear": {"type": "DOUBLE", "nullable": True, "description": "severity gear"},
    },
    "relationships": [
        {"table": "measurements", "type": "many-to-one", "on": "pdm_detection.measure_id = measurements.id"},
        {"table": "measurement_points", "type": "many-to-one", "on": "pdm_detection.point_id = measurement_points.id"},
        {"table": "assets", "type": "many-to-one", "on": "pdm_detection.subAsset_id = assets.id"},
        {"table": "assets", "type": "many-to-one", "on": "pdm_detection.parent_id = assets.id"},
    ],

    
}

# ═══════════════════════════════════════════════════════════════
# TABLE 24: email_histories (TOUS TENANTS) - 13 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_EMAIL_HISTORIES = {
    "name": "email_histories",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Historique des emails envoyés",
    "category": "utilisateurs",
    "used_in_objectifs": [85],
    "total_columns": 13,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "report_type": {"type": "VARCHAR", "nullable": True, "description": "Type de rapport"},
        "send_type": {"type": "ENUM", "nullable": True, "description": "Type d'envoi"},
        "to": {"type": "JSON", "nullable": True, "description": "Destinataires (JSON)"},
        "cc": {"type": "JSON", "nullable": True, "description": "CC (JSON)"},
        "status": {"type": "ENUM", "nullable": True, "description": "Statut ( MANUAL et AUTOMATIC)"},
        "generation_date": {"type": "TIMESTAMP", "nullable": True, "description": "Date de génération"},
        "send_date": {"type": "TIMESTAMP", "nullable": True, "description": "Date d'envoi"},
        "error_message": {"type": "TEXT", "nullable": True, "description": "Message d'erreur"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "automated_emails", "type": "many-to-one", "on": "email_histories.automated_email_id = automated_emails.id"},
        {"table": "users", "type": "many-to-one", "on": "email_histories.user_id = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 25: email_notif_config (TOUS TENANTS) - 13 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_EMAIL_NOTIF_CONFIG = {
    "name": "email_notif_config",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Configuration des notifications email",
    "category": "utilisateurs",
    "used_in_objectifs": [86],
    "total_columns": 13,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "entities_ids": {"type": "JSON", "nullable": True, "description": "IDs des entités (JSON)"},
        "assets_ids": {"type": "JSON", "nullable": True, "description": "IDs des équipements (JSON)"},
        "status_target": {"type": "JSON", "nullable": True, "description": "Statuts cibles (JSON)"},
        "email_limit": {"type": "INT", "nullable": True, "description": "Limite d'emails"},
        "email_used": {"type": "INT", "nullable": True, "description": "Emails utilisés"},
        "status": {"type": "TINYINT", "nullable": True, "description": "Statut"},
        "reminder": {"type": "INT", "nullable": True, "description": "Rappel (jours)"},
        "last_notification_time": {"type": "TIMESTAMP", "nullable": True, "description": "Dernière notification"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "created_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Créateur"},
    },
    "relationships": [
        {"table": "users", "type": "many-to-one", "on": "email_notif_config.created_by = users.id", "database": "i_sense_v3_devenv_db"},
        {"table": "user_notif_config", "type": "one-to-many", "on": "email_notif_config.id = user_notif_config.email_notif_config_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 26: sms_notif_config (TOUS TENANTS) - 13 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_SMS_NOTIF_CONFIG = {
    "name": "sms_notif_config",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Configuration des notifications SMS",
    "category": "utilisateurs",
    "used_in_objectifs": [87],
    "total_columns": 13,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "entities_ids": {"type": "JSON", "nullable": True, "description": "IDs des entités (JSON)"},
        "assets_ids": {"type": "JSON", "nullable": True, "description": "IDs des équipements (JSON)"},
        "status_target": {"type": "JSON", "nullable": True, "description": "Statuts cibles (JSON)"},
        "sms_limit": {"type": "INT", "nullable": True, "description": "Limite de SMS"},
        "sms_used": {"type": "INT", "nullable": True, "description": "SMS utilisés"},
        "status": {"type": "TINYINT", "nullable": True, "description": "Statut"},
        "reminder": {"type": "INT", "nullable": True, "description": "Rappel (jours)"},
        "last_notification_time": {"type": "TIMESTAMP", "nullable": True, "description": "Dernière notification"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "created_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Créateur"},
    },
    "relationships": [
        {"table": "users", "type": "many-to-one", "on": "sms_notif_config.created_by = users.id", "database": "i_sense_v3_devenv_db"},
        {"table": "user_notif_config", "type": "one-to-many", "on": "sms_notif_config.id = user_notif_config.sms_notif_config_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 27: user_notif_config (TOUS TENANTS) - 10 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_USER_NOTIF_CONFIG = {
    "name": "user_notif_config",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Configuration des notifications utilisateur",
    "category": "utilisateurs",
    "used_in_objectifs": [84],
    "total_columns": 10,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "user_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Utilisateur concerné"},
        "sms_notif_config_id": {"type": "BIGINT", "nullable": True, "foreign_key": "sms_notif_config.id", "description": "Config SMS"},
        "consumed_sms": {"type": "INT", "nullable": True, "description": "SMS consommés"},
        "email_notif_config_id": {"type": "BIGINT", "nullable": True, "foreign_key": "email_notif_config.id", "description": "Config email"},
        "consumed_email": {"type": "INT", "nullable": True, "description": "Emails consommés"},
        "status": {"type": "TINYINT", "nullable": True, "description": "Statut (0, 1)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "users", "type": "many-to-one", "on": "user_notif_config.user_id = users.id", "database": "i_sense_v3_devenv_db"},
        {"table": "sms_notif_config", "type": "many-to-one", "on": "user_notif_config.sms_notif_config_id = sms_notif_config.id"},
        {"table": "email_notif_config", "type": "many-to-one", "on": "user_notif_config.email_notif_config_id = email_notif_config.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 28: automated_emails (TOUS TENANTS) - 11 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_AUTOMATED_EMAILS = {
    "name": "automated_emails",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Emails automatisés configurés",
    "category": "utilisateurs",
    "used_in_objectifs": [88],
    "total_columns": 11,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "label": {"type": "VARCHAR", "nullable": True, "description": "Libellé"},
        "type": {"type": "ENUM", "nullable": True, "description": "Type"},
        "to": {"type": "JSON", "nullable": True, "description": "Destinataires (JSON)"},
        "cc": {"type": "JSON", "nullable": True, "description": "CC (JSON)"},
        "hours": {"type": "JSON", "nullable": True, "description": "Heures (JSON)"},
        "entities": {"type": "JSON", "nullable": True, "description": "Entités (JSON)"},
        "user_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Utilisateur propriétaire"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "users", "type": "many-to-one", "on": "automated_emails.user_id = users.id", "database": "i_sense_v3_devenv_db"},
        {"table": "email_histories", "type": "one-to-many", "on": "automated_emails.id = email_histories.automated_email_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 29: entity_user (TOUS TENANTS) - 4 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_ENTITY_USER = {
    "name": "entity_user",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Liaison entités-utilisateurs",
    "category": "entreprises",
    "used_in_objectifs": [89],
    "total_columns": 4,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "entity_id": {"type": "INT", "nullable": True, "foreign_key": "entities.id", "description": "Entité"},
        "user_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Utilisateur"},
    },
    "relationships": [
        {"table": "entities", "type": "many-to-one", "on": "entity_user.entity_id = entities.id"},
        {"table": "users", "type": "many-to-one", "on": "entity_user.user_id = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 30: tarifs (TOUS TENANTS) - 11 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_TARIFS = {
    "name": "tarifs",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Tarifs",
    "category": "entreprises",
    "used_in_objectifs": [68, 96],
    "total_columns": 11,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "identifiant": {"type": "VARCHAR", "nullable": True, "description": "Identifiant"},
        "type": {"type": "ENUM", "nullable": True, "description": "Type"},
        "heure_debut": {"type": "TIME", "nullable": True, "description": "Heure début"},
        "heure_fin": {"type": "TIME", "nullable": True, "description": "Heure fin"},
        "cost": {"type": "DOUBLE", "nullable": True, "description": "Coût"},
        "type_cost": {"type": "ENUM", "nullable": True, "description": "Type de coût"},
        "company_id": {"type": "INT", "nullable": True, "foreign_key": "companies.id", "description": "Entreprise"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "companies", "type": "many-to-one", "on": "tarifs.company_id = companies.id", "database": "i_sense_v3_devenv_db"},
        {"table": "tarif_measures", "type": "one-to-many", "on": "tarifs.id = tarif_measures.tarif_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 31: tarif_measures (TOUS TENANTS) - 9 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_TARIF_MEASURES = {
    "name": "tarif_measures",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Liaison tarifs-mesures",
    "category": "entreprises",
    "used_in_objectifs": [68, 96],
    "total_columns": 9,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "measure_id": {"type": "BIGINT", "nullable": True, "foreign_key": "measures.id", "description": "Mesure"},
        "tarif_id": {"type": "BIGINT", "nullable": True, "foreign_key": "tarifs.id", "description": "Tarif"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "created_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Créateur"},
        "updated_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Mise à jour par"},
        "validated_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Validé par"},
    },
    "relationships": [
        {"table": "measures", "type": "many-to-one", "on": "tarif_measures.measure_id = measures.id"},
        {"table": "tarifs", "type": "many-to-one", "on": "tarif_measures.tarif_id = tarifs.id"},
        {"table": "users", "type": "many-to-one", "on": "tarif_measures.created_by = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 32: operations (TOUS TENANTS) - 6 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_OPERATIONS = {
    "name": "operations",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Opérations",
    "category": "maintenance",
    "used_in_objectifs": [28, 49],
    "total_columns": 6,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "locked": {"type": "TINYINT", "nullable": True, "description": "Verrouillé (0 = Non, 1 = Oui)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "interventions", "type": "one-to-many", "on": "operations.id = interventions.operation_id"},
        {"table": "recommendation_operations", "type": "one-to-many", "on": "operations.id = recommendation_operations.operation_id"},
        {"table": "family_fault_operations", "type": "one-to-many", "on": "operations.id = family_fault_operations.operation_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 33: family_fault_operations (TOUS TENANTS) - 6 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_FAMILY_FAULT_OPERATIONS = {
    "name": "family_fault_operations",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Liaison familles-défauts-opérations",
    "category": "maintenance",
    "used_in_objectifs": [28],
    "total_columns": 6,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "family_fault_id": {"type": "INT", "nullable": True, "foreign_key": "family_fault.id", "description": "Family fault"},
        "operation_id": {"type": "INT", "nullable": True, "foreign_key": "operations.id", "description": "Opération"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "family_fault", "type": "many-to-one", "on": "family_fault_operations.family_fault_id = family_fault.id", "database": "v3_tenant_Site_Safi"},
        {"table": "operations", "type": "many-to-one", "on": "family_fault_operations.operation_id = operations.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 34: diagrams (TOUS TENANTS) - 8 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_DIAGRAMS = {
    "name": "diagrams",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Diagrammes",
    "category": "equipements",
    "used_in_objectifs": list(range(1, 16)),
    "total_columns": 8,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "path": {"type": "VARCHAR", "nullable": True, "description": "Chemin"},
        "family_id": {"type": "INT", "nullable": True, "foreign_key": "families.id", "description": "Famille"},
        "locked": {"type": "TINYINT", "nullable": True, "description": "Verrouillé (0 = Non, 1 = Oui)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "families", "type": "many-to-one", "on": "diagrams.family_id = families.id"},
        {"table": "assets", "type": "one-to-many", "on": "diagrams.id = assets.diagram_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 35: asset_classes (TOUS TENANTS) - 7 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_ASSET_CLASSES = {
    "name": "asset_classes",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Classes d'équipements",
    "category": "equipements",
    "used_in_objectifs": list(range(1, 16)),
    "total_columns": 7,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "duration": {"type": "INT", "nullable": True, "description": "Durée"},
        "locked": {"type": "TINYINT", "nullable": True, "description": "Verrouillé (0 = Non, 1 = Oui)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
    },
    "relationships": [
        {"table": "assets", "type": "one-to-many", "on": "asset_classes.id = assets.class_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLES UNIQUES SAFI (13 tables)
# ═══════════════════════════════════════════════════════════════

# TABLE 36: clients (v3_tenant_Site_Safi ONLY) - 19 colonnes
TABLE_CLIENTS = {
    "name": "clients",
    "databases": ["v3_tenant_Site_Safi"],
    "table_type": "unique_safi",
    "description": "Clients (facturation)",
    "category": "entreprises",
    "used_in_objectifs": [92, 94, 95],
    "total_columns": 19,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "address": {"type": "VARCHAR", "nullable": True, "description": "Adresse"},
        "phone": {"type": "VARCHAR", "nullable": True, "description": "Téléphone"},
        "email": {"type": "VARCHAR", "nullable": True, "description": "Email"},
        "city": {"type": "VARCHAR", "nullable": True, "description": "Ville"},
        "country": {"type": "VARCHAR", "nullable": True, "description": "Pays"},
        "IF": {"type": "VARCHAR", "nullable": True, "description": "IF"},
        "R_C": {"type": "VARCHAR", "nullable": True, "description": "RC"},
        "I_C_E": {"type": "VARCHAR", "nullable": True, "description": "ICE"},
        "C_N_S_S": {"type": "VARCHAR", "nullable": True, "description": "CNSS"},
        "C_I_N": {"type": "VARCHAR", "nullable": True, "description": "CIN"},
        "profile_image": {"type": "VARCHAR", "nullable": True, "description": "Image"},
        "C_I_N_image": {"type": "VARCHAR", "nullable": True, "description": "Image CIN"},
        "credit_limit": {"type": "DOUBLE", "nullable": True, "description": "Limite crédit"},
        "total_due_amount": {"type": "DOUBLE", "nullable": True, "description": "Montant dû"},
        "created_by": {"type": "BIGINT", "nullable": True, "foreign_key": "users.id", "description": "Créateur"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
    },
    "relationships": [
        {"table": "factures", "type": "one-to-many", "on": "clients.id = factures.client_id"},
        {"table": "users", "type": "many-to-one", "on": "clients.created_by = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# TABLE 37: factures (v3_tenant_Site_Safi ONLY) - 11 colonnes
TABLE_FACTURES = {
    "name": "factures",
    "databases": ["v3_tenant_Site_Safi"],
    "table_type": "unique_safi",
    "description": "Factures",
    "category": "entreprises",
    "used_in_objectifs": [94, 95, 99],
    "total_columns": 11,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "sale_id": {"type": "BIGINT", "nullable": True, "description": "Vente"},
        "purchase_id": {"type": "BIGINT", "nullable": True, "description": "Achat"},
        "transfer_id": {"type": "BIGINT", "nullable": True, "description": "Transfert"},
        "client_id": {"type": "BIGINT", "nullable": True, "foreign_key": "clients.id", "description": "Client"},
        "fournisseur_id": {"type": "BIGINT", "nullable": True, "foreign_key": "fournisseurs.id", "description": "Fournisseur"},
        "date": {"type": "DATETIME", "nullable": True, "description": "Date"},
        "total_amount": {"type": "DOUBLE", "nullable": True, "description": "Montant total"},
        "details": {"type": "JSON", "nullable": True, "description": "Détails (JSON)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
    },
    "relationships": [
        {"table": "clients", "type": "many-to-one", "on": "factures.client_id = clients.id"},
        {"table": "fournisseurs", "type": "many-to-one", "on": "factures.fournisseur_id = fournisseurs.id"},
    ],
}

# TABLE 38: fournisseurs (v3_tenant_Site_Safi ONLY) - 18 colonnes
TABLE_FOURNISSEURS = {
    "name": "fournisseurs",
    "databases": ["v3_tenant_Site_Safi"],
    "table_type": "unique_safi",
    "description": "Fournisseurs",
    "category": "entreprises",
    "used_in_objectifs": [93],
    "total_columns": 18,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom"},
        "address": {"type": "VARCHAR", "nullable": True, "description": "Adresse"},
        "phone": {"type": "VARCHAR", "nullable": True, "description": "Téléphone"},
        "email": {"type": "VARCHAR", "nullable": True, "description": "Email"},
        "city": {"type": "VARCHAR", "nullable": True, "description": "Ville"},
        "country": {"type": "VARCHAR", "nullable": True, "description": "Pays"},
        "IF": {"type": "VARCHAR", "nullable": True, "description": "IF"},
        "R_C": {"type": "VARCHAR", "nullable": True, "description": "RC"},
        "I_C_E": {"type": "VARCHAR", "nullable": True, "description": "ICE"},
        "C_N_S_S": {"type": "VARCHAR", "nullable": True, "description": "CNSS"},
        "C_I_N": {"type": "VARCHAR", "nullable": True, "description": "CIN"},
        "profile_image": {"type": "VARCHAR", "nullable": True, "description": "Image"},
        "C_I_N_image": {"type": "VARCHAR", "nullable": True, "description": "Image CIN"},
        "created_by": {"type": "BIGINT", "nullable": True, "foreign_key": "users.id", "description": "Créateur"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
    },
    "relationships": [
        {"table": "factures", "type": "one-to-many", "on": "fournisseurs.id = factures.fournisseur_id"},
        {"table": "users", "type": "many-to-one", "on": "fournisseurs.created_by = users.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# TABLE 39: burden_details (v3_tenant_Site_Safi ONLY) - 7 colonnes
TABLE_BURDEN_DETAILS = {
    "name": "burden_details",
    "databases": ["v3_tenant_Site_Safi"],
    "table_type": "unique_safi",
    "description": "Détails des charges/projets",
    "category": "entreprises",
    "used_in_objectifs": [98],
    "total_columns": 7,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "product_id": {"type": "BIGINT", "nullable": True, "foreign_key": "products.id", "description": "Produit"},
        "size": {"type": "VARCHAR", "nullable": True, "description": "Taille"},
        "initial_quantity": {"type": "INT", "nullable": True, "description": "Quantité initiale"},
        "remaining_quantity": {"type": "INT", "nullable": True, "description": "Quantité restante"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
    },
    "relationships": [
        {"table": "products", "type": "many-to-one", "on": "burden_details.product_id = products.id", "database": "i_sense_v3_devenv_db"},
    ],
}

# TABLE 40: family_fault (v3_tenant_Site_Safi ONLY) - 6 colonnes
TABLE_FAMILY_FAULT = {
    "name": "family_fault",
    "databases": ["v3_tenant_Site_Safi"],
    "table_type": "unique_safi",
    "description": "Liaison familles-défauts",
    "category": "defauts",
    "used_in_objectifs": list(range(16, 31)) + list(range(41, 51)),
    "total_columns": 6,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression"},
        "family_id": {"type": "INT", "nullable": True, "foreign_key": "families.id", "description": "Famille"},
        "fault_id": {"type": "INT", "nullable": True, "foreign_key": "faults.id", "description": "Défaut"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date mise à jour"},
    },
    "relationships": [
        {"table": "families", "type": "many-to-one", "on": "family_fault.family_id = families.id"},
        {"table": "faults", "type": "many-to-one", "on": "family_fault.fault_id = faults.id"},
        {"table": "family_fault_operations", "type": "one-to-many", "on": "family_fault.id = family_fault_operations.family_fault_id"},
    ],
}
# ═══════════════════════════════════════════════════════════════
# TABLE: feature_measurement (TOUS TENANTS) - 15 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_FEATURE_MEASUREMENT = {
    "name": "feature_measurement",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Valeurs des features extraites pour chaque mesure",
    "category": "predictions",
    "used_in_objectifs": [65, 67, 69],
    "total_columns": 15,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique"},
        "value": {"type": "DOUBLE", "nullable": True, "description": "Valeur calculée de la feature"},
        "feature_id": {"type": "INT", "nullable": True, "foreign_key": "i_sense_v3_devenv_db.features.id", "description": "Feature associée (base globale)"},
        "measure_id": {"type": "INT", "nullable": True, "foreign_key": "measurements.id", "description": "Mesure associée"},
        "grandeur_id": {"type": "INT", "nullable": True, "foreign_key": "i_sense_v3_devenv_db.grandeurs.id", "description": "Grandeur associée (base globale)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "delta": {"type": "DOUBLE", "nullable": True, "description": "Variation / écart par rapport à une référence"},
        "group_id": {"type": "INT", "nullable": True, "foreign_key": "groups.id", "description": "Groupe de features"},
        "subasset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Sous-équipement"},
        "asset_parent_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement parent"},
        "status": {"type": "INT", "nullable": True, "description": "Statut de la mesure (0='shut down', 1='Normal' , 2='MID', 3='Moderate', 4='Undifined', 5='critical',-1='Unassigned')"},
        "acquisition_date": {"type": "DATETIME", "nullable": True, "description": "Date d'acquisition réelle"},
        "point_id": {"type": "INT", "nullable": True, "foreign_key": "measurement_points.id", "description": "Point de mesure"},
    },
    "relationships": [
        {"table": "i_sense_v3_devenv_db.features", "type": "many-to-one", "on": "feature_measurement.feature_id = features.id", "database": "i_sense_v3_devenv_db"},
        {"table": "measurements", "type": "many-to-one", "on": "feature_measurement.measure_id = measurements.id"},
        {"table": "i_sense_v3_devenv_db.grandeurs", "type": "many-to-one", "on": "feature_measurement.grandeur_id = grandeurs.id", "database": "i_sense_v3_devenv_db"},
        {"table": "groups", "type": "many-to-one", "on": "feature_measurement.group_id = groups.id"},
        {"table": "assets", "type": "many-to-one", "on": "feature_measurement.subasset_id = assets.id"},
        {"table": "assets", "type": "many-to-one", "on": "feature_measurement.asset_parent_id = assets.id"},
        {"table": "measurement_points", "type": "many-to-one", "on": "feature_measurement.point_id = measurement_points.id"},
    ],
}
# ═══════════════════════════════════════════════════════════════
# TABLE: point_position (TOUS TENANTS) - 9 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_POINT_POSITION = {
    "name": "point_position",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Position des points de mesure sur les diagrammes",
    "category": "visualisation",
    "used_in_objectifs": list(range(1, 16)),   # objectifs liés aux diagrammes et assets
    "total_columns": 9,
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la position"},
        "asset_id": {"type": "INT", "nullable": True, "foreign_key": "assets.id", "description": "Équipement associé"},
        "point_id": {"type": "INT", "nullable": True, "foreign_key": "measurement_points.id", "description": "Point de mesure"},
        "diagram_id": {"type": "INT", "nullable": True, "foreign_key": "diagrams.id", "description": "Diagramme associé"},
        "xAxis": {"type": "VARCHAR", "nullable": True, "description": "Coordonnée X (px, pourcentage, ou valeur relative)"},
        "yAxis": {"type": "VARCHAR", "nullable": True, "description": "Coordonnée Y"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    "relationships": [
        {"table": "assets", "type": "many-to-one", "on": "point_position.asset_id = assets.id"},
        {"table": "measurement_points", "type": "many-to-one", "on": "point_position.point_id = measurement_points.id"},
        {"table": "diagrams", "type": "many-to-one", "on": "point_position.diagram_id = diagrams.id"},
    ],
}
# ═══════════════════════════════════════════════════════════════
# TABLE: groups (TOUS TENANTS) - 6 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_GROUPS = {
    "name": "groups",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Groupes d'équipements ou logiques",
    "category": "organisation",
    "used_in_objectifs": [65, 67, 69],
    "total_columns": 6,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique du groupe"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom du groupe"},
        "locked": {"type": "TINYINT", "nullable": True, "description": "Verrouillé (0 = Non, 1 = Oui)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    "relationships": [
        {"table": "assets", "type": "one-to-many", "on": "groups.id = assets.group_id"},
        {"table": "feature_group", "type": "one-to-many", "on": "groups.id = feature_group.group_id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE: feature_group (TOUS TENANTS) - 8 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_FEATURE_GROUP = {
    "name": "feature_group",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Groupes de features ML (seuils warning/alarm par groupe)",
    "category": "predictions",
    "used_in_objectifs": [65, 67, 69, 74],
    "total_columns": 8,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique du groupe de features"},
        "warning": {"type": "DOUBLE", "nullable": True, "description": "Seuil d'alerte (warning)"},
        "alarm": {"type": "DOUBLE", "nullable": True, "description": "alarme "},
        "feature_id": {"type": "INT", "nullable": True, "foreign_key": "i_sense_v3_devenv_db.features.id", "description": "Feature associée (base globale)"},
        "group_id": {"type": "INT", "nullable": True, "foreign_key": "groups.id", "description": "Groupe logique associé (tenant)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    "relationships": [
        {"table": "i_sense_v3_devenv_db.features", "type": "many-to-one", "on": "feature_group.feature_id = features.id", "database": "i_sense_v3_devenv_db"},
        {"table": "groups", "type": "many-to-one", "on": "feature_group.group_id = groups.id"},
    ],
}
# ═══════════════════════════════════════════════════════════════
# TABLE: fault_operation (TOUS TENANTS) - 6 colonnes
# ═══════════════════════════════════════════════════════════════

TABLE_FAULT_OPERATION = {
    "name": "fault_operation",
    "databases": ALL_TENANT_DATABASES,
    "table_type": "common",
    "description": "Liaison entre les défauts (faults) et les opérations de maintenance (operations)",
    "category": "maintenance",
    "used_in_objectifs": [28, 49],  # à ajuster selon les besoins
    "total_columns": 6,
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la liaison"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "operation_id": {"type": "INT", "nullable": True, "foreign_key": "operations.id", "description": "Opération associée"},
        "fault_id": {"type": "INT", "nullable": True, "foreign_key": "faults.id", "description": "Défaut associé"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
    },
    "relationships": [
        {"table": "operations", "type": "many-to-one", "on": "fault_operation.operation_id = operations.id"},
        {"table": "faults", "type": "many-to-one", "on": "fault_operation.fault_id = faults.id"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TOUTES LES TABLES
# ═══════════════════════════════════════════════════════════════

ALL_TABLES = {
    "assets": TABLE_ASSETS,
    "asset_faults": TABLE_ASSET_FAULTS,
    "alarms": TABLE_ALARMS,
    "faults": TABLE_FAULTS,
    "families": TABLE_FAMILIES,
    "recommendations_v3": TABLE_RECOMMENDATIONS_V3,
    "recommendation_assets": TABLE_RECOMMENDATION_ASSETS,
    "recommendation_faults": TABLE_RECOMMENDATION_FAULTS,
    "recommendation_operations": TABLE_RECOMMENDATION_OPERATIONS,
    "interventions": TABLE_INTERVENTIONS,
    "checklists": TABLE_CHECKLISTS,
    "assignment_checklist": TABLE_ASSIGNMENT_CHECKLIST,
    "actions": TABLE_ACTIONS,
    "actions_fault": TABLE_ACTIONS_FAULT,
    "activity_log": TABLE_ACTIVITY_LOG,
    "measurements": TABLE_MEASUREMENTS,
    "measurement_points": TABLE_MEASUREMENT_POINTS,
    "measurement_signal": TABLE_MEASUREMENT_SIGNAL,
    "measurements_faults": TABLE_MEASUREMENTS_FAULTS,
    "vibox_diagnosis": TABLE_VIBOX_DIAGNOSIS,
    "vibox_diagnosis_item": TABLE_VIBOX_DIAGNOSIS_ITEM,
    "vibox_diagnosis_recommended_action": TABLE_VIBOX_DIAGNOSIS_RECOMMENDED_ACTION,
    "pdm_detection": TABLE_PDM_DETECTION,
    "email_histories": TABLE_EMAIL_HISTORIES,
    "email_notif_config": TABLE_EMAIL_NOTIF_CONFIG,
    "sms_notif_config": TABLE_SMS_NOTIF_CONFIG,
    "user_notif_config": TABLE_USER_NOTIF_CONFIG,
    "automated_emails": TABLE_AUTOMATED_EMAILS,
    "entity_user": TABLE_ENTITY_USER,
    "tarifs": TABLE_TARIFS,
    "tarif_measures": TABLE_TARIF_MEASURES,
    "operations": TABLE_OPERATIONS,
    "family_fault_operations": TABLE_FAMILY_FAULT_OPERATIONS,
    "diagrams": TABLE_DIAGRAMS,
    "asset_classes": TABLE_ASSET_CLASSES,
    "clients": TABLE_CLIENTS,
    "factures": TABLE_FACTURES,
    "fournisseurs": TABLE_FOURNISSEURS,
    "burden_details": TABLE_BURDEN_DETAILS,
    "family_fault": TABLE_FAMILY_FAULT,
    "feature_measurement": TABLE_FEATURE_MEASUREMENT,
    "point_position": TABLE_POINT_POSITION,
    "groups": TABLE_GROUPS,
    "feature_group": TABLE_FEATURE_GROUP,
    "fault_operation": TABLE_FAULT_OPERATION,

}

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def get_all_tables() -> dict:
    """Récupérer toutes les tables"""
    return ALL_TABLES

def get_table_schema(table_name: str, database: str = None) -> dict:
    """Récupérer le schéma d'une table spécifique"""
    table = ALL_TABLES.get(table_name, {})
    if database:
        databases = table.get("databases", [])
        if databases and database not in databases:
            return {}
    return table

def get_tables_by_database(database: str) -> dict:
    """Récupérer les tables d'une base de données"""
    result = {}
    for name, info in ALL_TABLES.items():
        databases = info.get("databases", [])
        if not databases or database in databases:
            result[name] = info
    return result

def get_common_tables() -> list:
    """Récupérer les tables communes à tous les tenants"""
    return COMMON_TABLES

def get_unique_tables_safi() -> list:
    """Récupérer les tables uniques à Safi"""
    return UNIQUE_TABLES_SAFI

def is_table_available(table_name: str, database: str) -> bool:
    """Vérifier si une table est disponible dans une base"""
    table = ALL_TABLES.get(table_name, {})
    databases = table.get("databases", [])
    if not databases:
        return True
    return database in databases

def get_total_columns() -> int:
    """Récupérer le nombre total de colonnes"""
    total = 0
    for table_info in ALL_TABLES.values():
        total += table_info.get("total_columns", 0)
    return total

# ═══════════════════════════════════════════════════════════════
# EXEMPLE D'UTILISATION
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" " * 15 + " SCHÉMA COMPLET - v3_tenant_* (40 TABLES)")
    print(" " * 20 + "ARCHITECTURE MULTI-TENANT")
    print("="*80)
    
    print(f"\n Total tenants: {DATABASE_INFO['total_tenants']}")
    for tenant in DATABASE_INFO['tenants']:
        print(f"   • {tenant}")
    
    print(f"\n Tables communes (TOUS tenants): {len(COMMON_TABLES)}")
    for table in COMMON_TABLES[:10]:
        print(f"   • {table}")
    if len(COMMON_TABLES) > 10:
        print(f"   ... et {len(COMMON_TABLES) - 10} autres")
    
    print(f"\n Tables uniques (v3_tenant_Site_Safi ONLY): {len(UNIQUE_TABLES_SAFI)}")
    for table in UNIQUE_TABLES_SAFI:
        print(f"   • {table}")
    
    print(f"\n Total colonnes: ~{get_total_columns()}+")
    
    print("\n" + "="*80)
    print(" " * 25 + " 40 TABLES DOCUMENTÉES")
    print("="*80 + "\n")