# backend/app/agents/benchmark_v8.py
"""Benchmark V8 — Même interface que BenchmarkV7 mais utilise PlannerAgentV8."""

try:
    from app.agents.planner_agent_v8        import PlannerAgentV8
    from app.database.dataset_400_questions import DATASET_400_QUESTIONS
    from app.database.dataset_enrichment    import NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES
except ImportError:
    from planner_agent_v8           import PlannerAgentV8
    from database.dataset_400_questions import DATASET_400_QUESTIONS
    from database.dataset_enrichment    import NEGATIVE_EXAMPLES, AMBIGUOUS_EXAMPLES, EDGE_CASES


class BenchmarkV8:
    def __init__(self):
        self.agent = PlannerAgentV8()

    def run(self, max_main=None, max_negative=None, max_ambiguous=None,
            max_edge=None, extra_questions=None):
        tests = []
        for ex in (DATASET_400_QUESTIONS[:max_main] if max_main else DATASET_400_QUESTIONS):
            tests.append({"question": ex["question"], "type": "main"})
        for ex in (NEGATIVE_EXAMPLES[:max_negative] if max_negative else NEGATIVE_EXAMPLES):
            tests.append({"question": ex["question"], "type": "negative"})
        for ex in (AMBIGUOUS_EXAMPLES[:max_ambiguous] if max_ambiguous else AMBIGUOUS_EXAMPLES):
            tests.append({"question": ex["question"], "type": "ambiguous"})
        for ex in (EDGE_CASES[:max_edge] if max_edge else EDGE_CASES):
            tests.append({"question": ex["question"], "type": "edge"})
        if extra_questions:
            for q in extra_questions:
                tests.append({"question": q, "type": "extra"})

        stats = {"total": 0, "success": 0, "failed": 0, "avg_time": 0.0,
                 "success_rate": 0.0, "by_type": {}, "by_method": {}, "by_category": {}, "fail_reasons": {}}
        times, results = [], []

        for item in tests:
            r = self.agent.process_question(item["question"])
            stats["total"] += 1
            stats["by_type"].setdefault(item["type"], {"total": 0, "success": 0, "failed": 0})
            stats["by_type"][item["type"]]["total"] += 1
            method   = r.get("method", "unknown")
            category = r.get("category", "unknown")
            stats["by_method"][method]     = stats["by_method"].get(method, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            if r.get("success"):
                stats["success"] += 1
                stats["by_type"][item["type"]]["success"] += 1
            else:
                stats["failed"] += 1
                stats["by_type"][item["type"]]["failed"] += 1
                stats["fail_reasons"][method] = stats["fail_reasons"].get(method, 0) + 1
            times.append(r.get("processing_time", 0))
            results.append({"question": item["question"], "type": item["type"],
                            "success": r.get("success"), "method": method,
                            "processing_time": r.get("processing_time"),
                            "category": category, "row_count": r.get("row_count", 0),
                            "error": r.get("error")})

        if times:
            stats["avg_time"] = round(sum(times) / len(times), 2)
        if stats["total"]:
            stats["success_rate"] = round(stats["success"] / stats["total"] * 100, 2)

        return {"stats": stats, "results": results}


if __name__ == "__main__":
    b = BenchmarkV8()
    r = b.run(max_main=10, max_negative=3, max_ambiguous=3, max_edge=3,
              extra_questions=["Montre les alarmes critiques de Safi",
                               "Top équipements avec NGV élevée à JLN"])
    print(r["stats"])
