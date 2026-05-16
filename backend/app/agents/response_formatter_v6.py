# # ══════════════════════════════════════════════════════════════
# # response_formatter_v6.py — V6.0
# # Formatage de réponses fluides (fix affichage tronqué)
# # ══════════════════════════════════════════════════════════════

# from typing import List, Dict, Any, Optional
# from datetime import datetime


# class ResponseFormatterV6:
#     """
#     Formatage intelligent des réponses :
#     - Markdown pour UI web
#     - Texte pur pour console
#     - Gestion robuste NULL/NaN/vide
#     - Fix affichage tronqué (pas de limite à 40 chars)
#     """

#     STATUS_LABELS = {
#         -1: '🔘 Unassigned', 0: '⚫ Shut down', 1: '🟢 Normal',
#         2: '🟡 MID', 3: '🟠 Moderate', 5: '🔴 Critical',
#     }

#     ALARM_STATUS_LABELS = {
#         1: '🟢 Normal', 2: '🟡 MID', 3: '🟠 Moderate', 5: '🔴 Critical',
#     }

#     def __init__(self, mode='markdown', max_rows=15, max_col_width=50):
#         """
#         mode : 'markdown' (UI) ou 'console' (terminal)
#         max_rows : nb max de lignes à afficher
#         max_col_width : largeur max d'une cellule (60 chars par défaut)
#         """
#         self.mode = mode
#         self.max_rows = max_rows
#         self.max_col_width = max_col_width

#     # ═══════════════════════════════════════════════════════════
#     # POINT D'ENTRÉE PRINCIPAL
#     # ═══════════════════════════════════════════════════════════

#     def format(self, question: str, rows: List[Dict],
#                columns: List[str], tenant: str,
#                intent=None) -> str:
#         """Formatage adaptatif selon le type de question"""
#         n = len(rows) if rows else 0

#         if n == 0:
#             return self._format_empty(tenant, intent)

#         q = question.lower()

#         # Détecter le format optimal
#         if intent and intent.action == 'COUNT':
#             return self._format_count(rows, columns, tenant)

#         if intent and (intent.action == 'STATUS' or
#                        'résumé' in q or 'situation' in q or 'dashboard' in q):
#             return self._format_dashboard(rows, columns, tenant)

#         if any(k in q for k in ['combien', 'nombre', 'total', 'count']):
#             return self._format_count(rows, columns, tenant)

#         if (n == 1 and len(columns) >= 3 and
#                 any(k in q for k in ['résumé', 'situation', 'dashboard', 'état'])):
#             return self._format_dashboard(rows, columns, tenant)

#         # Format tableau standard
#         if self.mode == 'console':
#             return self._format_table_console(rows, columns, n, tenant)
#         else:
#             return self._format_table_markdown(rows, columns, n, tenant)

#     # ═══════════════════════════════════════════════════════════
#     # FORMATTERS SPÉCIALISÉS
#     # ═══════════════════════════════════════════════════════════

#     def _format_empty(self, tenant: str, intent=None) -> str:
#         suggestions = [
#             "💡 Essayez d'élargir la période (ex: '30 derniers jours')",
#             "💡 Vérifiez le tenant (ex: 'à JLN', 'à Safi')",
#             "💡 Reformulez (ex: 'liste' au lieu de 'montre')",
#         ]
#         msg = f"📭 Aucun résultat pour **{tenant.upper()}**.\n\n"
#         msg += "\n".join(suggestions[:2])
#         return msg

#     def _format_count(self, rows: List[Dict], columns: List[str],
#                       tenant: str) -> str:
#         """Format COUNT avec une seule ligne de résultats"""
#         if not rows:
#             return f" **{tenant.upper()}** : **0**"

#         row = rows[0] if isinstance(rows[0], dict) else dict(zip(columns, rows[0]))

#         # Single value
#         if len(columns) == 1:
#             val = list(row.values())[0]
#             return f" **{tenant.upper()}** : **{self._fmt(val)}**"

#         # Multiple values (total/actives/resolues...)
#         parts = [f" **{tenant.upper()}** :\n"]
#         for col in columns:
#             val = self._fmt(row.get(col))
#             label = self._beautify_label(col)
#             emoji = self._emoji_for(col)
#             parts.append(f"  {emoji} {label}: **{val}**")
#         return "\n".join(parts)

#     def _format_dashboard(self, rows: List[Dict], columns: List[str],
#                           tenant: str) -> str:
#         """Format dashboard / résumé"""
#         if not rows:
#             return self._format_empty(tenant)

#         row = rows[0] if isinstance(rows[0], dict) else dict(zip(columns, rows[0]))
#         parts = [f" **Résumé {tenant.upper()}** :\n"]

#         for col in columns:
#             val = self._fmt(row.get(col))
#             label = self._beautify_label(col)
#             emoji = self._emoji_for(col)
#             parts.append(f"  {emoji} {label}: **{val}**")

#         return "\n".join(parts)

#     def _format_table_markdown(self, rows: List[Dict], columns: List[str],
#                                 n: int, tenant: str) -> str:
#         """Tableau Markdown propre"""
#         parts = [f" **{n} résultat(s)** — **{tenant.upper()}** :\n"]

#         # Header
#         col_names = [self._beautify_label(c) for c in columns]
#         parts.append("| " + " | ".join(col_names) + " |")
#         parts.append("|" + "|".join(["---"] * len(columns)) + "|")

#         # Rows
#         for row in rows[:self.max_rows]:
#             if isinstance(row, dict):
#                 vals = [self._fmt(row.get(c), enrich_col=c) for c in columns]
#             else:
#                 vals = [self._fmt(v) for v in row]
#             parts.append("| " + " | ".join(vals) + " |")

#         if n > self.max_rows:
#             parts.append(f"\n_... et **{n - self.max_rows}** autres résultats_")

#         return "\n".join(parts)

#     def _format_table_console(self, rows: List[Dict], columns: List[str],
#                                n: int, tenant: str) -> str:
#         """Tableau ASCII pour console"""
#         # Largeurs dynamiques
#         widths = {}
#         for c in columns:
#             max_w = len(self._beautify_label(c))
#             for row in rows[:self.max_rows]:
#                 val = row.get(c) if isinstance(row, dict) else None
#                 w = len(self._fmt(val, enrich_col=c))
#                 if w > max_w:
#                     max_w = w
#             widths[c] = min(max_w, 30)

#         sep = "+" + "+".join(["-" * (widths[c] + 2) for c in columns]) + "+"
#         header = "| " + " | ".join(
#             self._beautify_label(c).ljust(widths[c]) for c in columns
#         ) + " |"

#         lines = [
#             f"\n{n} résultat(s) — {tenant.upper()}\n",
#             sep, header, sep
#         ]

#         for row in rows[:self.max_rows]:
#             vals = []
#             for c in columns:
#                 v = row.get(c) if isinstance(row, dict) else ''
#                 formatted = self._fmt(v, enrich_col=c)
#                 vals.append(formatted.ljust(widths[c])[:widths[c]])
#             lines.append("| " + " | ".join(vals) + " |")

#         lines.append(sep)
#         if n > self.max_rows:
#             lines.append(f"\n... et {n - self.max_rows} autres résultats")

#         return "\n".join(lines)

#     # ═══════════════════════════════════════════════════════════
#     # HELPERS DE FORMATAGE
#     # ═══════════════════════════════════════════════════════════

#     def _fmt(self, v, enrich_col: str = None) -> str:
#         """
#         Formatage robuste d'une valeur.
#         max_col_width = 50 par défaut (pas 40 comme avant)
#         """
#         if v is None or v == '':
#             return "—"

#         # Bool
#         if isinstance(v, bool):
#             return "✓" if v else "✗"

#         # Float (avec NaN/Inf)
#         if isinstance(v, float):
#             if v != v or v == float('inf') or v == float('-inf'):
#                 return "—"
#             return f"{v:.2f}"

#         # Int (avec séparateurs de milliers)
#         if isinstance(v, int):
#             # Enrichissement statut
#             if enrich_col:
#                 ec = enrich_col.lower()
#                 if ec == 'status' or 'status' in ec:
#                     if v in self.STATUS_LABELS:
#                         return self.STATUS_LABELS[v]
#             if abs(v) >= 1000:
#                 return f"{v:,}".replace(',', ' ')
#             return str(v)

#         # Datetime
#         if isinstance(v, datetime):
#             return v.strftime("%Y-%m-%d %H:%M")

#         # String
#         s = str(v).strip()
#         if not s:
#             return "—"

#         # Échapper pipe Markdown (cassait l'affichage)
#         if self.mode == 'markdown':
#             s = s.replace('|', '\\|')
#         s = s.replace('\n', ' ').replace('\r', '')

#         # Tronquer
#         if len(s) > self.max_col_width:
#             return s[:self.max_col_width - 1] + "…"
#         return s

#     def _beautify_label(self, col: str) -> str:
#         """Embellit un nom de colonne"""
#         # Mappings spéciaux
#         special = {
#             'id': 'ID', 'ref': 'Réf.', 'name': 'Nom',
#             'fault_type': 'Type Défaut', 'start_date': 'Début',
#             'end_date': 'Fin', 'created_at': 'Créé',
#             'heures_actives': 'Heures', 'nb_alarmes': 'Nb Alarmes',
#             'nb_defauts': 'Nb Défauts', 'total_equipements': 'Total Équipements',
#             'alarmes_actives': 'Alarmes Actives', 'pannes_actives': 'Pannes Actives',
#             'status_label': 'Statut',
#         }
#         if col.lower() in special:
#             return special[col.lower()]

#         # Default : remplacer _ par espaces + Title case
#         return col.replace('_', ' ').title()

#     def _emoji_for(self, col: str) -> str:
#         """Choisit un emoji selon la colonne"""
#         c = col.lower()
#         if 'critique' in c or 'critical' in c:
#             return '🔴'
#         if 'panne' in c or 'fault' in c or 'défaut' in c:
#             return '⚠️'
#         if 'alarm' in c:
#             return '🔔'
#         if 'arrete' in c or 'arretes' in c or 'stopped' in c:
#             return '⚫'
#         if 'normal' in c:
#             return '🟢'
#         if 'total' in c or 'count' in c or 'nb' in c:
#             return ''
#         if 'time' in c or 'date' in c or 'heure' in c:
#             return '⏱️'
#         return '📈'


# # ═══════════════════════════════════════════════════════════════
# # TEST
# # ═══════════════════════════════════════════════════════════════

# if __name__ == "__main__":
#     print("\n" + "=" * 80)
#     print(" " * 22 + "🎨 RESPONSE FORMATTER V6 - TEST")
#     print("=" * 80 + "\n")

#     formatter = ResponseFormatterV6(mode='markdown')

#     # Test 1 : Count
#     rows1 = [{'total': 1234, 'actives': 30, 'resolues': 1204, 'critiques': 6}]
#     print("--- TEST 1 : COUNT ---")
#     print(formatter.format(
#         "Combien d'alarmes ?", rows1,
#         ['total', 'actives', 'resolues', 'critiques'], 'safi'
#     ))

#     # Test 2 : Tableau normal
#     rows2 = [
#         {'id': 54, 'name': 'Pompe de circulation principale du circuit primaire',
#          'ref': 'P-001', 'status': 5, 'start_date': datetime(2024, 1, 15)},
#         {'id': 78, 'name': 'Moteur ventilateur', 'ref': 'M-042',
#          'status': 1, 'start_date': None},
#     ]
#     print("\n\n--- TEST 2 : TABLEAU ---")
#     print(formatter.format(
#         "Liste équipements", rows2,
#         ['id', 'name', 'ref', 'status', 'start_date'], 'jln'
#     ))

#     # Test 3 : Vide
#     print("\n\n--- TEST 3 : VIDE ---")
#     print(formatter.format("Test", [], [], 'ntn'))

#     print("\n" + "=" * 80 + "\n")


# ══════════════════════════════════════════════════════════════
# response_formatter_v6.py — V6.0
# Formatage de réponses fluides (fix affichage tronqué)
# ══════════════════════════════════════════════════════════════

from typing import List, Dict, Any, Optional
from datetime import datetime


class ResponseFormatterV6:
    """
    Formatage intelligent des réponses :
    - Markdown pour UI web
    - Texte pur pour console
    - Gestion robuste NULL/NaN/vide
    - Fix affichage tronqué (pas de limite à 40 chars)
    """

    STATUS_LABELS = {
        -1: ' Unassigned', 0: ' Shut down', 1: ' Normal',
        2: ' MID', 3: ' Moderate', 5: ' Critical',
    }

    ALARM_STATUS_LABELS = {
        1: ' Normal', 2: ' MID', 3: ' Moderate', 5: 'Critical',
    }

    def __init__(self, mode='markdown', max_rows=15, max_col_width=50):
        """
        mode : 'markdown' (UI) ou 'console' (terminal)
        max_rows : nb max de lignes à afficher
        max_col_width : largeur max d'une cellule (50 chars par défaut)
        """
        self.mode = mode
        self.max_rows = max_rows
        self.max_col_width = max_col_width

    # ═══════════════════════════════════════════════════════════
    # POINT D'ENTRÉE PRINCIPAL
    # ═══════════════════════════════════════════════════════════

    def format(self, question: str, rows: List[Dict],
               columns: List[str], tenant: str,
               intent=None) -> str:
        """Formatage adaptatif selon le type de question"""
        n = len(rows) if rows else 0

        if n == 0:
            return self._format_empty(tenant, intent)

        q = question.lower()

        # Détecter le format optimal
        if intent and intent.action == 'COUNT':
            return self._format_count(rows, columns, tenant)

        if intent and (intent.action == 'STATUS' or
                       'résumé' in q or 'situation' in q or 'dashboard' in q):
            return self._format_dashboard(rows, columns, tenant)

        if any(k in q for k in ['combien', 'nombre', 'total', 'count']):
            return self._format_count(rows, columns, tenant)

        if (n == 1 and len(columns) >= 3 and
                any(k in q for k in ['résumé', 'situation', 'dashboard', 'état'])):
            return self._format_dashboard(rows, columns, tenant)

        # Format tableau standard
        if self.mode == 'console':
            return self._format_table_console(rows, columns, n, tenant)
        else:
            return self._format_table_markdown(rows, columns, n, tenant)

    # ═══════════════════════════════════════════════════════════
    # FORMATTERS SPÉCIALISÉS
    # ═══════════════════════════════════════════════════════════

    def _format_empty(self, tenant: str, intent=None) -> str:
        suggestions = [
            " Essayez d'élargir la période (ex: '30 derniers jours')",
            " Vérifiez le tenant (ex: 'à JLN', 'à Safi')",
        ]
        lines = [
            f"\n  Aucun résultat pour {tenant.upper()}",
            "",
        ]
        lines += suggestions
        return "\n".join(lines)

    def _format_count(self, rows: List[Dict], columns: List[str],
                      tenant: str) -> str:
        """Format COUNT avec une seule ligne de résultats"""
        if not rows:
            return f"  {tenant.upper()} : 0"

        row = rows[0] if isinstance(rows[0], dict) else dict(zip(columns, rows[0]))

        # Single value
        if len(columns) == 1:
            val = list(row.values())[0]
            return f"  {tenant.upper()} : {self._fmt(val)}"

        # Multiple values
        label_w = max(len(self._beautify_label(c)) for c in columns)
        val_w   = max(len(self._fmt(row.get(c))) for c in columns)

        lines = [
            f"\n  Résumé — {tenant.upper()}\n",
            "─" * (label_w + val_w + 10),
        ]
        for col in columns:
            val   = self._fmt(row.get(col))
            label = self._beautify_label(col)
            emoji = self._emoji_for(col)
            lines.append(f"  {emoji}  {label:<{label_w}}  :  {val}")
        lines.append("─" * (label_w + val_w + 10))
        return "\n".join(lines)

    def _format_dashboard(self, rows: List[Dict], columns: List[str],
                          tenant: str) -> str:
        """Format dashboard / résumé"""
        if not rows:
            return self._format_empty(tenant)

        row = rows[0] if isinstance(rows[0], dict) else dict(zip(columns, rows[0]))

        label_w = max(len(self._beautify_label(c)) for c in columns)
        val_w   = max(len(self._fmt(row.get(c))) for c in columns)

        lines = [
            f"\n   Résumé — {tenant.upper()}\n",
            "─" * (label_w + val_w + 10),
        ]
        for col in columns:
            val   = self._fmt(row.get(col))
            label = self._beautify_label(col)
            emoji = self._emoji_for(col)
            lines.append(f"  {emoji}  {label:<{label_w}}  :  {val}")
        lines.append("─" * (label_w + val_w + 10))
        return "\n".join(lines)

    def _format_table_markdown(self, rows: List[Dict], columns: List[str],
                                n: int, tenant: str) -> str:
        """Table Markdown alignée — style image"""

        col_labels = {c: self._beautify_label(c) for c in columns}

        # ── Largeurs dynamiques ──────────────────────────────
        col_w = {}
        for c in columns:
            max_w = len(col_labels[c])
            for row in rows[:self.max_rows]:
                v = row.get(c) if isinstance(row, dict) else ''
                max_w = max(max_w, len(self._fmt(v, enrich_col=c)))
            col_w[c] = min(max_w, self.max_col_width)

        # ── Titre ────────────────────────────────────────────
        parts = [f"\nIl y a **{n}** résultat(s) — **{tenant.upper()}** :\n"]

        # ── En-tête ──────────────────────────────────────────
        header = "| " + " | ".join(
            col_labels[c].ljust(col_w[c]) for c in columns
        ) + " |"

        # ── Séparateur ───────────────────────────────────────
        separator = "| " + " | ".join(
            "-" * col_w[c] for c in columns
        ) + " |"

        parts += [header, separator]

        # ── Lignes données ───────────────────────────────────
        for row in rows[:self.max_rows]:
            if isinstance(row, dict):
                vals = [
                    self._fmt(row.get(c), enrich_col=c).ljust(col_w[c])
                    for c in columns
                ]
            else:
                vals = [
                    self._fmt(v).ljust(col_w[columns[i]])
                    for i, v in enumerate(row)
                ]
            parts.append("| " + " | ".join(vals) + " |")

        if n > self.max_rows:
            parts.append(f"\n_... et {n - self.max_rows} autres résultats_")

        return "\n".join(parts)

    def _format_table_console(self, rows: List[Dict], columns: List[str],
                               n: int, tenant: str) -> str:
        """Table ASCII — style image, bordures propres"""

        col_labels = {c: self._beautify_label(c) for c in columns}

        # ── Largeurs dynamiques ──────────────────────────────
        col_w = {}
        for c in columns:
            max_w = len(col_labels[c])
            for row in rows[:self.max_rows]:
                v = row.get(c) if isinstance(row, dict) else ''
                max_w = max(max_w, len(self._fmt(v, enrich_col=c)))
            col_w[c] = min(max_w, self.max_col_width)

        # ── Séparateurs ──────────────────────────────────────
        top_sep = "+" + "+".join("-" * (col_w[c] + 2) for c in columns) + "+"
        mid_sep = "+" + "+".join("-" * (col_w[c] + 2) for c in columns) + "+"
        bot_sep = "+" + "+".join("-" * (col_w[c] + 2) for c in columns) + "+"

        # ── En-tête colonnes ─────────────────────────────────
        header = "| " + " | ".join(
            col_labels[c].ljust(col_w[c]) for c in columns
        ) + " |"

        # ── Titre ────────────────────────────────────────────
        lines = [
            f"\nIl y a {n} résultat(s) — {tenant.upper()} :\n",
            top_sep,
            header,
            mid_sep,
        ]

        # ── Lignes données ───────────────────────────────────
        for row in rows[:self.max_rows]:
            cells = []
            for c in columns:
                v         = row.get(c) if isinstance(row, dict) else ''
                formatted = self._fmt(v, enrich_col=c)
                cells.append(formatted.ljust(col_w[c]))
            lines.append("| " + " | ".join(cells) + " |")

        lines.append(bot_sep)

        if n > self.max_rows:
            lines.append(
                f"\n  ... et {n - self.max_rows} autres résultats non affichés"
            )

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════
    # HELPERS DE FORMATAGE
    # ═══════════════════════════════════════════════════════════

    def _fmt(self, v, enrich_col: str = None) -> str:
        """
        Formatage robuste d'une valeur.
        max_col_width = 50 par défaut (pas 40 comme avant)
        """
        if v is None or v == '':
            return "—"

        # Bool
        if isinstance(v, bool):
            return "✓" if v else "✗"

        # Float (avec NaN/Inf)
        if isinstance(v, float):
            if v != v or v == float('inf') or v == float('-inf'):
                return "—"
            return f"{v:.2f}"

        # Int (avec séparateurs de milliers)
        if isinstance(v, int):
            # Enrichissement statut
            if enrich_col:
                ec = enrich_col.lower()
                if ec == 'status' or 'status' in ec:
                    if v in self.STATUS_LABELS:
                        return self.STATUS_LABELS[v]
            if abs(v) >= 1000:
                return f"{v:,}".replace(',', ' ')
            return str(v)

        # Datetime
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M")

        # String
        s = str(v).strip()
        if not s:
            return "—"

        # Échapper pipe Markdown (cassait l'affichage)
        if self.mode == 'markdown':
            s = s.replace('|', '\\|')
        s = s.replace('\n', ' ').replace('\r', '')

        # Tronquer
        if len(s) > self.max_col_width:
            return s[:self.max_col_width - 1] + "…"
        return s

    def _beautify_label(self, col: str) -> str:
        """Embellit un nom de colonne"""
        special = {
            'id': 'ID', 'ref': 'Réf.', 'name': 'Nom',
            'fault_type': 'Type Défaut', 'start_date': 'Début',
            'end_date': 'Fin', 'created_at': 'Créé',
            'heures_actives': 'Heures', 'nb_alarmes': 'Nb Alarmes',
            'nb_defauts': 'Nb Défauts', 'total_equipements': 'Total Équipements',
            'alarmes_actives': 'Alarmes Actives', 'pannes_actives': 'Pannes Actives',
            'status_label': 'Statut',
        }
        if col.lower() in special:
            return special[col.lower()]
        return col.replace('_', ' ').title()

    def _emoji_for(self, col: str) -> str:
        """Choisit un emoji selon la colonne"""
        c = col.lower()
        if 'critique' in c or 'critical' in c:
            return '🔴'
        if 'panne' in c or 'fault' in c or 'défaut' in c:
            return '⚠️'
        if 'alarm' in c:
            return '🔔'
        if 'arrete' in c or 'arretes' in c or 'stopped' in c:
            return '⚫'
        if 'normal' in c:
            return '🟢'
        if 'total' in c or 'count' in c or 'nb' in c:
            return '🔢'
        if 'time' in c or 'date' in c or 'heure' in c:
            return '⏱️'
        return '📈'


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" " * 22 + " RESPONSE FORMATTER V6 - TEST")
    print("=" * 80 + "\n")

    formatter = ResponseFormatterV6(mode='console')

    # ── Test 1 : Pannes actives (comme l'image) ──────────────
    rows0 = [
        {'id': 6, 'asset_id': 40, 'fault_id': 8,
         'start_date': '2025-02-07 10:23:33', 'end_date': None,
         'status': 5, 'percentage': 75.0},
        {'id': 7, 'asset_id': 40, 'fault_id': 4,
         'start_date': '2025-02-07 10:23:33', 'end_date': None,
         'status': 5, 'percentage': 75.0},
    ]
    print("--- TEST 0 : PANNES ACTIVES (image) ---")
    print(formatter.format(
        "Quelles sont les pannes actives à Safi ?", rows0,
        ['id', 'asset_id', 'fault_id', 'start_date', 'end_date',
         'status', 'percentage'],
        'safi'
    ))

    # ── Test 1 : Count ───────────────────────────────────────
    rows1 = [{'total': 1234, 'actives': 30, 'resolues': 1204, 'critiques': 6}]
    print("\n\n--- TEST 1 : COUNT ---")
    print(formatter.format(
        "Combien d'alarmes ?", rows1,
        ['total', 'actives', 'resolues', 'critiques'], 'safi'
    ))

    # ── Test 2 : Tableau normal ──────────────────────────────
    rows2 = [
        {'id': 54, 'name': 'Pompe de circulation principale du circuit primaire',
         'ref': 'P-001', 'status': 5, 'start_date': datetime(2024, 1, 15)},
        {'id': 78, 'name': 'Moteur ventilateur', 'ref': 'M-042',
         'status': 1, 'start_date': None},
    ]
    print("\n\n--- TEST 2 : TABLEAU ---")
    print(formatter.format(
        "Liste équipements", rows2,
        ['id', 'name', 'ref', 'status', 'start_date'], 'jln'
    ))

    # ── Test 3 : Vide ────────────────────────────────────────
    print("\n\n--- TEST 3 : VIDE ---")
    print(formatter.format("Test", [], [], 'ntn'))

    print("\n" + "=" * 80 + "\n")