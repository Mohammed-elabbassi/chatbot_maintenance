from typing import List, Dict, Any, Optional
from datetime import datetime


class ResponseFormatterV6:

    STATUS_LABELS = {
        -1: 'Unassigned', 0: 'Shut down', 1: 'Normal',
        2: 'MID', 3: 'Moderate', 5: 'Critical',
    }

    ALARM_STATUS_LABELS = {
        1: 'Normal', 2: 'MID', 3: 'Moderate', 5: 'Critical',
    }

    def __init__(self, mode='markdown', max_rows=15, max_col_width=50):
        self.mode = mode
        self.max_rows = max_rows
        self.max_col_width = max_col_width

    # ═══════════════════════════════════════════════════════════
    # POINT D'ENTRÉE PRINCIPAL
    # ═══════════════════════════════════════════════════════════

    def format(self, question: str, rows: List[Dict],
               columns: List[str], tenant: str,
               intent=None) -> str:
        n = len(rows) if rows else 0

        if n == 0:
            return self._format_empty(tenant, intent)

        q = question.lower()

        # COUNT → résumé chiffres uniquement (pas de tableau)
        if intent and intent.action == 'COUNT':
            return self._format_count(rows, columns, tenant)
        if any(k in q for k in ['combien', 'nombre', 'total', 'count']):
            return self._format_count(rows, columns, tenant)

        # DASHBOARD → résumé chiffres uniquement (pas de tableau)
        if intent and (intent.action == 'STATUS' or
                       'résumé' in q or 'situation' in q or 'dashboard' in q):
            return self._format_dashboard(rows, columns, tenant)

        # Tous les autres cas → juste le titre, le tableau est géré par le frontend
        return f"Il y a **{n}** résultat(s) — **{tenant.upper()}** :"

    # ═══════════════════════════════════════════════════════════
    # FORMATTERS SPÉCIALISÉS
    # ═══════════════════════════════════════════════════════════

    def _format_empty(self, tenant: str, intent=None) -> str:
        return (
            f"Aucun résultat trouvé pour **{tenant.upper()}**.\n\n"
            "Essayez d'élargir la période ou vérifiez le tenant sélectionné."
        )

    def _format_count(self, rows: List[Dict], columns: List[str],
                      tenant: str) -> str:
        """
        FORMAT COUNT : affiche uniquement les chiffres clés en texte.
        Pas de tableau markdown — le frontend n'affiche pas de tableau pour COUNT.
        """
        if not rows:
            return f"**{tenant.upper()}** : 0 résultat."

        row = rows[0] if isinstance(rows[0], dict) else dict(zip(columns, rows[0]))

        # Valeur unique
        if len(columns) == 1:
            val = list(row.values())[0]
            label = self._beautify_label(columns[0])
            return f"**{tenant.upper()}** — {label} : **{self._fmt(val)}**"

        # Plusieurs valeurs → liste markdown propre
        lines = [f"**Résumé — {tenant.upper()}**\n"]
        for col in columns:
            val   = self._fmt(row.get(col))
            label = self._beautify_label(col)
            emoji = self._emoji_for(col)
            lines.append(f"- {emoji} **{label}** : {val}")
        return "\n".join(lines)

    def _format_dashboard(self, rows: List[Dict], columns: List[str],
                          tenant: str) -> str:
        """
        FORMAT DASHBOARD : liste markdown propre, pas de tableau.
        """
        if not rows:
            return self._format_empty(tenant)

        row = rows[0] if isinstance(rows[0], dict) else dict(zip(columns, rows[0]))

        lines = [f"**Résumé — {tenant.upper()}**\n"]
        for col in columns:
            val   = self._fmt(row.get(col))
            label = self._beautify_label(col)
            emoji = self._emoji_for(col)
            lines.append(f"- {emoji} **{label}** : {val}")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════
    # HELPERS DE FORMATAGE
    # ═══════════════════════════════════════════════════════════

    def _fmt(self, v, enrich_col: str = None) -> str:
        if v is None or v == '':
            return "—"
        if isinstance(v, bool):
            return "Oui" if v else "Non"
        if isinstance(v, float):
            if v != v or v == float('inf') or v == float('-inf'):
                return "—"
            return f"{v:.2f}"
        if isinstance(v, int):
            if enrich_col:
                ec = enrich_col.lower()
                if 'status' in ec and v in self.STATUS_LABELS:
                    return self.STATUS_LABELS[v]
            if abs(v) >= 1000:
                return f"{v:,}".replace(',', ' ')
            return str(v)
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M")
        s = str(v).strip()
        if not s:
            return "—"
        if self.mode == 'markdown':
            s = s.replace('|', '\\|')
        s = s.replace('\n', ' ').replace('\r', '')
        if len(s) > self.max_col_width:
            return s[:self.max_col_width - 1] + "…"
        return s

    def _beautify_label(self, col: str) -> str:
        special = {
            'id': 'ID', 'ref': 'Réf.', 'name': 'Nom',
            'fault_type': 'Type Défaut', 'start_date': 'Début',
            'end_date': 'Fin', 'created_at': 'Créé',
            'heures': 'Heures', 'heures_actives': 'Heures Actives',
            'nb_alarmes': 'Nb Alarmes', 'nb_defauts': 'Nb Défauts',
            'total_equipements': 'Total Équipements',
            'alarmes_actives': 'Alarmes Actives',
            'pannes_actives': 'Pannes Actives',
            'alarmes_critiques': 'Alarmes Critiques',
            'status_label': 'Statut', 'total': 'Total',
            'actives': 'Actives', 'resolues': 'Résolues',
            'critiques': 'Critiques', 'normaux': 'Normaux',
            'arretes': 'Arrêtés', 'moderes': 'Modérés',
        }
        if col.lower() in special:
            return special[col.lower()]
        return col.replace('_', ' ').title()

    def _emoji_for(self, col: str) -> str:
        c = col.lower()
        if 'critique' in c or 'critical' in c:   return '🔴'
        if 'panne' in c or 'fault' in c:          return '⚠️'
        if 'alarm' in c:                           return '🔔'
        if 'arrete' in c or 'stopped' in c:       return '⚫'
        if 'normal' in c:                          return '🟢'
        if 'total' in c or 'nb' in c:             return '🔢'
        if 'date' in c or 'heure' in c:           return '⏱️'
        if 'modere' in c or 'mid' in c:           return '🟠'
        return '📊'