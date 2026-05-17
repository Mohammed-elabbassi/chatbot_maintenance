# # ══════════════════════════════════════════════════════════════
# # feedback_logger_v6.py — V6.0
# # Boucle d'apprentissage continu (SQLite)
# # ══════════════════════════════════════════════════════════════

# import sqlite3
# import json
# import threading
# from datetime import datetime, timedelta
# from pathlib import Path
# from typing import Dict, List, Optional


# class FeedbackLoggerV6:
#     """
#     Logger de feedback pour apprentissage continu :
#     - Sauvegarde TOUTES les questions traitées
#     - Marque succès/échec
#     - Permet de réindexer les questions réussies dans le RAG
#     - Statistiques globales pour analyse
#     - Détection de patterns récurrents
#     """

#     def __init__(self, db_path="./feedback_v6.db"):
#         self.db_path = db_path
#         self._lock = threading.Lock()
#         self._conn = None
#         self._init_db()

#         self.stats = {
#             'logged': 0,
#             'success_logged': 0,
#             'fail_logged': 0,
#             'reindexed': 0,
#         }

#     def _init_db(self):
#         """Initialise la base SQLite"""
#         try:
#             self._conn = sqlite3.connect(
#                 self.db_path, check_same_thread=False, timeout=10
#             )

#             # Table principale
#             self._conn.execute("""
#                 CREATE TABLE IF NOT EXISTS feedback (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     question TEXT NOT NULL,
#                     normalized TEXT,
#                     tenant TEXT,
#                     intent_name TEXT,
#                     intent_category TEXT,
#                     intent_action TEXT,
#                     intent_confidence REAL,
#                     method TEXT,
#                     sql_query TEXT,
#                     success INTEGER,
#                     row_count INTEGER,
#                     processing_time REAL,
#                     error_message TEXT,
#                     response_summary TEXT,
#                     user_rating INTEGER DEFAULT 0,
#                     indexed_in_rag INTEGER DEFAULT 0,
#                     created_at TEXT NOT NULL
#                 )
#             """)

#             # Index pour requêtes fréquentes
#             self._conn.execute(
#                 "CREATE INDEX IF NOT EXISTS idx_success ON feedback(success)"
#             )
#             self._conn.execute(
#                 "CREATE INDEX IF NOT EXISTS idx_method ON feedback(method)"
#             )
#             self._conn.execute(
#                 "CREATE INDEX IF NOT EXISTS idx_tenant ON feedback(tenant)"
#             )
#             self._conn.execute(
#                 "CREATE INDEX IF NOT EXISTS idx_normalized ON feedback(normalized)"
#             )
#             self._conn.execute(
#                 "CREATE INDEX IF NOT EXISTS idx_indexed ON feedback(indexed_in_rag)"
#             )

#             # Table des patterns récurrents (questions qui reviennent souvent)
#             self._conn.execute("""
#                 CREATE TABLE IF NOT EXISTS patterns (
#                     normalized TEXT PRIMARY KEY,
#                     count INTEGER DEFAULT 1,
#                     last_seen TEXT,
#                     success_rate REAL DEFAULT 0,
#                     avg_time REAL DEFAULT 0,
#                     best_sql TEXT
#                 )
#             """)

#             self._conn.commit()
#             print(f"   📝 Feedback Logger initialisé: {self.db_path}")
#         except Exception as e:
#             print(f"   ❌ Feedback Logger erreur: {e}")
#             self._conn = None

#     # ═══════════════════════════════════════════════════════════
#     # LOG (méthode principale)
#     # ═══════════════════════════════════════════════════════════

#     def log(self, question: str, result: Dict, intent=None,
#             normalized: str = None) -> Optional[int]:
#         """
#         Enregistre un feedback complet.
#         Retourne l'ID du feedback ou None en cas d'erreur.
#         """
#         if not self._conn:
#             return None

#         try:
#             with self._lock:
#                 cursor = self._conn.execute("""
#                     INSERT INTO feedback (
#                         question, normalized, tenant,
#                         intent_name, intent_category, intent_action, intent_confidence,
#                         method, sql_query, success, row_count,
#                         processing_time, error_message, response_summary,
#                         created_at
#                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                 """, (
#                     question,
#                     normalized or question.lower().strip(),
#                     result.get('tenant', 'unknown'),
#                     intent.name if intent else None,
#                     intent.category if intent else None,
#                     intent.action if intent else None,
#                     intent.confidence if intent else None,
#                     result.get('method', 'unknown'),
#                     result.get('sql', '')[:2000] if result.get('sql') else None,
#                     1 if result.get('success') else 0,
#                     result.get('row_count', 0),
#                     result.get('processing_time', 0),
#                     result.get('error', '')[:500] if result.get('error') else None,
#                     (result.get('natural_response', '') or '')[:300],
#                     datetime.now().isoformat(),
#                 ))
#                 feedback_id = cursor.lastrowid
#                 self._conn.commit()

#                 # Stats
#                 self.stats['logged'] += 1
#                 if result.get('success'):
#                     self.stats['success_logged'] += 1
#                 else:
#                     self.stats['fail_logged'] += 1

#                 # Mise à jour patterns
#                 self._update_pattern(
#                     normalized or question.lower().strip(),
#                     result.get('success', False),
#                     result.get('processing_time', 0),
#                     result.get('sql', '') if result.get('success') else None
#                 )

#                 return feedback_id

#         except Exception as e:
#             print(f"   ⚠️ Feedback log erreur: {e}")
#             return None

#     def _update_pattern(self, normalized: str, success: bool,
#                         time_taken: float, sql: Optional[str]):
#         """Met à jour la table des patterns récurrents"""
#         try:
#             cursor = self._conn.execute(
#                 "SELECT count, success_rate, avg_time FROM patterns WHERE normalized = ?",
#                 (normalized,)
#             )
#             row = cursor.fetchone()

#             if row:
#                 count, old_rate, old_time = row
#                 new_count = count + 1
#                 # Moyenne glissante
#                 new_rate = (old_rate * count + (1 if success else 0)) / new_count
#                 new_time = (old_time * count + time_taken) / new_count

#                 self._conn.execute("""
#                     UPDATE patterns SET count = ?, last_seen = ?,
#                                         success_rate = ?, avg_time = ?,
#                                         best_sql = COALESCE(?, best_sql)
#                     WHERE normalized = ?
#                 """, (
#                     new_count, datetime.now().isoformat(),
#                     new_rate, new_time, sql if success else None, normalized
#                 ))
#             else:
#                 self._conn.execute("""
#                     INSERT INTO patterns
#                     (normalized, count, last_seen, success_rate, avg_time, best_sql)
#                     VALUES (?, 1, ?, ?, ?, ?)
#                 """, (
#                     normalized, datetime.now().isoformat(),
#                     1.0 if success else 0.0, time_taken,
#                     sql if success else None
#                 ))
#         except Exception as e:
#             print(f"   ⚠️ Pattern update: {e}")

#     # ═══════════════════════════════════════════════════════════
#     # USER RATING (optionnel, si UI permet)
#     # ═══════════════════════════════════════════════════════════

#     def rate(self, feedback_id: int, rating: int):
#         """Note utilisateur : 1=bad, 2=ok, 3=good"""
#         if not self._conn or rating not in (1, 2, 3):
#             return False
#         try:
#             with self._lock:
#                 self._conn.execute(
#                     "UPDATE feedback SET user_rating = ? WHERE id = ?",
#                     (rating, feedback_id)
#                 )
#                 self._conn.commit()
#             return True
#         except Exception as e:
#             print(f"   ⚠️ Rating: {e}")
#             return False

#     # ═══════════════════════════════════════════════════════════
#     # RÉINDEXATION DANS LE RAG
#     # ═══════════════════════════════════════════════════════════

#     def get_unindexed_successes(self, min_count: int = 2,
#                                   limit: int = 50) -> List[Dict]:
#         """
#         Récupère les questions réussies pas encore indexées dans le RAG.
#         Privilégie celles qui reviennent souvent (min_count fois).
#         """
#         if not self._conn:
#             return []

#         try:
#             cursor = self._conn.execute("""
#                 SELECT f.id, f.question, f.normalized, f.sql_query,
#                        f.intent_category, p.count
#                 FROM feedback f
#                 LEFT JOIN patterns p ON f.normalized = p.normalized
#                 WHERE f.success = 1
#                   AND f.indexed_in_rag = 0
#                   AND f.sql_query IS NOT NULL
#                   AND f.method LIKE 'llm%'
#                   AND COALESCE(p.count, 1) >= ?
#                 ORDER BY p.count DESC, f.created_at DESC
#                 LIMIT ?
#             """, (min_count, limit))

#             return [
#                 {
#                     'id': row[0],
#                     'question': row[1],
#                     'normalized': row[2],
#                     'sql': row[3],
#                     'category': row[4] or 'feedback',
#                     'count': row[5] or 1,
#                 }
#                 for row in cursor.fetchall()
#             ]
#         except Exception as e:
#             print(f"   ⚠️ get_unindexed: {e}")
#             return []

#     def mark_as_indexed(self, feedback_id: int):
#         """Marque un feedback comme indexé dans le RAG"""
#         if not self._conn:
#             return
#         try:
#             with self._lock:
#                 self._conn.execute(
#                     "UPDATE feedback SET indexed_in_rag = 1 WHERE id = ?",
#                     (feedback_id,)
#                 )
#                 self._conn.commit()
#                 self.stats['reindexed'] += 1
#         except Exception as e:
#             print(f"   ⚠️ mark_indexed: {e}")

#     def reindex_to_rag(self, rag_agent, min_count: int = 2,
#                        limit: int = 50) -> int:
#         """
#         Réindexe les questions réussies dans le RAG.
#         Retourne le nombre de questions indexées.
#         """
#         candidates = self.get_unindexed_successes(min_count, limit)
#         if not candidates:
#             print(f"   ℹ️ Aucune question à réindexer")
#             return 0

#         indexed = 0
#         for c in candidates:
#             try:
#                 ok = rag_agent.index_feedback(
#                     question=c['question'],
#                     sql=c['sql'],
#                     category=c['category']
#                 )
#                 if ok:
#                     self.mark_as_indexed(c['id'])
#                     indexed += 1
#             except Exception as e:
#                 print(f"   ⚠️ Reindex {c['id']}: {e}")

#         print(f"   ✅ {indexed} questions réindexées dans le RAG")
#         return indexed

#     # ═══════════════════════════════════════════════════════════
#     # ANALYSE / STATS
#     # ═══════════════════════════════════════════════════════════

#     def get_failure_patterns(self, limit: int = 20) -> List[Dict]:
#         """Récupère les questions qui échouent souvent"""
#         if not self._conn:
#             return []
#         try:
#             cursor = self._conn.execute("""
#                 SELECT normalized, COUNT(*) as nb_fails,
#                        MAX(question) as example_question,
#                        MAX(error_message) as last_error
#                 FROM feedback
#                 WHERE success = 0
#                 GROUP BY normalized
#                 HAVING nb_fails >= 2
#                 ORDER BY nb_fails DESC
#                 LIMIT ?
#             """, (limit,))
#             return [
#                 {
#                     'normalized': row[0],
#                     'nb_fails': row[1],
#                     'example': row[2],
#                     'last_error': row[3],
#                 }
#                 for row in cursor.fetchall()
#             ]
#         except Exception as e:
#             print(f"   ⚠️ get_failures: {e}")
#             return []

#     def get_top_questions(self, limit: int = 20) -> List[Dict]:
#         """Top questions les plus fréquentes"""
#         if not self._conn:
#             return []
#         try:
#             cursor = self._conn.execute("""
#                 SELECT normalized, count, success_rate, avg_time
#                 FROM patterns
#                 ORDER BY count DESC
#                 LIMIT ?
#             """, (limit,))
#             return [
#                 {
#                     'normalized': row[0],
#                     'count': row[1],
#                     'success_rate': f"{row[2] * 100:.0f}%",
#                     'avg_time': f"{row[3]:.2f}s",
#                 }
#                 for row in cursor.fetchall()
#             ]
#         except Exception as e:
#             return []

#     def get_global_stats(self) -> Dict:
#         """Statistiques globales du système"""
#         if not self._conn:
#             return {}
#         try:
#             stats = {}

#             # Volumes
#             cursor = self._conn.execute("SELECT COUNT(*) FROM feedback")
#             stats['total_questions'] = cursor.fetchone()[0]

#             cursor = self._conn.execute(
#                 "SELECT COUNT(*) FROM feedback WHERE success = 1"
#             )
#             stats['successful'] = cursor.fetchone()[0]

#             if stats['total_questions'] > 0:
#                 stats['success_rate'] = (
#                     f"{stats['successful'] / stats['total_questions'] * 100:.1f}%"
#                 )

#             # Méthodes
#             cursor = self._conn.execute("""
#                 SELECT method, COUNT(*) FROM feedback
#                 GROUP BY method ORDER BY 2 DESC
#             """)
#             stats['by_method'] = dict(cursor.fetchall())

#             # Tenants
#             cursor = self._conn.execute("""
#                 SELECT tenant, COUNT(*) FROM feedback
#                 GROUP BY tenant ORDER BY 2 DESC
#             """)
#             stats['by_tenant'] = dict(cursor.fetchall())

#             # Performance moyenne
#             cursor = self._conn.execute("""
#                 SELECT AVG(processing_time), MIN(processing_time), MAX(processing_time)
#                 FROM feedback WHERE success = 1
#             """)
#             row = cursor.fetchone()
#             if row and row[0]:
#                 stats['avg_time'] = f"{row[0]:.2f}s"
#                 stats['min_time'] = f"{row[1]:.2f}s"
#                 stats['max_time'] = f"{row[2]:.2f}s"

#             # Patterns
#             cursor = self._conn.execute("SELECT COUNT(*) FROM patterns")
#             stats['unique_patterns'] = cursor.fetchone()[0]

#             stats.update(self.stats)
#             return stats

#         except Exception as e:
#             print(f"   ⚠️ get_stats: {e}")
#             return self.stats.copy()

#     # ═══════════════════════════════════════════════════════════
#     # MAINTENANCE
#     # ═══════════════════════════════════════════════════════════

#     def cleanup_old(self, days: int = 90):
#         """Supprime les feedback de plus de N jours"""
#         if not self._conn:
#             return 0
#         try:
#             cutoff = (datetime.now() - timedelta(days=days)).isoformat()
#             with self._lock:
#                 cursor = self._conn.execute(
#                     "DELETE FROM feedback WHERE created_at < ?", (cutoff,)
#                 )
#                 deleted = cursor.rowcount
#                 self._conn.commit()
#             print(f"   🧹 {deleted} anciens feedbacks supprimés (>{days}j)")
#             return deleted
#         except Exception as e:
#             print(f"   ⚠️ Cleanup: {e}")
#             return 0

#     def export_csv(self, output_path: str = "./feedback_export.csv"):
#         """Exporte les feedbacks en CSV pour analyse"""
#         if not self._conn:
#             return False
#         try:
#             import csv
#             cursor = self._conn.execute("""
#                 SELECT id, question, tenant, intent_category, method,
#                        success, row_count, processing_time, created_at
#                 FROM feedback
#                 ORDER BY created_at DESC
#             """)

#             with open(output_path, 'w', newline='', encoding='utf-8') as f:
#                 writer = csv.writer(f)
#                 writer.writerow([
#                     'id', 'question', 'tenant', 'category', 'method',
#                     'success', 'rows', 'time', 'created_at'
#                 ])
#                 writer.writerows(cursor.fetchall())

#             print(f"   📤 Export CSV: {output_path}")
#             return True
#         except Exception as e:
#             print(f"   ⚠️ Export: {e}")
#             return False


# # ═══════════════════════════════════════════════════════════════
# # TEST
# # ═══════════════════════════════════════════════════════════════

# if __name__ == "__main__":
#     print("\n" + "=" * 80)
#     print(" " * 25 + "📝 FEEDBACK LOGGER V6 - TEST")
#     print("=" * 80 + "\n")

#     logger = FeedbackLoggerV6(db_path="./feedback_v6_test.db")

#     # Test 1 : Log de quelques feedbacks
#     print("--- TEST 1 : Logging ---")
#     test_data = [
#         ("Pannes actives à JLN ?", {
#             'success': True, 'tenant': 'jln', 'method': 'template:list_fault',
#             'sql': 'SELECT * FROM v3_tenant_jln.asset_faults...',
#             'row_count': 30, 'processing_time': 1.2,
#         }),
#         ("Combien d'alarmes critiques ?", {
#             'success': True, 'tenant': 'safi', 'method': 'template:count_alarm',
#             'sql': 'SELECT COUNT(*)...', 'row_count': 1, 'processing_time': 0.8,
#         }),
#         ("Question incompréhensible xyz", {
#             'success': False, 'tenant': 'unknown', 'method': 'failed',
#             'error': 'No template/RAG match', 'processing_time': 5.0,
#         }),
#         ("Pannes actives à JLN ?", {  # Doublon
#             'success': True, 'tenant': 'jln', 'method': 'template:list_fault',
#             'sql': 'SELECT * FROM v3_tenant_jln.asset_faults...',
#             'row_count': 32, 'processing_time': 0.9,
#         }),
#     ]

#     for q, r in test_data:
#         fid = logger.log(q, r)
#         status = "✅" if r.get('success') else "❌"
#         print(f"   {status} ID={fid} | {q[:50]}")

#     # Test 2 : Stats
#     print("\n--- TEST 2 : Stats globales ---")
#     for k, v in logger.get_global_stats().items():
#         print(f"   {k}: {v}")

#     # Test 3 : Top questions
#     print("\n--- TEST 3 : Top questions ---")
#     for q in logger.get_top_questions(5):
#         print(f"   📌 {q['normalized'][:50]} ({q['count']}x, {q['success_rate']})")

#     # Test 4 : Échecs récurrents
#     print("\n--- TEST 4 : Échecs ---")
#     for f in logger.get_failure_patterns(5):
#         print(f"   ❌ {f['example'][:50]} ({f['nb_fails']} échecs)")

#     print("\n" + "=" * 80 + "\n")