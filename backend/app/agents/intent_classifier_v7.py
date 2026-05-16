# backend/app/agents/intent_classifier_v7.py
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class Intent:
    name: str
    category: str
    action: str
    confidence: float
    entities: Dict = field(default_factory=dict)
    modifiers: List[str] = field(default_factory=list)
    raw_question: str = ""
    normalized: str = ""

class IntentClassifierV7:
    ACTIONS = {
        'LIST': [
            'liste', 'lister', 'affiche', 'afficher', 'montre', 'montrer',
            'donne', 'donner', 'voir', 'show', 'list', 'display',
            'quels sont', 'quelles sont', 'qui sont', 'lesquels',
            'présente', 'présenter', 'détaille',
        ],
        'COUNT': [
            'combien', 'nombre', 'compte', 'compter', 'total', 'quantité',
            'count', 'how many', 'how much', 'somme',
        ],
        'TOP': [
            'top', 'meilleur', 'meilleurs', 'meilleure', 'meilleures',
            'pire', 'pires', 'plus', 'maximum', 'minimum', 'classement',
            'ranking', 'highest', 'lowest', 'le plus', 'la plus',
            'les plus', 'élevée', 'élevé', 'élevées', 'élevés',
        ],
        'COMPARE': [
            'compare', 'comparer', 'comparaison', 'différence', 'versus',
            'vs', 'entre', 'compared to',
        ],
        'EXPLAIN': [
            "qu'est-ce", "c'est quoi", 'explique', 'expliquer', 'définition',
            'définir', 'comment', 'pourquoi', 'what is', 'why', 'how',
            'décris', 'décrire',
        ],
        'TREND': [
            'évolution', 'évolue', 'tendance', 'progression', 'historique',
            'trend', 'history', 'over time', 'au fil du temps',
            'mensuel', 'mensuelle', 'hebdomadaire',
        ],
        'STATUS': [
            'statut', 'état', 'situation', 'health', 'état actuel',
            'status', 'condition', 'résumé', 'dashboard', 'bilan',
        ],
        'PREDICT': [
            'prédiction', 'prédire', 'prévision', 'risque', 'va tomber',
            'prevoir', 'predict', 'forecast', 'va casser',
        ],
        'FIND': [
            'trouve', 'trouver', 'cherche', 'chercher', 'recherche',
            'find', 'search', 'localise',
        ],
    }

    OBJECTS = {
        'asset': [
            'équipement', 'équipements', 'machine', 'machines', 'asset', 'assets',
            'matériel', 'appareil', 'appareils', 'pompe', 'pompes', 'moteur', 'moteurs',
            'compresseur', 'compresseurs', 'ventilateur', 'ventilateurs', 'broyeur',
            'broyeurs', 'turbine', 'turbines',
        ],
        'fault': [
            'panne', 'pannes', 'défaut', 'défauts', 'fault', 'faults',
            'problème', 'problèmes', 'dysfonctionnement', 'erreur', 'erreurs',
            'avarie', 'avaries', 'incident', 'incidents', 'anomalie', 'anomalies',
        ],
        'alarm': [
            'alarme', 'alarmes', 'alerte', 'alertes', 'alarm', 'alarms',
            'warning', 'warnings', 'avertissement', 'avertissements',
            'notification', 'notifications',
        ],
        'measurement': [
            'mesure', 'mesures', 'measurement', 'measurements',
            'capteur', 'capteurs', 'sensor', 'sensors', 'données', 'data',
            'valeur', 'valeurs', 'lecture', 'lectures', 'relevé', 'relevés',
        ],
        'recommendation': [
            'recommandation', 'recommandations', 'recommendation', 'recommendations',
            'conseil', 'conseils', 'suggestion', 'suggestions',
            'préconisation', 'préconisations',
        ],
        'intervention': [
            'intervention', 'interventions', 'maintenance', 'maintenances',
            'réparation', 'réparations', 'opération', 'opérations',
            'travaux', 'service',
        ],
        'user': [
            'utilisateur', 'utilisateurs', 'user', 'users', 'personne',
            'personnes', 'opérateur', 'opérateurs', 'technicien',
            'techniciens', 'expert', 'experts', 'compte', 'comptes',
        ],
        'company': [
            'entreprise', 'entreprises', 'company', 'companies',
            'société', 'sociétés', 'client', 'clients', 'tenant',
            'site', 'sites', 'établissement',
        ],
        'prediction': [
            'prédiction', 'prédictions', 'prediction', 'predictions',
            'prévision', 'prévisions', 'forecast',
        ],
        'feature': [
            'feature', 'features', 'caractéristique', 'caractéristiques',
        ],
        'device': [
            'device', 'devices', 'vibox', 'capteur connecté',
        ],
    }

    MODIFIERS = {
        'active': [
            'actif', 'active', 'actifs', 'actives', 'en cours', 'ongoing',
            'current', 'présent', 'maintenant', 'now', 'pas résolu',
            'non résolu', 'non résolus', 'pending',
        ],
        'resolved': [
            'résolu', 'résolus', 'résolue', 'résolues', 'terminé', 'terminée',
            'fini', 'finis', 'closed', 'solved', 'fixed', 'corrigé',
        ],
        'critical': [
            'critique', 'critiques', 'critical', 'urgent', 'urgents',
            'sévère', 'sévères', 'grave', 'graves', 'severe',
        ],
        'today': [
            "aujourd'hui", 'today', 'ce jour', 'du jour',
        ],
        'yesterday': [
            'hier', 'yesterday',
        ],
        'this_week': [
            'cette semaine', 'this week', 'semaine en cours',
        ],
        'last_week': [
            'semaine dernière', 'last week', 'semaine passée',
        ],
        'this_month': [
            'ce mois', 'mois en cours', 'this month',
        ],
        'last_30_days': [
            '30 jours', '30 derniers jours', 'last 30 days',
            'mois dernier', 'last month',
        ],
        'recent': [
            'récent', 'récente', 'récents', 'récentes', 'recent',
            'dernier', 'dernière', 'last', 'latest',
        ],
        'all': [
            'tous', 'toutes', 'all', 'everything', 'tout',
        ],
        'stopped': [
            'arrêté', 'arrêtés', 'arrêtée', 'arrêtées', 'stoppé',
            'stopped', 'shut down', 'shutdown', 'off', 'à l\'arrêt',
            'éteint', 'éteints', 'inactif', 'inactifs',
        ],
        'normal': [
            'normal', 'normaux', 'normale', 'normales', 'sain', 'saine',
            'healthy', 'ok', 'bon', 'bonne',
        ],
        'with_alarms': [
            'avec alarme', 'avec alarmes', 'en alarme',
        ],
        'without_alarms': [
            'sans alarme', 'sans alarmes', 'pas d\'alarme',
        ],
    }

    FAULT_TYPES = {
        'bearing': [
            'roulement', 'bearing', 'inner race', 'outer race',
            'bague intérieure', 'bague extérieure', 'rolling element',
        ],
        'lubrication': [
            'lubrification', 'lubrifiant', 'lubrication', 'huile', 'oil', 'graissage',
        ],
        'misalignment': [
            'alignement', 'désalignement', 'misalignment', 'aligned', 'mal aligné',
        ],
        'imbalance': ['balourd', 'déséquilibre', 'imbalance', 'unbalance'],
        'cavitation': ['cavitation'],
        'belt': ['courroie', 'courroies', 'belt', 'belts'],
        'gear': ['engrenage', 'engrenages', 'gear', 'gears'],
        'electrical': [
            'électrique', 'electrical', 'ac electrical', 'dc electrical',
        ],
        'sensor_fault': [
            'capteur défectueux', 'sensor saturation', 'fault sensor', 'sonde défectueuse',
        ],
        'looseness': ['desserrage', 'looseness', 'jeu', 'mechanical looseness'],
        'friction': ['friction', 'frottement'],
        'outlier': ['outlier', 'outliers', 'aberrant', 'aberrants'],
        'shutdown': ['shutdown', 'arrêt'],
        'structural': ['structural', 'structurel'],
        'oil_turbulence': ['turbulence d\'huile', 'oil turbulence'],
        'ski_slope': ['ski slope', 'pente de ski'],
        'normal': ['normal'],
        'bearing_wear_rolling_element': [
            'bearing wear - rolling element', 'usure roulement élément roulant',
        ],
        'bearing_wear_inner_race': [
            'bearing wear - inner race', 'usure roulement bague intérieure',
        ],
        'bearing_wear_outer_race': [
            'bearing wear - outer race', 'usure roulement bague extérieure',
        ],
        'aerial_fault': ['aerial fault', 'défaut aéraulique'],
        'cavitation_fault': ['cavitation fault'],
        'ac_electrical_fault': ['ac electrical fault'],
        'dc_electrical_fault': ['dc electrical fault'],
        'gear_fault': ['gear fault'],
        'belt_fault': ['belt fault'],
        'sensor_saturation': ['sensor saturation'],
        'fault_sensor': ['fault sensor'],
    }

    FEATURES = {
        'NGV': ['ngv', 'niveau global vibration', 'vibration globale'],
        'NGA': ['nga', 'niveau global accélération'],
        'NGD': ['ngd', 'niveau global déplacement'],
        'temperature': ['température', 'temp', 'temperature', 'chaleur'],
        'rpm': ['rpm', 'tours minute', 'vitesse rotation'],
        'humidity': ['humidité', 'humidity'],
        'speed': ['speed', 'vitesse'],
        'level': ['level', 'niveau'],
        'pressure': ['pressure', 'pression'],
        'current': ['current', 'courant'],
        'CO2': ['co2', 'dioxyde'],
        'PM10': ['pm10'],
        'PM2_5': ['pm2_5', 'pm2.5'],
        'TVOC': ['tvoc'],
        'FC': ['fc'],
        'Energy': ['energy', 'énergie'],
        'Power': ['power', 'puissance'],
        'Voltage': ['voltage', 'tension'],
        'Temperature_Air': ['température air', 'temperature air'],
        'Humidity_Relative': ['humidité relative', 'humidity relative'],
        'Pressure_Atmo': ['pression atmo', 'pressure atmo'],
        'Temperature_Sol': ['température sol', 'temperature sol'],
        'Humidity_Sol': ['humidité sol', 'humidity sol'],
        'Oil_temperature': ['oil temperature', 'température huile'],
        'Oil_H2O_saturation': ['oil h2o saturation'],
        'Oil_H2O_temperature': ['oil h2o temperature'],
        'Oil_conductivity': ['oil conductivity', 'conductivité huile'],
        'TDN': ['tdn'],
        'DC': ['dc'],
        'GAP': ['gap'],
        'HF_concentration': ['hf concentration', 'concentration hf'],
        'Density': ['density', 'densité'],
        'D_viscosity': ['d viscosité', 'd_viscosity'],
        'K_viscosity': ['k viscosité', 'k_viscosity'],
        'Vis_40': ['vis 40'],
        'Oil_H2O_ppm': ['oil h2o ppm'],
        'VCC_g': ['vcc_g', 'vcc g'],
        'VCC_v': ['vcc_v', 'vcc v'],
        'VCC_d': ['vcc_d', 'vcc d'],
        'VCC97_d': ['vcc97_d', 'vcc97 d'],
        'NGENV': ['ngenv'],
        'A1F0': ['a1f0'],
        'A2F0': ['a2f0'],
        'A3F0': ['a3f0'],
        'FDS': ['fds'],
        'FDSENV': ['fdsenv'],
        'K': [' k '],
        'VC_g': ['vc_g', 'vc g'],
        'ISO_4': ['iso 4'],
        'ISO_6': ['iso 6'],
        'ISO_14': ['iso 14'],
    }

    TENANTS = {
        'safi': ['safi', 'site safi', 'ocp safi'],
        'jln': ['jln', 'khouribga'],
        'jfc4': ['jfc4', 'jorf lasfar', 'jorf'],
        'ntn': ['ntn'],
        'cmcp': ['cmcp', 'casablanca chimie', 'cmcp ip'],
        'cobomi': ['cobomi'],
        'nomac': ['nomac'],
        'onee': ['onee'],
        'bouskoura': ['bouskoura', 'lafarge', 'lafarge holcim'],
    }

    CATEGORY_MAP = {
        "equipements": "asset",
        "equipment": "asset",
        "alarmes": "alarm",
        "mesures": "measurement",
        "utilisateurs": "user",
        "entreprises": "company",
        "defauts": "fault",
        "défauts": "fault",
        "faults": "fault",
        "predictions": "prediction",
        "recommandations": "recommendation",
        "maintenance": "intervention",
    }

    def __init__(self):
        self._compile_patterns()
        self.SMALL_TALK_RGX = re.compile(
            r"\b(bonjour|salut|hello|hey|coucou|merci|au revoir|bonne journée|bonsoir|comment (ça va|vas-?tu))\b",
            re.IGNORECASE
        )

    def _compile_patterns(self):
        self._action_patterns = {
            k: re.compile(r'\b(' + '|'.join(map(re.escape, v)) + r')\b', re.IGNORECASE)
            for k, v in self.ACTIONS.items()
        }
        self._object_patterns = {
            k: re.compile(r'\b(' + '|'.join(map(re.escape, v)) + r')\b', re.IGNORECASE)
            for k, v in self.OBJECTS.items()
        }
        self._modifier_patterns = {
            k: re.compile(r'\b(' + '|'.join(map(re.escape, v)) + r')\b', re.IGNORECASE)
            for k, v in self.MODIFIERS.items()
        }

    def normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = unicodedata.normalize('NFC', text)
        text = re.sub(r"[^\w\s'àâäéèêëîïôöùûüÿæœç-]", ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def classify(self, question: str) -> Intent:
        normalized = self.normalize(question)

        if self.SMALL_TALK_RGX.search(normalized):
            return Intent('chat_smalltalk', 'chat', 'GREETING', 1.0,
                          raw_question=question, normalized=normalized)

        action, action_score = self._detect_best(normalized, self._action_patterns)
        obj, obj_score = self._detect_best(normalized, self._object_patterns)
        modifiers = [m for m, p in self._modifier_patterns.items() if p.search(normalized)]

        entities = {
            'fault_type': self._detect_in_dict(normalized, self.FAULT_TYPES),
            'feature': self._detect_in_dict(normalized, self.FEATURES),
            'tenant': self._detect_in_dict(normalized, self.TENANTS),
        }
        entities = {k: v for k, v in entities.items() if v}

        # Priorité métier
        if entities.get('fault_type'):
            obj = 'fault'
            if not action: action = 'LIST'
        elif entities.get('feature') and not entities.get('fault_type'):
            obj = 'measurement'
        elif any(w in normalized for w in ('notification','notifiable','email','sms')):
            obj = 'user'
        elif any(w in normalized for w in ('alarme','alerte','alarm','warning')):
            obj = 'alarm'
        elif any(w in normalized for w in ('intervention','maintenance','réparation')):
            obj = 'intervention'
        elif any(w in normalized for w in ('recommandation','préconisation','conseil')):
            obj = 'recommendation'
        elif any(w in normalized for w in ('entreprise','société','client','tenant','abonnement')):
            obj = 'company'
        elif any(w in normalized for w in ('prédiction','prediction','prévision')):
            obj = 'prediction'
        elif any(w in normalized for w in ('feature','caractéristique')):
            obj = 'feature'
        elif any(w in normalized for w in ('device','vibox')):
            obj = 'device'
        elif not obj:
            obj = 'asset'

        intent_name = f"{action.lower()}_{obj}" if action else f"list_{obj}"
        confidence = (action_score + obj_score) / 2
        if entities: confidence = min(1.0, confidence + 0.1)
        if modifiers: confidence = min(1.0, confidence + 0.05)

        return Intent(
            name=intent_name,
            category=obj,
            action=action or 'LIST',
            confidence=round(confidence, 2),
            entities=entities,
            modifiers=modifiers,
            raw_question=question,
            normalized=normalized,
        )

    def extract_key_elements(self, question: str) -> Dict:
        intent = self.classify(question)
        tables = []
        cat = intent.category
        if cat == 'fault': tables = ['assets','asset_faults','faults']
        elif cat == 'alarm': tables = ['assets','alarms']
        elif cat == 'measurement': tables = ['assets','measurements','feature_measurement','feature_group']
        elif cat == 'asset': tables = ['assets']
        elif cat == 'intervention': tables = ['assets','interventions']
        elif cat == 'recommendation': tables = ['recommendations_v3','recommendation_assets']
        elif cat == 'user': tables = []
        elif cat == 'company': tables = []
        elif cat == 'prediction': tables = ['predictions','assets']
        elif cat == 'feature': tables = ['feature_measurement','feature_group','features']
        elif cat == 'device': tables = ['vibox_diagnosis','devices']
        return {
            'action': intent.action,
            'category': intent.category,
            'entities': intent.entities,
            'modifiers': intent.modifiers,
            'main_tables': tables,
            'confidence': intent.confidence
        }

    def _detect_best(self, text, patterns) -> Tuple[Optional[str], float]:
        best, best_len = None, 0
        for k, p in patterns.items():
            m = p.search(text)
            if m:
                l = len(m.group(0))
                if l > best_len:
                    best_len = l
                    best = k
        return best, (best_len / 10) if best else 0

    def _detect_in_dict(self, text, mapping) -> Optional[str]:
        for key, syns in mapping.items():
            for s in syns:
                if re.search(r'\b' + re.escape(s) + r'\b', text):
                    return key
        return None