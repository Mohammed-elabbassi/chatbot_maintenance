# # backend/app/agents/prompt_builder_v7.py
# from typing import List, Dict


# class PromptBuilderV7:
#     def build_sql_system_prompt(self) -> str:
#         return """Tu es un expert senior SQL MySQL spécialisé en maintenance prédictive industrielle pour i-sense / i-predict.

# Tu dois générer une unique requête SQL SELECT correcte, sûre et exécutable.

# Règles strictes :
# - Utilise uniquement les tables et colonnes fournies.
# - N'invente jamais de table, colonne ou jointure.
# - Génère uniquement une requête SELECT.
# - Interdiction absolue : INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE.
# - Utilise deleted_at IS NULL lorsque pertinent.
# - Si pannes actives: end_date IS NULL.
# - Si alarmes actives: ended_at IS NULL.
# - Jamais de SELECT *.
# - Si le contexte est insuffisant ou ambigu, réponds 'clarify' au lieu d'inventer.
# - Termine toujours la requête par ;
# - Réponds uniquement en JSON valide.

# Format de sortie obligatoire :
# {
#   "decision": "sql|refuse|clarify",
#   "reasoning": "résumé bref",
#   "tables": ["table1", "table2"],
#   "sql": "SELECT ...;"
# }"""

#     def build_sql_user_prompt(
#         self,
#         question: str,
#         tenant_db: str,
#         intent,
#         schema_context: str,
#         join_hints: str,
#         examples_context: str,
#         category_examples_context: str = "",
#         negative_examples_context: str = "",
#         rag_context: str = "",
#     ) -> str:
#         return f"""Question utilisateur:
# {question}

# Tenant cible:
# {tenant_db}

# Intent détecté:
# - name: {getattr(intent, 'name', 'unknown')}
# - action: {getattr(intent, 'action', 'unknown')}
# - category: {getattr(intent, 'category', 'unknown')}
# - entities: {getattr(intent, 'entities', {})}
# - modifiers: {getattr(intent, 'modifiers', [])}

# Schéma pertinent:
# {schema_context or "Aucun schéma compact disponible"}

# Hints de jointure:
# {join_hints or "Aucun hint déterministe"}

# Exemples proches:
# {examples_context or "Aucun exemple proche"}

# Exemples de même catégorie:
# {category_examples_context or "Aucun exemple de catégorie"}

# Exemples négatifs:
# {negative_examples_context or "Aucun"}

# Contexte RAG:
# {rag_context or "Aucun contexte RAG pertinent"}

# Instructions supplémentaires importantes:
# - Les exemples fournis ne sont pas forcément des paraphrases exactes de la question.
# - Utilise les exemples comme modèles transférables pour:
#   - choisir les bonnes tables,
#   - réutiliser les bonnes jointures,
#   - appliquer les bons filtres métier,
#   - reproduire les calculs SQL pertinents,
#   - adapter les conditions WHERE à la nouvelle question.
# - Si aucun exemple très proche n'existe, appuie-toi sur :
#   1. le schéma,
#   2. les hints de jointure,
#   3. les exemples de même catégorie,
#   4. le contexte RAG.
# - Si les informations sont ambiguës ou insuffisantes, retourne decision="clarify".
# - N'invente jamais une colonne absente du contexte.
# """

#     def build_repair_prompt(
#         self,
#         question: str,
#         failed_sql: str,
#         error_msg: str,
#         schema_context: str,
#         join_hints: str,
#         examples_context: str,
#     ) -> str:
#         return f"""La requête précédente a échoué.

# Question:
# {question}

# SQL précédent:
# {failed_sql}

# Erreur SQL:
# {error_msg}

# Schéma pertinent:
# {schema_context}

# Hints de jointure:
# {join_hints}

# Exemples similaires:
# {examples_context}

# Corrige la requête et retourne uniquement un JSON valide :
# {{
#   "decision": "sql|refuse|clarify",
#   "reasoning": "résumé bref",
#   "tables": ["table1", "table2"],
#   "sql": "SELECT ...;"
# }}"""

#     def build_rewrite_prompt(
#         self,
#         question: str,
#         tenant: str,
#         columns: List[str],
#         rows: List[Dict],
#     ) -> str:
#         return f"""Tu es un assistant analytique métier.
# Réponds en français clair, précis et professionnel.
# N'invente aucun chiffre.

# Question:
# {question}

# Tenant:
# {tenant}

# Colonnes:
# {columns}

# Résultats:
# {rows}

# Règles:
# - Si aucun résultat: indique qu'aucune donnée ne correspond.
# - Si une seule ligne: réponds directement.
# - Si plusieurs lignes: fais une synthèse concise puis mentionne les principaux éléments.
# """



# backend/app/agents/prompt_builder_v7.py
"""
CORRECTIONS V8.1 :
- Fix 3 : règle anti-tenant dans system prompt (WHERE tenant= interdit)
- Fix 4 : hint dynamique top assets vs top faults dans user prompt
- Fix 5 : règle OR avec parenthèses obligatoires
- Fix 6 : SQL sur une seule ligne obligatoire
"""
from typing import List, Dict


class PromptBuilderV7:

    def build_sql_system_prompt(self) -> str:
        return """Tu es un expert senior SQL MySQL spécialisé en maintenance prédictive industrielle pour i-sense / i-predict.

Tu dois générer une unique requête SQL SELECT correcte, sûre et exécutable.

Règles strictes :
- Utilise uniquement les tables et colonnes fournies dans le schéma.
- N'invente jamais de table, colonne ou jointure absente du schéma.
- ended_at appartient UNIQUEMENT à alarms et à  recommendation_assets.
- (start_date , end_date) appartient UNIQUEMENT à users et à  asset_faults.
- RÈGLE CRITIQUE — pannes actives : Si la question dit "actif / actuellement / en cours" → ajouter af.end_date IS NULL.
- RÈGLE CRITIQUE — alarme actives : Si la question dit "actif / actuellement / en cours" → ajouter al.ended_at IS NULL.
- Génère uniquement une requête SELECT.
- Interdiction absolue : INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE.
- Utilise deleted_at IS NULL lorsque pertinent.
- Si pannes actives : end_date IS NULL.
- Si alarmes actives : ended_at IS NULL.
- Jamais de SELECT *.
- Si le contexte est insuffisant ou ambigu, réponds decision="clarify".
- Termine toujours la requête par ;

RÈGLE : Pour les requêtes de type STATUS (recherche d'un équipement par nom/ref),
utiliser UNIQUEMENT la table assets. Ne pas joindre recommendation_assets, families 
ou asset_classes sauf si la question demande explicitement la famille ou la classe.

RÈGLE STATUS : Pour chercher un équipement par nom ou ref, utiliser UNIQUEMENT
FROM assets a WHERE (a.name = 'X' OR a.ref = 'X') AND a.deleted_at IS NULL.
Ne pas joindre recommendation_assets ni asset_classes sauf si explicitement demandé.

RÈGLE CRITIQUE — TENANT :
Le tenant (site client) est déjà défini par le préfixe de la base de données fourni dans le schéma.
Exemples de préfixes valides : v3_tenant_Site_Safi, v3_tenant_jln, v3_tenant_ntn, v3_tenant_nomac.
N'ajoute JAMAIS de filtre WHERE sur tenant, tenant_id, site, ou site_id.
Ces colonnes N'EXISTENT PAS dans les tables. Le préfixe de la base de données suffit.
EXEMPLES INTERDITS :
  WHERE a.tenant = 'safi'
  WHERE a.tenant_id = 'safi'
  WHERE a.site = 'jln'
  AND ac.locked = 1  (si locked absent du schéma)

RÈGLE CRITIQUE — TOP ASSETS vs TOP FAULTS :
- Question "top N ASSETS / équipements avec le plus de X" → GROUP BY a.id, a.name (grouper par équipement).
- Question "top N FAULTS / types de défauts les plus fréquents" → GROUP BY f.id, f.name (grouper par type de défaut).
- Ne jamais confondre les deux.

RÈGLE CRITIQUE — WHERE avec OR :
Quand tu utilises OR dans un WHERE, toujours entourer de parenthèses :
  CORRECT   : WHERE (a.name = 'X' OR a.ref = 'X') AND a.deleted_at IS NULL
  INTERDIT  : WHERE a.name = 'X' OR a.ref = 'X' AND a.deleted_at IS NULL

RÈGLE CRITIQUE — FORMAT JSON :
- Réponds UNIQUEMENT en JSON valide sur une seule ligne.
- Le champ "sql" doit tenir sur UNE SEULE LIGNE, sans retour à la ligne ni tabulation.
- Utilise des espaces à la place des sauts de ligne dans le SQL.
- Format obligatoire :
{"decision": "sql|refuse|clarify", "reasoning": "résumé bref", "tables": ["table1", "table2"], "sql": "SELECT ... FROM ... WHERE ...;"}"""

    def build_sql_user_prompt(
        self,
        question:                  str,
        tenant_db:                 str,
        intent,
        schema_context:            str,
        join_hints:                str,
        examples_context:          str,
        category_examples_context: str = "",
        negative_examples_context: str = "",
        rag_context:               str = "",
    ) -> str:

        # FIX 4 : détecter top assets → injecter hint grouping
        q_lower = question.lower()
        grouping_hint = ""
        mots_assets = ["asset", "équipement", "equipement", "appareil", "machine"]
        mots_top    = ["top", "plus de", "plus d'", "maximum", "max", "les plus"]
        if any(w in q_lower for w in mots_assets) and any(w in q_lower for w in mots_top):
            grouping_hint = (
                "\n⚠ GROUPING : La question porte sur les ÉQUIPEMENTS (assets). "
                "Utilise GROUP BY a.id, a.name — PAS GROUP BY f.id ou f.name."
            )

        # FIX 3 : rappel tenant dans chaque prompt
        tenant_hint = (
            f"\n⚠ TENANT : Le site est défini par le préfixe '{tenant_db}'. "
            "N'ajoute JAMAIS de filtre WHERE tenant= ou tenant_id= (colonne inexistante)."
        )

        return f"""Question utilisateur:
{question}

Tenant cible:
{tenant_db}{tenant_hint}{grouping_hint}

Intent détecté:
- name: {getattr(intent, 'name', 'unknown')}
- action: {getattr(intent, 'action', 'unknown')}
- category: {getattr(intent, 'category', 'unknown')}
- entities: {getattr(intent, 'entities', {})}
- modifiers: {getattr(intent, 'modifiers', [])}

Schéma pertinent:
{schema_context or "Aucun schéma compact disponible"}

Hints de jointure:
{join_hints or "Aucun hint déterministe"}

Exemples proches:
{examples_context or "Aucun exemple proche"}

Exemples de même catégorie:
{category_examples_context or "Aucun exemple de catégorie"}

Exemples négatifs:
{negative_examples_context or "Aucun"}

Contexte RAG:
{rag_context or "Aucun contexte RAG pertinent"}

Instructions supplémentaires importantes:
- Les exemples fournis sont des modèles transférables : adapte les JOINs, filtres et calculs à la nouvelle question.
- Si aucun exemple très proche n'existe, appuie-toi sur le schéma + hints + RAG.
- N'invente jamais une colonne absente du schéma fourni.
- Si les informations sont ambiguës ou insuffisantes : decision="clarify".
- Le champ "sql" du JSON doit être sur UNE SEULE LIGNE (pas de \\n dans le JSON).
"""

    def build_repair_prompt(
        self,
        question:         str,
        failed_sql:       str,
        error_msg:        str,
        schema_context:   str,
        join_hints:       str,
        examples_context: str,
    ) -> str:
        return f"""La requête précédente a échoué.

Question:
{question}

SQL précédent:
{failed_sql}

Erreur SQL:
{error_msg}

Schéma pertinent:
{schema_context}

Hints de jointure:
{join_hints}

Exemples similaires:
{examples_context}

Règles de correction :
- N'invente pas de colonne absente du schéma.
- N'ajoute PAS de filtre WHERE tenant= ou tenant_id= (colonne inexistante).
- WHERE avec OR → parenthèses obligatoires : (a.name='X' OR a.ref='X').
- SQL sur une seule ligne dans le champ "sql" du JSON.

Retourne uniquement un JSON valide sur une ligne :
{{"decision": "sql|refuse|clarify", "reasoning": "résumé bref", "tables": ["table1"], "sql": "SELECT ...;"}}"""

    def build_rewrite_prompt(
        self,
        question: str,
        tenant:   str,
        columns:  List[str],
        rows:     List[Dict],
    ) -> str:
        return f"""Tu es un assistant analytique métier.
Réponds en français clair, précis et professionnel.
N'invente aucun chiffre.

Question:
{question}

Tenant:
{tenant}

Colonnes:
{columns}

Résultats:
{rows}

Règles:
- Si aucun résultat: indique qu'aucune donnée ne correspond.
- Si une seule ligne: réponds directement.
- Si plusieurs lignes: fais une synthèse concise puis mentionne les principaux éléments.
"""