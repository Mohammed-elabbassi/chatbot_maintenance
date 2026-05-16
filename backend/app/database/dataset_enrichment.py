# dataset_enrichment.py
"""
Enrichissement du dataset : questions négatives, edge cases, ambiguës, etc.
Chatbot Maintenance Prédictive - i-sense / i-predict

V3.1 : 45 exemples négatifs (au lieu de 8)
        Ambiguës et Edge Cases IDENTIQUES à V3
"""

# ═══════════════════════════════════════════════════════════════════════════
# 1. EXEMPLES NÉGATIFS (refus d'exécution) - 45 exemples
# ═══════════════════════════════════════════════════════════════════════════

NEGATIVE_EXAMPLES = [
    # ═══ DELETE (10 exemples) ═══
    {
        "question": "Supprime tous les équipements de JLN",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Supprime les pannes de JLN",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Efface les alarmes",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Supprime l'équipement Moteur 1",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Efface toutes les mesures du mois dernier",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "DELETE FROM asset_faults WHERE asset_id = 123",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Supprime toutes les recommandations",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Efface les interventions de cette semaine",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Supprime les utilisateurs inactifs",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Efface les données de v3_tenant_ntn",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    # ═══ UPDATE (10 exemples) ═══
    {
        "question": "Mets à jour le statut de l'équipement X",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées. Pour modifier un statut, utilisez l'interface i-sense.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Change le statut de l'alarme à normal",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "UPDATE assets SET status = 1 WHERE name = 'Moteur'",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Modifie la date de l'intervention",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Mets à jour le RPM de tous les moteurs",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Corrige le nom de l'équipement 42",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Change la famille de l'équipement",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Mets le statut critique pour tous les moteurs",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Réinitialise les statuts de tous les équipements",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Désactive tous les utilisateurs de ONEE",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    # ═══ INSERT (8 exemples) ═══
    {
        "question": "INSERT INTO alarms (asset_id, status) VALUES (456, 5)",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Ajoute un nouvel équipement",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées. Utilisez l'interface i-sense.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Crée une nouvelle alarme pour l'équipement 10",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Insère une intervention pour demain",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Ajoute un défaut de roulement",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Enregistre une nouvelle mesure",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Crée un nouvel utilisateur admin",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Ajoute une nouvelle entreprise",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    # ═══ DROP / ALTER / TRUNCATE (7 exemples) ═══
    {
        "question": "DROP TABLE assets",
        "sql": "-- OPÉRATION INTERDITE : Injection SQL détectée. Commande refusée.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "DROP DATABASE v3_tenant_jln",
        "sql": "-- OPÉRATION INTERDITE : Injection SQL détectée. Commande refusée.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "ALTER TABLE measurements ADD COLUMN test INT",
        "sql": "-- OPÉRATION INTERDITE : Modification de schéma non autorisée.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "TRUNCATE TABLE alarms",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "ALTER TABLE assets DROP COLUMN status",
        "sql": "-- OPÉRATION INTERDITE : Modification de schéma non autorisée.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "DROP TABLE faults CASCADE",
        "sql": "-- OPÉRATION INTERDITE : Injection SQL détectée. Commande refusée.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "CREATE TABLE test (id INT)",
        "sql": "-- OPÉRATION INTERDITE : Modification de schéma non autorisée.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    # ═══ Formulations naturelles de suppression/modification (10 exemples) ═══
    {
        "question": "Peux-tu supprimer les anciennes alarmes ?",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Je veux effacer les données de test",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Nettoie la table des mesures",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Vide la table des interventions",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Remets à zéro les compteurs d'alarmes",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Ferme toutes les alarmes ouvertes",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Marque toutes les pannes comme résolues",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Valide toutes les recommandations en attente",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Transfère les équipements de JLN vers ONEE",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
    {
        "question": "Duplique l'équipement Moteur 1",
        "sql": "-- OPÉRATION INTERDITE : Seules les requêtes SELECT sont autorisées.",
        "metadata": {"category": "securite", "type": "negative"}
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 2. EXEMPLES AMBIGUËS (IDENTIQUE à V3)
# ═══════════════════════════════════════════════════════════════════════════

AMBIGUOUS_EXAMPLES = [
    {
        "question": "Montre-moi tout",
        "sql": """
            SELECT a.id, a.name, a.ref, a.status, a.created_at
            FROM {tenant_db}.assets a
            WHERE a.deleted_at IS NULL
            ORDER BY a.id DESC
            LIMIT 50;
        """,
        "metadata": {"category": "equipements", "type": "ambiguous"}
    },
    {
        "question": "Y a des problèmes ?",
        "sql": """
            SELECT a.id, a.name, a.ref, af.start_date, f.name AS fault_type
            FROM {tenant_db}.assets a
            INNER JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.end_date IS NULL
            AND af.deleted_at IS NULL
            AND a.deleted_at IS NULL
            ORDER BY af.start_date DESC
            LIMIT 20;
        """,
        "metadata": {"category": "defauts", "type": "ambiguous"}
    },
    {
        "question": "Quoi de neuf ?",
        "sql": """
            SELECT 'Nouvelle alarme' AS type, a.name, al.created_at
            FROM {tenant_db}.alarms al
            JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
              AND al.deleted_at IS NULL
            UNION ALL
            SELECT 'Nouvelle panne' AS type, a.name, af.start_date
            FROM {tenant_db}.asset_faults af
            JOIN {tenant_db}.assets a ON af.asset_id = a.id
            WHERE af.start_date >= DATE_SUB(NOW(), INTERVAL 1 DAY)
              AND af.deleted_at IS NULL
            UNION ALL
            SELECT 'Nouvelle intervention' AS type, a.name, i.created_at
            FROM {tenant_db}.interventions i
            JOIN {tenant_db}.assets a ON i.asset_id = a.id
            WHERE i.created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
              AND i.deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT 20;
        """,
        "metadata": {"category": "general", "type": "ambiguous"}
    },
    {
        "question": "Ça va ou pas ?",
        "sql": """
            SELECT 
                COUNT(DISTINCT a.id) AS total_equipements,
                COUNT(DISTINCT CASE WHEN a.status = 5 THEN a.id END) AS nb_critiques,
                COUNT(DISTINCT CASE WHEN al.id IS NOT NULL THEN a.id END) AS nb_en_alarme,
                COUNT(DISTINCT CASE WHEN af.id IS NOT NULL THEN a.id END) AS nb_en_panne
            FROM {tenant_db}.assets a
            LEFT JOIN {tenant_db}.alarms al ON a.id = al.asset_id AND al.ended_at IS NULL AND al.deleted_at IS NULL
            LEFT JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id AND af.end_date IS NULL AND af.deleted_at IS NULL
            WHERE a.deleted_at IS NULL;
        """,
        "metadata": {"category": "general", "type": "ambiguous"}
    },
    {
        "question": "Donne-moi un résumé de la situation",
        "sql": """
            SELECT 
                'Équipements' AS rubrique,
                COUNT(*) AS total,
                SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) AS critiques,
                SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) AS arretes
            FROM {tenant_db}.assets WHERE deleted_at IS NULL
            UNION ALL
            SELECT 'Alarmes actives', COUNT(*), SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END), NULL
            FROM {tenant_db}.alarms WHERE ended_at IS NULL AND deleted_at IS NULL
            UNION ALL
            SELECT 'Pannes actives', COUNT(*), NULL, NULL
            FROM {tenant_db}.asset_faults WHERE end_date IS NULL AND deleted_at IS NULL;
        """,
        "metadata": {"category": "general", "type": "ambiguous"}
    },
    {
        "question": "Les machines qui tournent mal",
        "sql": """
            SELECT a.id, a.name, a.ref, a.status,
                   CASE WHEN al.id IS NOT NULL THEN 'Alarme active' END AS alerte,
                   CASE WHEN af.id IS NOT NULL THEN 'Panne active' END AS defaut
            FROM {tenant_db}.assets a
            LEFT JOIN {tenant_db}.alarms al ON a.id = al.asset_id AND al.ended_at IS NULL AND al.deleted_at IS NULL
            LEFT JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id AND af.end_date IS NULL AND af.deleted_at IS NULL
            WHERE (al.id IS NOT NULL OR af.id IS NOT NULL OR a.status IN (5,3,2))
              AND a.deleted_at IS NULL
            ORDER BY a.status DESC
            LIMIT 30;
        """,
        "metadata": {"category": "equipements", "type": "ambiguous"}
    },
    {
        "question": "Qu'est-ce qui s'est passé récemment ?",
        "sql": """
            (SELECT 'Alarme' AS type, a.name, al.created_at AS date, al.status
             FROM {tenant_db}.alarms al
             JOIN {tenant_db}.assets a ON al.asset_id = a.id
             WHERE al.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
               AND al.deleted_at IS NULL)
            UNION ALL
            (SELECT 'Panne' AS type, a.name, af.start_date, NULL
             FROM {tenant_db}.asset_faults af
             JOIN {tenant_db}.assets a ON af.asset_id = a.id
             WHERE af.start_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
               AND af.deleted_at IS NULL)
            UNION ALL
            (SELECT 'Intervention' AS type, a.name, i.date_intervention, NULL
             FROM {tenant_db}.interventions i
             JOIN {tenant_db}.assets a ON i.asset_id = a.id
             WHERE i.date_intervention >= DATE_SUB(NOW(), INTERVAL 7 DAY)
               AND i.deleted_at IS NULL)
            ORDER BY date DESC
            LIMIT 20;
        """,
        "metadata": {"category": "general", "type": "ambiguous"}
    },
    {
        "question": "Fais le point sur les équipements critiques",
        "sql": """
            SELECT a.id, a.name, a.ref, a.status,
                   COUNT(DISTINCT al.id) AS alarmes_actives,
                   COUNT(DISTINCT af.id) AS pannes_actives
            FROM {tenant_db}.assets a
            LEFT JOIN {tenant_db}.alarms al ON a.id = al.asset_id AND al.ended_at IS NULL AND al.deleted_at IS NULL
            LEFT JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id AND af.end_date IS NULL AND af.deleted_at IS NULL
            WHERE a.status >= 3 AND a.deleted_at IS NULL
            GROUP BY a.id, a.name, a.ref, a.status
            ORDER BY a.status DESC, alarmes_actives DESC
            LIMIT 20;
        """,
        "metadata": {"category": "equipements", "type": "ambiguous"}
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 3. EDGE CASES (IDENTIQUE à V3)
# ═══════════════════════════════════════════════════════════════════════════

EDGE_CASES = [
    {
        "question": "Quels utilisateurs sont associés aux équipements en alarme à JLN ?",
        "sql": """
            SELECT DISTINCT u.id, u.first_name, u.last_name, u.email,
                   a.name AS equipment_name
            FROM i_sense_v3_devenv_db.users u
            INNER JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id
            INNER JOIN i_sense_v3_devenv_db.companies c ON uc.company_id = c.id
            INNER JOIN v3_tenant_jln.assets a ON 1=1
            INNER JOIN v3_tenant_jln.alarms al ON a.id = al.asset_id
            WHERE c.reference = 'v3_tenant_jln'
            AND al.ended_at IS NULL
            AND al.deleted_at IS NULL
            AND u.deleted_at IS NULL
            ORDER BY u.last_name;
        """,
        "metadata": {"category": "cross_database", "type": "edge_case"}
    },
    {
        "question": "Quel est le top 5 des types de pannes les plus fréquents avec leur durée moyenne ?",
        "sql": """
            SELECT f.name AS fault_type,
                   COUNT(af.id) AS occurrences,
                   ROUND(AVG(af.duration), 2) AS duree_moyenne_heures,
                   MIN(af.start_date) AS premiere_occurrence,
                   MAX(af.start_date) AS derniere_occurrence
            FROM {tenant_db}.asset_faults af
            INNER JOIN {tenant_db}.faults f ON af.fault_id = f.id
            WHERE af.deleted_at IS NULL
            GROUP BY f.id, f.name
            ORDER BY occurrences DESC
            LIMIT 5;
        """,
        "metadata": {"category": "defauts", "type": "edge_case"}
    },
    {
        "question": "Quels sont les équipements qui n'ont jamais eu de mesure ?",
        "sql": """
            SELECT a.id, a.name, a.ref
            FROM {tenant_db}.assets a
            LEFT JOIN {tenant_db}.measurements m ON a.id = m.asset_id AND m.deleted_at IS NULL
            WHERE m.id IS NULL AND a.deleted_at IS NULL
            ORDER BY a.name;
        """,
        "metadata": {"category": "equipements", "type": "edge_case"}
    },
    {
        "question": "Quelles alarmes ont duré plus de 48h sans être résolues ?",
        "sql": """
            SELECT a.name, al.created_at, TIMESTAMPDIFF(HOUR, al.created_at, NOW()) AS heures_actives
            FROM {tenant_db}.alarms al
            JOIN {tenant_db}.assets a ON al.asset_id = a.id
            WHERE al.ended_at IS NULL
              AND al.created_at <= DATE_SUB(NOW(), INTERVAL 48 HOUR)
              AND al.deleted_at IS NULL
            ORDER BY heures_actives DESC;
        """,
        "metadata": {"category": "alarmes", "type": "edge_case"}
    },
    {
        "question": "Classement des équipements par ratio pannes / interventions (taux de maintenance)",
        "sql": """
            SELECT a.id, a.name, a.ref,
                   COUNT(DISTINCT af.id) AS nb_pannes,
                   COUNT(DISTINCT i.id) AS nb_interventions,
                   ROUND(COUNT(DISTINCT af.id) / NULLIF(COUNT(DISTINCT i.id), 0), 2) AS ratio_pannes_par_intervention
            FROM {tenant_db}.assets a
            LEFT JOIN {tenant_db}.asset_faults af ON a.id = af.asset_id AND af.deleted_at IS NULL
            LEFT JOIN {tenant_db}.interventions i ON a.id = i.asset_id AND i.deleted_at IS NULL
            WHERE a.deleted_at IS NULL
            GROUP BY a.id, a.name, a.ref
            HAVING nb_pannes > 0
            ORDER BY ratio_pannes_par_intervention DESC;
        """,
        "metadata": {"category": "defauts", "type": "edge_case"}
    },
    {
        "question": "Quels utilisateurs ont validé des recommandations mais n'ont jamais fait d'intervention ?",
        "sql": """
            SELECT DISTINCT u.id, u.first_name, u.last_name
            FROM i_sense_v3_devenv_db.users u
            WHERE u.id IN (SELECT DISTINCT validated_by FROM {tenant_db}.recommendations_v3 WHERE validated_by IS NOT NULL)
              AND u.id NOT IN (SELECT DISTINCT expert_id FROM {tenant_db}.interventions WHERE expert_id IS NOT NULL)
              AND u.deleted_at IS NULL;
        """,
        "metadata": {"category": "utilisateurs", "type": "edge_case", "cross_database": True}
    },
    {
        "question": "Quelles sont les recommandations créées plus de 7 jours après la date de défaut ?",
        "sql": """
            SELECT r.id, a.name, r.fault_date, r.created_at,
                   DATEDIFF(r.created_at, r.fault_date) AS jours_delai
            FROM {tenant_db}.recommendations_v3 r
            JOIN {tenant_db}.assets a ON r.asset_id = a.id
            WHERE r.fault_date IS NOT NULL
              AND r.created_at > DATE_ADD(r.fault_date, INTERVAL 7 DAY)
              AND r.deleted_at IS NULL
            ORDER BY jours_delai DESC;
        """,
        "metadata": {"category": "recommandations", "type": "edge_case"}
    },
    {
        "question": "Quels équipements ont un écart anormal entre leur RPM réel et leur RPM nominal ?",
        "sql": """
            SELECT a.id, a.name, a.rpm AS rpm_nominal, pd.rpm AS rpm_mesure,
                   ABS(pd.rpm - a.rpm) AS ecart
            FROM {tenant_db}.pdm_detection pd
            JOIN {tenant_db}.assets a ON pd.parent_id = a.id
            WHERE a.rpm IS NOT NULL
              AND pd.rpm IS NOT NULL
              AND ABS(pd.rpm - a.rpm) > 50
              AND pd.deleted_at IS NULL
            ORDER BY ecart DESC;
        """,
        "metadata": {"category": "predictions", "type": "edge_case"}
    },
    {
        "question": "Top 3 des features qui déclenchent le plus d'alarmes (feature_group.alarm dépassé)",
        "sql": """
            SELECT f.name, COUNT(*) AS nb_depassements
            FROM {tenant_db}.feature_measurement fm
            JOIN {tenant_db}.feature_group fg ON fm.feature_id = fg.feature_id AND fm.group_id = fg.group_id
            JOIN i_sense_v3_devenv_db.features f ON fm.feature_id = f.id
            WHERE fm.value > fg.alarm
              AND fm.deleted_at IS NULL
            GROUP BY f.id, f.name
            ORDER BY nb_depassements DESC
            LIMIT 3;
        """,
        "metadata": {"category": "mesures", "type": "edge_case", "cross_database": True}
    },
    {
        "question": "Quels sont les équipements dont le dernier point de mesure est antérieur à 30 jours ?",
        "sql": """
            SELECT a.id, a.name, a.ref, MAX(m.created_at) AS derniere_mesure
            FROM {tenant_db}.assets a
            JOIN {tenant_db}.measurements m ON a.id = m.asset_id
            WHERE m.deleted_at IS NULL AND a.deleted_at IS NULL
            GROUP BY a.id, a.name, a.ref
            HAVING derniere_mesure < DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY derniere_mesure;
        """,
        "metadata": {"category": "mesures", "type": "edge_case"}
    },
    {
        "question": "Y a-t-il des doublons d'équipements (même nom et même référence) ?",
        "sql": """
            SELECT name, ref, COUNT(*) AS occurrences
            FROM {tenant_db}.assets
            WHERE deleted_at IS NULL
            GROUP BY name, ref
            HAVING COUNT(*) > 1;
        """,
        "metadata": {"category": "equipements", "type": "edge_case"}
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 4. COMBINAISON FINALE
# ═══════════════════════════════════════════════════════════════════════════

ALL_ENRICHMENT = NEGATIVE_EXAMPLES + AMBIGUOUS_EXAMPLES + EDGE_CASES

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" " * 25 + "📊 ENRICHISSEMENT DU DATASET V3.1")
    print("=" * 80)
    print(f"\n✅ Total des exemples d'enrichissement : {len(ALL_ENRICHMENT)}")
    print(f"   - Négatifs  : {len(NEGATIVE_EXAMPLES)}")
    print(f"   - Ambiguës  : {len(AMBIGUOUS_EXAMPLES)}")
    print(f"   - Edge cases: {len(EDGE_CASES)}")

    categories = {}
    for ex in ALL_ENRICHMENT:
        cat = ex.get('metadata', {}).get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print("\n📋 Répartition par catégorie :")
    for cat, count in sorted(categories.items()):
        print(f"   • {cat}: {count}")

    print("\n" + "=" * 80)
    print(" " * 25 + "✅ FICHIER V3.1 PRÊT")
    print("=" * 80 + "\n")