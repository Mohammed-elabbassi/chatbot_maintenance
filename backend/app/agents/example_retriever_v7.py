# # backend/app/agents/example_retriever_v7.py
# import re
# from typing import List, Dict

# try:
#     from app.database.dataset_400_questions import DATASET_400_QUESTIONS
#     from app.database.dataset_enrichment import NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES
# except ImportError:
#     from database.dataset_400_questions import DATASET_400_QUESTIONS
#     from database.dataset_enrichment import NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES


# class ExampleRetrieverV7:
#     STOP_WORDS = {
#         "le", "la", "les", "de", "du", "des", "un", "une", "et", "ou",
#         "à", "au", "aux", "en", "dans", "sur", "pour", "par", "avec",
#         "est", "sont", "qui", "que", "quoi", "combien", "quel", "quelle",
#         "quels", "quelles", "show", "list", "give", "what", "how", "many"
#     }

#     def __init__(self):
#         self.dataset = DATASET_400_QUESTIONS
#         self.negative = NEGATIVE_EXAMPLES
#         self.ambiguous = AMBIGUOUS_EXAMPLES
#         self.edge_cases = EDGE_CASES

#     def _normalize_words(self, text: str) -> set:
#         text = text.lower().strip()
#         text = re.sub(r"[^\w\sàâäéèêëîïôöùûüÿæœç]", " ", text)
#         words = [w for w in text.split() if w not in self.STOP_WORDS and len(w) > 1]
#         return set(words)

#     def _score(self, q1: str, q2: str) -> float:
#         s1 = self._normalize_words(q1)
#         s2 = self._normalize_words(q2)
#         if not s1 or not s2:
#             return 0.0
#         inter = len(s1 & s2)
#         union = len(s1 | s2)
#         return inter / union if union else 0.0

#     def retrieve_examples(self, question: str, intent=None, top_k: int = 6) -> List[Dict]:
#         scored = []
#         intent_category = getattr(intent, "category", None)

#         for ex in self.dataset:
#             score = self._score(question, ex["question"])
#             meta = ex.get("metadata", {})

#             if intent_category and meta.get("category") == intent_category:
#                 score += 0.10

#             if score > 0:
#                 scored.append((score, ex))

#         scored.sort(key=lambda x: x[0], reverse=True)
#         return [ex for _, ex in scored[:top_k]]

#     def retrieve_category_examples(self, intent=None, top_k: int = 3) -> List[Dict]:
#         category = getattr(intent, "category", None)
#         if not category:
#             return []

#         out = []
#         seen = set()

#         for ex in self.dataset:
#             meta = ex.get("metadata", {})
#             if meta.get("category") == category:
#                 key = ex.get("question", "").strip().lower()
#                 if key not in seen:
#                     seen.add(key)
#                     out.append(ex)
#             if len(out) >= top_k:
#                 break

#         return out

#     def merge_examples(self, primary: List[Dict], secondary: List[Dict], max_total: int = 6) -> List[Dict]:
#         merged = []
#         seen = set()

#         for bucket in (primary or [], secondary or []):
#             for ex in bucket:
#                 key = ex.get("question", "").strip().lower()
#                 if key and key not in seen:
#                     seen.add(key)
#                     merged.append(ex)
#                 if len(merged) >= max_total:
#                     return merged

#         return merged

#     def retrieve_negative_examples(self, question: str, top_k: int = 2) -> List[Dict]:
#         scored = []
#         for ex in self.negative:
#             score = self._score(question, ex["question"])
#             if score > 0:
#                 scored.append((score, ex))
#         scored.sort(key=lambda x: x[0], reverse=True)
#         return [ex for _, ex in scored[:top_k]]

#     def retrieve_edge_cases(self, question: str, top_k: int = 2) -> List[Dict]:
#         scored = []
#         for ex in self.edge_cases:
#             score = self._score(question, ex["question"])
#             if score > 0:
#                 scored.append((score, ex))
#         scored.sort(key=lambda x: x[0], reverse=True)
#         return [ex for _, ex in scored[:top_k]]

#     def format_examples_for_prompt(self, examples: List[Dict], tenant_db: str, title: str = "EXEMPLES") -> str:
#         if not examples:
#             return ""

#         parts = [f"=== {title} ==="]
#         for i, ex in enumerate(examples, start=1):
#             sql = ex.get("sql", "").replace("{tenant_db}", tenant_db)
#             parts.append(
#                 f"EXEMPLE {i}\n"
#                 f"Question: {ex['question']}\n"
#                 f"SQL:\n{sql.strip()}"
#             )
#         return "\n\n".join(parts)

# backend/app/agents/example_retriever_v7.py
import re
from typing import List, Dict

try:
    from app.database.dataset_400_questions import DATASET_400_QUESTIONS
    from app.database.dataset_enrichment import NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES
except ImportError:
    from database.dataset_400_questions import DATASET_400_QUESTIONS
    from database.dataset_enrichment import NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES

# Mapping de normalisation des catégories (dataset → interne)
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


def _normalize_category(raw_cat: str) -> str:
    """Normalise une catégorie (issue du dataset ou de l'intent) vers une catégorie standard."""
    if not raw_cat:
        return "unknown"
    return CATEGORY_MAP.get(raw_cat.lower(), raw_cat.lower())


class ExampleRetrieverV7:
    STOP_WORDS = {
        "le", "la", "les", "de", "du", "des", "un", "une", "et", "ou",
        "à", "au", "aux", "en", "dans", "sur", "pour", "par", "avec",
        "est", "sont", "qui", "que", "quoi", "combien", "quel", "quelle",
        "quels", "quelles", "show", "list", "give", "what", "how", "many"
    }

    def __init__(self):
        self.dataset = DATASET_400_QUESTIONS
        self.negative = NEGATIVE_EXAMPLES
        self.ambiguous = AMBIGUOUS_EXAMPLES
        self.edge_cases = EDGE_CASES

    def _normalize_words(self, text: str) -> set:
        text = text.lower().strip()
        text = re.sub(r"[^\w\sàâäéèêëîïôöùûüÿæœç]", " ", text)
        words = [w for w in text.split() if w not in self.STOP_WORDS and len(w) > 1]
        return set(words)

    def _score(self, q1: str, q2: str) -> float:
        s1 = self._normalize_words(q1)
        s2 = self._normalize_words(q2)
        if not s1 or not s2:
            return 0.0
        inter = len(s1 & s2)
        union = len(s1 | s2)
        return inter / union if union else 0.0

    def retrieve_examples(self, question: str, intent=None, top_k: int = 6) -> List[Dict]:
        scored = []
        intent_cat = _normalize_category(getattr(intent, "category", ""))

        for ex in self.dataset:
            score = self._score(question, ex["question"])
            meta = ex.get("metadata", {})

            # Boost si la catégorie de l'exemple correspond à celle de l'intent (après normalisation)
            ex_cat = _normalize_category(meta.get("category", ""))
            if intent_cat and ex_cat == intent_cat:
                score += 0.10

            if score > 0:
                scored.append((score, ex))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored[:top_k]]

    def retrieve_category_examples(self, intent=None, top_k: int = 3) -> List[Dict]:
        cat = _normalize_category(getattr(intent, "category", ""))
        if not cat:
            return []

        out = []
        seen = set()

        for ex in self.dataset:
            meta = ex.get("metadata", {})
            ex_cat = _normalize_category(meta.get("category", ""))
            if ex_cat == cat:
                key = ex.get("question", "").strip().lower()
                if key not in seen:
                    seen.add(key)
                    out.append(ex)
            if len(out) >= top_k:
                break

        return out

    def merge_examples(self, primary: List[Dict], secondary: List[Dict], max_total: int = 6) -> List[Dict]:
        merged = []
        seen = set()

        for bucket in (primary or [], secondary or []):
            for ex in bucket:
                key = ex.get("question", "").strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    merged.append(ex)
                if len(merged) >= max_total:
                    return merged

        return merged

    def retrieve_negative_examples(self, question: str, top_k: int = 2) -> List[Dict]:
        scored = []
        for ex in self.negative:
            score = self._score(question, ex["question"])
            if score > 0:
                scored.append((score, ex))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored[:top_k]]

    def retrieve_edge_cases(self, question: str, top_k: int = 2) -> List[Dict]:
        scored = []
        for ex in self.edge_cases:
            score = self._score(question, ex["question"])
            if score > 0:
                scored.append((score, ex))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored[:top_k]]

    def format_examples_for_prompt(self, examples: List[Dict], tenant_db: str, title: str = "EXEMPLES") -> str:
        if not examples:
            return ""

        parts = [f"=== {title} ==="]
        for i, ex in enumerate(examples, start=1):
            sql = ex.get("sql", "").replace("{tenant_db}", tenant_db)
            parts.append(
                f"EXEMPLE {i}\n"
                f"Question: {ex['question']}\n"
                f"SQL:\n{sql.strip()}"
            )
        return "\n\n".join(parts)