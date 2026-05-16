# queries.py
"""
Templates SQL pour le Chatbot de Maintenance Prédictive
Supporte TOUTES les bases de données disponibles
"""

QUERIES = {
    # ═══════════════════════════════════════════════════════════════
    # OBJECTIF PFE #1: HISTORIQUE DES DÉFAUTS
    # ═══════════════════════════════════════════════════════════════
    "historique_defauts": """
        SELECT 
            af.id AS defect_id,
            a.name AS equipment_name,
            a.asset_class_id,
            f.name AS defect_type,
            ff.name AS fault_family,
            af.start_date,
            af.end_date,
            af.duration,
            af.status,
            af.percentage
        FROM {tenant_db}.asset_faults af
        JOIN {tenant_db}.assets a ON af.asset_id = a.id
        JOIN v3_tenant_Site_Safi.faults f ON af.fault_id = f.id
        LEFT JOIN v3_tenant_Site_Safi.family_fault ff ON f.family_id = ff.id
        WHERE a.id = %s
        ORDER BY af.start_date DESC
        LIMIT %s
    """,
    
    "historique_defauts_par_equipment": """
        SELECT 
            a.name AS equipment_name,
            COUNT(af.id) AS nb_defauts,
            AVG(af.duration) AS duree_moyenne,
            MIN(af.start_date) AS premier_defaut,
            MAX(af.start_date) AS dernier_defaut
        FROM {tenant_db}.asset_faults af
        JOIN {tenant_db}.assets a ON af.asset_id = a.id
        WHERE a.id = %s
        GROUP BY a.id, a.name
    """,
    
    # ═══════════════════════════════════════════════════════════════
    # OBJECTIF PFE #2: ÉQUIPEMENTS SIMILAIRES
    # ═══════════════════════════════════════════════════════════════
    "equipements_similaires": """
        SELECT 
            a2.id AS similar_asset_id,
            a2.name AS similar_equipment,
            a2.asset_class_id,
            af2.start_date,
            af2.end_date,
            af2.duration,
            f.name AS defect_type
        FROM {tenant_db}.asset_faults af1
        JOIN {tenant_db}.asset_faults af2 ON af1.fault_id = af2.fault_id
        JOIN {tenant_db}.assets a1 ON af1.asset_id = a1.id
        JOIN {tenant_db}.assets a2 ON af2.asset_id = a2.id
        JOIN v3_tenant_Site_Safi.faults f ON af1.fault_id = f.id
        WHERE a1.id = %s
        AND a2.id != a1.id
        ORDER BY af2.start_date DESC
        LIMIT %s
    """,
    
    "equipements_similaires_par_classe": """
        SELECT 
            a2.id,
            a2.name,
            a2.asset_class_id,
            COUNT(af2.id) AS nb_defauts_communs
        FROM {tenant_db}.asset_faults af1
        JOIN {tenant_db}.asset_faults af2 ON af1.fault_id = af2.fault_id
        JOIN {tenant_db}.assets a1 ON af1.asset_id = a1.id
        JOIN {tenant_db}.assets a2 ON af2.asset_id = a2.id
        WHERE a1.id = %s
        AND a2.asset_class_id = a1.asset_class_id
        AND a2.id != a1.id
        GROUP BY a2.id, a2.name, a2.asset_class_id
        ORDER BY nb_defauts_communs DESC
        LIMIT %s
    """,
    
    # ═══════════════════════════════════════════════════════════════
    # OBJECTIF PFE #3: DATES ET DURÉES
    # ═══════════════════════════════════════════════════════════════
    "statistiques_defauts_par_mois": """
        SELECT 
            DATE_FORMAT(af.start_date, '%Y-%m') AS mois,
            COUNT(*) AS nb_defauts,
            AVG(af.duration) AS duree_moyenne,
            SUM(CASE WHEN af.status = 0 THEN 1 ELSE 0 END) AS defauts_actifs,
            SUM(CASE WHEN af.status = 1 THEN 1 ELSE 0 END) AS defauts_resolus
        FROM {tenant_db}.asset_faults af
        GROUP BY mois
        ORDER BY mois DESC
        LIMIT 12
    """,
    
    "duree_moyenne_par_type_defaut": """
        SELECT 
            f.name AS type_defaut,
            ff.name AS famille,
            COUNT(*) AS nb_occurrences,
            AVG(af.duration) AS duree_moyenne,
            MIN(af.start_date) AS premier_defaut,
            MAX(af.start_date) AS dernier_defaut
        FROM {tenant_db}.asset_faults af
        JOIN v3_tenant_Site_Safi.faults f ON af.fault_id = f.id
        LEFT JOIN v3_tenant_Site_Safi.family_fault ff ON f.family_id = ff.id
        GROUP BY f.id, ff.id
        ORDER BY nb_occurrences DESC
    """,
    
    # ═══════════════════════════════════════════════════════════════
    # OBJECTIF PFE #4: RECOMMANDATIONS
    # ═══════════════════════════════════════════════════════════════
    "recommandations_par_defaut": """
        SELECT 
            r.id AS recommendation_id,
            r.title,
            r.description,
            r.priority,
            f.name AS defect_type,
            ff.name AS fault_family
        FROM v3_tenant_Site_Safi.recommendations_v3 r
        JOIN v3_tenant_Site_Safi.recommendation_faults rf ON r.id = rf.recommendation_id
        JOIN v3_tenant_Site_Safi.faults f ON rf.fault_id = f.id
        LEFT JOIN v3_tenant_Site_Safi.family_fault ff ON f.family_id = ff.id
        WHERE f.id = %s
        ORDER BY r.priority ASC
    """,
    
    "recommandations_par_equipment": """
        SELECT DISTINCT
            r.id,
            r.title,
            r.description,
            r.priority
        FROM v3_tenant_Site_Safi.recommendations_v3 r
        JOIN v3_tenant_Site_Safi.recommendation_faults rf ON r.id = rf.recommendation_id
        JOIN {tenant_db}.asset_faults af ON rf.fault_id = af.fault_id
        WHERE af.asset_id = %s
        ORDER BY r.priority ASC
    """,
    
    # ═══════════════════════════════════════════════════════════════
    # OBJECTIF PFE #5: ALARMES (AJOUTÉ)
    # ═══════════════════════════════════════════════════════════════
    "dernieres_alarmes": """
        SELECT 
            al.id AS alarm_id,
            a.name AS equipment,
            a.asset_class_id,
            al.alarm_type,
            al.severity,
            al.message,
            al.created_at,
            al.status
        FROM {tenant_db}.alarms al
        JOIN {tenant_db}.assets a ON al.asset_id = a.id
        ORDER BY al.created_at DESC
        LIMIT %s
    """,
    
    "alarmes_actives": """
        SELECT 
            al.id AS alarm_id,
            a.name AS equipment,
            al.alarm_type,
            al.severity,
            al.message,
            al.created_at,
            TIMESTAMPDIFF(HOUR, al.created_at, NOW()) AS heures_actives
        FROM {tenant_db}.alarms al
        JOIN {tenant_db}.assets a ON al.asset_id = a.id
        WHERE al.status = 0
        ORDER BY al.created_at DESC
    """,
    
    "alarmes_par_gravite": """
        SELECT 
            al.severity,
            COUNT(*) AS nb_alarmes,
            SUM(CASE WHEN al.status = 0 THEN 1 ELSE 0 END) AS actives,
            SUM(CASE WHEN al.status = 1 THEN 1 ELSE 0 END) AS resolues
        FROM {tenant_db}.alarms al
        GROUP BY al.severity
        ORDER BY al.severity DESC
    """,
    
    # ═══════════════════════════════════════════════════════════════
    # REQUÊTES GÉNÉRALES (TOUTES BASES)
    # ═══════════════════════════════════════════════════════════════
    "liste_tous_equipe": """
        SELECT 
            a.id,
            a.name,
            a.asset_class_id,
            ac.name AS asset_class_name,
            COUNT(af.id) AS nb_defauts_total,
            SUM(CASE WHEN af.status = 0 THEN 1 ELSE 0 END) AS nb_defauts_actifs
        FROM {tenant_db}.assets a
        LEFT JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
        LEFT JOIN {tenant_db}.asset_classes ac ON a.asset_class_id = ac.id
        GROUP BY a.id, a.name, a.asset_class_id, ac.name
        ORDER BY nb_defauts_total DESC
    """,
    
    "liste_tous_defauts": """
        SELECT 
            f.id,
            f.name,
            ff.name AS family_name,
            COUNT(af.id) AS nb_occurrences
        FROM v3_tenant_Site_Safi.faults f
        LEFT JOIN v3_tenant_Site_Safi.family_fault ff ON f.family_id = ff.id
        LEFT JOIN {tenant_db}.asset_faults af ON f.id = af.fault_id
        GROUP BY f.id, f.name, ff.name
        ORDER BY nb_occurrences DESC
    """,
    
    "predictions_disponibles": """
        SELECT 
            p.id,
            p.device_id,
            p.prediction_date,
            p.risk_level,
            p.confidence_score,
            d.name AS device_name
        FROM i_sense_v3_devenv_db.predictions p
        JOIN i_sense_v3_devenv_db.devices d ON p.device_id = d.id
        ORDER BY p.prediction_date DESC
        LIMIT %s
    """,
    
    "statut_quotidien": """
        SELECT 
            a.name AS equipement,
            das.status,
            das.date,
            das.health_score
        FROM v3_tenant_Site_Safi.daily_asset_status das
        JOIN {tenant_db}.assets a ON das.asset_id = a.id
        WHERE das.date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY das.date DESC
    """,
    
    # ═══════════════════════════════════════════════════════════════
    # REQUÊTES SPÉCIFIQUES PAR BASE TENANT
    # ═══════════════════════════════════════════════════════════════
    "comparaison_multi_tenants": """
        SELECT 
            '{tenant_db}' AS tenant,
            COUNT(af.id) AS nb_defauts,
            AVG(af.duration) AS duree_moyenne
        FROM {tenant_db}.asset_faults af
        WHERE af.start_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
    """,
}

# ═══════════════════════════════════════════════════════════════
# LISTE DE TOUTES LES BASES DISPONIBLES
# ═══════════════════════════════════════════════════════════════
ALL_DATABASES = [
    # Globales
    'i_sense_v3_devenv_db',
    'i_sense_v3_devenv_db3',
    'test_company_db',
    
    # Tenants
    'v3_tenant_Site_Safi',
    'v3_tenant_jln',
    'v3_tenant_cmcp_ip',
    'v3_tenant_cobomi',
    'v3_tenant_jfc4',
    'v3_tenant_lafarge_holcim_bouskoura',
    'v3_tenant_nomac',
    'v3_tenant_ntn',
    'v3_tenant_onee',
    'v3_tenant_test',
]

# ═══════════════════════════════════════════════════════════════
# BASES PRIORITAIRES POUR LE CHATBOT
# ═══════════════════════════════════════════════════════════════
PRIORITY_DATABASES = {
    'global': 'i_sense_v3_devenv_db',
    'reference': 'v3_tenant_Site_Safi',
    'active': 'v3_tenant_jln',
}

def get_query(query_name: str, tenant_db: str = 'v3_tenant_jln') -> str:
    """
    Récupérer une requête SQL avec le nom de la base tenant
    
    Args:
        query_name: Nom de la requête dans QUERIES
        tenant_db: Nom de la base tenant (par défaut: v3_tenant_jln)
    
    Returns:
        str: Requête SQL formatée
    """
    query_template = QUERIES.get(query_name)
    if not query_template:
        raise ValueError(f"Requête '{query_name}' non trouvée")
    
    return query_template.format(tenant_db=tenant_db)