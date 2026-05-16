# dataset_400_questions.py
"""
Dataset de 400 questions-réponses SQL pour le fine-tuning
Chatbot Maintenance Prédictive - i-sense / i-predict
Basé sur les schémas : schema_global.py + schema_tenants.py

✅ VERSION GÉNÉRIQUE MULTI-TENANT :
- Utilise {tenant_db} pour les tables communes (TOUS les 9 tenants)
- Garde v3_tenant_Site_Safi pour les tables uniques à Safi
- Garde i_sense_v3_devenv_db pour les tables globales
"""

DATASET_400_QUESTIONS = [
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 1 : ÉQUIPEMENTS (ASSETS) - 50 questions
    # ═══════════════════════════════════════════════════════════════
    
    {
        "question": "Quels sont les équipements présentant actuellement un problème de roulement ?",
        "sql": """
            SELECT a.id, a.name, a.ref, af.start_date, f.name AS defect_type
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE (f.name LIKE '%roulement%' OR f.name LIKE '%Bearing%')
            AND a.deleted_at IS NULL
            ORDER BY af.start_date DESC
            
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Depuis combien de temps l'équipement X présente-t-il un problème de lubrification ?",
        "sql": """
            SELECT a.name, af.start_date, 
                   TIMESTAMPDIFF(DAY, af.start_date, NOW()) AS jours_depuis_defaut
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE (a.name = 'X' OR a.ref = 'X')
            AND f.name LIKE '%lubrification%'
            ORDER BY af.start_date DESC
            LIMIT 1
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quel est le statut actuel de l'équipement X ?",
        "sql": """
            SELECT a.id, a.name, a.ref, a.status,
                   CASE 
                       WHEN a.status = -1 THEN 'Unassigned '
                       WHEN a.status = 0 THEN 'shut down'
                       WHEN a.status = 1 THEN 'Normal'
                       WHEN a.status = 2 THEN 'MID'
                       WHEN a.status = 3 THEN 'Moderate'
                       WHEN a.status = 4 THEN 'Undifined'
                       WHEN a.status = 5 THEN 'critical'
                       WHEN a.status IS NULL THEN 'Undifined'
                       ELSE 'Inconnu'
                   END AS statut_label
            FROM {tenant_db}.assets a
            WHERE (a.name = 'X' OR a.ref = 'X')
            AND a.deleted_at IS NULL
            LIMIT 1
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
            "question": "Combien de pannes actives ce mois ?",
            "sql": 
                """
                SELECT COUNT(*) AS nb_pannes_actives
                FROM {tenant_db}.asset_faults af
                WHERE af.start_date >= DATE_FORMAT(NOW(), '%Y-%m-01')
                AND af.end_date IS NULL
                AND af.deleted_at IS NULL;
                """,
                "metadata": {"category": "défauts",  "tables": ["asset_faults"] , "tenant_generic": True}
    },
    
    {
        "question": "L'équipement X possède-t-il une référence de roulement connue ou un roulement unknown ?",
        "sql": """
            SELECT a.name, a.ref,
                   CASE 
                       WHEN a.ref IS NOT NULL AND a.ref != '' THEN 'Référence connue'
                       ELSE 'Unknown'
                   END AS reference_statut
            FROM {tenant_db}.assets a
            WHERE a.name = 'X'
            LIMIT 1
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements en alarme critique aujourd'hui ?",
        "sql": """
            SELECT a.id, a.name,a.ref, al.id AS alarm_id, al.created_at, al.status
            FROM {tenant_db}.assets a
            JOIN {tenant_db}.alarms al ON a.id = al.asset_id
            WHERE al.ended_at IS NULL
            AND DATE(al.created_at) = CURDATE()
            AND al.deleted_at IS NULL
            AND al.status = 5  
            ORDER BY a.id;
        """,
        "metadata": {"category": "alarmes", "tables": ["assets", "alarms"], "tenant_generic": True}
    },
    {
        "question": "Quel est l’équipement ayant aujourd’hui la NGV la plus élevée au-dessus du seuil, sans être un outlier et sans effet ski-slope ?",
        "sql": """
        SELECT 
            a.id AS asset_id,
            a.name AS asset_name,
            a.ref,
            fm.value AS ngv_value,
            fg.alarm AS seuil_alarm,
            (fm.value - fg.alarm) AS depassement
        FROM {tenant_db}.feature_measurement fm
        JOIN {tenant_db}.assets a ON fm.asset_parent_id = a.id
        JOIN {tenant_db}.feature_group fg ON fm.feature_id = fg.feature_id AND fm.group_id = fg.group_id
        JOIN i_sense_v3_devenv_db.features f ON fm.feature_id = f.id
        WHERE f.name = 'NGV'
        AND fm.created_at >= CURDATE()
        AND fm.created_at < CURDATE() + INTERVAL 1 DAY
        AND fm.value > fg.alarm
        AND fm.deleted_at IS NULL
        AND a.deleted_at IS NULL
        AND NOT EXISTS (
            SELECT 1
            FROM {tenant_db}.asset_faults af
            JOIN {tenant_db}.faults ft ON af.fault_id = ft.id
            WHERE af.asset_id = a.id
                AND af.end_date IS NULL
                AND af.deleted_at IS NULL
                AND ft.name IN ('Outliers', 'Ski slope')
        )
        ORDER BY depassement DESC
        LIMIT 1;
        """,
        "metadata": {
            "category": "predictions",
            "tables": ["feature_measurement", "assets", "feature_group", "i_sense_v3_devenv_db.features", "asset_faults", "faults"],
            "tenant_generic": True
        }
    },
    {
        "question": "Quel est l’équipement ayant aujourd’hui la NGV la plus élevée au-dessus du seuil aujourd'hui ?",
        "sql": """
        SELECT 
            a.id AS asset_id,
            a.name AS asset_name,
            a.ref,
            fm.value AS ngv_value,
            fg.alarm AS seuil_alarm,
            (fm.value - fg.alarm) AS depassement
        FROM {tenant_db}.feature_measurement fm
        JOIN {tenant_db}.assets a ON fm.asset_parent_id = a.id
        JOIN {tenant_db}.feature_group fg ON fm.feature_id = fg.feature_id AND fm.group_id = fg.group_id
        JOIN i_sense_v3_devenv_db.features f ON fm.feature_id = f.id
        WHERE f.name = 'NGV'
        AND fm.created_at >= CURDATE()
        AND fm.created_at < CURDATE() + INTERVAL 1 DAY
        AND fm.value > fg.alarm
        AND fm.deleted_at IS NULL
        AND a.deleted_at IS NULL
        ORDER BY depassement DESC
        LIMIT 1;
        """,
        "metadata": {
            "category": "predictions",
            "tables": ["feature_measurement", "assets", "feature_group", "i_sense_v3_devenv_db.features", "asset_faults", "faults"],
            "tenant_generic": True
        }
    },
    {
        "question": "Quelle est l'asset à grand température aujourd'hui ?",
        "sql": """
            SELECT a.id, a.name, a.ref, fm.value AS temperature, fm.created_at
            FROM {tenant_db}.feature_measurement fm
            JOIN {tenant_db}.assets a ON fm.asset_parent_id = a.id
            JOIN i_sense_v3_devenv_db.features f ON fm.feature_id = f.id
            WHERE f.name = 'temperature'
            AND fm.created_at >= CURDATE()
            AND fm.created_at < CURDATE() + INTERVAL 1 DAY
            AND fm.deleted_at IS NULL
            AND a.deleted_at IS NULL
            ORDER BY fm.value DESC
            LIMIT 1;
        """,
        "metadata": {
            "category": "mesures",
            "tables": ["feature_measurement", "assets", "i_sense_v3_devenv_db.features"],
            "tenant_generic": True
        }
    },
    
    {
        "question": "Quels équipements présentent une augmentation anormale de la vibration par rapport aux 7 derniers jours ?",
        "sql": """
            SELECT a.name, a.ref,
                   AVG(m.status) AS vibration_moyenne,
                   COUNT(*) AS nb_mesures
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.measurements m ON a.id = m.asset_id
            WHERE m.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            AND m.is_online = 1
            GROUP BY a.id, a.name
            HAVING vibration_moyenne > (
                SELECT AVG(status) 
                FROM {tenant_db}.measurements 
                WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY)
            )
            ORDER BY vibration_moyenne DESC
        """,
        "metadata": {"category": "mesures", "tables": ["assets", "measurements"], "tenant_generic": True}
    },
    {
        "question": "Quel équipement a enregistré le plus grand dépassement de seuil aujourd'hui ?",
        "sql": """
          SELECT a.id, a.name, pd.max_amplitude_vel, pd.Seuil_Alarm_Vitesse AS seuil,
                (pd.max_amplitude_vel - pd.Seuil_Alarm_Vitesse) AS depassement
            FROM {tenant_db}.assets a
            JOIN {tenant_db}.pdm_detection pd ON a.id = pd.parent_id
            WHERE DATE(pd.created_at) = CURDATE()
            AND pd.max_amplitude_vel > pd.Seuil_Alarm_Vitesse
            AND pd.deleted_at IS NULL
            ORDER BY depassement DESC
            LIMIT 1;
        """,
        "metadata": {"category": "mesures", "tables": ["assets", "pdm_detection"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements dont le défaut de roulement s'est aggravé au cours des 30 derniers jours ?",
        "sql": """
            SELECT a.name, a.asset_id, COUNT(af.id) AS nb_defauts,
                   MAX(af.start_date) AS dernier_defaut
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.start_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY a.id, a.name
            HAVING nb_defauts > 1
            ORDER BY nb_defauts DESC
        """,
        "metadata": {"category": "defauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels équipements présentent un problème de lubrification sans défaut de roulement ?",
        "sql": """
        SELECT DISTINCT a.id, a.name, a.ref
        FROM assets a
        INNER JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
        INNER JOIN faults f ON af.fault_id = f.id
        WHERE f.name LIKE '%lubrification%'
        AND af.end_date IS NULL         
        AND af.deleted_at IS NULL
        AND NOT EXISTS (
            SELECT 1
            FROM {tenant_db}.asset_faults af2
            INNER JOIN {tenant_db}.faults f2 ON af2.fault_id = f2.id
            WHERE af2.asset_id = a.id
                AND af2.end_date IS NULL   
                AND af2.deleted_at IS NULL
                AND (f2.name LIKE '%roulement%' OR f2.name LIKE '%Bearing%')
        )
        ORDER BY a.id;
        """,
        "metadata": {"category": "defauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements ayant des mesures invalides à cause d’un défaut capteur ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref, f.name AS defaut_capteur
            FROM {tenant_db}.assets a
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE (f.name = 'Fault sensor' OR f.name LIKE '%fault capteur%')
            AND af.end_date IS NULL   
            AND af.deleted_at IS NULL
            ORDER BY a.id;
        """,
        "metadata": {
            "category": "défauts capteur",
            "tables": ["assets", "asset_faults", "faults"],
            "tenant_generic": True,
           
        }
    },
    {
        "question": "Quels équipements ont été exclus comme outliers aujourd'hui ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref
            FROM {tenant_db}.assets a
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE f.name = 'Outliers'
            AND DATE(af.start_date) = CURDATE()
            AND af.deleted_at IS NULL
            ORDER BY a.id;
            
        """,
        "metadata": {"category": "mesures", "tables": ["assets", "measurements"], "tenant_generic": True}
    },
    {
        "question": "Quels équipements ont changé de statut entre hier et aujourd'hui ?",
        "sql": """
            SELECT a.id, a.name, a.ref,
                   MAX(CASE WHEN DATE(m.created_at) = CURDATE() THEN m.status END) AS statut_aujourdhui,
                   MAX(CASE WHEN DATE(m.created_at) = DATE_SUB(CURDATE(), INTERVAL 1 DAY) THEN m.status END) AS statut_hier
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.measurements m ON a.id = m.asset_id
            WHERE DATE(m.created_at) IN (CURDATE(), DATE_SUB(CURDATE(), INTERVAL 1 DAY))
            GROUP BY a.id, a.name
            HAVING statut_aujourdhui != statut_hier
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "measurements"], "tenant_generic": True}
    }, 
    {
        "question": "Quels équipements n'ont aucune référence de roulement renseignée ?",
        "sql": """
            SELECT id, name, ref
            FROM {tenant_db}.assets
            WHERE (ref IS NULL OR ref = '')
            AND deleted_at IS NULL
            ORDER BY name
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Quel équipement présente simultanément un défaut de roulement et un problème de lubrification ?",
        "sql": """
            SELECT a.id, a.name, 
                   GROUP_CONCAT(DISTINCT f.name SEPARATOR ', ') AS defauts
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE (LOWER(f.name) LIKE '%bearing%' OR LOWER(f.name) LIKE '%lubrification%')
            GROUP BY a.id, a.name
            HAVING COUNT(DISTINCT 
                CASE 
                    WHEN LOWER(f.name) LIKE '%bearing%' THEN 'bearing'
                    WHEN LOWER(f.name) LIKE '%lubrification%' THEN 'lubrification'
                END) = 2
        """,
        "metadata": {"category": "defauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements actuellement en état sain (healthy) ?",
        "sql": """
            SELECT 
                a.id AS asset_id,
                a.name AS asset_name,
                a.ref,
                a.family_id
            FROM {tenant_db}.assets a
            WHERE a.deleted_at IS NULL
            AND NOT EXISTS (
                SELECT 1 FROM {tenant_db}.asset_faults af
                WHERE af.asset_id = a.id
                    AND af.deleted_at IS NULL
            )
            AND NOT EXISTS (
                SELECT 1 FROM {tenant_db}.alarms al
                WHERE al.asset_id = a.id
                    AND al.ended_at IS NULL
                    AND al.deleted_at IS NULL
            )
            ORDER BY a.id;
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "asset_faults", "alarms"], "tenant_generic": True}
    },
    {
        "question": "Quel équipement a généré le plus d'alarmes sur le dernier mois ?",
        "sql": """
            SELECT a.id, a.name, a.ref, COUNT(al.id) AS nb_alarmes
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.alarms al ON a.id = al.asset_id
            WHERE al.created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            GROUP BY a.id, a.name
            ORDER BY nb_alarmes DESC
            LIMIT 1
        """,
        "metadata": {"category": "alarmes", "tables": ["assets", "alarms"], "tenant_generic": True}
    },
   {
        "question": "Quel est l'équipement prioritaire à traiter selon le niveau de criticité actuel ?",
        "sql": """
            SELECT 
                a.id, a.name, a.ref,
                CASE 
                    WHEN a.status = 5 THEN 'critical'
                    WHEN a.status = 3 THEN 'Moderate'
                    WHEN a.status = 2 THEN 'MID'
                    WHEN a.status = 1 THEN 'Normal'
                    WHEN a.status = 0 THEN 'shut down'
                    WHEN a.status = -1 THEN 'Unassigned'
                    ELSE 'Undefined'
                END AS criticite,
                COUNT(DISTINCT al.id) AS nb_alarmes_actives,
                COUNT(DISTINCT af.id) AS nb_defauts_actifs
            FROM {tenant_db}.assets a
            LEFT JOIN {tenant_db}.alarms al 
                ON a.id = al.asset_id AND al.ended_at IS NULL AND al.deleted_at IS NULL
            LEFT JOIN {tenant_db}.asset_faults af 
                ON a.id = af.asset_id AND af.end_date IS NULL AND af.deleted_at IS NULL
            WHERE a.deleted_at IS NULL
            GROUP BY a.id, a.name, a.ref, a.status
            ORDER BY 
                a.status DESC,           
                nb_alarmes_actives DESC,
                nb_defauts_actifs DESC
            LIMIT 1
        """,
        "metadata": {
            "category": "equipements",
            "tables": ["assets", "alarms", "asset_faults"],
            "tenant_generic": True
        }
    },
    {
        "question": "Liste tous les équipements de {tenant}",
        "sql": """
            SELECT id, name, ref, status, created_at
            FROM {tenant_db}.assets
            WHERE deleted_at IS NULL
            ORDER BY name ASC
            LIMIT 100
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Combien d'équipements avons-nous au total ?",
        "sql": """
            SELECT COUNT(*) AS total_equipements
            FROM {tenant_db}.assets
            WHERE deleted_at IS NULL
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements critiques ?",
        "sql": """
            SELECT a.id, a.name, ac.name AS classe
            FROM {tenant_db}.assets a
            WHERE a.status = 5                        
            AND a.deleted_at IS NULL
            ORDER BY a.name
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "asset_classes"], "tenant_generic": True}
    },
    {
        "question": "les équipements critiques ?",
        "sql": """
            SELECT a.id, a.name, ac.name AS classe
            FROM {tenant_db}.assets a
            WHERE a.status = 5                        
            AND a.deleted_at IS NULL
            ORDER BY a.name
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "asset_classes"], "tenant_generic": True}
    }, 
    {
        "question": "Affiche les équipements sans défauts",
        "sql": """
            SELECT a.id, a.name, a.ref
            FROM {tenant_db}.assets a
            LEFT JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            WHERE af.id IS NULL
            AND a.deleted_at IS NULL
            ORDER BY a.name
            
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels équipements ont des checklists associées ?",
        "sql": """
            SELECT a.id, a.name, a.ref, COUNT(ac.id) AS nb_checklists
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.assignment_checklist ac ON a.id = ac.asset_id
            WHERE a.deleted_at IS NULL
            GROUP BY a.id, a.name
            ORDER BY nb_checklists DESC  
        """,
        "metadata": {"category": "maintenance", "tables": ["assets", "assignment_checklist"], "tenant_generic": True}
    },

    {
        "question": "Quels sont les équipements génériques ?",
        "sql": """
            SELECT id, name, created_at
            FROM v3_tenant_Site_Safi.generic_assets
            ORDER BY created_at DESC
            
        """,
        "metadata": {"category": "equipements", "tables": ["generic_assets"], "tenant_generic": False, "safi_only": True}
    },

    {
        "question": "Quels équipements ont des composants ?",
        "sql": """
            SELECT a.id, a.name, a.ref, COUNT(comp.id) AS nb_composants
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.asset_components comp ON a.id = comp.asset_id
            WHERE a.deleted_at IS NULL
            GROUP BY a.id, a.name
            HAVING nb_composants > 0
            ORDER BY nb_composants DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "asset_components"], "tenant_generic": True}
    },
    {
        "question": "Affiche les équipements avec accouplements",
        "sql": """
            SELECT a.id, a.name, a.ref, COUNT(c.id) AS nb_accouplements
            FROM {tenant_db}.assets a
            INNER JOIN v3_tenant_Site_Safi.couplings c ON a.id = c.asset_id
            WHERE a.deleted_at IS NULL
            GROUP BY a.id, a.name
            ORDER BY nb_accouplements DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "couplings"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels sont les équipements inactifs ?",
        "sql": """
            SELECT id, name, ref, status
            FROM {tenant_db}.assets
            WHERE status = 0                 -INACIF
            AND deleted_at IS NULL
            ORDER BY name
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Donne les équipements créés cette semaine",
        "sql": """
            SELECT id, name, ref, created_at
            FROM {tenant_db}.assets
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            AND deleted_at IS NULL
            ORDER BY created_at DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
 
    {
        "question": "Combien d'équipements par famille ?",
        "sql": """
            SELECT f.name AS famille, COUNT(a.id) AS nb_equipements
            FROM {tenant_db}.families f
            LEFT JOIN {tenant_db}.assets a ON f.id = a.family_id
            WHERE a.deleted_at IS NULL
            GROUP BY f.id, f.name
            ORDER BY nb_equipements DESC
        """,
        "metadata": {"category": "equipements", "tables": ["families", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec diagrammes ?",
        "sql": """
            SELECT a.id, a.name, a.ref, d.name AS diagramme
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.diagrams d ON a.diagram_id = d.id
            WHERE a.deleted_at IS NULL
            ORDER BY a.name
        """,
        "metadata": {"category": "equipements", "tables": ["assets", "diagrams"], "tenant_generic": True}
    },
    {
        "question": "Affiche les équipements par marque",
        "sql": """
            SELECT brand, COUNT(*) AS nb
            FROM {tenant_db}.assets
            WHERE brand IS NOT NULL
            AND deleted_at IS NULL
            GROUP BY brand
            ORDER BY nb DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Quels équipements ont un RPM renseigné ?",
        "sql": """
            SELECT name, ref, rpm
            FROM {tenant_db}.assets
            WHERE rpm IS NOT NULL
            AND deleted_at IS NULL
            ORDER BY rpm DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Donne les équipements avec coordonnées GPS",
        "sql": """
            SELECT name, ref, latitude, longitude
            FROM {tenant_db}.assets
            WHERE latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND deleted_at IS NULL
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements manuels ?",
        "sql": """
            SELECT id, name, ref, is_manual
            FROM {tenant_db}.assets
            WHERE is_manual = 1
            AND deleted_at IS NULL
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements manuels ?",
        "sql": """
            SELECT id, name, ref, is_manual
            FROM {tenant_db}.assets
            WHERE is_manual = 0
            AND deleted_at IS NULL
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
        {
        "question": "Quels sont les équipements en ligne(online) ?",
        "sql": """
            SELECT id, name, ref, is_manual
            FROM {tenant_db}.assets
            WHERE is_manual = 1
            AND deleted_at IS NULL
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Combien d'équipements ont des alarmes actives ?",
        "sql": """
            SELECT COUNT(DISTINCT a.id) AS nb_equipements_avec_alarmes
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.alarms al ON a.id = al.asset_id
            WHERE a.deleted_at IS NULL AND al.ended_at IS NULL
        """,
        "metadata": {"category": "alarmes", "tables": ["assets", "alarms"], "tenant_generic": True}
    },
    {
        "question": "Quels équipements ont des interventions planifiées ?",
        "sql": """
            SELECT a.name, a.ref, COUNT(i.id) AS nb_interventions
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.interventions i ON a.id = i.asset_id
            WHERE i.status IN (0, 1, 2, 3, 4, 5)
            GROUP BY a.id, a.name
            ORDER BY nb_interventions DESC
        """,
        "metadata": {"category": "maintenance", "tables": ["assets", "interventions"], "tenant_generic": True}
    },
    {
        "question": "Affiche les équipements avec leur dernière mesure",
        "sql": """
            SELECT a.id, a.name, a.ref, a.last_measure_created_at AS derniere_mesure_date,
                a.last_measure_id
            FROM {tenant_db}.assets a
            WHERE a.deleted_at IS NULL
            AND a.last_measure_created_at IS NOT NULL
            ORDER BY a.last_measure_created_at DESC;
        """,
        "metadata": {
            "category": "mesures",
            "tables": ["assets"],
            "tenant_generic": True
        }
    },


    {
        "question": "Affiche les équipements par entité",
        "sql": """
            SELECT e.name AS entite, COUNT(a.id) AS nb_equipements
            FROM {tenant_db}.entities e
            LEFT JOIN {tenant_db}.assets a ON e.id = a.entity_id
            WHERE a.deleted_at IS NULL
            GROUP BY e.id, e.name
            ORDER BY nb_equipements DESC
        """,
        "metadata": {"category": "equipements", "tables": ["entities", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec score supérieur ou égal à 20 ?",
        "sql": """
            SELECT name, assets_scores
            FROM {tenant_db}.assets
            WHERE assets_scores > 20
            AND deleted_at IS NULL
            ORDER BY assets_scores DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Combien d'équipements par utilisateur créateur ?",
        "sql": """
            SELECT u.first_name, u.last_name, COUNT(a.id) AS nb_equipements
            FROM {tenant_db}.assets a
            LEFT JOIN i_sense_v3_devenv_db.users u ON a.created_by = u.id
            WHERE a.deleted_at IS NULL
            GROUP BY u.id, u.first_name, u.last_name
            ORDER BY nb_equipements DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True, "cross_database": True}
    },
    {
        "question": "Quels équipements ont un RUL (Remaining Useful Life) calculé ?",
        "sql": """
            SELECT name, ref, rul
            FROM {tenant_db}.assets
            WHERE rul IS NOT NULL
            AND deleted_at IS NULL
            ORDER BY rul ASC
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Donne les équipements avec détection d'anomalies",
        "sql": """
            SELECT name, ref, outlier_detection
            FROM {tenant_db}.assets
            WHERE outlier_detection IS NOT NULL
            AND deleted_at IS NULL
            ORDER BY outlier_detection DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec modèle 3D ?",
        "sql": """
            SELECT a.name, a.ref, a.3d_model_id
            FROM {tenant_db}.assets a
            WHERE a.3d_model_id IS NOT NULL
            AND a.deleted_at IS NULL
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    {
        "question": "Affiche les équipements avec leur durée de transition",
        "sql": """
            SELECT name, ref, transition_duration
            FROM {tenant_db}.assets
            WHERE transition_duration IS NOT NULL
            AND deleted_at IS NULL
            ORDER BY transition_duration DESC
        """,
        "metadata": {"category": "equipements", "tables": ["assets"], "tenant_generic": True}
    },
    
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 2 : DÉFAUTS (FAULTS) - 50 questions
    # ═══════════════════════════════════════════════════════════════
    
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Normal' ?",
        "sql": """
        SELECT DISTINCT a.id, a.name, a.ref 
        FROM {tenant_db}.assets a 
        JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
        JOIN {tenant_db}.faults f ON af.fault_id = f.id 
        WHERE (f.name = 'Normal' OR f.name LIKE '%Normal%') AND af.end_date IS NULL AND af.deleted_at IS NULL
        ORDER BY a.id
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
        
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Bearing Wear - Rolling Element' (usure roulement - élément roulant) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Bearing Wear - Rolling Element' OR f.name LIKE '%roulement%' OR f.name LIKE '%rolling%')
              AND af.end_date IS NULL
              AND af.deleted_at IS NULL
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Bearing Wear - Inner Race' (usure roulement - bague intérieure) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Bearing Wear - Inner Race' OR f.name LIKE '%Inner Race%' OR f.name LIKE '%bague intérieure%') AND af.end_date IS NULL AND af.deleted_at IS NULL ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Bearing Wear - Outer Race' (usure roulement - bague extérieure) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Bearing Wear - Outer Race' OR f.name LIKE '%Outer Race%' OR f.name LIKE '%bague extérieure%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Outliers' (valeurs aberrantes) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Outliers' OR f.name LIKE '%aberrant%' OR f.name LIKE '%outlier%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Sensor Saturation' (saturation capteur) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Sensor Saturation' OR f.name LIKE '%saturation%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Fault sensor' (défaut capteur) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Fault sensor' OR f.name LIKE '%fault capteur%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Friction' (frottement) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Friction' OR f.name LIKE '%frottement%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Structural Fault' (défaut structurel) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Structural Fault' OR f.name LIKE '%structurel%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Bearing Wear' (usure de roulement générique) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Bearing Wear' OR f.name LIKE '%bearing%' OR f.name LIKE '%roulement%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Cavitation Fault' (défaut de cavitation) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Cavitation Fault' OR f.name LIKE '%cavitation%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'AC Electrical Fault' (défaut électrique AC) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'AC Electrical Fault' OR f.name LIKE '%AC%' OR f.name LIKE '%électrique%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'DC Electrical Fault' (défaut électrique DC) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'DC Electrical Fault' OR f.name LIKE '%DC%' OR f.name LIKE '%électrique%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Aerial Fault' (défaut aéraulique) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Aerial Fault' OR f.name LIKE '%aéraulique%' OR f.name LIKE '%aerial%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Gear Fault' (défaut d'engrenage) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Gear Fault' OR f.name LIKE '%gear%' OR f.name LIKE '%engrenage%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Imbalance' (balourd) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Imbalance' OR f.name LIKE '%balourd%' OR f.name LIKE '%déséquilibre%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Mechanical looseness' (desserrage mécanique) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Mechanical looseness' OR f.name LIKE '%looseness%' OR f.name LIKE '%desserrage%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Lubrification' (lubrification) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Lubrification' OR f.name LIKE '%lubrification%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Misalignment' (défaut d'alignement) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Misalignment' OR f.name LIKE '%alignement%' OR f.name LIKE '%misalignment%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Turbulence d'huile' (turbulence d'huile) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Turbulence d''huile' OR f.name LIKE '%turbulence%' OR f.name LIKE '%huile%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Belt Fault' (défaut de courroie) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Belt Fault' OR f.name LIKE '%belt%' OR f.name LIKE '%courroie%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'shutdown' (arrêt) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'shutdown' OR f.name LIKE '%arrêt%' OR f.name LIKE '%shutdown%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les équipements avec un défaut actif de type 'Ski slope' (pente de ski / problème de mesure) ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref 
            FROM {tenant_db}.assets a 
            JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id 
            JOIN {tenant_db}.faults f ON af.fault_id = f.id 
            WHERE (f.name = 'Ski slope' OR f.name LIKE '%ski%' OR f.name LIKE '%pente%' OR f.name LIKE '%mesure%') 
              AND af.end_date IS NULL 
              AND af.deleted_at IS NULL 
             ORDER BY a.id;
        """,
        "metadata": {"category": "défauts", "tables": ["assets", "asset_faults", "faults"], "tenant_generic": True}
    },

    {
        "question": "Quels sont les types de défauts les plus fréquents ?",
        "sql": """
            SELECT f.name, COUNT(af.id) AS nb_occurrences
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.deleted_at IS NULL
            GROUP BY f.id, f.name
            ORDER BY nb_occurrences DESC
            LIMIT 20
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    },

    {
        "question": "Combien de défauts actifs avons-nous ?",
        "sql": """
            SELECT COUNT(*) AS nb_defauts_actifs
            FROM {tenant_db}.asset_faults
            WHERE deleted_at IS NULL
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les défauts résolus cette semaine ?",
        "sql": """
            SELECT af.id, a.name AS asset_name, f.name AS fault_name,
                af.start_date, af.end_date, af.duration
            FROM {tenant_db}.asset_faults af
            JOIN {tenant_db}.assets a ON af.asset_id = a.id
            JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.end_date IS NOT NULL
            AND af.end_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
            AND af.end_date < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY)
            AND af.deleted_at IS NULL
            ORDER BY af.end_date DESC;
        """,
        "metadata": {"category": "defauts", "tables": ["assets","asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quelle est la durée moyenne des défauts ?",
        "sql": """
            SELECT AVG(duration) AS duree_moyenne_heures
            FROM {tenant_db}.asset_faults
            WHERE duration IS NOT NULL
            AND deleted_at IS NULL
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels défauts ont une durée supérieure à 100 heures ?",
        "sql": """
            SELECT a.name, a.ref, f.name, af.duration
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.assets a ON af.asset_id = a.id
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.duration > 100
            ORDER BY af.duration DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "assets", "faults"], "tenant_generic": True}
    },
    {
        "question": "Donne les défauts par famille",
        "sql": """
            SELECT fam.name AS famille, COUNT(af.id) AS nb_defauts
            FROM v3_tenant_Site_Safi.families fam
            INNER JOIN v3_tenant_Site_Safi.family_fault ff ON fam.id = ff.family_id
            INNER JOIN v3_tenant_Site_Safi.faults f ON ff.fault_id = f.id
            INNER JOIN {tenant_db}.asset_faults af ON f.id = af.fault_id
            GROUP BY fam.id, fam.name
            ORDER BY nb_defauts DESC
        """,
        "metadata": {"category": "defauts", "tables": ["families", "family_fault", "faults", "asset_faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels sont les défauts récurrents ?",
        "sql": """
            SELECT f.name, COUNT(af.id) AS nb_repetitions
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            GROUP BY f.id, f.name
            HAVING nb_repetitions > 5
            ORDER BY nb_repetitions DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Affiche les défauts avec leur pourcentage de probabilité",
        "sql": """
            SELECT a.name, a.ref, f.name AS faults, af.percentage
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.assets a ON af.asset_id = a.id
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.percentage IS NOT NULL
            ORDER BY af.percentage DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "assets", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels défauts ont été traités par l'utilisateur X ?",
        "sql": """
            SELECT f.name, af.treated_by
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.treated_by = (SELECT id FROM i_sense_v3_devenv_db.users WHERE first_name = 'X')
            ORDER BY af.start_date DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True, "cross_database": True}
    },
    {
        "question": "Combien de défauts par mois ?",
        "sql": """
            SELECT DATE_FORMAT(af.start_date, '%Y-%m') AS mois, COUNT(*) AS nb_defauts
            FROM {tenant_db}.asset_faults af
            WHERE af.start_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY mois
            ORDER BY mois DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les défauts sans recommandations ?",
        "sql": """
            SELECT f.name, COUNT(af.id) AS nb_occurrences
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.asset_faults af ON f.id = af.fault_id
            LEFT JOIN {tenant_db}.recommendation_faults rf ON f.id = rf.fault_id
            WHERE rf.fault_id IS NULL
            GROUP BY f.id, f.name
            ORDER BY nb_occurrences DESC
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "asset_faults", "recommendation_faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Donne les défauts avec leurs causes",
        "sql": """
            SELECT f.name, c.name AS cause_fault
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.cause_fault cf ON f.id = cf.fault_id
            INNER JOIN {tenant_db}.causes c ON cf.cause_id = c.id
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "cause_fault", "causes"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels défauts nécessitent un RPM ?",
        "sql": """
            SELECT name, require_rpm
            FROM {tenant_db}.faults
            WHERE require_rpm = 1
            ORDER BY name
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Affiche les défauts verrouillés",
        "sql": """
            SELECT name, locked
            FROM {tenant_db}.faults
            WHERE locked = 1
            ORDER BY name
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels sont les défauts créés ce mois-ci ?",
        "sql": """
            SELECT f.name, af.start_date
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.start_date >= DATE_FORMAT(NOW(), '%Y-%m-01')
            ORDER BY af.start_date DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Combien de défauts par équipement ?",
        "sql": """
            SELECT a.id, a.name, a.ref, COUNT(af.id) AS nb_defauts
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            GROUP BY a.id, a.name
            ORDER BY nb_defauts DESC
        """,
        "metadata": {"category": "defauts", "tables": ["assets", "asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les défauts avec mesures associées ?",
        "sql": """
            SELECT f.name, COUNT(mf.id) AS nb_mesures
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.asset_faults af ON f.id = af.fault_id
            INNER JOIN {tenant_db}.measurements_faults mf ON af.id = mf.fault_id
            GROUP BY f.id, f.name
            ORDER BY nb_mesures DESC
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "asset_faults", "measurements_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels défauts ont des opérations associées ?",
        "sql": """
            SELECT f.id, f.name, o.name AS operation
            FROM {v3_tenant_Site_Safi}.faults f
            INNER JOIN {v3_tenant_Site_Safi}.family_fault ff ON f.id = ff.fault_id
            INNER JOIN {v3_tenant_Site_Safi}.family_fault_operations ffo ON ff.id = ffo.family_fault_id
            INNER JOIN {v3_tenant_Site_Safi}.operations o ON ffo.operation_id = o.id
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "family_fault", "family_fault_operations", "operations"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Affiche les défauts avec prérequis",
        "sql": """
            SELECT f.id, f.name, fp.extrafield_id
            FROM {v3_tenant_Site_Safi}.faults f
            INNER JOIN {v3_tenant_Site_Safi}.fault_prerequis fp ON f.id = fp.fault_id
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "fault_prerequis"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Combien de défauts résolus vs actifs ?",
        "sql": """
          SELECT 
            CASE 
                WHEN end_date IS NULL THEN 'Actifs'
                ELSE 'Résolus'
            END AS statut,
            COUNT(*) AS nb_defauts
        FROM {tenant_db}.asset_faults
        WHERE deleted_at IS NULL
        GROUP BY statut
        ORDER BY nb_defauts DESC;
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels défauts ont un pourcentage de feature ?",
        "sql": """
            SELECT f.name, fp.percentage_feature
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.faults_percentage fp ON f.id = fp.fault_id
            WHERE fp.percentage_feature IS NOT NULL
            ORDER BY fp.percentage_feature DESC
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "faults_percentage"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Donne les défauts avec leur date de début",
        "sql": """
            SELECT f.name, af.start_date, af.end_date, af.status
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.end_date IS NULL
            ORDER BY af.start_date DESC
      
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les défauts avec end_date renseignée ?",
        "sql": """
            SELECT f.name, af.end_date, af.duration
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.end_date IS NOT NULL
            ORDER BY af.end_date DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    }, 
    {
        "question": "Affiche les défauts par point de mesure",
        "sql": """
            SELECT mp.name AS point, COUNT(af.id) AS nb_defauts
            FROM {tenant_db}.measurement_points mp
            INNER JOIN {tenant_db}.asset_faults af ON mp.id = af.point_id
            GROUP BY mp.id, mp.name
            ORDER BY nb_defauts DESC
        """,
        "metadata": {"category": "defauts", "tables": ["measurement_points", "asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels défauts ont des sous-équipements ?",
        "sql": """
            SELECT f.name, af.sub_asset_id
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.sub_asset_id IS NOT NULL
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Combien de défauts par état ?",
        "sql": """
            SELECT etats, COUNT(*) AS nb
            FROM {tenant_db}.asset_faults
            WHERE etats IS NOT NULL
            GROUP BY etats
            ORDER BY nb DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les défauts avec start_measure_id ?",
        "sql": """
            SELECT f.name, af.start_measure_id
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.start_measure_id IS NOT NULL
            ORDER BY af.start_date DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Donne les défauts avec end_measure_id",
        "sql": """
            SELECT f.name, af.end_measure_id
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.end_measure_id IS NOT NULL
            ORDER BY af.end_date DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Quels défauts sont liés à des alarmes ?",
        "sql": """
            SELECT DISTINCT f.name
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.asset_faults af ON f.id = af.fault_id
            INNER JOIN {tenant_db}.assets a ON af.asset_id = a.id
            INNER JOIN {tenant_db}.alarms al ON a.id = al.asset_id
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "asset_faults", "assets", "alarms"], "tenant_generic": True}
    },
    {
        "question": "Affiche les défauts avec leur image",
        "sql": """
            SELECT name, image_path
            FROM {tenant_db}.faults
            WHERE image_path IS NOT NULL
            ORDER BY name
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels sont les défauts pour équipements ?",
        "sql": """
            SELECT name, is_asset
            FROM {tenant_db}.faults
            ORDER BY name
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels sont les défauts ?",
        "sql": """
            SELECT name, is_asset
            FROM {tenant_db}.faults
            ORDER BY name
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Combien de défauts par jour cette semaine ?",
        "sql": """
            SELECT DATE(af.start_date) AS jour, COUNT(*) AS nb_defauts
            FROM {tenant_db}.asset_faults af
            WHERE af.start_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY jour
            ORDER BY jour DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels défauts ont été créés aujourd'hui ?",
        "sql": """
            SELECT f.name, af.start_date
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE DATE(af.start_date) = CURDATE()
            ORDER BY af.start_date DESC
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults", "faults"], "tenant_generic": True}
    },
    {
        "question": "Donne les défauts avec description",
        "sql": """
            SELECT name, description
            FROM {tenant_db}.faults
            WHERE description IS NOT NULL 
            ORDER BY name
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels sont les défauts sans description ?",
        "sql": """
            SELECT name
            FROM {tenant_db}.faults
            WHERE description IS NULL OR description = ''
            ORDER BY name
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Affiche les défauts avec updated_at",
        "sql": """
            SELECT name, updated_at
            FROM {tenant_db}.faults
            WHERE updated_at IS NOT NULL
            ORDER BY updated_at DESC
         
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels défauts récent ?",
        "sql": """
            SELECT name, created_at
            FROM {tenant_db}.faults
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY created_at DESC
        """,
        "metadata": {"category": "defauts", "tables": ["faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Combien de défauts ont été supprimés (soft delete) ?",
        "sql": """
            SELECT COUNT(*) AS nb_supprimes
            FROM {tenant_db}.asset_faults
            WHERE deleted_at IS NOT NULL
        """,
        "metadata": {"category": "defauts", "tables": ["asset_faults"], "tenant_generic": True}
    },
    {
        "question": "Quels sont les défauts avec asset_parent_id ?",
        "sql": """
            SELECT f.name, al.asset_parent_id
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.faults f ON al.asset_id = f.id
            WHERE al.asset_parent_id IS NOT NULL
            ORDER BY al.created_at DESC
        """,
        "metadata": {"category": "defauts", "tables": ["alarms", "faults"], "tenant_generic": True}
    },
    {
        "question": "Donne les défauts liés à des devices",
        "sql": """
            SELECT f.name, d.ref AS device_ref
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.asset_faults af ON f.id = af.fault_id
            INNER JOIN {tenant_db}.assets a ON af.asset_id = a.id
            INNER JOIN i_sense_v3_devenv_db.devices d ON a.id = d.id
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "asset_faults", "assets"], "tenant_generic": True, "cross_database": True}
    },
    {
        "question": "Quels défauts ont des recommendations_v3 ?",
        "sql": """
            SELECT f.name, COUNT(r.id) AS nb_recommendations
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.recommendation_faults rf ON f.id = rf.fault_id
            INNER JOIN {tenant_db}.recommendations_v3 r ON rf.recommendation_id = r.id
            GROUP BY f.id, f.name
            ORDER BY nb_recommendations DESC
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "recommendation_faults", "recommendations_v3"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Affiche les défauts avec probability",
        "sql": """
            SELECT f.name, rf.probability
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.recommendation_faults rf ON f.id = rf.fault_id
            WHERE rf.probability IS NOT NULL
            ORDER BY rf.probability DESC
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "recommendation_faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels sont les défauts avec actions_fault ?",
        "sql": """
            SELECT f.name, act.name AS action_name
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.asset_faults af ON f.id = af.fault_id
            LEFT JOIN {tenant_db}.actions_fault af_act ON af.id = af_act.fault_id
            LEFT JOIN {tenant_db}.actions act ON af_act.action_id = act.id
            WHERE act.id IS NOT NULL
            ORDER BY f.name
        """, 
        "metadata": {"category": "defauts", "tables": ["faults", "asset_faults", "actions_fault", "actions"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Combien de défauts ont des activity_log ?",
        "sql": """
            SELECT COUNT(DISTINCT al.subject_id) AS nb_defauts_avec_logs
            FROM {tenant_db}.activity_log al
            WHERE al.subject_type = 'App\\Models\\Asset'
        """,
        "metadata": {"category": "defauts", "tables": ["activity_log"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels défauts sont associés à des interventions ?",
        "sql": """
            SELECT DISTINCT f.name
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.asset_faults af ON f.id = af.fault_id
            INNER JOIN {tenant_db}.interventions i ON af.asset_id = i.asset_id
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "asset_faults", "interventions"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Donne les défauts avec checklists",
        "sql": """
            SELECT f.name, c.name AS checklist
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.family_fault ff ON f.id = ff.fault_id
            INNER JOIN {tenant_db}.families fam ON ff.family_id = fam.id
            INNER JOIN {tenant_db}.checklists c ON fam.id = c.family_id
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "family_fault", "families", "checklists"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quels sont les défauts avec measurements_faults ?",
        "sql": """
            SELECT f.name, COUNT(mf.id) AS nb_liaisons
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.measurements_faults mf ON f.id = mf.fault_id
            GROUP BY f.id, f.name
            ORDER BY nb_liaisons DESC
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "measurements_faults"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Affiche les défauts avec pdm_detection",
        "sql": """
            SELECT f.name, pd.id AS pdm_id
            FROM {tenant_db}.faults f
            INNER JOIN {tenant_db}.pdm_detection pd ON f.id = pd.faults
            ORDER BY f.name
        """,
        "metadata": {"category": "defauts", "tables": ["faults", "pdm_detection"], "tenant_generic": False, "safi_only": True}
    },
    
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 3 : ALARMES (ALARMS) - 20 questions
    # ═══════════════════════════════════════════════════════════════
    
    {
        "question": "Quelles sont les dernières alarmes survenues ?",
        "sql": """
            SELECT al.id AS alarm_id, al.asset_id, a.name AS equipment_name,
                al.status, al.created_at, al.ended_at, al.duration
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.ended_at IS NULL AND al.deleted_at IS NULL
            ORDER BY al.created_at DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quelles alarmes sont actuellement actives ?",
        "sql": """
            SELECT al.id AS alarm_id, al.asset_id, a.name AS equipment_name,
                al.created_at, TIMESTAMPDIFF(HOUR, al.created_at, NOW()) AS heures_actives,
                'Active' AS statut
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.ended_at IS NULL AND al.deleted_at IS NULL
            ORDER BY al.created_at DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Équipements en état d'arrêt mais avec des alarmes actives ?",
        "sql": """
            SELECT DISTINCT a.id, a.name, a.ref, a.status,
                COUNT(al.id) AS nb_alarmes_actives
            FROM {tenant_db}.assets a
            JOIN {tenant_db}.alarms al ON a.id = al.asset_id
            WHERE a.status = 0                  
            AND al.ended_at IS NULL             
            AND al.deleted_at IS NULL
            AND a.deleted_at IS NULL
            GROUP BY a.id, a.name, a.ref, a.status
            ORDER BY nb_alarmes_actives DESC;
        """,
        "metadata": {
            "category": "alarmes",
            "tables": ["assets", "alarms"],
            "tenant_generic": True,
            "description": "Retourne les équipements en état 'shut down' (a.status=0) mais qui ont encore des alarmes actives (ended_at IS NULL)."
        }
    },
    {
        "question": "Quels équipements ont le plus d'alarmes ?",
        "sql": """
            SELECT a.id AS asset_id, a.name AS equipment_name, a.ref,
                COUNT(al.id) AS nb_alarmes,
                MAX(al.created_at) AS derniere_alarme
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.deleted_at IS NULL
            GROUP BY a.id, a.name
            ORDER BY nb_alarmes DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quelles sont les alarmes de lubrification ?",
        "sql": """
            SELECT la.id AS alarm_id, la.config_id, la.status, la.created_at, la.deleted_at,
                'Lubrification' AS type_alarme
            FROM {tenant_db}.lubrication_alarms la
            WHERE la.deleted_at IS NULL
            ORDER BY la.created_at DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["lubrication_alarms"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Quelle est la durée des alarmes ?",
        "sql": """
            SELECT al.id AS alarm_id, a.name AS equipment_name, a.ref, al.duration,
                al.created_at, al.ended_at,
                CASE WHEN al.duration IS NULL THEN 'En cours' ELSE 'Terminée' END AS statut_duree
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.duration IS NOT NULL AND al.deleted_at IS NULL
            ORDER BY al.duration DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Statistiques des alarmes par mois ?",
        "sql": """
            SELECT DATE_FORMAT(al.created_at, '%Y-%m') AS mois,
                COUNT(*) AS nb_alarmes,
                AVG(al.duration) AS duree_moyenne
            FROM {tenant_db}.alarms al
            WHERE al.created_at >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            AND al.deleted_at IS NULL
            GROUP BY mois
            ORDER BY mois DESC
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms"], "tenant_generic": True}
    },
    {
        "question": "Alarmes avec device associé ?",
        "sql": """
            SELECT al.id AS alarm_id, a.name AS equipment_name, al.asset_id, al.device_id,
                d.id AS device_id_global, d.ref AS device_ref, d.mac AS device_mac,
                d.status AS device_status, d.product_id, d.company_id, al.created_at
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            LEFT JOIN i_sense_v3_devenv_db.devices d ON al.device_id = d.id
            WHERE al.deleted_at IS NULL AND d.deleted_at IS NULL
            ORDER BY al.created_at DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True, "cross_database": True}
    },
    {
        "question": "Combien d'alarmes cette semaine ?",
        "sql": """
            SELECT DATE(al.created_at) AS jour, COUNT(*) AS nb_alarmes
            FROM {tenant_db}.alarms al
            WHERE al.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            AND al.deleted_at IS NULL
            GROUP BY jour
            ORDER BY jour DESC
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms"], "tenant_generic": True}
    },
    {
        "question": "Quelles alarmes ont été créées aujourd'hui ?",
        "sql": """
            SELECT al.id, a.name AS equipment_name, a.ref, al.created_at, al.status
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE DATE(al.created_at) = CURDATE()
            AND al.deleted_at IS NULL
            ORDER BY al.created_at DESC
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Alarmes par équipement à {tenant} ?",
        "sql": """
            SELECT a.id, a.name, a.ref, COUNT(al.id) AS nb_alarmes
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.deleted_at IS NULL
            GROUP BY a.id, a.name
            ORDER BY nb_alarmes DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quelles alarmes sont non résolues depuis plus de 24h ?",
        "sql": """
            SELECT al.id, a.name AS equipment_name, a.ref, al.status, al.created_at,
                TIMESTAMPDIFF(HOUR, al.created_at, NOW()) AS heures_actives
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.created_at < DATE_SUB(NOW(), INTERVAL 24 HOUR)
            AND al.deleted_at IS NULL
            ORDER BY heures_actives DESC
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quelle est la dernière alarme de l'état d'arrêt (statut 0)  par équipement ?",
        "sql": """
            SELECT a.id, a.name, a.ref, MAX(al.created_at) AS derniere_alarme
            FROM {tenant_db}.alarms al 
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.status = 0 AND al.deleted_at IS NULL 
            GROUP BY a.id, a.name, a.ref 
            ORDER BY derniere_alarme DESC
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quelle est la dernière alarme de l'état normal (statut 1) par équipement ?",
        "sql": """
            SELECT a.id, a.name, a.ref, MAX(al.created_at) AS derniere_alarme
            FROM {tenant_db}.alarms al 
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.status = 1 AND al.deleted_at IS NULL 
            GROUP BY a.id, a.name, a.ref 
            ORDER BY derniere_alarme DESC
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quelle est la dernière alarme par équipement ?",
        "sql": """
            SELECT a.id, a.name, a.ref, MAX(al.created_at) AS derniere_alarme 
            FROM {tenant_db}.alarms al 
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.deleted_at IS NULL 
            GROUP BY a.id, a.name, a.ref 
            ORDER BY derniere_alarme DESC
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Top 10 des équipements par date de dernière alarme ?",
        "sql": """
            SELECT a.id, a.name, a.ref, MAX(al.created_at) AS derniere_alarme, COUNT(al.id) AS nb_alarmes
            FROM {tenant_db}.alarms al 
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id 
            WHERE al.deleted_at IS NULL 
            GROUP BY a.id, a.name, a.ref
            ORDER BY derniere_alarme DESC LIMIT 10
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quelles alarmes ont un device_id renseigné ?",
        "sql": """
            SELECT al.id, al.device_id, a.name AS equipment_name, a.ref
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.device_id IS NOT NULL AND al.deleted_at IS NULL
            ORDER BY al.created_at DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Durée moyenne des alarmes par équipement ?",
        "sql": """
            SELECT a.name, a.ref, AVG(al.duration) AS duree_moyenne_heures
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.duration IS NOT NULL AND al.deleted_at IS NULL
            GROUP BY a.id, a.name, a.ref
            ORDER BY duree_moyenne_heures DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    { 
        "question": "Alarmes avec measure_id associé ?",
        "sql": """
            SELECT al.id, al.measure_id, a.name AS equipment_name, a.ref, al.created_at
            FROM {tenant_db}.alarms al
            INNER JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.measure_id IS NOT NULL AND al.deleted_at IS NULL
            ORDER BY al.created_at DESC
            
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms", "assets"], "tenant_generic": True}
    },
    {
        "question": "Combien d'alarmes supprimées (soft delete) ?",
        "sql": """
            SELECT COUNT(*) AS nb_alarmes_supprimees
            FROM {tenant_db}.alarms
            WHERE deleted_at IS NOT NULL
        """,
        "metadata": {"category": "alarmes", "tables": ["alarms"], "tenant_generic": True}
    },
    
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 4 : MESURES (MEASUREMENTS) - 10 questions
    # ═══════════════════════════════════════════════════════════════
    {
        "question": "Quel équipement (parent) a la valeur NGV la plus élevée aujourd'huit ?",
        "sql": """
        SELECT 
            a.id AS asset_id,
            a.name AS asset_name,
            a.ref,
            fm.value AS ngv_value,
            fg.alarm AS seuil_alarm,
            (fm.value - fg.alarm) AS depassement
        FROM {tenant_db}.feature_measurement fm
        JOIN {tenant_db}.assets a ON fm.asset_parent_id = a.id
        JOIN {tenant_db}.feature_group fg ON fm.feature_id = fg.feature_id AND fm.group_id = fg.group_id
        JOIN i_sense_v3_devenv_db.features f ON fm.feature_id = f.id
        WHERE f.name = 'NGV'
        AND fm.created_at >= CURDATE()
        AND fm.created_at < CURDATE() + INTERVAL 1 DAY
        AND fm.value > fg.alarm
        AND fm.deleted_at IS NULL
        AND a.deleted_at IS NULL
        ORDER BY depassement DESC
        LIMIT 1;
        """,
        "metadata": {
            "category": "predictions",
            "tables": ["feature_measurement", "assets", "feature_group", "i_sense_v3_devenv_db.features", "asset_faults", "faults"],
            "tenant_generic": True
        }
    },
    

 
    {
        "question": "Liste des détections où la sévérité roulement (severity_bearing) dépasse 0.8, avec le nom de l'équipement parent",
        "sql": """
            SELECT a.id, a.name, a.ref, pd.severity_bearing, pd.measure_id, pd.created_at
            FROM {tenant_db}.pdm_detection pd
            INNER JOIN {tenant_db}.assets a ON pd.parent_id = a.id
            WHERE pd.severity_bearing > 0.8
            ORDER BY pd.severity_bearing DESC
            
        """,
        "metadata": {"category": "predictions", "tables": ["pdm_detection", "assets"], "tenant_generic": True}
    },
    {
        "question": "Pourcentage de lubrification (percentage_lubrification) moyen par famille d'équipement parent",
        "sql": """
            SELECT a.family_id, f.name AS family_name, 
                   AVG(pd.percentage_lubrification) AS avg_lubrification,
                   COUNT(pd.id) AS nb_detections
            FROM {tenant_db}.pdm_detection pd
            INNER JOIN {tenant_db}.assets a ON pd.parent_id = a.id
            INNER JOIN {tenant_db}.families f ON a.family_id = f.id
            WHERE pd.percentage_lubrification IS NOT NULL
            GROUP BY a.family_id, f.name
            ORDER BY avg_lubrification DESC
        """,
        "metadata": {"category": "predictions", "tables": ["pdm_detection", "assets", "families"], "tenant_generic": True}
    },

    {
        "question": "Dernières 20 détections où le RMS vitesse (rms_vel) dépasse le seuil d'alarme vitesse (Seuil_Alarm_Vitesse)",
        "sql": """
            SELECT pd.id, pd.parent_id, a.name AS parent_asset, pd.rms_vel, pd.Seuil_Alarm_Vitesse,
                   (pd.rms_vel - pd.Seuil_Alarm_Vitesse) AS ecart, pd.created_at
            FROM {tenant_db}.pdm_detection pd
            INNER JOIN {tenant_db}.assets a ON pd.parent_id = a.id
            WHERE pd.rms_vel > pd.Seuil_Alarm_Vitesse
              AND pd.rms_vel IS NOT NULL
              AND pd.Seuil_Alarm_Vitesse IS NOT NULL
            ORDER BY pd.created_at DESC
            LIMIT 20
        """,
        "metadata": {"category": "predictions", "tables": ["pdm_detection", "assets"], "tenant_generic": True}
    },
    {
        "question": "Top 10 des mesures avec le plus grand écart entre l'amplitude max de vitesse et son seuil d'alerte",
        "sql": """
            SELECT pd.id, pd.parent_id, a.name, pd.max_amplitude_vel, pd.Seuil_Alert_Vitesse,
                   (pd.max_amplitude_vel - pd.Seuil_Alert_Vitesse) AS delta
            FROM {tenant_db}.pdm_detection pd
            INNER JOIN {tenant_db}.assets a ON pd.parent_id = a.id
            WHERE pd.max_amplitude_vel IS NOT NULL AND pd.Seuil_Alert_Vitesse IS NOT NULL
            ORDER BY delta DESC
            LIMIT 10
        """,
        "metadata": {"category": "predictions", "tables": ["pdm_detection", "assets"], "tenant_generic": True}
    },
    {
        "question": "Quelles sont les dernières mesures par équipement ?",
        "sql": """
            SELECT m.id AS measurement_id, m.asset_id, a.name AS equipment_name, a.ref,
                m.status, m.created_at AS measurement_date, m.is_online
            FROM {tenant_db}.measurements m
            INNER JOIN {tenant_db}.assets a ON m.asset_id = a.id
            WHERE m.deleted_at IS NULL AND a.deleted_at IS NULL
            ORDER BY m.created_at DESC
            
        """,
        "metadata": {"category": "mesures", "tables": ["measurements", "assets"], "tenant_generic": True}
    },
    {
        "question": "Mesures par point de mesure ?",
        "sql": """
            SELECT mp.id AS point_id, mp.name AS point_name, mp.asset_id,
                a.name AS equipment_name, a.ref, COUNT(m.id) AS nb_mesures, m.status
            FROM {tenant_db}.measurement_points mp
            INNER JOIN {tenant_db}.assets a ON mp.asset_id = a.id
            LEFT JOIN {tenant_db}.measurements m ON mp.id = m.point_id
            WHERE mp.deleted_at IS NULL
            GROUP BY mp.id, mp.name, mp.asset_id, a.name, m.status
            ORDER BY nb_mesures DESC
            
        """,
        "metadata": {"category": "mesures", "tables": ["measurement_points", "assets", "measurements"], "tenant_generic": True}
    },
    {
        "question": "Mesures avec signaux associés ?",
        "sql": """
            SELECT ms.id AS signal_id, ms.measure_id, ms.signal_id, ms.value,
                ms.point_id, ms.treated, ms.created_at
            FROM {tenant_db}.measurement_signal ms
            WHERE ms.deleted_at IS NULL
            ORDER BY ms.created_at DESC
            
        """,
        "metadata": {"category": "mesures", "tables": ["measurement_signal"], "tenant_generic": True}
    },
    {
        "question": "Mesures liées aux défauts ?",
        "sql": """
            SELECT mf.id AS liaison_id, mf.measure_id, mf.fault_id, af.asset_id,
                a.name AS equipment_name, f.name AS defect_type,
                mf.percentage, mf.status, mf.created_at
            FROM {tenant_db}.measurements_faults mf
            INNER JOIN {tenant_db}.asset_faults af ON mf.fault_id = af.id
            INNER JOIN {tenant_db}.assets a ON af.asset_id = a.id
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE mf.deleted_at IS NULL
            ORDER BY mf.created_at DESC
           =
        """,
        "metadata": {"category": "mesures", "tables": ["measurements_faults", "asset_faults", "assets", "faults"], "tenant_generic": True}
    },
    {
        "question": "Features par device ?",
        "sql": """
            SELECT fd.id AS liaison_id, fd.feature_id, fd.device_id,
                d.ref AS device_ref, f.name AS feature_name, fd.created_at
            FROM i_sense_v3_devenv_db.features_device fd
            INNER JOIN i_sense_v3_devenv_db.features f ON fd.feature_id = f.id
            LEFT JOIN i_sense_v3_devenv_db.devices d ON fd.device_id = d.id
            WHERE fd.deleted_at IS NULL
            ORDER BY fd.created_at DESC
            
        """,
        "metadata": {"category": "mesures", "tables": ["features_device", "features", "devices"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Configurations d'acquisition ?",
        "sql": """
            SELECT ac.id AS config_id, ac.name, ac.description,
                ac.sampling, ac.duration, ac.overlap, ac.created_at
            FROM i_sense_v3_devenv_db.acquisition_configurations ac
            WHERE ac.deleted_at IS NULL
            ORDER BY ac.created_at DESC
            
        """,
        "metadata": {"category": "mesures", "tables": ["acquisition_configurations"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Grandeurs par feature ?",
        "sql": """
            SELECT f.id AS feature_id, f.name AS feature_name,
                g.id AS grandeur_id, g.name AS grandeur_name, g.type,
                g.grandeur_category_id, gc.name AS grandeur_category
            FROM i_sense_v3_devenv_db.features f
            LEFT JOIN i_sense_v3_devenv_db.product_grandeurs pg ON f.id = pg.product_id
            LEFT JOIN i_sense_v3_devenv_db.grandeurs g ON pg.grandeur_id = g.id
            LEFT JOIN i_sense_v3_devenv_db.grandeur_categories gc ON g.grandeur_category_id = gc.id
            WHERE f.deleted_at IS NULL
            ORDER BY f.name
           
        """,
        "metadata": {"category": "mesures", "tables": ["features", "product_grandeurs", "grandeurs", "grandeur_categories"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Mesures tarifées ?",
        "sql": """
            SELECT m.id AS measure_id, m.name AS measure_name,
                tm.tarif_id, t.identifiant AS tarif_identifiant,
                t.cost, t.type_cost, tm.created_at
            FROM {tenant_db}.measures m
            INNER JOIN {tenant_db}.tarif_measures tm ON m.id = tm.measure_id
            LEFT JOIN {tenant_db}.tarifs t ON tm.tarif_id = t.id
            ORDER BY tm.created_at DESC
            
        """,
        "metadata": {"category": "mesures", "tables": ["measures", "tarif_measures", "tarifs"], "tenant_generic": True}
    },
    {
        "question": "Features manuelles saisies ?",
        "sql": """
            SELECT mf.my_row_id AS feature_id, mf.feature_id,
                f.name AS feature_name, mf.deleted_at
            FROM i_sense_v3_devenv_db.manual_features mf
            LEFT JOIN i_sense_v3_devenv_db.features f ON mf.feature_id = f.id
            WHERE mf.deleted_at IS NULL
            ORDER BY mf.my_row_id DESC
            
        """,
        "metadata": {"category": "mesures", "tables": ["manual_features", "features"], "tenant_generic": False, "cross_database": True}
    },
    
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 5 : PRÉDICTIONS (PREDICTIONS) - 10 questions
    # ═══════════════════════════════════════════════════════════════
    
    {
        "question": "Prédictions par équipement ?",
        "sql": """
            SELECT p.id AS prediction_id, p.asset_id, a.name AS equipment_name,
                p.model, p.failure, p.cause, p.failures_probability,
                p.timestamp, p.created_at
            FROM i_sense_v3_devenv_db.predictions p
            LEFT JOIN {tenant_db}.assets a ON p.asset_id = a.id
            WHERE p.deleted_at IS NULL
            ORDER BY p.timestamp DESC
            
        """,
        "metadata": {"category": "predictions", "tables": ["predictions", "assets"], "tenant_generic": True, "cross_database": True}
    },
    {
        "question": "Features PDM disponibles ?",
        "sql": """
            SELECT pf.id AS feature_id, pf.feature, pf.label, pf.type, pf.unit
            FROM i_sense_v3_devenv_db.pdm_features pf
            WHERE pf.deleted_at IS NULL
            ORDER BY pf.feature
          
        """,
        "metadata": {"category": "predictions", "tables": ["pdm_features"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Valeurs de puissance disponibles ?",
        "sql": """
            SELECT pv.id AS power_value_id, pv.name
            FROM i_sense_v3_devenv_db.power_values pv
            WHERE pv.deleted_at IS NULL
            ORDER BY pv.name
           
        """,
        "metadata": {"category": "predictions", "tables": ["power_values"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Valeurs de transmission disponibles ?",
        "sql": """
            SELECT tv.id AS transmission_value_id, tv.name
            FROM i_sense_v3_devenv_db.transmission_values tv
            WHERE tv.deleted_at IS NULL
            ORDER BY tv.name
            
        """,
        "metadata": {"category": "predictions", "tables": ["transmission_values"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Diagnostics Vibox ?",
        "sql": """
            SELECT vd.id AS diagnosis_id, vd.device_id, vd.diagnosis,
                vd.recommended_action, vd.start_date, vd.end_date,
                vd.lead, vd.created_at
            FROM {tenant_db}.vibox_diagnosis vd
            WHERE vd.deleted_at IS NULL
            ORDER BY vd.created_at DESC
           
        """,
        "metadata": {"category": "predictions", "tables": ["vibox_diagnosis"], "tenant_generic": True}
    },
    {
        "question": "Items de diagnostic Vibox ?",
        "sql": """
            SELECT vdi.id AS item_id, vdi.name, vdi.description, vdi.product_id
            FROM {tenant_db}.vibox_diagnosis_item vdi
            WHERE vdi.deleted_at IS NULL
            ORDER BY vdi.name
          
        """,
        "metadata": {"category": "predictions", "tables": ["vibox_diagnosis_item"], "tenant_generic": True}
    },
    {
        "question": "Actions recommandées Vibox ?",
        "sql": """
            SELECT vdra.id AS action_id, vdra.name, vdra.description, vdra.product_id
            FROM {tenant_db}.vibox_diagnosis_recommended_action vdra
            WHERE vdra.deleted_at IS NULL
            ORDER BY vdra.name
           
        """,
        "metadata": {"category": "predictions", "tables": ["vibox_diagnosis_recommended_action"], "tenant_generic": True}
    },
    {
        "question": "Statistiques des prédictions par mois >= 'X'?",
        "sql": """
            SELECT DATE_FORMAT(FROM_UNIXTIME(p.timestamp), '%Y-%m') AS mois,
                COUNT(*) AS nb_predictions,
                AVG(p.failures_probability) AS probabilite_moyenne,
                SUM(CASE WHEN p.failures_probability >= 'X' THEN 1 ELSE 0 END) AS predictions_critiques
            FROM i_sense_v3_devenv_db.predictions p
            WHERE p.timestamp >= UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 12 MONTH))
            AND p.deleted_at IS NULL
            GROUP BY mois
            ORDER BY mois DESC
        """,
        "metadata": {"category": "predictions", "tables": ["predictions"], "tenant_generic": False, "cross_database": True}
    },
    
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 6 : MAINTENANCE/INTERVENTIONS - 10 questions
    # ═══════════════════════════════════════════════════════════════
    
    {
        "question": "Interventions par équipement ?",
        "sql": """
            SELECT i.id AS intervention_id, i.asset_id, a.name AS equipment_name,
                i.description, i.status, i.date_intervention, i.created_at
            FROM {tenant_db}.interventions i
            INNER JOIN {tenant_db}.assets a ON i.asset_id = a.id
            WHERE i.deleted_at IS NULL AND a.deleted_at IS NULL
            ORDER BY i.created_at DESC
            
        """,
        "metadata": {"category": "maintenance", "tables": ["interventions", "assets"], "tenant_generic": True}
    },
    {
        "question": "Checklists disponibles ?",
        "sql": """
            SELECT c.id AS checklist_id, c.name AS checklist_name, c.ref,
                c.family_id, f.name AS family_name, c.created_at
            FROM {tenant_db}.checklists c
            LEFT JOIN {tenant_db}.families f ON c.family_id = f.id
            WHERE c.deleted_at IS NULL
            ORDER BY c.created_at DESC
            
        """,
        "metadata": {"category": "maintenance", "tables": ["checklists", "families"], "tenant_generic": True}
    },
    {
        "question": "Actions sur les défauts ?",
        "sql": """
            SELECT af.id AS fault_id, af.asset_id, a.name AS equipment_name,
                act.id AS action_id, act.name AS action_name, af.start_date
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.assets a ON af.asset_id = a.id
            LEFT JOIN {tenant_db}.actions_fault af_act ON af.id = af_act.fault_id
            LEFT JOIN {tenant_db}.actions act ON af_act.action_id = act.id
            WHERE af.deleted_at IS NULL
            ORDER BY af.start_date DESC
            
        """,
        "metadata": {"category": "maintenance", "tables": ["asset_faults", "assets", "actions_fault", "actions"], "tenant_generic": True}
    },
    {
        "question": "Historique d'activité des équipements ?",
        "sql": """
            SELECT al.id AS log_id, al.subject_id AS asset_id, al.log_name,
                al.description, al.user_id, al.event, al.created_at
            FROM {tenant_db}.activity_log al
            WHERE al.deleted_at IS NULL AND al.subject_type = 'App\\Models\\Asset'
            ORDER BY al.created_at DESC
            
        """,
        "metadata": {"category": "maintenance", "tables": ["activity_log"], "tenant_generic": True}
    },
    {
        "question": "Actions par utilisateur ?",
        "sql": """
            SELECT al.user_id, al.event, COUNT(*) AS nb_actions,
                MIN(al.created_at) AS premiere_action,
                MAX(al.created_at) AS derniere_action
            FROM {tenant_db}.activity_log al
            WHERE al.deleted_at IS NULL AND al.user_id IS NOT NULL
            GROUP BY al.user_id, al.event
            ORDER BY nb_actions DESC
            
        """,
        "metadata": {"category": "maintenance", "tables": ["activity_log"], "tenant_generic": True}
    },
    {
        "question": "Interventions avec opérations associées ?",
        "sql": """
            SELECT i.id AS intervention_id, i.asset_id, a.name AS equipment_name,
                i.operation_id, o.name AS operation_name, i.date_intervention
            FROM {tenant_db}.interventions i
            INNER JOIN {tenant_db}.assets a ON i.asset_id = a.id
            LEFT JOIN {tenant_db}.operations o ON i.operation_id = o.id
            WHERE i.deleted_at IS NULL
            ORDER BY i.created_at DESC
            
        """,
        "metadata": {"category": "maintenance", "tables": ["interventions", "assets", "operations"], "tenant_generic": True}
    },
    {
        "question": "Checklists par équipement ?",
        "sql": """
            SELECT a.id AS asset_id, a.name AS equipment_name,
                COUNT(ac.id) AS nb_checklists,
                SUM(CASE WHEN ac.status = 'completed' THEN 1 ELSE 0 END) AS checklists_completees,
                SUM(CASE WHEN ac.status = 'pending' THEN 1 ELSE 0 END) AS checklists_en_attente,
                MAX(ac.created_at) AS derniere_checklist
            FROM {tenant_db}.assets a
            LEFT JOIN {tenant_db}.assignment_checklist ac ON a.id = ac.asset_id
            WHERE a.deleted_at IS NULL
            GROUP BY a.id, a.name
            ORDER BY nb_checklists DESC
            
        """,
        "metadata": {"category": "maintenance", "tables": ["assets", "assignment_checklist"], "tenant_generic": True}
    },
    {
        "question": "Interventions par période (12 mois) ?",
        "sql": """
            SELECT DATE_FORMAT(i.created_at, '%Y-%m') AS mois,
                COUNT(*) AS nb_interventions
            FROM {tenant_db}.interventions i
            WHERE i.created_at >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            AND i.deleted_at IS NULL
            GROUP BY mois
            ORDER BY mois DESC
        """,
        "metadata": {"category": "maintenance", "tables": ["interventions"], "tenant_generic": True}
    },
    
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 7 : RECOMMANDATIONS - 10 questions
    # ═══════════════════════════════════════════════════════════════
    
    {
        "question": "Recommandations par type de défaut ?",
        "sql": """
            SELECT r.id AS recommendation_id, r.severity, r.fault_date,
                r.diagnostic_details, r.recommendation_details, r.actions_taken,
                f.id AS fault_id, f.name AS defect_type, fam.name AS fault_family
            FROM {tenant_db}.recommendations_v3 r
            INNER JOIN {tenant_db}.recommendation_faults rf ON r.id = rf.recommendation_id
            INNER JOIN {tenant_db}.faults f ON rf.fault_id = f.id
            INNER JOIN {tenant_db}.family_fault ff ON f.id = ff.fault_id
            INNER JOIN {tenant_db}.families fam ON ff.family_id = fam.id
            ORDER BY r.fault_date DESC
          
        """,
        "metadata": {"category": "recommandations", "tables": ["recommendations_v3", "recommendation_faults", "faults", "families"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Recommandations par équipement ?",
        "sql": """
            SELECT ra.id AS recommendation_id, ra.status AS severity,
                ra.notes AS diagnostic_details, ra.cause AS recommendation_details,
                ra.started_at AS fault_date, ra.asset_id, a.name AS equipment_name
            FROM {tenant_db}.recommendation_assets ra
            LEFT JOIN {tenant_db}.assets a ON ra.asset_id = a.id
            WHERE ra.deleted_at IS NULL
            ORDER BY ra.started_at DESC
          
        """,
        "metadata": {"category": "recommandations", "tables": ["recommendation_assets", "assets"], "tenant_generic": False, "safi_only": True}
    },
    
    {
        "question": "Recommandations avec actions entreprises ?",
        "sql": """
            SELECT r.id AS recommendation_id, r.severity, r.diagnostic_details,
                r.recommendation_details, r.actions_taken, r.fault_date,
                CASE WHEN r.actions_taken IS NOT NULL AND r.actions_taken != '' THEN 'Appliquée'
                        ELSE 'Non appliquée' END AS statut_action
            FROM {tenant_db}.recommendations_v3 r
            WHERE r.deleted_at IS NULL AND r.actions_taken IS NOT NULL
            ORDER BY r.fault_date DESC
          
        """,
        "metadata": {"category": "recommandations", "tables": ["recommendations_v3"], "tenant_generic": False, "safi_only": True}
    },

    {
        "question": "Recommandations par famille de défauts ?",
        "sql": """
            SELECT fam.id AS family_id, fam.name AS fault_family,
                COUNT(r.id) AS nb_recommandations,
                AVG(r.severity) AS severity_moyenne,
                SUM(CASE WHEN r.actions_taken IS NOT NULL THEN 1 ELSE 0 END) AS recommandations_appliquees
            FROM {tenant_db}.recommendations_v3 r
            INNER JOIN {tenant_db}.recommendation_faults rf ON r.id = rf.recommendation_id
            INNER JOIN {tenant_db}.faults f ON rf.fault_id = f.id
            INNER JOIN {tenant_db}.family_fault ff ON f.id = ff.fault_id
            INNER JOIN {tenant_db}.families fam ON ff.family_id = fam.id
            WHERE r.deleted_at IS NULL
            GROUP BY fam.id, fam.name
            ORDER BY nb_recommandations DESC
        """,
        "metadata": {"category": "recommandations", "tables": ["recommendations_v3", "recommendation_faults", "faults", "families"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Recommandations avec détails de diagnostic ?",
        "sql": """
            SELECT ra.id AS recommendation_id, ra.status AS severity,
                ra.notes AS diagnostic_details, ra.cause AS recommendation_details,
                ra.started_at AS fault_date, a.name AS equipment_name
            FROM {tenant_db}.recommendation_assets ra
            LEFT JOIN {tenant_db}.assets a ON ra.asset_id = a.id
            WHERE ra.deleted_at IS NULL AND ra.notes IS NOT NULL AND ra.notes != ''
            ORDER BY ra.started_at DESC
          
        """,
        "metadata": {"category": "recommandations", "tables": ["recommendation_assets", "assets"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Recommandations Vibox (diagnostics automatiques) ?",
        "sql": """
            SELECT vd.id AS diagnosis_id, vd.device_id,
                d.id AS device_id_global, d.ref AS device_ref,
                vd.diagnosis, vd.recommended_action,
                vd.start_date, vd.end_date, vd.lead
            FROM {tenant_db}.vibox_diagnosis vd
            LEFT JOIN {tenant_db}.devices d ON vd.device_id = d.id
            WHERE vd.deleted_at IS NULL
            ORDER BY vd.created_at DESC
           
        """,
        "metadata": {"category": "recommandations", "tables": ["vibox_diagnosis"], "tenant_generic": False, "safi_only": True, "cross_database": True}
    },
    {
        "question": "Opérations recommandées ?",
        "sql": """
            SELECT ro.id AS liaison_id, ro.recommendation_id,
                ro.operation_id, o.name AS operation_name
            FROM {tenant_db}.recommendation_operations ro
            INNER JOIN {tenant_db}.operations o ON ro.operation_id = o.id
            WHERE o.deleted_at IS NULL
            ORDER BY ro.recommendation_id, ro.operation_id
           
        """,
        "metadata": {"category": "recommandations", "tables": ["recommendation_operations", "operations"], "tenant_generic": False, "safi_only": True}
    },

    
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 8 : UTILISATEURS/NOTIFICATIONS - 10 questions
    # ═══════════════════════════════════════════════════════════════
    
    {
        "question": "Utilisateurs par entreprise ?",
        "sql": """
            SELECT u.id AS user_id, CONCAT(u.first_name, ' ', u.last_name) AS user_name,
                u.email, uc.company_id, c.name AS company_name, u.created_at
            FROM i_sense_v3_devenv_db.users u
            LEFT JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id
            LEFT JOIN i_sense_v3_devenv_db.companies c ON uc.company_id = c.id
            WHERE u.deleted_at IS NULL
            ORDER BY u.created_at DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["users", "user_company", "companies"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Notifications par utilisateur ?",
        "sql": """
            SELECT n.id AS notification_id, n.notifiable_id AS user_id,
                CONCAT(u.first_name, ' ', u.last_name) AS user_name,
                n.type, n.data, n.read_at, n.created_at
            FROM i_sense_v3_devenv_db.notifications n
            LEFT JOIN i_sense_v3_devenv_db.users u ON n.notifiable_id = u.id
            WHERE n.notifiable_type = 'App\\Models\\User'
            ORDER BY n.created_at DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["notifications", "users"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Notifications non lues ?",
        "sql": """
            SELECT n.id AS notification_id, n.notifiable_id AS user_id,
                CONCAT(u.first_name, ' ', u.last_name) AS user_name,
                n.type, n.data, n.created_at, 'Non lue' AS statut
            FROM i_sense_v3_devenv_db.notifications n
            LEFT JOIN i_sense_v3_devenv_db.users u ON n.notifiable_id = u.id
            WHERE n.read_at IS NULL AND n.notifiable_type = 'App\\Models\\User'
            ORDER BY n.created_at DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["notifications", "users"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Configuration des notifications utilisateur ?",
        "sql": """
            SELECT unc.id AS config_id, unc.user_id,
                CONCAT(u.first_name, ' ', u.last_name) AS user_name,
                unc.sms_notif_config_id, unc.email_notif_config_id,
                unc.consumed_sms, unc.consumed_email, unc.status, unc.created_at
            FROM {tenant_db}.user_notif_config unc
            LEFT JOIN i_sense_v3_devenv_db.users u ON unc.user_id = u.id
            WHERE unc.deleted_at IS NULL
            ORDER BY unc.created_at DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["user_notif_config", "users"], "tenant_generic": True, "cross_database": True}
    },
    {
        "question": "Historique des emails envoyés ?",
        "sql": """
            SELECT eh.id AS email_id, eh.name, eh.report_type, eh.send_type,
                eh.to AS recipients, eh.cc, eh.status,
                eh.send_date, eh.generation_date, eh.created_at
            FROM {tenant_db}.email_histories eh
            WHERE eh.deleted_at IS NULL
            ORDER BY eh.send_date DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["email_histories"], "tenant_generic": True}
    },
    {
        "question": "Configuration des notifications email ?",
        "sql": """
            SELECT enc.id AS config_id, enc.entities_ids, enc.assets_ids,
                enc.status_target, enc.email_limit, enc.email_used,
                enc.status, enc.reminder, enc.last_notification_time, enc.created_at
            FROM {tenant_db}.email_notif_config enc
            WHERE enc.deleted_at IS NULL
            ORDER BY enc.created_at DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["email_notif_config"], "tenant_generic": True}
    },
    {
        "question": "Configuration des notifications SMS ?",
        "sql": """
            SELECT snc.id AS config_id, snc.entities_ids, snc.assets_ids,
                snc.status_target, snc.sms_limit, snc.sms_used,
                snc.status, snc.reminder, snc.last_notification_time, snc.created_at
            FROM {tenant_db}.sms_notif_config snc
            WHERE snc.deleted_at IS NULL
            ORDER BY snc.created_at DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["sms_notif_config"], "tenant_generic": True}
    },
    {
        "question": "Emails automatisés ?",
        "sql": """
            SELECT ae.id AS automated_email_id, ae.label, ae.type,
                ae.to, ae.cc, ae.hours, ae.entities, ae.user_id, ae.created_at
            FROM {tenant_db}.automated_emails ae
            WHERE ae.deleted_at IS NULL
            ORDER BY ae.created_at DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["automated_emails"], "tenant_generic": True}
    },
    {
        "question": "Utilisateurs par entité ?",
        "sql": """
            SELECT eu.id AS liaison_id, eu.entity_id, e.name AS entity_name,
                eu.user_id, CONCAT(u.first_name, ' ', u.last_name) AS user_name,
                eu.deleted_at
            FROM {tenant_db}.entity_user eu
            LEFT JOIN {tenant_db}.entities e ON eu.entity_id = e.id
            LEFT JOIN i_sense_v3_devenv_db.users u ON eu.user_id = u.id
            WHERE eu.deleted_at IS NULL
            ORDER BY eu.id DESC
            
        """,
        "metadata": {"category": "utilisateurs", "tables": ["entity_user", "entities", "users"], "tenant_generic": True, "cross_database": True}
    },
    {
        "question": "Statistiques des notifications par mois ?",
        "sql": """
            SELECT DATE_FORMAT(n.created_at, '%Y-%m') AS mois,
                COUNT(*) AS nb_notifications,
                SUM(CASE WHEN n.read_at IS NOT NULL THEN 1 ELSE 0 END) AS notifications_lues,
                SUM(CASE WHEN n.read_at IS NULL THEN 1 ELSE 0 END) AS notifications_non_lues
            FROM i_sense_v3_devenv_db.notifications n
            WHERE n.created_at >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            AND n.notifiable_type = 'App\\Models\\User'
            GROUP BY mois
            ORDER BY mois DESC
        """,
        "metadata": {"category": "utilisateurs", "tables": ["notifications"], "tenant_generic": False, "cross_database": True}
    },
    
    # ═══════════════════════════════════════════════════════════════
    # CATÉGORIE 9 : ENTREPRISES/CLIENTS - 10 questions
    # ═══════════════════════════════════════════════════════════════
    
    {
        "question": "Entreprises enregistrées ?",
        "sql": """
            SELECT c.id, c.name, c.reference, c.alias, c.created_at
            FROM i_sense_v3_devenv_db.companies c
            WHERE c.deleted_at IS NULL
            ORDER BY c.name
            
        """,
        "metadata": {"category": "entreprises", "tables": ["companies"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Clients du site {tenant} ?",
        "sql": """
            SELECT id, name, email, phone, city, country,
                credit_limit, total_due_amount, created_at
            FROM v3_tenant_Site_Safi.clients
            ORDER BY name
            
        """,
        "metadata": {"category": "entreprises", "tables": ["clients"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Fournisseurs du site {tenant} ?",
        "sql": """
            SELECT id, name, email, phone, city, country, created_at
            FROM v3_tenant_Site_Safi.fournisseurs
            ORDER BY name
            
        """,
        "metadata": {"category": "entreprises", "tables": ["fournisseurs"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Factures ?",
        "sql": """
            SELECT id, client_id, fournisseur_id, date, total_amount, created_at
            FROM v3_tenant_Site_Safi.factures
            ORDER BY date DESC
            
        """,
        "metadata": {"category": "entreprises", "tables": ["factures"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Factures impayées ?",
        "sql": """
            SELECT id, client_id, fournisseur_id, date, total_amount, created_at
            FROM v3_tenant_Site_Safi.factures
            WHERE total_amount > 0
            ORDER BY date DESC
            
        """,
        "metadata": {"category": "entreprises", "tables": ["factures"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Tarifs par mesure ?",
        "sql": """
            SELECT tm.id AS liaison_id, tm.measure_id, m.name AS measure_name,
                tm.tarif_id, t.identifiant AS tarif_identifiant,
                t.cost, t.type_cost, tm.created_at
            FROM {tenant_db}.tarif_measures tm
            LEFT JOIN {tenant_db}.measures m ON tm.measure_id = m.id
            LEFT JOIN {tenant_db}.tarifs t ON tm.tarif_id = t.id
            WHERE tm.deleted_at IS NULL
            ORDER BY tm.created_at DESC
            
        """,
        "metadata": {"category": "entreprises", "tables": ["tarif_measures", "measures", "tarifs"], "tenant_generic": True}
    },
    {
        "question": "Abonnements ?",
        "sql": """
            SELECT a.id, a.company_id, c.name AS company_name,
                a.package_id, a.status, a.start_date, a.end_date,
                a.max_users, a.max_devices, a.sms_used, a.email_used, a.created_at
            FROM i_sense_v3_devenv_db.abonnements a
            INNER JOIN i_sense_v3_devenv_db.companies c ON a.company_id = c.id
            WHERE a.deleted_at IS NULL
            ORDER BY a.end_date DESC
            
        """,
        "metadata": {"category": "entreprises", "tables": ["abonnements", "companies"], "tenant_generic": False, "cross_database": True}
    },
    {
        "question": "Charges par projet ?",
        "sql": """
            SELECT id, product_id, size, initial_quantity,
                remaining_quantity, created_at
            FROM v3_tenant_Site_Safi.burden_details
            ORDER BY created_at DESC
            
        """,
        "metadata": {"category": "entreprises", "tables": ["burden_details"], "tenant_generic": False, "safi_only": True}
    }, 
    {
        "question": "Statistiques des factures par mois ?",
        "sql": """
            SELECT DATE_FORMAT(date, '%Y-%m') AS mois,
                COUNT(*) AS nb_factures,
                SUM(total_amount) AS montant_total,
                AVG(total_amount) AS montant_moyen
            FROM v3_tenant_Site_Safi.factures
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY mois
            ORDER BY mois DESC
        """,
        "metadata": {"category": "entreprises", "tables": ["factures"], "tenant_generic": False, "safi_only": True}
    },
    {
        "question": "Résumé global ?",
        "sql": """
            SELECT 'Entreprises' AS categorie, COUNT(*) AS total
            FROM i_sense_v3_devenv_db.companies
            WHERE deleted_at IS NULL
            
            UNION ALL
            
            SELECT 'Abonnements' AS categorie, COUNT(*) AS total
            FROM i_sense_v3_devenv_db.abonnements
            WHERE deleted_at IS NULL
            
            UNION ALL
            
            SELECT 'Utilisateurs' AS categorie, COUNT(*) AS total
            FROM i_sense_v3_devenv_db.users
            WHERE deleted_at IS NULL
        """,
        "metadata": {"category": "entreprises", "tables": ["companies", "abonnements", "users"], "tenant_generic": False, "cross_database": True}
    },
]

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def get_tenant_databases():
    """Retourne la liste des 9 bases tenant"""
    return [
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

def format_query_for_tenant(sql_template: str, tenant_db: str) -> str:
    """
    Remplace {tenant_db} par le nom de la base tenant
    """
    return sql_template.format(tenant_db=tenant_db)

def get_questions_by_category(category: str) -> list:
    """Filtre les questions par catégorie"""
    return [q for q in DATASET_400_QUESTIONS if q.get('metadata', {}).get('category') == category]

def get_generic_questions() -> list:
    """Retourne uniquement les questions génériques (supportent tous les tenants)"""
    return [q for q in DATASET_400_QUESTIONS if q.get('metadata', {}).get('tenant_generic', False)]

def get_safi_only_questions() -> list:
    """Retourne les questions spécifiques à Safi"""
    return [q for q in DATASET_400_QUESTIONS if q.get('metadata', {}).get('safi_only', False)]

def get_cross_database_questions() -> list:
    """Retourne les questions qui font des JOIN cross-database"""
    return [q for q in DATASET_400_QUESTIONS if q.get('metadata', {}).get('cross_database', False)]

# ═══════════════════════════════════════════════════════════════
# EXEMPLE D'UTILISATION
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" " * 20 + "📊 DATASET 400 QUESTIONS - VERSION GÉNÉRIQUE")
    print("="*80)
    
    print(f"\n✅ Total questions : {len(DATASET_400_QUESTIONS)}")
    print(f"✅ Questions génériques : {len(get_generic_questions())}")
    print(f"✅ Questions Safi-only : {len(get_safi_only_questions())}")
    print(f"✅ Questions cross-database : {len(get_cross_database_questions())}")
    
    print(f"\n📋 Bases tenant supportées :")
    for tenant in get_tenant_databases():
        print(f"   • {tenant}")
    
    print(f"\n📋 Catégories :")
    categories = {}
    for q in DATASET_400_QUESTIONS:
        cat = q.get('metadata', {}).get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items()):
        print(f"   • {cat}: {count} questions")
    
    # Exemple de formatage pour un tenant spécifique
    print(f"\n📋 Exemple de requête formatée pour v3_tenant_ntn :")
    sample_question = DATASET_400_QUESTIONS[0]
    formatted_sql = format_query_for_tenant(sample_question['sql'], 'v3_tenant_ntn')
    print(f"   Question : {sample_question['question']}")
    print(f"   SQL : {formatted_sql[:200]}...")
    
    print("\n" + "="*80)
    print(" " * 25 + "✅ PRÊT POUR LE FINE-TUNING")
    print("="*80 + "\n")
   