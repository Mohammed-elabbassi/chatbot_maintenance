# backend/app/agents/rag_agent_v8.py
"""
RAG Agent V8 — Pipeline Hybride Milvus (MilvusClient API 2.4+)
Dense HNSW → BM25 Sparse → RRF Fusion → Cross-Encoder Reranking

Collections :
  - ocp_sql_examples   : question → SQL  (depuis dataset_400_questions)
  - ocp_table_schemas  : schémas tables  (depuis schema_global / schema_tenants)
  - ocp_join_patterns  : patterns JOIN   (depuis standards_v3.JOINS)

Dépendances :
    pip install "pymilvus>=2.4.0" sentence-transformers rank_bm25
"""

import hashlib
import json
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional

from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer
from pymilvus import MilvusClient, DataType

# ─────────────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL  = "cross-encoder/ms-marco-MiniLM-L-6-v2"
VECTOR_DIM      = 384
TOP_DENSE       = 15
TOP_BM25        = 15
TOP_AFTER_RRF   = 20
TOP_FINAL       = 5
RRF_K           = 60


def _rrf(rank: int, k: int = RRF_K) -> float:
    return 1.0 / (k + rank + 1)


class RAGAgentV8:
    """RAG hybride OCP — MilvusClient (API 2.4+) + BM25 + Cross-Encoder."""

    CATEGORY_TABLES = {
        "fault":          ["assets", "asset_faults", "faults"],
        "alarm":          ["assets", "alarms"],
        "measurement":    ["assets", "measurements", "feature_measurement", "feature_group"],
        "asset":          ["assets", "asset_classes", "families"],
        "intervention":   ["assets", "interventions"],
        "recommendation": ["assets", "recommendations_v3", "recommendation_assets"],
        "user":           ["users", "user_company", "companies"],
        "company":        ["companies", "abonnements"],
        "prediction":     ["predictions", "assets"],
        "feature":        ["feature_measurement", "feature_group", "features"],
        "device":         ["vibox_diagnosis", "devices"],
    }

    def __init__(
        self,
        milvus_uri:      str = "http://localhost:19530",
        embedding_model: str = EMBEDDING_MODEL,
        reranker_model:  str = RERANKER_MODEL,
    ):
        self.client = MilvusClient(uri=milvus_uri)

        print(f"[RAGAgentV8] Chargement embeddings : {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        print(f"[RAGAgentV8] Chargement reranker   : {reranker_model}")
        self.reranker = CrossEncoder(reranker_model)

        self._init_collections()

        self._cache: OrderedDict = OrderedDict()
        self._cache_max = 200
        self._cache_ttl = 300

        self.stats = {
            "total_searches": 0,
            "cache_hits":     0,
            "dense_searches": 0,
            "bm25_searches":  0,
            "reranks":        0,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Création des collections
    # ──────────────────────────────────────────────────────────────────────

    def _make_index_params(self) -> object:
        ip = self.client.prepare_index_params()
        ip.add_index(
            field_name="vector",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 200},
        )
        return ip

    def _init_collections(self):
        # ocp_sql_examples
        if not self.client.has_collection("ocp_sql_examples"):
            schema = self.client.create_schema(auto_id=True, enable_dynamic_field=False)
            schema.add_field("id",       DataType.INT64,        is_primary=True)
            schema.add_field("text",     DataType.VARCHAR,      max_length=2048)
            schema.add_field("vector",   DataType.FLOAT_VECTOR, dim=VECTOR_DIM)
            schema.add_field("question", DataType.VARCHAR,      max_length=1024)
            schema.add_field("sql",      DataType.VARCHAR,      max_length=4096)
            schema.add_field("category", DataType.VARCHAR,      max_length=128)
            schema.add_field("tables",   DataType.VARCHAR,      max_length=512)
            self.client.create_collection(
                "ocp_sql_examples", schema=schema, index_params=self._make_index_params()
            )
            print("[RAGAgentV8] Collection 'ocp_sql_examples' créée.")

        # ocp_table_schemas
        if not self.client.has_collection("ocp_table_schemas"):
            schema = self.client.create_schema(auto_id=True, enable_dynamic_field=False)
            schema.add_field("id",          DataType.INT64,        is_primary=True)
            schema.add_field("text",        DataType.VARCHAR,      max_length=4096)
            schema.add_field("vector",      DataType.FLOAT_VECTOR, dim=VECTOR_DIM)
            schema.add_field("table_name",  DataType.VARCHAR,      max_length=256)
            schema.add_field("description", DataType.VARCHAR,      max_length=1024)
            self.client.create_collection(
                "ocp_table_schemas", schema=schema, index_params=self._make_index_params()
            )
            print("[RAGAgentV8] Collection 'ocp_table_schemas' créée.")

        # ocp_join_patterns
        if not self.client.has_collection("ocp_join_patterns"):
            schema = self.client.create_schema(auto_id=True, enable_dynamic_field=False)
            schema.add_field("id",          DataType.INT64,        is_primary=True)
            schema.add_field("text",        DataType.VARCHAR,      max_length=2048)
            schema.add_field("vector",      DataType.FLOAT_VECTOR, dim=VECTOR_DIM)
            schema.add_field("description", DataType.VARCHAR,      max_length=512)
            schema.add_field("sql_pattern", DataType.VARCHAR,      max_length=4096)
            self.client.create_collection(
                "ocp_join_patterns", schema=schema, index_params=self._make_index_params()
            )
            print("[RAGAgentV8] Collection 'ocp_join_patterns' créée.")

    # ──────────────────────────────────────────────────────────────────────
    # Indexation
    # ──────────────────────────────────────────────────────────────────────

    def index_sql_examples(self, examples: List[Dict]):
        if not examples:
            return
        texts = [ex["question"] for ex in examples]
        vecs  = self.embedder.encode(texts, show_progress_bar=True).tolist()
        data  = [
            {
                "text":     ex["question"],
                "vector":   vecs[i],
                "question": ex["question"],
                "sql":      ex.get("sql", ""),
                "category": ex.get("category", ""),
                "tables":   json.dumps(ex.get("tables", [])),
            }
            for i, ex in enumerate(examples)
        ]
        self.client.insert("ocp_sql_examples", data)
        print(f"[RAGAgentV8] {len(data)} exemples SQL indexés.")

    def index_table_schemas(self, schemas: List[Dict]):
        if not schemas:
            return
        texts = [s["text"] for s in schemas]
        vecs  = self.embedder.encode(texts, show_progress_bar=True).tolist()
        data  = [
            {
                "text":        s["text"],
                "vector":      vecs[i],
                "table_name":  s.get("table_name", ""),
                "description": s.get("description", ""),
            }
            for i, s in enumerate(schemas)
        ]
        self.client.insert("ocp_table_schemas", data)
        print(f"[RAGAgentV8] {len(data)} schémas indexés.")

    def index_join_patterns(self, patterns: List[Dict]):
        if not patterns:
            return
        texts = [p["text"] for p in patterns]
        vecs  = self.embedder.encode(texts, show_progress_bar=True).tolist()
        data  = [
            {
                "text":        p["text"],
                "vector":      vecs[i],
                "description": p.get("description", ""),
                "sql_pattern": p.get("sql_pattern", ""),
            }
            for i, p in enumerate(patterns)
        ]
        self.client.insert("ocp_join_patterns", data)
        print(f"[RAGAgentV8] {len(data)} patterns jointure indexés.")

    # ──────────────────────────────────────────────────────────────────────
    # Recherche hybride
    # ──────────────────────────────────────────────────────────────────────

    def _count(self, collection: str) -> int:
        try:
            return int(self.client.get_collection_stats(collection).get("row_count", 0))
        except Exception:
            return 0

    def _dense_search(
        self,
        collection:    str,
        query_vec:     List[float],
        output_fields: List[str],
        top_k:         int = TOP_DENSE,
    ) -> List[Dict]:
        self.stats["dense_searches"] += 1
        count = self._count(collection)
        if count == 0:
            return []
        try:
            results = self.client.search(
                collection_name=collection,
                data=[query_vec],
                anns_field="vector",
                search_params={"metric_type": "COSINE", "params": {"ef": 64}},
                limit=min(top_k, count),
                output_fields=output_fields,
            )
            out = []
            for hit in results[0]:
                item = {"_id": hit["id"], "_score_dense": float(hit["distance"])}
                for f in output_fields:
                    item[f] = hit["entity"].get(f, "")
                out.append(item)
            return out
        except Exception as e:
            print(f"[RAGAgentV8] Dense search error ({collection}): {e}")
            return []

    def _bm25_search(
        self,
        collection:    str,
        query:         str,
        output_fields: List[str],
        top_k:         int = TOP_BM25,
    ) -> List[Dict]:
        self.stats["bm25_searches"] += 1
        count = self._count(collection)
        if count == 0:
            return []
        try:
            all_res = self.client.query(
                collection_name=collection,
                filter="id > 0",
                output_fields=["id", "text"] + output_fields,
                limit=min(count, 3000),
            )
            if not all_res:
                return []
            tok    = [r["text"].lower().split() for r in all_res]
            bm25   = BM25Okapi(tok)
            scores = bm25.get_scores(query.lower().split())
            ranked = sorted(zip(scores, all_res), key=lambda x: x[0], reverse=True)
            out = []
            for score, r in ranked[:top_k]:
                if score > 0:
                    item = {"_id": r["id"], "_score_bm25": float(score)}
                    for f in output_fields:
                        item[f] = r.get(f, "")
                    out.append(item)
            return out
        except Exception as e:
            print(f"[RAGAgentV8] BM25 error ({collection}): {e}")
            return []

    def _rrf_fusion(self, dense: List[Dict], bm25: List[Dict]) -> List[Dict]:
        scores:   Dict[int, float] = {}
        items:    Dict[int, Dict]  = {}
        for rank, item in enumerate(dense):
            uid = item["_id"]
            scores[uid] = scores.get(uid, 0) + _rrf(rank)
            items[uid]  = item
        for rank, item in enumerate(bm25):
            uid = item["_id"]
            scores[uid] = scores.get(uid, 0) + _rrf(rank)
            if uid not in items:
                items[uid] = item
        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        out = []
        for uid, score in fused[:TOP_AFTER_RRF]:
            item = items[uid].copy()
            item["_score_rrf"] = score
            out.append(item)
        return out

    def _rerank(self, query: str, candidates: List[Dict], text_field: str = "text") -> List[Dict]:
        self.stats["reranks"] += 1
        if not candidates:
            return []
        pairs  = [[query, c.get(text_field, c.get("text", ""))] for c in candidates]
        scores = self.reranker.predict(pairs)
        for c, s in zip(candidates, scores):
            c["_score_final"] = float(s)
        candidates.sort(key=lambda x: x["_score_final"], reverse=True)
        return candidates[:TOP_FINAL]

    # ──────────────────────────────────────────────────────────────────────
    # Interface publique
    # ──────────────────────────────────────────────────────────────────────

    def search_sql_examples(
        self, question: str, category: Optional[str] = None, top_k: int = TOP_FINAL
    ) -> List[Dict]:
        """Recherche hybride Dense+BM25+RRF+CrossEncoder sur les exemples SQL."""
        self.stats["total_searches"] += 1
        ck = hashlib.md5(f"sql|{question}|{category}".encode()).hexdigest()
        cached = self._cache_get(ck)
        if cached is not None:
            self.stats["cache_hits"] += 1
            return cached

        qv     = self.embedder.encode([question])[0].tolist()
        fields = ["question", "sql", "category", "tables"]
        dense  = self._dense_search("ocp_sql_examples", qv, fields)
        bm25   = self._bm25_search("ocp_sql_examples", question, fields)

        if category:
            dense = [r for r in dense if not r.get("category") or r["category"] == category]
            bm25  = [r for r in bm25  if not r.get("category") or r["category"] == category]

        fused    = self._rrf_fusion(dense, bm25)
        reranked = self._rerank(question, fused, text_field="question")

        results = []
        for r in reranked:
            try:
                tables = json.loads(r.get("tables", "[]"))
            except Exception:
                tables = []
            results.append({
                "question": r.get("question", ""),
                "sql":      r.get("sql", ""),
                "category": r.get("category", ""),
                "tables":   tables,
                "score":    r.get("_score_final", 0.0),
            })

        self._cache_put(ck, results)
        return results

    def search_schemas(self, question: str, category: Optional[str] = None) -> List[Dict]:
        qv     = self.embedder.encode([question])[0].tolist()
        tbls   = self.CATEGORY_TABLES.get(category, []) if category else []
        fields = ["table_name", "description"]
        dense  = self._dense_search("ocp_table_schemas", qv, fields)
        bm25   = self._bm25_search("ocp_table_schemas", question, fields)
        if tbls:
            dense = [r for r in dense if r.get("table_name") in tbls]
            bm25  = [r for r in bm25  if r.get("table_name") in tbls]
        return self._rerank(question, self._rrf_fusion(dense, bm25), text_field="description")

    def search_join_patterns(self, question: str) -> List[Dict]:
        qv     = self.embedder.encode([question])[0].tolist()
        fields = ["description", "sql_pattern"]
        dense  = self._dense_search("ocp_join_patterns", qv, fields, top_k=10)
        bm25   = self._bm25_search("ocp_join_patterns", question, fields, top_k=10)
        return self._rerank(question, self._rrf_fusion(dense, bm25), text_field="description")

    def build_prompt_context(
        self, question: str, tenant_db: str, intent=None, max_chars: int = 1800
    ) -> str:
        """Construit le contexte RAG à injecter dans le prompt SQL."""
        category = getattr(intent, "category", None)
        parts = []
        cur   = 0

        # Schémas
        for s in self.search_schemas(question, category)[:3]:
            tn  = s.get("table_name", "")
            txt = s.get("text", s.get("description", "")).replace("{tenant_db}", tenant_db)
            sec = "\n".join(txt.strip().split("\n")[:15]) + "\n"
            if cur + len(sec) > max_chars:
                break
            if tn:
                parts.append(f"-- TABLE {tn}\n{sec}")
                cur += len(sec)

        # Jointures
        for p in self.search_join_patterns(question)[:2]:
            sp  = p.get("sql_pattern", "").replace("{tenant_db}", tenant_db)
            sec = f"-- {p.get('description', '')}\n{sp}\n"
            if cur + len(sec) > max_chars:
                break
            parts.append(sec)
            cur += len(sec)

        # Exemples SQL
        for ex in self.search_sql_examples(question, category)[:2]:
            sql = ex.get("sql", "").replace("{tenant_db}", tenant_db)
            sec = f"-- {ex.get('question', '')}\n{sql}\n"
            if cur + len(sec) > max_chars:
                break
            parts.append(sec)
            cur += len(sec)

        return "\n".join(parts)

    def get_collection_stats(self) -> Dict:
        return {
            "ocp_sql_examples":  self._count("ocp_sql_examples"),
            "ocp_table_schemas": self._count("ocp_table_schemas"),
            "ocp_join_patterns": self._count("ocp_join_patterns"),
        }

    def get_stats(self) -> Dict:
        s     = self.stats.copy()
        total = s["total_searches"]
        if total > 0:
            s["cache_hit_rate"] = f"{s['cache_hits'] / total * 100:.1f}%"
        return s

    # Cache LRU
    def _cache_get(self, key):
        if key in self._cache:
            value, ts = self._cache[key]
            if (datetime.now().timestamp() - ts) < self._cache_ttl:
                self._cache.move_to_end(key)
                return value
            del self._cache[key]
        return None

    def _cache_put(self, key, value):
        self._cache[key] = (value, datetime.now().timestamp())
        while len(self._cache) > self._cache_max:
            self._cache.popitem(last=False)
