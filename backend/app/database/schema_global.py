# schema_global.py
"""
Schéma complet de la base i_sense_v3_devenv_db
15 tables essentielles avec TOUTES les colonnes, relations et métadonnées
Pour l'Agent NLP - Génération de requêtes SQL exactes
"""

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION DE LA BASE
# ═══════════════════════════════════════════════════════════════

DATABASE_INFO = {
    "name": "i_sense_v3_devenv_db",
    "type": "global",
    "description": "Base de données globale - Configuration, Users, Predictions, Features",
    "total_tables": 50,
    "essential_tables": 15,
    "total_columns": 136,
    "used_in_objectifs": [40, 65, 66, 67, 69, 71, 72, 73, 74, 75, 76, 77, 80, 81, 82, 83, 84, 89, 90, 91, 92, 93, 97, 100],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 1: users (21 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_USERS = {
    "name": "users",
    "description": "Utilisateurs du système (tous tenants confondus)",
    "category": "utilisateurs",
    "used_in_objectifs": [81, 82, 83, 84, 89],
    "total_columns": 21,
    
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de l'utilisateur"},
        "first_name": {"type": "VARCHAR", "nullable": True, "description": "Prénom"},
        "last_name": {"type": "VARCHAR", "nullable": True, "description": "Nom de famille"},
        "phone": {"type": "VARCHAR", "nullable": True, "description": "Téléphone"},
        "address": {"type": "VARCHAR", "nullable": True, "description": "Adresse"},
        "country": {"type": "VARCHAR", "nullable": True, "description": "Pays"},
        "active": {"type": "TINYINT", "nullable": False, "default": 1, "description": "Actif (0=non, 1=oui)"},
        "email": {"type": "VARCHAR", "nullable": False, "unique": True, "description": "Email (identifiant)"},
        "email_verified_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date vérification email"},
        "password": {"type": "VARCHAR", "nullable": False, "description": "Mot de passe (hashé)"},
        "fcm_token": {"type": "VARCHAR", "nullable": True, "description": "Token notifications push"},
        "last_connection": {"type": "DATE", "nullable": True, "description": "Dernière connexion"},
        "remember_token": {"type": "VARCHAR", "nullable": True, "description": "Token de session"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "start_date": {"type": "DATE", "nullable": True, "description": "Date de début (contrat)"},
        "end_date": {"type": "DATE", "nullable": True, "description": "Date de fin (contrat)"},
        "parent_id": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "ID du parent (hiérarchie)"},
        "is_oms_user": {"type": "TINYINT", "nullable": True, "description": "Utilisateur OMS (0/1)"},
        "last_seen_version_id": {"type": "BIGINT", "nullable": True, "description": "Dernière version vue"},
    },
    
    "relationships": [
        {"table": "user_company", "type": "one-to-many", "on": "users.id = user_company.user_id"},
        {"table": "notifications", "type": "one-to-many", "on": "users.id = notifications.notifiable_id", "condition": "notifications.notifiable_type = 'App\\\\Models\\\\User'"},
        {"table": "entity_user", "type": "one-to-many", "on": "users.id = entity_user.user_id", "database": "v3_tenant_Site_Safi"},
    ],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 2: companies (8 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_COMPANIES = {
    "name": "companies",
    "description": "Entreprises/Compagnies clientes",
    "category": "entreprises",
    "used_in_objectifs": [81, 91, 92, 93, 97],
    "total_columns": 8,
    
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de l'entreprise"},
        "name": {"type": "VARCHAR", "nullable": False, "description": "Nom de l'entreprise (ex: JLN, ONEE, CMCP, NOMAC , Lafarge Holcim Bouskoura, Site Safi, test, NTN, JFC 4)"},
        "reference": {"type": "VARCHAR", "nullable": True, "description": "Référence interne ( ex : v3_tenant_jln, v3_tenant_Site_Safi, v3_tenant_ntn, v3_tenant_jfc4 , v3_tenant_lafarge_holcim_bouskoura, v3_tenant_nomac, v3_tenant_onee, v3_tenant_test, v3_tenant_cmcp_ip)"},
        "alias": {"type": "VARCHAR", "nullable": True, "description": "Alias/nom court (ex: JLN, ONEE, CMCP, NOMAC , Lafarge Holcim Bouskoura, Site Safi, test, NTN, JFC 4)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "created_by": {"type": "INT", "nullable": True, "foreign_key": "users.id", "description": "Utilisateur créateur"},
    },
    
    "relationships": [
        {"table": "user_company", "type": "one-to-many", "on": "companies.id = user_company.company_id"},
        {"table": "abonnements", "type": "one-to-many", "on": "companies.id = abonnements.company_id"},
        {"table": "devices", "type": "one-to-many", "on": "companies.id = devices.company_id"},
    ],
    
}

    # ═══════════════════════════════════════════════════════════════
    # TABLE: tenants (Base globale) - 5 colonnes
    # ═══════════════════════════════════════════════════════════════

TABLE_TENANTS = {
    "name": "tenants",
    "description": "Liste des bases de données tenant (multi-tenant)",
    "category": "administration",
    "used_in_objectifs": [],  
    "total_columns": 5,
    
    "columns": {
        "id": {"type": "VARCHAR", "primary_key": True, "nullable": False, "description": "Identifiant unique du tenant (ex: v3_tenant_jln, v3_tenant_cmcp_ip , etc...)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création de l'enregistrement"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "data": {"type": "JSON", "nullable": True, "description": "Données de configuration du tenant (ex: tenancy_db_name)"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    
    "relationships": [
        # Aucune relation directe dans le schéma actuel
    ],
}
# ═══════════════════════════════════════════════════════════════
# TABLE 3: user_company (7 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_USER_COMPANY = {
    "name": "user_company",
    "description": "Table de liaison utilisateurs-entreprises (plusieurs-à-plusieurs)",
    "category": "utilisateurs",
    "used_in_objectifs": [81],
    "total_columns": 7,
    
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la liaison"},
        "company_id": {"type": "INT", "nullable": False, "foreign_key": "companies.id", "description": "Entreprise concernée"},
        "user_id": {"type": "INT", "nullable": False, "foreign_key": "users.id", "description": "Utilisateur concerné"},
        "is_default": {"type": "TINYINT", "nullable": False, "default": 0, "description": "Entreprise par défaut (0/1)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    
    "relationships": [
        {"table": "users", "type": "many-to-one", "on": "user_company.user_id = users.id"},
        {"table": "companies", "type": "many-to-one", "on": "user_company.company_id = companies.id"},
    ],
    
    "indexes": [{"columns": ["user_id", "company_id"], "type": "unique"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 4: notifications (8 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_NOTIFICATIONS = {
    "name": "notifications",
    "description": "Notifications système (polymorphique - users, assets, etc.)",
    "category": "utilisateurs",
    "used_in_objectifs": [82, 83, 90],
    "total_columns": 8,
    
    "columns": {
        "id": {"type": "CHAR", "primary_key": True, "nullable": False, "description": "ID unique (UUID/CHAR)"},
        "type": {"type": "VARCHAR", "nullable": False, "description": "Type de notification"},
        "notifiable_type": {"type": "VARCHAR", "nullable": False, "description": "Type d'entité (ex: App\\Core\\\Models\\User\\User)"},
        "notifiable_id": {"type": "BIGINT", "nullable": False, "description": "ID de l'entité (user_id, asset_id)"},
        "data": {"type": "TEXT", "nullable": False, "description": "Données de la notification (JSON)"},
        "read_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de lecture (NULL = non lue)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
    },
    
    "relationships": [
        {"table": "users", "type": "many-to-one", "on": "notifications.notifiable_id = users.id", "condition": "notifications.notifiable_type = 'App\\\\Models\\\\User'"},
        {"table": "v3_tenant_jln.assets", "type": "many-to-one", "on": "notifications.notifiable_id = assets.id", "condition": "notifications.notifiable_type = 'App\\\\Models\\\\Asset'", "database": "v3_tenant_jln"},
    ],
    
    "indexes": [{"columns": ["notifiable_type", "notifiable_id"], "type": "index"}, {"columns": ["read_at"], "type": "index"}, {"columns": ["created_at"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 5: devices (16 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_DEVICES = {
    "name": "devices",
    "description": "Devices de mesure (VIBOX, capteurs, etc.)",
    "category": "predictions",
    "used_in_objectifs": [40, 65, 66, 71],
    "total_columns": 16,
    
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique du device"},
        "ref": {"type": "VARCHAR", "nullable": True, "description": "Référence (ex: VIBOX05-AA-0117)"},
        "mac": {"type": "VARCHAR", "nullable": True, "description": "Adresse MAC"},
        "date_etallonnage": {"type": "DATE", "nullable": True, "description": "Date d'étalonnage"},
        "date_service": {"type": "DATE", "nullable": True, "description": "Date de mise en service"},
        "duree_vie": {"type": "VARCHAR", "nullable": True, "description": "Durée de vie estimée"},
        "frequence_etallonnage": {"type": "INT", "nullable": True, "description": "Fréquence d'étalonnage (mois)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "product_id": {"type": "INT", "nullable": True, "foreign_key": "products.id", "description": "Produit associé"},
        "company_id": {"type": "INT", "nullable": True, "foreign_key": "companies.id", "description": "Entreprise propriétaire"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "status": {"type": "INT", "nullable": True, "description": "Statut (0 , 1)"},
        "external_dev_id": {"type": "VARCHAR", "nullable": True, "description": "ID device externe"},
        "config_id": {"type": "INT", "nullable": True, "foreign_key": "acquisition_configurations.id", "description": "Configuration associée"},
        "grandeur_category_id": {"type": "BIGINT", "nullable": True, "foreign_key": "grandeur_categories.id", "description": "Catégorie de grandeur mesurée"},
    },
    
    "relationships": [
        {"table": "v3_tenant_jln.alarms", "type": "one-to-many", "on": "devices.id = alarms.device_id", "database": "v3_tenant_jln"},
        {"table": "features_device", "type": "one-to-many", "on": "devices.id = features_device.device_id"},
        {"table": "companies", "type": "many-to-one", "on": "devices.company_id = companies.id"},
        {"table": "grandeur_categories", "type": "many-to-one", "on": "devices.grandeur_category_id = grandeur_categories.id"},
    ],
    
    "indexes": [{"columns": ["ref"], "type": "index"}, {"columns": ["mac"], "type": "index"}, {"columns": ["deleted_at"], "type": "index"}, {"columns": ["company_id"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 6: features (12 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_FEATURES = {
    "name": "features",
    "description": "Features de machine learning (caractéristiques extraites des signaux)",
    "category": "predictions",
    "used_in_objectifs": [65, 67, 69, 74],
    "total_columns": 12,
    
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la feature"},
        "name": {"type": "VARCHAR", "nullable": False, "unique": True, "description": "Nom de la feature (ex: NGV, NGA, NGD, VCC_g, VCC_v, Energy, Power, Voltage(kV), Temperature_Air , Humidite_Relative , temperature , K, FC, CO2 ,oil, etc...)"},
        "label": {"type": "VARCHAR", "nullable": True, "description": "Label/étiquette"},
        "description": {"type": "VARCHAR", "nullable": True, "description": "Description détaillée"},
        "unit": {"type": "VARCHAR", "nullable": True, "description": "Unité de mesure (ex : °C , g, %, µm, BAR, mm/s, etc...)"},
        "grandeur_id": {"type": "INT", "nullable": True, "foreign_key": "grandeurs.id", "description": "Grandeur associée"},
        "tags": {"type": "VARCHAR", "nullable": True, "description": "Tags/mots-clés"},
        "data_type": {"type": "INT", "nullable": True, "description": "Type de données (1=numeric, 2=text)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "priority": {"type": "TINYINT", "nullable": True, "description": "Priorité (1=haute, 2=moyenne, 3=basse)"},
    },
    
    "relationships": [
        {"table": "features_device", "type": "one-to-many", "on": "features.id = features_device.feature_id"},
        {"table": "pdm_features", "type": "one-to-many", "on": "features.id = pdm_features.feature_id"},
        {"table": "manual_features", "type": "one-to-many", "on": "features.id = manual_features.feature_id"},
        {"table": "grandeurs", "type": "many-to-one", "on": "features.grandeur_id = grandeurs.id"},
    ],
    
    "indexes": [{"columns": ["name"], "type": "unique"}, {"columns": ["deleted_at"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 7: features_device (6 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_FEATURES_DEVICE = {
    "name": "features_device",
    "description": "Liaison features-devices (quelle feature est activée sur quel device)",
    "category": "predictions",
    "used_in_objectifs": [65],
    "total_columns": 6,
    
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la liaison"},
        "feature_id": {"type": "INT", "nullable": False, "foreign_key": "features.id", "description": "Feature associée"},
        "device_id": {"type": "INT", "nullable": False, "foreign_key": "devices.id", "description": "Device concerné"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    
    "relationships": [
        {"table": "features", "type": "many-to-one", "on": "features_device.feature_id = features.id"},
        {"table": "devices", "type": "many-to-one", "on": "features_device.device_id = devices.id"},
    ],
    
    "indexes": [{"columns": ["feature_id", "device_id"], "type": "unique"}, {"columns": ["deleted_at"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 8: predictions (13 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_PREDICTIONS = {
    "name": "predictions",
    "description": "Prédictions de risque de panne (résultats du modèle ML)",
    "category": "predictions",
    "used_in_objectifs": [71, 72, 73, 75, 76, 80],
    "total_columns": 13,
    
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la prédiction"},
        "asset_id": {"type": "INT", "nullable": True, "description": "Équipement concerné (v3_tenant_jln.assets.id)"},
        "measurement_id": {"type": "INT", "nullable": True, "description": "Mesure associée (v3_tenant_Site_Safi.measurements.id)"},
        "timestamp": {"type": "INT", "nullable": True, "description": "Timestamp Unix de la prédiction"},
        "model": {"type": "VARCHAR", "nullable": True, "description": "Modèle ML utilisé"},
        "failure": {"type": "VARCHAR", "nullable": True, "description": "Type de défaillance prédite"},
        "cause": {"type": "VARCHAR", "nullable": True, "description": "Cause identifiée"},
        "failures_probability": {"type": "MEDIUMTEXT", "nullable": True, "description": "Probabilités de défaillance (JSON)"},
        "causes_probability": {"type": "MEDIUMTEXT", "nullable": True, "description": "Probabilités des causes (JSON)"},
        "predictions_path": {"type": "MEDIUMTEXT", "nullable": True, "description": "Chemin vers les résultats complets"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    
    "relationships": [
        {"table": "v3_tenant_jln.assets", "type": "many-to-one", "on": "predictions.asset_id = assets.id", "database": "v3_tenant_jln"},
        {"table": "v3_tenant_Site_Safi.measurements", "type": "many-to-one", "on": "predictions.measurement_id = measurements.id", "database": "v3_tenant_Site_Safi"},
    ],
    
    "indexes": [{"columns": ["asset_id"], "type": "index"}, {"columns": ["timestamp"], "type": "index"}, {"columns": ["deleted_at"], "type": "index"}, {"columns": ["model"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 9: pdm_features (6 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_PDM_FEATURES = {
    "name": "pdm_features",
    "description": "Features PDM (Predictive Maintenance)",
    "category": "predictions",
    "used_in_objectifs": [74],
    "total_columns": 6,
    
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la feature PDM"},
        "feature": {"type": "VARCHAR", "nullable": True, "description": "Nom de la feature (ex : A1F0_Energy, A3F0_Energy, A2F0_Energy, A3F0, A2F0, A1F0)"},
        "label": {"type": "VARCHAR", "nullable": True, "description": "Label/étiquette (ex: 1X ,2X , 3X,Energy 1X (1X/NGV),Energy 2X (2X/NGV),Energy 3X (3X/NGV))"},
        "type": {"type": "VARCHAR", "nullable": True, "description": "Type de feature ( ex: Amplitude, Ratios)"},
        "unit": {"type": "VARCHAR", "nullable": True, "description": "Unité de mesure (ex: mm/s, %)"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    
    "relationships": [
        {"table": "features", "type": "many-to-one", "on": "pdm_features.feature = features.name"},
    ],
    
    "indexes": [{"columns": ["deleted_at"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 10: power_values (5 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_POWER_VALUES = {
    "name": "power_values",
    "description": "Valeurs de puissance",
    "category": "predictions",
    "used_in_objectifs": [75],
    "total_columns": 5,
    
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la valeur de puissance"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom de la valeur ( ex: Batterie, Wired)"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
    },
    
    "relationships": [],
    "indexes": [{"columns": ["deleted_at"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 11: transmission_values (5 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_TRANSMISSION_VALUES = {
    "name": "transmission_values",
    "description": "Valeurs de transmission",
    "category": "predictions",
    "used_in_objectifs": [76],
    "total_columns": 5,
    
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la valeur de transmission"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom de la valeur ( ex : Lora, Hybrid, Wifi, Bluetooth, 4G, MQTT )"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
    },
    
    "relationships": [],
    "indexes": [{"columns": ["deleted_at"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 12: manual_features (3 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_MANUAL_FEATURES = {
    "name": "manual_features",
    "description": "Features saisies manuellement",
    "category": "predictions",
    "used_in_objectifs": [69],
    "total_columns": 3,
    
    "columns": {
        "my_row_id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la feature manuelle"},
        "feature_id": {"type": "INT", "nullable": True, "foreign_key": "features.id", "description": "Feature associée"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    
    "relationships": [
        {"table": "features", "type": "many-to-one", "on": "manual_features.feature_id = features.id"},
    ],
    
    "indexes": [{"columns": ["feature_id"], "type": "index"}, {"columns": ["deleted_at"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 13: grandeurs (8 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_GRANDEURS = {
    "name": "grandeurs",
    "description": "Grandeurs de mesure",
    "category": "predictions",
    "used_in_objectifs": [67],
    "total_columns": 8,
    
    "columns": {
        "id": {"type": "INT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la grandeur"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom de la grandeur (ex : OIL CONDUCTIVITY, vibration, battery, FAUX ROND, VOILE, speed, CO2, PM10, PM2_5, etc...)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "image": {"type": "VARCHAR", "nullable": True, "description": "Image/illustration"},
        "type": {"type": "INT", "nullable": True, "description": "Type (0 , 1)"},
        "grandeur_category_id": {"type": "BIGINT", "nullable": True, "foreign_key": "grandeur_categories.id", "description": "Catégorie de la grandeur"},
    },
    
    "relationships": [
        {"table": "grandeur_categories", "type": "many-to-one", "on": "grandeurs.grandeur_category_id = grandeur_categories.id"},
        {"table": "features", "type": "one-to-many", "on": "grandeurs.id = features.grandeur_id"},
        {"table": "devices", "type": "one-to-many", "on": "grandeurs.id = devices.grandeur_category_id"},
    ],
    
    "indexes": [{"columns": ["deleted_at"], "type": "index"}, {"columns": ["grandeur_category_id"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 14: grandeur_categories (5 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_GRANDEUR_CATEGORIES = {
    "name": "grandeur_categories",
    "description": "Catégories de grandeurs",
    "category": "predictions",
    "used_in_objectifs": [67],
    "total_columns": 5,
    
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de la catégorie"},
        "name": {"type": "VARCHAR", "nullable": True, "description": "Nom de la catégorie ( ex : Oil, Lubrication, Other, Agriculture, Vibration)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
    },
    
    "relationships": [
        {"table": "grandeurs", "type": "one-to-many", "on": "grandeur_categories.id = grandeurs.grandeur_category_id"},
    ],
    
    "indexes": [{"columns": ["deleted_at"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# TABLE 15: abonnements (16 colonnes)
# ═══════════════════════════════════════════════════════════════

TABLE_ABONNEMENTS = {
    "name": "abonnements",
    "description": "Abonnements des entreprises",
    "category": "entreprises",
    "used_in_objectifs": [97, 100],
    "total_columns": 16,
    
    "columns": {
        "id": {"type": "BIGINT", "primary_key": True, "auto_increment": True, "nullable": False, "description": "ID unique de l'abonnement"},
        "package_id": {"type": "INT", "nullable": True, "foreign_key": "packages.id", "description": "Package/plan associé"},
        "company_id": {"type": "INT", "nullable": True, "foreign_key": "companies.id", "description": "Entreprise abonnée"},
        "max_sms": {"type": "INT", "nullable": True, "description": "Nombre maximum de SMS"},
        "max_email": {"type": "INT", "nullable": True, "description": "Nombre maximum d'emails"},
        "max_users": {"type": "INT", "nullable": True, "description": "Nombre maximum d'utilisateurs"},
        "max_storage": {"type": "INT", "nullable": True, "description": "Stockage maximum (GB)"},
        "max_devices": {"type": "INT", "nullable": True, "description": "Nombre maximum de devices"},
        "start_date": {"type": "TIMESTAMP", "nullable": True, "description": "Date de début d'abonnement"},
        "end_date": {"type": "TIMESTAMP", "nullable": True, "description": "Date de fin d'abonnement"},
        "status": {"type": "TINYINT", "nullable": True, "description": "Statut (0 ,1)"},
        "created_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de création"},
        "updated_at": {"type": "TIMESTAMP", "nullable": True, "description": "Date de mise à jour"},
        "deleted_at": {"type": "TIMESTAMP", "nullable": True, "description": "Suppression (soft delete)"},
        "sms_used": {"type": "BIGINT", "nullable": True, "description": "Nombre de SMS utilisés"},
        "email_used": {"type": "BIGINT", "nullable": True, "description": "Nombre d'emails utilisés"},
    },
    
    "relationships": [
        {"table": "companies", "type": "many-to-one", "on": "abonnements.company_id = companies.id"},
        {"table": "packages", "type": "many-to-one", "on": "abonnements.package_id = packages.id"},
    ],
    
    "indexes": [{"columns": ["deleted_at"], "type": "index"}, {"columns": ["company_id"], "type": "index"}, {"columns": ["status"], "type": "index"}],
}

# ═══════════════════════════════════════════════════════════════
# SCHÉMA DE JOINTURE GLOBAL
# ═══════════════════════════════════════════════════════════════

GLOBAL_JOIN_SCHEMAS = {
    "utilisateurs": {
        "main_table": "i_sense_v3_devenv_db.users",
        "joins": [
            {"table": "i_sense_v3_devenv_db.user_company", "on": "users.id = user_company.user_id", "type": "LEFT"},
            {"table": "i_sense_v3_devenv_db.companies", "on": "user_company.company_id = companies.id", "type": "LEFT"},
            {"table": "i_sense_v3_devenv_db.notifications", "on": "users.id = notifications.notifiable_id", "type": "LEFT", "condition": "notifications.notifiable_type = 'App\\\\Models\\\\User'"},
        ],
        "filters": ["users.deleted_at IS NULL"],
    },
    "predictions": {
        "main_table": "i_sense_v3_devenv_db.predictions",
        "joins": [
            {"table": "v3_tenant_jln.assets", "on": "predictions.asset_id = assets.id", "type": "LEFT"},
            {"table": "v3_tenant_Site_Safi.measurements", "on": "predictions.measurement_id = measurements.id", "type": "LEFT"},
        ],
        "filters": ["predictions.deleted_at IS NULL"],
    },
    "features": {
        "main_table": "i_sense_v3_devenv_db.features",
        "joins": [
            {"table": "i_sense_v3_devenv_db.features_device", "on": "features.id = features_device.feature_id", "type": "LEFT"},
            {"table": "i_sense_v3_devenv_db.devices", "on": "features_device.device_id = devices.id", "type": "LEFT"},
            {"table": "i_sense_v3_devenv_db.grandeurs", "on": "features.grandeur_id = grandeurs.id", "type": "LEFT"},
        ],
        "filters": ["features.deleted_at IS NULL"],
    },
    "entreprises": {
        "main_table": "i_sense_v3_devenv_db.companies",
        "joins": [
            {"table": "i_sense_v3_devenv_db.user_company", "on": "companies.id = user_company.company_id", "type": "LEFT"},
            {"table": "i_sense_v3_devenv_db.users", "on": "user_company.user_id = users.id", "type": "LEFT"},
            {"table": "i_sense_v3_devenv_db.abonnements", "on": "companies.id = abonnements.company_id", "type": "LEFT"},
        ],
        "filters": ["companies.deleted_at IS NULL"],
    },
}

# ═══════════════════════════════════════════════════════════════
# RÉCAPITULATIF DE TOUTES LES TABLES
# ═══════════════════════════════════════════════════════════════

ALL_TABLES = {
    "users": TABLE_USERS,
    "companies": TABLE_COMPANIES,
    "user_company": TABLE_USER_COMPANY,
    "notifications": TABLE_NOTIFICATIONS,
    "devices": TABLE_DEVICES,
    "features": TABLE_FEATURES,
    "features_device": TABLE_FEATURES_DEVICE,
    "predictions": TABLE_PREDICTIONS,
    "pdm_features": TABLE_PDM_FEATURES,
    "power_values": TABLE_POWER_VALUES,
    "transmission_values": TABLE_TRANSMISSION_VALUES,
    "manual_features": TABLE_MANUAL_FEATURES,
    "grandeurs": TABLE_GRANDEURS,
    "grandeur_categories": TABLE_GRANDEUR_CATEGORIES,
    "abonnements": TABLE_ABONNEMENTS,
    "tenants": TABLE_TENANTS,
}

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def get_all_tables() -> dict:
    """Récupérer toutes les tables"""
    return ALL_TABLES


def get_table_schema(table_name: str) -> dict:
    """Récupérer le schéma d'une table spécifique"""
    return ALL_TABLES.get(table_name, {})


def get_join_schema(category: str) -> dict:
    """Récupérer le schéma de jointure pour une catégorie"""
    return GLOBAL_JOIN_SCHEMAS.get(category, {})


def get_tables_for_objectif(objectif_number: int) -> list:
    """Récupérer les tables utilisées par un objectif"""
    tables = []
    for table_name, table_info in ALL_TABLES.items():
        if objectif_number in table_info.get("used_in_objectifs", []):
            tables.append(table_name)
    return tables


def get_columns_for_table(table_name: str) -> dict:
    """Récupérer toutes les colonnes d'une table"""
    table = get_table_schema(table_name)
    return table.get("columns", {})


def get_relationships_for_table(table_name: str) -> list:
    """Récupérer les relations d'une table"""
    table = get_table_schema(table_name)
    return table.get("relationships", [])


def is_foreign_key(table_name: str, column_name: str) -> bool:
    """Vérifier si une colonne est une foreign key"""
    columns = get_columns_for_table(table_name)
    column_info = columns.get(column_name, {})
    return "foreign_key" in column_info


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
    print(" " * 20 + "📊 SCHÉMA COMPLET - i_sense_v3_devenv_db")
    print("="*80)
    
    print(f"\n📋 Base: {DATABASE_INFO['name']}")
    print(f"   Type: {DATABASE_INFO['type']}")
    print(f"   Tables totales: {DATABASE_INFO['essential_tables']}")
    print(f"   Colonnes totales: {get_total_columns()}")
    
    print("\n📋 Tables documentées:")
    for table_name, table_info in ALL_TABLES.items():
        objectifs = table_info.get("used_in_objectifs", [])
        colonnes = table_info.get("total_columns", 0)
        print(f"   • {table_name:25} → {colonnes:2} colonnes → Objectifs: {objectifs}")
    
    print("\n📋 Exemple: Schéma de 'users'")
    users_schema = get_table_schema("users")
    print(f"   Description: {users_schema.get('description')}")
    print(f"   Colonnes: {users_schema.get('total_columns')}")
    print(f"   Relations: {len(users_schema.get('relationships', []))}")
    
    print("\n📋 Exemple: Jointures pour 'utilisateurs'")
    join_schema = get_join_schema("utilisateurs")
    print(f"   Table principale: {join_schema.get('main_table')}")
    print(f"   Nombre de jointures: {len(join_schema.get('joins', []))}")
    
    print("\n📋 Exemple: Colonnes de 'predictions'")
    predictions_columns = get_columns_for_table("predictions")
    for col_name, col_info in predictions_columns.items():
        pk = "🔑 PK" if col_info.get("primary_key") else "  "
        fk = "🔗 FK" if col_info.get("foreign_key") else "  "
        print(f"   {pk} {fk} {col_name:25} → {col_info.get('type')}")
    
    print("\n" + "="*80)
    print(" " * 25 + "✅ 15 TABLES DOCUMENTÉES")
    print("="*80 + "\n")