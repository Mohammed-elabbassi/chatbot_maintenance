# # ══════════════════════════════════════════════════════════════
# # parametric_templates_v6.py — V6.0
# # 18 Templates dynamiques couvrant 1000+ variantes de questions
# # ══════════════════════════════════════════════════════════════

# from typing import Dict, List, Optional
# from dataclasses import dataclass


# @dataclass
# class TemplateMatch:
#     """Résultat d'un matching template"""
#     template_name: str
#     sql: str
#     confidence: float
#     entities_used: Dict


# class ParametricTemplateEngineV6:
#     """Moteur de templates SQL paramétrés"""

#     # Synonymes étendus pour types de défauts (LIKE patterns)
#     FAULT_LIKE_PATTERNS = {
#         'bearing': ['Bearing', 'roulement', 'Rolling Element', 'Inner Race', 'Outer Race'],
#         'lubrication': ['Lubrification', 'lubrification', 'Lubrication'],
#         'misalignment': ['Misalignment', 'alignement'],
#         'imbalance': ['Imbalance', 'balourd'],
#         'cavitation': ['Cavitation'],
#         'belt': ['Belt', 'courroie'],
#         'gear': ['Gear', 'engrenage'],
#         'electrical': ['Electrical', 'AC Electrical', 'DC Electrical'],
#         'sensor': ['Fault sensor', 'Sensor Saturation'],
#         'looseness': ['Mechanical looseness'],
#         'friction': ['Friction', 'frottement'],
#         'outlier': ['Outliers'],
#         'shutdown': ['shutdown'],
#         'structural': ['Structural Fault'],
#         'oil_turbulence': ["Turbulence d'huile"],
#         'ski_slope': ['Ski slope'],
#     }

#     # Filtres temporels
#     TIME_FILTERS = {
#         'today':       "DATE({col}) = CURDATE()",
#         'yesterday':   "DATE({col}) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)",
#         'this_week':   "{col} >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)",
#         'last_week':   "{col} >= DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND {col} < DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
#         'this_month':  "YEAR({col}) = YEAR(CURDATE()) AND MONTH({col}) = MONTH(CURDATE())",
#         'last_30_days': "{col} >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
#         'recent':      "{col} >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
#     }

#     def __init__(self):
#         self.templates = self._build_templates()
#         self.stats = {
#             'total': 0,
#             'matched': 0,
#             'by_template': {},
#         }

#     def _build_templates(self) -> Dict:
#         """Registry de templates paramétrés"""
#         return {
#             # FAULTS
#             'list_fault':  {'matches': lambda i: i.category == 'fault' and i.action == 'LIST',     'builder': self._fault_list},
#             'count_fault': {'matches': lambda i: i.category == 'fault' and i.action == 'COUNT',    'builder': self._fault_count},
#             'top_fault':   {'matches': lambda i: i.category == 'fault' and i.action == 'TOP',      'builder': self._fault_top},
#             'trend_fault': {'matches': lambda i: i.category == 'fault' and i.action == 'TREND',    'builder': self._fault_trend},
#             # ALARMS
#             'list_alarm':  {'matches': lambda i: i.category == 'alarm' and i.action == 'LIST',     'builder': self._alarm_list},
#             'count_alarm': {'matches': lambda i: i.category == 'alarm' and i.action == 'COUNT',    'builder': self._alarm_count},
#             'top_alarm':   {'matches': lambda i: i.category == 'alarm' and i.action == 'TOP',      'builder': self._alarm_top},
#             # ASSETS
#             'list_asset':   {'matches': lambda i: i.category == 'asset' and i.action == 'LIST',    'builder': self._asset_list},
#             'count_asset':  {'matches': lambda i: i.category == 'asset' and i.action == 'COUNT',   'builder': self._asset_count},
#             'status_asset': {'matches': lambda i: i.category == 'asset' and i.action == 'STATUS',  'builder': self._asset_status},
#             # MEASUREMENTS
#             'list_measurement': {'matches': lambda i: i.category == 'measurement' and i.action == 'LIST',  'builder': self._measure_list},
#             'top_measurement':  {'matches': lambda i: i.category == 'measurement' and i.action == 'TOP',   'builder': self._measure_top},
#             # RECOMMENDATIONS
#             'list_recommendation': {'matches': lambda i: i.category == 'recommendation', 'builder': self._reco_list},
#             # INTERVENTIONS
#             'list_intervention': {'matches': lambda i: i.category == 'intervention', 'builder': self._intervention_list},
#             # DASHBOARD
#             'dashboard': {'matches': lambda i: i.action == 'STATUS' or 'résumé' in i.normalized or 'situation' in i.normalized or 'dashboard' in i.normalized,
#                           'builder': self._dashboard},
#             # GLOBAL
#             'list_user':    {'matches': lambda i: i.category == 'user',    'builder': self._user_list},
#             'list_company': {'matches': lambda i: i.category == 'company', 'builder': self._company_list},
#             # FEATURES (NGV, NGA, etc.)
#             'top_feature': {'matches': lambda i: i.entities.get('feature') and i.action == 'TOP',
#                             'builder': self._feature_top},
#         }

#     # ═══════════════════════════════════════════════════════════
#     # MATCHING
#     # ═══════════════════════════════════════════════════════════

#     def match(self, intent, db_name: str) -> Optional[TemplateMatch]:
#         self.stats['total'] += 1
#         for name, tmpl in self.templates.items():
#             try:
#                 if tmpl['matches'](intent):
#                     sql = tmpl['builder'](intent, db_name)
#                     if sql:
#                         self.stats['matched'] += 1
#                         self.stats['by_template'][name] = self.stats['by_template'].get(name, 0) + 1
#                         return TemplateMatch(
#                             template_name=name,
#                             sql=sql.strip(),
#                             confidence=intent.confidence,
#                             entities_used=intent.entities,
#                         )
#             except Exception as e:
#                 print(f"   ⚠️ Template {name} erreur: {e}")
#                 continue
#         return None

#     # ═══════════════════════════════════════════════════════════
#     # HELPERS
#     # ═══════════════════════════════════════════════════════════

#     def _build_time_filter(self, column: str, modifiers: List[str]) -> str:
#         for mod in modifiers:
#             if mod in self.TIME_FILTERS:
#                 return f"AND {self.TIME_FILTERS[mod].format(col=column)}"
#         return ""

#     def _fault_conditions(self, fault_type: str) -> str:
#         patterns = self.FAULT_LIKE_PATTERNS.get(fault_type, [fault_type])
#         return " OR ".join([f"f.name LIKE '%{p}%'" for p in patterns])

#     # ═══════════════════════════════════════════════════════════
#     # BUILDERS — FAULTS
#     # ═══════════════════════════════════════════════════════════

#     def _fault_list(self, intent, db: str) -> str:
#         ft = intent.entities.get('fault_type')
#         fault_filter = f"AND ({self._fault_conditions(ft)})" if ft else ""
#         status_filter = "AND af.end_date IS NULL"
#         if 'resolved' in intent.modifiers:
#             status_filter = "AND af.end_date IS NOT NULL"
#         elif 'all' in intent.modifiers:
#             status_filter = ""
#         time_filter = self._build_time_filter('af.start_date', intent.modifiers)

#         return f"""
#             SELECT a.id, a.name, a.ref, f.name AS fault_type,
#                    af.start_date, af.end_date,
#                    TIMESTAMPDIFF(HOUR, af.start_date, COALESCE(af.end_date, NOW())) AS heures
#             FROM {db}.assets a
#             INNER JOIN {db}.asset_faults af ON a.id = af.asset_id
#             INNER JOIN {db}.faults f ON af.fault_id = f.id
#             WHERE a.deleted_at IS NULL
#               AND af.deleted_at IS NULL
#               {status_filter}
#               {fault_filter}
#               {time_filter}
#             ORDER BY af.start_date DESC
#             LIMIT 30;
#         """

#     def _fault_count(self, intent, db: str) -> str:
#         ft = intent.entities.get('fault_type')
#         join_f = f"INNER JOIN {db}.faults f ON af.fault_id = f.id" if ft else ""
#         fault_filter = f"AND ({self._fault_conditions(ft)})" if ft else ""
#         time_filter = self._build_time_filter('af.start_date', intent.modifiers)

#         return f"""
#             SELECT
#                 COUNT(*) AS total,
#                 SUM(CASE WHEN af.end_date IS NULL THEN 1 ELSE 0 END) AS actives,
#                 SUM(CASE WHEN af.end_date IS NOT NULL THEN 1 ELSE 0 END) AS resolues
#             FROM {db}.asset_faults af
#             {join_f}
#             WHERE af.deleted_at IS NULL
#               {fault_filter}
#               {time_filter};
#         """

#     def _fault_top(self, intent, db: str) -> str:
#         time_filter = self._build_time_filter('af.start_date', intent.modifiers)
#         return f"""
#             SELECT a.id, a.name, a.ref,
#                    COUNT(af.id) AS nb_defauts,
#                    COUNT(DISTINCT af.fault_id) AS types_distincts
#             FROM {db}.assets a
#             INNER JOIN {db}.asset_faults af ON a.id = af.asset_id
#             WHERE a.deleted_at IS NULL
#               AND af.deleted_at IS NULL
#               {time_filter}
#             GROUP BY a.id, a.name, a.ref
#             ORDER BY nb_defauts DESC
#             LIMIT 10;
#         """

#     def _fault_trend(self, intent, db: str) -> str:
#         return f"""
#             SELECT DATE_FORMAT(af.start_date, '%Y-%m') AS mois,
#                    COUNT(*) AS nb_defauts,
#                    COUNT(DISTINCT af.asset_id) AS equipements_touches
#             FROM {db}.asset_faults af
#             WHERE af.start_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
#               AND af.deleted_at IS NULL
#             GROUP BY mois
#             ORDER BY mois ASC;
#         """

#     # ═══════════════════════════════════════════════════════════
#     # BUILDERS — ALARMS
#     # ═══════════════════════════════════════════════════════════

#     def _alarm_list(self, intent, db: str) -> str:
#         status_filter = "AND al.ended_at IS NULL"
#         if 'resolved' in intent.modifiers:
#             status_filter = "AND al.ended_at IS NOT NULL"
#         elif 'all' in intent.modifiers:
#             status_filter = ""
#         critical = "AND al.status = 5" if 'critical' in intent.modifiers else ""
#         time_f = self._build_time_filter('al.created_at', intent.modifiers)

#         return f"""
#             SELECT a.id, a.name, a.ref, al.status, al.created_at, al.ended_at,
#                    TIMESTAMPDIFF(HOUR, al.created_at, COALESCE(al.ended_at, NOW())) AS heures
#             FROM {db}.alarms al
#             INNER JOIN {db}.assets a ON al.asset_id = a.id
#             WHERE a.deleted_at IS NULL
#               AND al.deleted_at IS NULL
#               {status_filter}
#               {critical}
#               {time_f}
#             ORDER BY al.created_at DESC
#             LIMIT 30;
#         """

#     def _alarm_count(self, intent, db: str) -> str:
#         critical = "AND status = 5" if 'critical' in intent.modifiers else ""
#         time_f = self._build_time_filter('created_at', intent.modifiers)

#         return f"""
#             SELECT
#                 COUNT(*) AS total,
#                 SUM(CASE WHEN ended_at IS NULL THEN 1 ELSE 0 END) AS actives,
#                 SUM(CASE WHEN ended_at IS NOT NULL THEN 1 ELSE 0 END) AS resolues,
#                 SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) AS critiques
#             FROM {db}.alarms
#             WHERE deleted_at IS NULL
#               {critical}
#               {time_f};
#         """

#     def _alarm_top(self, intent, db: str) -> str:
#         time_f = self._build_time_filter('al.created_at', intent.modifiers)
#         return f"""
#             SELECT a.id, a.name, a.ref, COUNT(al.id) AS nb_alarmes
#             FROM {db}.alarms al
#             INNER JOIN {db}.assets a ON al.asset_id = a.id
#             WHERE a.deleted_at IS NULL
#               AND al.deleted_at IS NULL
#               {time_f}
#             GROUP BY a.id, a.name, a.ref
#             ORDER BY nb_alarmes DESC
#             LIMIT 10;
#         """

#     # ═══════════════════════════════════════════════════════════
#     # BUILDERS — ASSETS
#     # ═══════════════════════════════════════════════════════════

#     def _asset_list(self, intent, db: str) -> str:
#         status_filter = ""
#         if 'critical' in intent.modifiers:
#             status_filter = "AND a.status = 5"
#         elif 'normal' in intent.modifiers:
#             status_filter = "AND a.status = 1"
#         elif 'stopped' in intent.modifiers:
#             status_filter = "AND a.status = 0"

#         return f"""
#             SELECT a.id, a.name, a.ref, a.status,
#                    CASE
#                        WHEN a.status = -1 THEN 'Unassigned'
#                        WHEN a.status = 0  THEN 'Shut down'
#                        WHEN a.status = 1  THEN 'Normal'
#                        WHEN a.status = 2  THEN 'MID'
#                        WHEN a.status = 3  THEN 'Moderate'
#                        WHEN a.status = 5  THEN 'Critical'
#                        ELSE 'Undefined'
#                    END AS status_label,
#                    a.brand, a.rpm
#             FROM {db}.assets a
#             WHERE a.deleted_at IS NULL
#               {status_filter}
#             ORDER BY a.status DESC, a.name
#             LIMIT 50;
#         """

#     def _asset_count(self, intent, db: str) -> str:
#         return f"""
#             SELECT
#                 COUNT(*) AS total,
#                 SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) AS critiques,
#                 SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS normaux,
#                 SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) AS arretes,
#                 SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) AS moderes
#             FROM {db}.assets
#             WHERE deleted_at IS NULL;
#         """

#     def _asset_status(self, intent, db: str) -> str:
#         return f"""
#             SELECT a.id, a.name, a.ref, a.status,
#                    COUNT(DISTINCT al.id) AS alarmes_actives,
#                    COUNT(DISTINCT af.id) AS pannes_actives
#             FROM {db}.assets a
#             LEFT JOIN {db}.alarms al ON a.id = al.asset_id
#                 AND al.ended_at IS NULL AND al.deleted_at IS NULL
#             LEFT JOIN {db}.asset_faults af ON a.id = af.asset_id
#                 AND af.end_date IS NULL AND af.deleted_at IS NULL
#             WHERE a.deleted_at IS NULL
#             GROUP BY a.id, a.name, a.ref, a.status
#             ORDER BY a.status DESC
#             LIMIT 30;
#         """

#     # ═══════════════════════════════════════════════════════════
#     # BUILDERS — MEASUREMENTS
#     # ═══════════════════════════════════════════════════════════

#     def _measure_list(self, intent, db: str) -> str:
#         time_f = self._build_time_filter('m.created_at', intent.modifiers) or \
#                  "AND m.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
#         return f"""
#             SELECT a.id, a.name, a.ref, m.status, m.is_online, m.created_at
#             FROM {db}.measurements m
#             INNER JOIN {db}.assets a ON m.asset_id = a.id
#             WHERE m.deleted_at IS NULL
#               AND a.deleted_at IS NULL
#               {time_f}
#             ORDER BY m.created_at DESC
#             LIMIT 30;
#         """

#     def _measure_top(self, intent, db: str) -> str:
#         feat = intent.entities.get('feature', 'NGV')
#         return f"""
#             SELECT a.id, a.name, a.ref,
#                    fm.value AS valeur,
#                    fg.alarm AS seuil,
#                    (fm.value - fg.alarm) AS depassement,
#                    fm.created_at
#             FROM {db}.feature_measurement fm
#             INNER JOIN {db}.assets a ON fm.asset_parent_id = a.id
#             INNER JOIN {db}.feature_group fg
#                 ON fm.feature_id = fg.feature_id AND fm.group_id = fg.group_id
#             WHERE fm.feature_id = (
#                 SELECT id FROM i_sense_v3_devenv_db.features
#                 WHERE name = '{feat}' AND deleted_at IS NULL LIMIT 1
#             )
#             AND fm.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
#             AND fm.deleted_at IS NULL
#             AND a.deleted_at IS NULL
#             ORDER BY fm.value DESC
#             LIMIT 10;
#         """

#     def _feature_top(self, intent, db: str) -> str:
#         return self._measure_top(intent, db)

#     # ═══════════════════════════════════════════════════════════
#     # BUILDERS — RECOMMENDATIONS / INTERVENTIONS
#     # ═══════════════════════════════════════════════════════════

#     def _reco_list(self, intent, db: str) -> str:
#         return f"""
#             SELECT ra.id, a.name, a.ref, ra.fault, ra.cause,
#                    ra.notes, ra.status, ra.started_at, ra.ended_at
#             FROM {db}.recommendation_assets ra
#             INNER JOIN {db}.assets a ON ra.asset_id = a.id
#             WHERE ra.deleted_at IS NULL
#               AND a.deleted_at IS NULL
#             ORDER BY ra.started_at DESC
#             LIMIT 20;
#         """

#     def _intervention_list(self, intent, db: str) -> str:
#         time_f = self._build_time_filter('i.created_at', intent.modifiers)
#         return f"""
#             SELECT i.id, a.name, a.ref, i.description, i.status,
#                    i.date_intervention, i.created_at
#             FROM {db}.interventions i
#             INNER JOIN {db}.assets a ON i.asset_id = a.id
#             WHERE i.deleted_at IS NULL
#               AND a.deleted_at IS NULL
#               {time_f}
#             ORDER BY i.created_at DESC
#             LIMIT 20;
#         """

#     # ═══════════════════════════════════════════════════════════
#     # BUILDER — DASHBOARD
#     # ═══════════════════════════════════════════════════════════

#     def _dashboard(self, intent, db: str) -> str:
#         return f"""
#             SELECT
#                 (SELECT COUNT(*) FROM {db}.assets WHERE deleted_at IS NULL) AS total_equipements,
#                 (SELECT COUNT(*) FROM {db}.assets WHERE status = 5 AND deleted_at IS NULL) AS critiques,
#                 (SELECT COUNT(*) FROM {db}.assets WHERE status = 0 AND deleted_at IS NULL) AS arretes,
#                 (SELECT COUNT(*) FROM {db}.alarms WHERE ended_at IS NULL AND deleted_at IS NULL) AS alarmes_actives,
#                 (SELECT COUNT(*) FROM {db}.alarms WHERE ended_at IS NULL AND status = 5 AND deleted_at IS NULL) AS alarmes_critiques,
#                 (SELECT COUNT(*) FROM {db}.asset_faults WHERE end_date IS NULL AND deleted_at IS NULL) AS pannes_actives;
#         """

#     # ═══════════════════════════════════════════════════════════
#     # BUILDERS — USERS / COMPANIES
#     # ═══════════════════════════════════════════════════════════

#     def _user_list(self, intent, db: str) -> str:
#         return """
#             SELECT u.id, u.first_name, u.last_name, u.email,
#                    u.active, u.last_connection, c.name AS company
#             FROM i_sense_v3_devenv_db.users u
#             LEFT JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id
#             LEFT JOIN i_sense_v3_devenv_db.companies c ON uc.company_id = c.id
#             WHERE u.deleted_at IS NULL
#             ORDER BY u.last_connection DESC
#             LIMIT 30;
#         """

#     def _company_list(self, intent, db: str) -> str:
#         return """
#             SELECT c.id, c.name, c.reference, c.alias,
#                    COUNT(DISTINCT uc.user_id) AS nb_users
#             FROM i_sense_v3_devenv_db.companies c
#             LEFT JOIN i_sense_v3_devenv_db.user_company uc ON c.id = uc.company_id
#             WHERE c.deleted_at IS NULL
#             GROUP BY c.id, c.name, c.reference, c.alias
#             ORDER BY c.name;
#         """

#     def get_stats(self):
#         s = self.stats.copy()
#         if s['total'] > 0:
#             s['match_rate'] = f"{s['matched'] / s['total'] * 100:.1f}%"
#         return s


# # ═══════════════════════════════════════════════════════════════
# # TEST
# # ═══════════════════════════════════════════════════════════════

# if __name__ == "__main__":
#     from intent_classifier_v6 import IntentClassifierV6

#     print("\n" + "=" * 80)
#     print(" " * 20 + "🎯 PARAMETRIC TEMPLATES V6 - TEST")
#     print("=" * 80)

#     classifier = IntentClassifierV6()
#     engine = ParametricTemplateEngineV6()

#     questions = [
#         "Pannes actives à JLN ?",
#         "Combien d'alarmes critiques aujourd'hui ?",
#         "Top 10 équipements avec NGV élevée",
#         "Liste des défauts de roulement",
#         "Évolution des pannes ce mois",
#         "Recommandations à Safi",
#         "Résumé situation",
#         "Équipements arrêtés",
#         "Mesures récentes",
#     ]

#     for q in questions:
#         intent = classifier.classify(q)
#         match = engine.match(intent, "v3_tenant_jln")
#         print(f"\n❓ {q}")
#         if match:
#             print(f"   ✅ Template: {match.template_name}")
#             print(f"   SQL: {match.sql[:120]}...")
#         else:
#             print(f"   ❌ No match (intent: {intent.name})")

#     print(f"\n {engine.get_stats()}")
#     print("\n" + "=" * 80 + "\n")
# ------------------------2------------------------------------------------------------
# # backend/app/agents/parametric_templates_v6.py
# """
# Parametric Template Engine V6 – avec gardes métier
# Empêche les templates génériques de répondre à des questions
# sur les défauts, mesures, features ou alarmes.
# """

# from typing import Dict, List, Optional
# from dataclasses import dataclass


# @dataclass
# class TemplateMatch:
#     template_name: str
#     sql: str
#     confidence: float
#     entities_used: Dict


# class ParametricTemplateEngineV6:

#     # Synonymes étendus pour types de défauts (LIKE patterns)
#     FAULT_LIKE_PATTERNS = {
#         'bearing': ['Bearing', 'roulement', 'Rolling Element', 'Inner Race', 'Outer Race'],
#         'lubrication': ['Lubrification', 'lubrification', 'Lubrication'],
#         'misalignment': ['Misalignment', 'alignement'],
#         'imbalance': ['Imbalance', 'balourd'],
#         'cavitation': ['Cavitation'],
#         'belt': ['Belt', 'courroie'],
#         'gear': ['Gear', 'engrenage'],
#         'electrical': ['Electrical', 'AC Electrical', 'DC Electrical'],
#         'sensor': ['Fault sensor', 'Sensor Saturation'],
#         'looseness': ['Mechanical looseness'],
#         'friction': ['Friction', 'frottement'],
#         'outlier': ['Outliers'],
#         'shutdown': ['shutdown'],
#         'structural': ['Structural Fault'],
#         'oil_turbulence': ["Turbulence d'huile"],
#         'ski_slope': ['Ski slope'],
#     }

#     # Filtres temporels
#     TIME_FILTERS = {
#         'today':       "DATE({col}) = CURDATE()",
#         'yesterday':   "DATE({col}) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)",
#         'this_week':   "{col} >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)",
#         'last_week':   "{col} >= DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND {col} < DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
#         'this_month':  "YEAR({col}) = YEAR(CURDATE()) AND MONTH({col}) = MONTH(CURDATE())",
#         'last_30_days': "{col} >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
#         'recent':      "{col} >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
#     }

#     # -----------------------------------------------------------------
#     # GARDES MÉTIER (ajout V7)
#     # -----------------------------------------------------------------
#     TEMPLATE_GUARDS = {
#         'list_asset': lambda intent: not (
#             intent.entities.get('fault_type') or
#             intent.entities.get('feature') or
#             any(w in intent.normalized for w in (
#                 'alarme', 'alerte', 'notification', 'durée', 'depuis',
#                 'mesure', 'ngv', 'nga', 'temperature', 'défaut',
#                 'panne', 'problème', 'intervention', 'recommandation',
#                 'facture', 'email', 'sms', 'abonnement'
#             ))
#         ),
#         # On peut ajouter d'autres gardes si nécessaire, par défaut tout est autorisé
#     }

#     def __init__(self):
#         self.templates = self._build_templates()
#         self.stats = {
#             'total': 0,
#             'matched': 0,
#             'by_template': {},
#         }

#     def _build_templates(self) -> Dict:
#         return {
#             # FAULTS
#             'list_fault':  {'matches': lambda i: i.category == 'fault' and i.action == 'LIST',     'builder': self._fault_list},
#             'count_fault': {'matches': lambda i: i.category == 'fault' and i.action == 'COUNT',    'builder': self._fault_count},
#             'top_fault':   {'matches': lambda i: i.category == 'fault' and i.action == 'TOP',      'builder': self._fault_top},
#             'trend_fault': {'matches': lambda i: i.category == 'fault' and i.action == 'TREND',    'builder': self._fault_trend},
#             # ALARMS
#             'list_alarm':  {'matches': lambda i: i.category == 'alarm' and i.action == 'LIST',     'builder': self._alarm_list},
#             'count_alarm': {'matches': lambda i: i.category == 'alarm' and i.action == 'COUNT',    'builder': self._alarm_count},
#             'top_alarm':   {'matches': lambda i: i.category == 'alarm' and i.action == 'TOP',      'builder': self._alarm_top},
#             # ASSETS
#             'list_asset':   {'matches': lambda i: i.category == 'asset' and i.action == 'LIST',    'builder': self._asset_list},
#             'count_asset':  {'matches': lambda i: i.category == 'asset' and i.action == 'COUNT',   'builder': self._asset_count},
#             'status_asset': {'matches': lambda i: i.category == 'asset' and i.action == 'STATUS',  'builder': self._asset_status},
#             # MEASUREMENTS
#             'list_measurement': {'matches': lambda i: i.category == 'measurement' and i.action == 'LIST',  'builder': self._measure_list},
#             'top_measurement':  {'matches': lambda i: i.category == 'measurement' and i.action == 'TOP',   'builder': self._measure_top},
#             # RECOMMENDATIONS
#             'list_recommendation': {'matches': lambda i: i.category == 'recommendation', 'builder': self._reco_list},
#             # INTERVENTIONS
#             'list_intervention': {'matches': lambda i: i.category == 'intervention', 'builder': self._intervention_list},
#             # DASHBOARD
#             'dashboard': {'matches': lambda i: i.action == 'STATUS' or 'résumé' in i.normalized or 'situation' in i.normalized or 'dashboard' in i.normalized,
#                           'builder': self._dashboard},
#             # GLOBAL
#             'list_user':    {'matches': lambda i: i.category == 'user',    'builder': self._user_list},
#             'list_company': {'matches': lambda i: i.category == 'company', 'builder': self._company_list},
#             # FEATURES
#             'top_feature': {'matches': lambda i: i.entities.get('feature') and i.action == 'TOP',
#                             'builder': self._feature_top},
#         }

#     # -----------------------------------------------------------------
#     # MATCHING avec gardes
#     # -----------------------------------------------------------------
#     def match(self, intent, db_name: str) -> Optional[TemplateMatch]:
#         self.stats['total'] += 1
#         for name, tmpl in self.templates.items():
#             try:
#                 if tmpl['matches'](intent):
#                     # Vérifier les gardes métier
#                     guard = self.TEMPLATE_GUARDS.get(name, lambda i: True)
#                     if not guard(intent):
#                         continue   # ce template ne doit pas répondre

#                     sql = tmpl['builder'](intent, db_name)
#                     if sql:
#                         self.stats['matched'] += 1
#                         self.stats['by_template'][name] = self.stats['by_template'].get(name, 0) + 1
#                         return TemplateMatch(
#                             template_name=name,
#                             sql=sql.strip(),
#                             confidence=intent.confidence,
#                             entities_used=intent.entities,
#                         )
#             except Exception as e:
#                 print(f"   ⚠️ Template {name} erreur: {e}")
#                 continue
#         return None

#     # -----------------------------------------------------------------
#     # HELPERS (inchangés)
#     # -----------------------------------------------------------------
#     def _build_time_filter(self, column: str, modifiers: List[str]) -> str:
#         for mod in modifiers:
#             if mod in self.TIME_FILTERS:
#                 return f"AND {self.TIME_FILTERS[mod].format(col=column)}"
#         return ""

#     def _fault_conditions(self, fault_type: str) -> str:
#         patterns = self.FAULT_LIKE_PATTERNS.get(fault_type, [fault_type])
#         return " OR ".join([f"f.name LIKE '%{p}%'" for p in patterns])

#     # -----------------------------------------------------------------
#     # BUILDERS (identiques à l'original)
#     # -----------------------------------------------------------------
#     def _fault_list(self, intent, db: str) -> str:
#         ft = intent.entities.get('fault_type')
#         fault_filter = f"AND ({self._fault_conditions(ft)})" if ft else ""
#         status_filter = "AND af.end_date IS NULL"
#         if 'resolved' in intent.modifiers:
#             status_filter = "AND af.end_date IS NOT NULL"
#         elif 'all' in intent.modifiers:
#             status_filter = ""
#         time_filter = self._build_time_filter('af.start_date', intent.modifiers)

#         return f"""
#             SELECT a.id, a.name, a.ref, f.name AS fault_type,
#                    af.start_date, af.end_date,
#                    TIMESTAMPDIFF(HOUR, af.start_date, COALESCE(af.end_date, NOW())) AS heures
#             FROM {db}.assets a
#             INNER JOIN {db}.asset_faults af ON a.id = af.asset_id
#             INNER JOIN {db}.faults f ON af.fault_id = f.id
#             WHERE a.deleted_at IS NULL
#               AND af.deleted_at IS NULL
#               {status_filter}
#               {fault_filter}
#               {time_filter}
#             ORDER BY af.start_date DESC
#             LIMIT 30;
#         """

#     def _fault_count(self, intent, db: str) -> str:
#         ft = intent.entities.get('fault_type')
#         join_f = f"INNER JOIN {db}.faults f ON af.fault_id = f.id" if ft else ""
#         fault_filter = f"AND ({self._fault_conditions(ft)})" if ft else ""
#         time_filter = self._build_time_filter('af.start_date', intent.modifiers)

#         return f"""
#             SELECT
#                 COUNT(*) AS total,
#                 SUM(CASE WHEN af.end_date IS NULL THEN 1 ELSE 0 END) AS actives,
#                 SUM(CASE WHEN af.end_date IS NOT NULL THEN 1 ELSE 0 END) AS resolues
#             FROM {db}.asset_faults af
#             {join_f}
#             WHERE af.deleted_at IS NULL
#               {fault_filter}
#               {time_filter};
#         """

#     def _fault_top(self, intent, db: str) -> str:
#         time_filter = self._build_time_filter('af.start_date', intent.modifiers)
#         return f"""
#             SELECT a.id, a.name, a.ref,
#                    COUNT(af.id) AS nb_defauts,
#                    COUNT(DISTINCT af.fault_id) AS types_distincts
#             FROM {db}.assets a
#             INNER JOIN {db}.asset_faults af ON a.id = af.asset_id
#             WHERE a.deleted_at IS NULL
#               AND af.deleted_at IS NULL
#               {time_filter}
#             GROUP BY a.id, a.name, a.ref
#             ORDER BY nb_defauts DESC
#             LIMIT 10;
#         """

#     def _fault_trend(self, intent, db: str) -> str:
#         return f"""
#             SELECT DATE_FORMAT(af.start_date, '%Y-%m') AS mois,
#                    COUNT(*) AS nb_defauts,
#                    COUNT(DISTINCT af.asset_id) AS equipements_touches
#             FROM {db}.asset_faults af
#             WHERE af.start_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
#               AND af.deleted_at IS NULL
#             GROUP BY mois
#             ORDER BY mois ASC;
#         """

#     def _alarm_list(self, intent, db: str) -> str:
#         status_filter = "AND al.ended_at IS NULL"
#         if 'resolved' in intent.modifiers:
#             status_filter = "AND al.ended_at IS NOT NULL"
#         elif 'all' in intent.modifiers:
#             status_filter = ""
#         critical = "AND al.status = 5" if 'critical' in intent.modifiers else ""
#         time_f = self._build_time_filter('al.created_at', intent.modifiers)

#         return f"""
#             SELECT a.id, a.name, a.ref, al.status, al.created_at, al.ended_at,
#                    TIMESTAMPDIFF(HOUR, al.created_at, COALESCE(al.ended_at, NOW())) AS heures
#             FROM {db}.alarms al
#             INNER JOIN {db}.assets a ON al.asset_id = a.id
#             WHERE a.deleted_at IS NULL
#               AND al.deleted_at IS NULL
#               {status_filter}
#               {critical}
#               {time_f}
#             ORDER BY al.created_at DESC
#             LIMIT 30;
#         """

#     def _alarm_count(self, intent, db: str) -> str:
#         critical = "AND status = 5" if 'critical' in intent.modifiers else ""
#         time_f = self._build_time_filter('created_at', intent.modifiers)

#         return f"""
#             SELECT
#                 COUNT(*) AS total,
#                 SUM(CASE WHEN ended_at IS NULL THEN 1 ELSE 0 END) AS actives,
#                 SUM(CASE WHEN ended_at IS NOT NULL THEN 1 ELSE 0 END) AS resolues,
#                 SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) AS critiques
#             FROM {db}.alarms
#             WHERE deleted_at IS NULL
#               {critical}
#               {time_f};
#         """

#     def _alarm_top(self, intent, db: str) -> str:
#         time_f = self._build_time_filter('al.created_at', intent.modifiers)
#         return f"""
#             SELECT a.id, a.name, a.ref, COUNT(al.id) AS nb_alarmes
#             FROM {db}.alarms al
#             INNER JOIN {db}.assets a ON al.asset_id = a.id
#             WHERE a.deleted_at IS NULL
#               AND al.deleted_at IS NULL
#               {time_f}
#             GROUP BY a.id, a.name, a.ref
#             ORDER BY nb_alarmes DESC
#             LIMIT 10;
#         """

#     def _asset_list(self, intent, db: str) -> str:
#         status_filter = ""
#         if 'critical' in intent.modifiers:
#             status_filter = "AND a.status = 5"
#         elif 'normal' in intent.modifiers:
#             status_filter = "AND a.status = 1"
#         elif 'stopped' in intent.modifiers:
#             status_filter = "AND a.status = 0"

#         return f"""
#             SELECT a.id, a.name, a.ref, a.status,
#                    CASE
#                        WHEN a.status = -1 THEN 'Unassigned'
#                        WHEN a.status = 0  THEN 'Shut down'
#                        WHEN a.status = 1  THEN 'Normal'
#                        WHEN a.status = 2  THEN 'MID'
#                        WHEN a.status = 3  THEN 'Moderate'
#                        WHEN a.status = 5  THEN 'Critical'
#                        ELSE 'Undefined'
#                    END AS status_label,
#                    a.brand, a.rpm
#             FROM {db}.assets a
#             WHERE a.deleted_at IS NULL
#               {status_filter}
#             ORDER BY a.status DESC, a.name
#             LIMIT 50;
#         """

#     def _asset_count(self, intent, db: str) -> str:
#         return f"""
#             SELECT
#                 COUNT(*) AS total,
#                 SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) AS critiques,
#                 SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS normaux,
#                 SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) AS arretes,
#                 SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) AS moderes
#             FROM {db}.assets
#             WHERE deleted_at IS NULL;
#         """

#     def _asset_status(self, intent, db: str) -> str:
#         return f"""
#             SELECT a.id, a.name, a.ref, a.status,
#                    COUNT(DISTINCT al.id) AS alarmes_actives,
#                    COUNT(DISTINCT af.id) AS pannes_actives
#             FROM {db}.assets a
#             LEFT JOIN {db}.alarms al ON a.id = al.asset_id
#                 AND al.ended_at IS NULL AND al.deleted_at IS NULL
#             LEFT JOIN {db}.asset_faults af ON a.id = af.asset_id
#                 AND af.end_date IS NULL AND af.deleted_at IS NULL
#             WHERE a.deleted_at IS NULL
#             GROUP BY a.id, a.name, a.ref, a.status
#             ORDER BY a.status DESC
#             LIMIT 30;
#         """

#     def _measure_list(self, intent, db: str) -> str:
#         time_f = self._build_time_filter('m.created_at', intent.modifiers) or \
#                  "AND m.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
#         return f"""
#             SELECT a.id, a.name, a.ref, m.status, m.is_online, m.created_at
#             FROM {db}.measurements m
#             INNER JOIN {db}.assets a ON m.asset_id = a.id
#             WHERE m.deleted_at IS NULL
#               AND a.deleted_at IS NULL
#               {time_f}
#             ORDER BY m.created_at DESC
#             LIMIT 30;
#         """

#     def _measure_top(self, intent, db: str) -> str:
#         feat = intent.entities.get('feature', 'NGV')
#         return f"""
#             SELECT a.id, a.name, a.ref,
#                    fm.value AS valeur,
#                    fg.alarm AS seuil,
#                    (fm.value - fg.alarm) AS depassement,
#                    fm.created_at
#             FROM {db}.feature_measurement fm
#             INNER JOIN {db}.assets a ON fm.asset_parent_id = a.id
#             INNER JOIN {db}.feature_group fg
#                 ON fm.feature_id = fg.feature_id AND fm.group_id = fg.group_id
#             WHERE fm.feature_id = (
#                 SELECT id FROM i_sense_v3_devenv_db.features
#                 WHERE name = '{feat}' AND deleted_at IS NULL LIMIT 1
#             )
#             AND fm.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
#             AND fm.deleted_at IS NULL
#             AND a.deleted_at IS NULL
#             ORDER BY fm.value DESC
#             LIMIT 10;
#         """

#     def _feature_top(self, intent, db: str) -> str:
#         return self._measure_top(intent, db)

#     def _reco_list(self, intent, db: str) -> str:
#         return f"""
#             SELECT ra.id, a.name, a.ref, ra.fault, ra.cause,
#                    ra.notes, ra.status, ra.started_at, ra.ended_at
#             FROM {db}.recommendation_assets ra
#             INNER JOIN {db}.assets a ON ra.asset_id = a.id
#             WHERE ra.deleted_at IS NULL
#               AND a.deleted_at IS NULL
#             ORDER BY ra.started_at DESC
#             LIMIT 20;
#         """

#     def _intervention_list(self, intent, db: str) -> str:
#         time_f = self._build_time_filter('i.created_at', intent.modifiers)
#         return f"""
#             SELECT i.id, a.name, a.ref, i.description, i.status,
#                    i.date_intervention, i.created_at
#             FROM {db}.interventions i
#             INNER JOIN {db}.assets a ON i.asset_id = a.id
#             WHERE i.deleted_at IS NULL
#               AND a.deleted_at IS NULL
#               {time_f}
#             ORDER BY i.created_at DESC
#             LIMIT 20;
#         """

#     def _dashboard(self, intent, db: str) -> str:
#         return f"""
#             SELECT
#                 (SELECT COUNT(*) FROM {db}.assets WHERE deleted_at IS NULL) AS total_equipements,
#                 (SELECT COUNT(*) FROM {db}.assets WHERE status = 5 AND deleted_at IS NULL) AS critiques,
#                 (SELECT COUNT(*) FROM {db}.assets WHERE status = 0 AND deleted_at IS NULL) AS arretes,
#                 (SELECT COUNT(*) FROM {db}.alarms WHERE ended_at IS NULL AND deleted_at IS NULL) AS alarmes_actives,
#                 (SELECT COUNT(*) FROM {db}.alarms WHERE ended_at IS NULL AND status = 5 AND deleted_at IS NULL) AS alarmes_critiques,
#                 (SELECT COUNT(*) FROM {db}.asset_faults WHERE end_date IS NULL AND deleted_at IS NULL) AS pannes_actives;
#         """

#     def _user_list(self, intent, db: str) -> str:
#         return """
#             SELECT u.id, u.first_name, u.last_name, u.email,
#                    u.active, u.last_connection, c.name AS company
#             FROM i_sense_v3_devenv_db.users u
#             LEFT JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id
#             LEFT JOIN i_sense_v3_devenv_db.companies c ON uc.company_id = c.id
#             WHERE u.deleted_at IS NULL
#             ORDER BY u.last_connection DESC
#             LIMIT 30;
#         """

#     def _company_list(self, intent, db: str) -> str:
#         return """
#             SELECT c.id, c.name, c.reference, c.alias,
#                    COUNT(DISTINCT uc.user_id) AS nb_users
#             FROM i_sense_v3_devenv_db.companies c
#             LEFT JOIN i_sense_v3_devenv_db.user_company uc ON c.id = uc.company_id
#             WHERE c.deleted_at IS NULL
#             GROUP BY c.id, c.name, c.reference, c.alias
#             ORDER BY c.name;
#         """

#     def get_stats(self):
#         s = self.stats.copy()
#         if s['total'] > 0:
#             s['match_rate'] = f"{s['matched'] / s['total'] * 100:.1f}%"
#         return s






# backend/app/agents/parametric_templates_v6.py
"""
Parametric Template Engine V6 – corrections appliquées :

  fix-A : garde métier étendue sur list_asset (évite les faux positifs)
  fix-B : _fault_count() — filtre this_month utilise la colonne af.start_date
          et gère correctement le cas COUNT = 0 (retourne 0 et non NULL)
  fix-C : _fault_top() — limite à LIMIT 5 quand "top 5" est demandé
          (était toujours LIMIT 10 ; on lit intent.modifiers pour détecter le N)
  fix-D : _alarm_count() retire le filtre « status = 5 » par défaut
          (critique filtre seulement si 'critical' dans modifiers)
  fix-E : _dashboard() — utilise des alias sans espace pour MySQL 5.7+
  fix-F : _asset_count() ajoute SUM MID (status=2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import re


@dataclass
class TemplateMatch:
    template_name: str
    sql: str
    confidence: float
    entities_used: Dict


class ParametricTemplateEngineV6:

    # ── Synonymes LIKE pour les types de défauts ──────────────────────
    FAULT_LIKE_PATTERNS: Dict[str, List[str]] = {
        "bearing":       ["Bearing", "roulement", "Rolling Element", "Inner Race", "Outer Race"],
        "lubrication":   ["Lubrification", "lubrification", "Lubrication"],
        "misalignment":  ["Misalignment", "alignement"],
        "imbalance":     ["Imbalance", "balourd"],
        "cavitation":    ["Cavitation"],
        "belt":          ["Belt", "courroie"],
        "gear":          ["Gear", "engrenage"],
        "electrical":    ["Electrical", "AC Electrical", "DC Electrical"],
        "sensor":        ["Fault sensor", "Sensor Saturation"],
        "looseness":     ["Mechanical looseness"],
        "friction":      ["Friction", "frottement"],
        "outlier":       ["Outliers"],
        "shutdown":      ["shutdown"],
        "structural":    ["Structural Fault"],
        "oil_turbulence": ["Turbulence d'huile"],
        "ski_slope":     ["Ski slope"],
    }

    # ── Filtres temporels ─────────────────────────────────────────────
    TIME_FILTERS: Dict[str, str] = {
        "today":        "DATE({col}) = CURDATE()",
        "yesterday":    "DATE({col}) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)",
        "this_week":    "{col} >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)",
        "last_week":    "{col} >= DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND {col} < DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
        "this_month":   "YEAR({col}) = YEAR(CURDATE()) AND MONTH({col}) = MONTH(CURDATE())",
        "last_30_days": "{col} >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
        "recent":       "{col} >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
    }

    # ── Gardes métier — empêche les templates génériques de répondre
    #    à des questions qui nécessitent un traitement LLM spécialisé ──
    _ASSET_LIST_BANNED_WORDS = frozenset({
        "alarme", "alerte", "notification", "durée", "depuis",
        "mesure", "ngv", "nga", "temperature", "température",
        "défaut", "defaut", "panne", "problème", "probleme",
        "intervention", "recommandation", "facture", "email",
        "sms", "abonnement",
    })

    TEMPLATE_GUARDS: Dict[str, object] = {}  # rempli après définition de la méthode

    def __init__(self):
        self.templates = self._build_templates()
        # Guard dynamique défini ici pour avoir accès à self
        self.TEMPLATE_GUARDS = {
            "list_asset": lambda intent: not (
                intent.entities.get("fault_type")
                or intent.entities.get("feature")
                or any(
                    w in intent.normalized
                    for w in self._ASSET_LIST_BANNED_WORDS
                )
            ),
        }
        self.stats = {"total": 0, "matched": 0, "by_template": {}}

    # ─────────────────────────────────────────────────────────────────
    # REGISTRY DE TEMPLATES
    # ─────────────────────────────────────────────────────────────────
    def _build_templates(self) -> Dict:
        return {
            # FAULTS
            "list_fault":  {"matches": lambda i: i.category == "fault" and i.action == "LIST",   "builder": self._fault_list},
            "count_fault": {"matches": lambda i: i.category == "fault" and i.action == "COUNT",  "builder": self._fault_count},
            "top_fault":   {"matches": lambda i: i.category == "fault" and i.action == "TOP",    "builder": self._fault_top},
            "trend_fault": {"matches": lambda i: i.category == "fault" and i.action == "TREND",  "builder": self._fault_trend},
            # ALARMS
            "list_alarm":  {"matches": lambda i: i.category == "alarm" and i.action == "LIST",   "builder": self._alarm_list},
            "count_alarm": {"matches": lambda i: i.category == "alarm" and i.action == "COUNT",  "builder": self._alarm_count},
            "top_alarm":   {"matches": lambda i: i.category == "alarm" and i.action == "TOP",    "builder": self._alarm_top},
            # ASSETS
            "list_asset":   {"matches": lambda i: i.category == "asset" and i.action == "LIST",   "builder": self._asset_list},
            "count_asset":  {"matches": lambda i: i.category == "asset" and i.action == "COUNT",  "builder": self._asset_count},
            "status_asset": {"matches": lambda i: i.category == "asset" and i.action == "STATUS", "builder": self._asset_status},
            # MEASUREMENTS
            "list_measurement": {"matches": lambda i: i.category == "measurement" and i.action == "LIST", "builder": self._measure_list},
            "top_measurement":  {"matches": lambda i: i.category == "measurement" and i.action == "TOP",  "builder": self._measure_top},
            # RECOMMENDATIONS
            "list_recommendation": {"matches": lambda i: i.category == "recommendation", "builder": self._reco_list},
            # INTERVENTIONS
            "list_intervention": {"matches": lambda i: i.category == "intervention", "builder": self._intervention_list},
            # DASHBOARD
            "dashboard": {
                "matches": lambda i: (
                    i.action == "STATUS"
                    or "résumé" in i.normalized
                    or "situation" in i.normalized
                    or "dashboard" in i.normalized
                ),
                "builder": self._dashboard,
            },
            # GLOBAL
            "list_user":    {"matches": lambda i: i.category == "user",    "builder": self._user_list},
            "list_company": {"matches": lambda i: i.category == "company", "builder": self._company_list},
            # FEATURES
            "top_feature": {
                "matches": lambda i: bool(i.entities.get("feature")) and i.action == "TOP",
                "builder": self._feature_top,
            },
        }

    # ─────────────────────────────────────────────────────────────────
    # MATCHING
    # ─────────────────────────────────────────────────────────────────
    def match(self, intent, db_name: str) -> Optional[TemplateMatch]:
        self.stats["total"] += 1
        for name, tmpl in self.templates.items():
            try:
                if not tmpl["matches"](intent):
                    continue
                guard = self.TEMPLATE_GUARDS.get(name, lambda _: True)
                if not guard(intent):
                    continue
                sql = tmpl["builder"](intent, db_name)
                if sql:
                    self.stats["matched"] += 1
                    self.stats["by_template"][name] = (
                        self.stats["by_template"].get(name, 0) + 1
                    )
                    return TemplateMatch(
                        template_name=name,
                        sql=sql.strip(),
                        confidence=intent.confidence,
                        entities_used=intent.entities,
                    )
            except Exception as exc:
                print(f"   ⚠️ Template {name} erreur: {exc}")
        return None

    # ─────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────
    def _build_time_filter(self, column: str, modifiers: List[str]) -> str:
        for mod in modifiers:
            if mod in self.TIME_FILTERS:
                return f"AND {self.TIME_FILTERS[mod].format(col=column)}"
        return ""

    def _fault_conditions(self, fault_type: str) -> str:
        patterns = self.FAULT_LIKE_PATTERNS.get(fault_type, [fault_type])
        return " OR ".join(f"f.name LIKE '%{p}%'" for p in patterns)

    @staticmethod
    def _extract_top_n(intent) -> int:
        """Tente d'extraire le N dans 'top N' depuis la question normalisée."""
        m = re.search(r"\btop\s+(\d+)\b", getattr(intent, "normalized", ""), re.IGNORECASE)
        if m:
            return int(m.group(1))
        # Fallback : chercher le chiffre seul
        m = re.search(r"\b([3-9]|1[0-9]|20)\b", getattr(intent, "normalized", ""))
        return int(m.group(1)) if m else 10

    # ─────────────────────────────────────────────────────────────────
    # BUILDERS — FAULTS
    # ─────────────────────────────────────────────────────────────────
    def _fault_list(self, intent, db: str) -> str:
        ft = intent.entities.get("fault_type")
        fault_filter  = f"AND ({self._fault_conditions(ft)})" if ft else ""
        status_filter = "AND af.end_date IS NULL"
        if "resolved" in intent.modifiers:
            status_filter = "AND af.end_date IS NOT NULL"
        elif "all" in intent.modifiers:
            status_filter = ""
        time_filter = self._build_time_filter("af.start_date", intent.modifiers)

        return f"""
            SELECT a.id, a.name, a.ref, f.name AS fault_type,
                   af.start_date, af.end_date,
                   TIMESTAMPDIFF(HOUR, af.start_date, COALESCE(af.end_date, NOW())) AS heures
            FROM {db}.assets a
            INNER JOIN {db}.asset_faults af ON a.id = af.asset_id
            INNER JOIN {db}.faults f ON af.fault_id = f.id
            WHERE a.deleted_at IS NULL
              AND af.deleted_at IS NULL
              {status_filter}
              {fault_filter}
              {time_filter}
            ORDER BY af.start_date DESC
            LIMIT 30;
        """

    def _fault_count(self, intent, db: str) -> str:
        """
        fix-B : COALESCE sur les SUM pour que MySQL retourne 0 et non NULL
                quand il n'y a aucune ligne (filtre this_month sur start_date).
        """
        ft = intent.entities.get("fault_type")
        join_f       = f"INNER JOIN {db}.faults f ON af.fault_id = f.id" if ft else ""
        fault_filter = f"AND ({self._fault_conditions(ft)})" if ft else ""
        time_filter  = self._build_time_filter("af.start_date", intent.modifiers)

        return f"""
            SELECT
                COUNT(af.id)                                          AS total,
                COALESCE(SUM(af.end_date IS NULL),     0)            AS actives,
                COALESCE(SUM(af.end_date IS NOT NULL), 0)            AS resolues
            FROM {db}.asset_faults af
            {join_f}
            WHERE af.deleted_at IS NULL
              {fault_filter}
              {time_filter};
        """

    def _fault_top(self, intent, db: str) -> str:
        """fix-C : LIMIT adaptatif selon le N demandé dans la question."""
        limit       = self._extract_top_n(intent)
        time_filter = self._build_time_filter("af.start_date", intent.modifiers)

        return f"""
            SELECT a.id, a.name, a.ref,
                   COUNT(af.id)              AS nb_defauts,
                   COUNT(DISTINCT af.fault_id) AS types_distincts
            FROM {db}.assets a
            INNER JOIN {db}.asset_faults af ON a.id = af.asset_id
            WHERE a.deleted_at IS NULL
              AND af.deleted_at IS NULL
              {time_filter}
            GROUP BY a.id, a.name, a.ref
            ORDER BY nb_defauts DESC
            LIMIT {limit};
        """

    def _fault_trend(self, intent, db: str) -> str:
        return f"""
            SELECT DATE_FORMAT(af.start_date, '%Y-%m') AS mois,
                   COUNT(*)                             AS nb_defauts,
                   COUNT(DISTINCT af.asset_id)          AS equipements_touches
            FROM {db}.asset_faults af
            WHERE af.start_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
              AND af.deleted_at IS NULL
            GROUP BY mois
            ORDER BY mois ASC;
        """

    # ─────────────────────────────────────────────────────────────────
    # BUILDERS — ALARMS
    # ─────────────────────────────────────────────────────────────────
    def _alarm_list(self, intent, db: str) -> str:
        status_filter = "AND al.ended_at IS NULL"
        if "resolved" in intent.modifiers:
            status_filter = "AND al.ended_at IS NOT NULL"
        elif "all" in intent.modifiers:
            status_filter = ""
        critical = "AND al.status = 5" if "critical" in intent.modifiers else ""
        time_f   = self._build_time_filter("al.created_at", intent.modifiers)

        return f"""
            SELECT a.id, a.name, a.ref, al.status, al.created_at, al.ended_at,
                   TIMESTAMPDIFF(HOUR, al.created_at, COALESCE(al.ended_at, NOW())) AS heures
            FROM {db}.alarms al
            INNER JOIN {db}.assets a ON al.asset_id = a.id
            WHERE a.deleted_at IS NULL
              AND al.deleted_at IS NULL
              {status_filter}
              {critical}
              {time_f}
            ORDER BY al.created_at DESC
            LIMIT 30;
        """

    def _alarm_count(self, intent, db: str) -> str:
        """fix-D : le filtre 'critique' s'applique uniquement si demandé."""
        critical = "AND status = 5" if "critical" in intent.modifiers else ""
        time_f   = self._build_time_filter("created_at", intent.modifiers)

        return f"""
            SELECT
                COUNT(*)                                          AS total,
                COALESCE(SUM(ended_at IS NULL),     0)           AS actives,
                COALESCE(SUM(ended_at IS NOT NULL), 0)           AS resolues,
                COALESCE(SUM(status = 5),           0)           AS critiques
            FROM {db}.alarms
            WHERE deleted_at IS NULL
              {critical}
              {time_f};
        """

    def _alarm_top(self, intent, db: str) -> str:
        limit  = self._extract_top_n(intent)
        time_f = self._build_time_filter("al.created_at", intent.modifiers)

        return f"""
            SELECT a.id, a.name, a.ref, COUNT(al.id) AS nb_alarmes
            FROM {db}.alarms al
            INNER JOIN {db}.assets a ON al.asset_id = a.id
            WHERE a.deleted_at IS NULL
              AND al.deleted_at IS NULL
              {time_f}
            GROUP BY a.id, a.name, a.ref
            ORDER BY nb_alarmes DESC
            LIMIT {limit};
        """

    # ─────────────────────────────────────────────────────────────────
    # BUILDERS — ASSETS
    # ─────────────────────────────────────────────────────────────────
    def _asset_list(self, intent, db: str) -> str:
        status_filter = ""
        if "critical" in intent.modifiers:
            status_filter = "AND a.status = 5"
        elif "normal" in intent.modifiers:
            status_filter = "AND a.status = 1"
        elif "stopped" in intent.modifiers:
            status_filter = "AND a.status = 0"

        return f"""
            SELECT a.id, a.name, a.ref, a.status,
                   CASE
                       WHEN a.status = -1 THEN 'Unassigned'
                       WHEN a.status = 0  THEN 'Shut down'
                       WHEN a.status = 1  THEN 'Normal'
                       WHEN a.status = 2  THEN 'MID'
                       WHEN a.status = 3  THEN 'Moderate'
                       WHEN a.status = 5  THEN 'Critical'
                       ELSE 'Undefined'
                   END AS status_label,
                   a.brand, a.rpm
            FROM {db}.assets a
            WHERE a.deleted_at IS NULL
              {status_filter}
            ORDER BY a.status DESC, a.name
            LIMIT 50;
        """

    def _asset_count(self, intent, db: str) -> str:
        """fix-F : ajoute le comptage MID (status=2)."""
        return f"""
            SELECT
                COUNT(*)                          AS total,
                COALESCE(SUM(status = 5),  0)     AS critiques,
                COALESCE(SUM(status = 3),  0)     AS moderes,
                COALESCE(SUM(status = 2),  0)     AS mid,
                COALESCE(SUM(status = 1),  0)     AS normaux,
                COALESCE(SUM(status = 0),  0)     AS arretes
            FROM {db}.assets
            WHERE deleted_at IS NULL;
        """

    def _asset_status(self, intent, db: str) -> str:
        return f"""
            SELECT a.id, a.name, a.ref, a.status,
                   COUNT(DISTINCT al.id) AS alarmes_actives,
                   COUNT(DISTINCT af.id) AS pannes_actives
            FROM {db}.assets a
            LEFT JOIN {db}.alarms al
                ON a.id = al.asset_id AND al.ended_at IS NULL AND al.deleted_at IS NULL
            LEFT JOIN {db}.asset_faults af
                ON a.id = af.asset_id AND af.end_date IS NULL AND af.deleted_at IS NULL
            WHERE a.deleted_at IS NULL
            GROUP BY a.id, a.name, a.ref, a.status
            ORDER BY a.status DESC
            LIMIT 30;
        """

    # ─────────────────────────────────────────────────────────────────
    # BUILDERS — MEASUREMENTS
    # ─────────────────────────────────────────────────────────────────
    def _measure_list(self, intent, db: str) -> str:
        time_f = (
            self._build_time_filter("m.created_at", intent.modifiers)
            or "AND m.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        )
        return f"""
            SELECT a.id, a.name, a.ref, m.status, m.is_online, m.created_at
            FROM {db}.measurements m
            INNER JOIN {db}.assets a ON m.asset_id = a.id
            WHERE m.deleted_at IS NULL
              AND a.deleted_at IS NULL
              {time_f}
            ORDER BY m.created_at DESC
            LIMIT 30;
        """

    def _measure_top(self, intent, db: str) -> str:
        feat  = intent.entities.get("feature", "NGV")
        limit = self._extract_top_n(intent)
        return f"""
            SELECT a.id, a.name, a.ref,
                   fm.value            AS valeur,
                   fg.alarm            AS seuil,
                   (fm.value - fg.alarm) AS depassement,
                   fm.created_at
            FROM {db}.feature_measurement fm
            INNER JOIN {db}.assets a ON fm.asset_parent_id = a.id
            INNER JOIN {db}.feature_group fg
                ON fm.feature_id = fg.feature_id AND fm.group_id = fg.group_id
            WHERE fm.feature_id = (
                SELECT id FROM i_sense_v3_devenv_db.features
                WHERE name = '{feat}' AND deleted_at IS NULL LIMIT 1
            )
              AND fm.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
              AND fm.deleted_at IS NULL
              AND a.deleted_at IS NULL
            ORDER BY fm.value DESC
            LIMIT {limit};
        """

    def _feature_top(self, intent, db: str) -> str:
        return self._measure_top(intent, db)

    # ─────────────────────────────────────────────────────────────────
    # BUILDERS — RECOMMENDATIONS / INTERVENTIONS
    # ─────────────────────────────────────────────────────────────────
    def _reco_list(self, intent, db: str) -> str:
        return f"""
            SELECT ra.id, a.name, a.ref, ra.fault, ra.cause,
                   ra.notes, ra.status, ra.started_at, ra.ended_at
            FROM {db}.recommendation_assets ra
            INNER JOIN {db}.assets a ON ra.asset_id = a.id
            WHERE ra.deleted_at IS NULL
              AND a.deleted_at IS NULL
            ORDER BY ra.started_at DESC
            LIMIT 20;
        """

    def _intervention_list(self, intent, db: str) -> str:
        time_f = self._build_time_filter("i.created_at", intent.modifiers)
        return f"""
            SELECT i.id, a.name, a.ref, i.description, i.status,
                   i.date_intervention, i.created_at
            FROM {db}.interventions i
            INNER JOIN {db}.assets a ON i.asset_id = a.id
            WHERE i.deleted_at IS NULL
              AND a.deleted_at IS NULL
              {time_f}
            ORDER BY i.created_at DESC
            LIMIT 20;
        """

    # ─────────────────────────────────────────────────────────────────
    # BUILDER — DASHBOARD
    # ─────────────────────────────────────────────────────────────────
    def _dashboard(self, intent, db: str) -> str:
        """fix-E : alias sans espaces → compatibilité MySQL 5.7+."""
        return f"""
            SELECT
                (SELECT COUNT(*) FROM {db}.assets
                 WHERE deleted_at IS NULL)                          AS total_equipements,
                (SELECT COUNT(*) FROM {db}.assets
                 WHERE status = 5 AND deleted_at IS NULL)           AS critiques,
                (SELECT COUNT(*) FROM {db}.assets
                 WHERE status = 0 AND deleted_at IS NULL)           AS arretes,
                (SELECT COUNT(*) FROM {db}.alarms
                 WHERE ended_at IS NULL AND deleted_at IS NULL)     AS alarmes_actives,
                (SELECT COUNT(*) FROM {db}.alarms
                 WHERE ended_at IS NULL AND status = 5
                   AND deleted_at IS NULL)                          AS alarmes_critiques,
                (SELECT COUNT(*) FROM {db}.asset_faults
                 WHERE end_date IS NULL AND deleted_at IS NULL)     AS pannes_actives;
        """

    # ─────────────────────────────────────────────────────────────────
    # BUILDERS — USERS / COMPANIES
    # ─────────────────────────────────────────────────────────────────
    def _user_list(self, intent, db: str) -> str:
        return """
            SELECT u.id, u.first_name, u.last_name, u.email,
                   u.active, u.last_connection, c.name AS company
            FROM i_sense_v3_devenv_db.users u
            LEFT JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id
            LEFT JOIN i_sense_v3_devenv_db.companies c     ON uc.company_id = c.id
            WHERE u.deleted_at IS NULL
            ORDER BY u.last_connection DESC
            LIMIT 30;
        """

    def _company_list(self, intent, db: str) -> str:
        return """
            SELECT c.id, c.name, c.reference, c.alias,
                   COUNT(DISTINCT uc.user_id) AS nb_users
            FROM i_sense_v3_devenv_db.companies c
            LEFT JOIN i_sense_v3_devenv_db.user_company uc ON c.id = uc.company_id
            WHERE c.deleted_at IS NULL
            GROUP BY c.id, c.name, c.reference, c.alias
            ORDER BY c.name;
        """

    def get_stats(self) -> Dict:
        s = self.stats.copy()
        if s["total"] > 0:
            s["match_rate"] = f"{s['matched'] / s['total'] * 100:.1f}%"
        return s
