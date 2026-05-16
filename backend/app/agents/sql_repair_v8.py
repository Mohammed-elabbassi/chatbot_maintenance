# backend/app/agents/sql_repair_v8.py
"""
SQL Repair V8 — Groq LLaMA 3.1 8B
Remplace sql_repair_v7.py (Ollama). Interface identique.
"""
from typing import Dict

try:
    from app.agents.prompt_builder_v7 import PromptBuilderV7
    from app.agents.llm_agent_v8      import LLMAgentV8
except ImportError:
    from prompt_builder_v7 import PromptBuilderV7
    from llm_agent_v8      import LLMAgentV8


class SQLRepairV8:
    def __init__(self):
        self.pb  = PromptBuilderV7()
        self.llm = LLMAgentV8()

    def repair(
        self,
        question:         str,
        failed_sql:       str,
        error_msg:        str,
        schema_context:   str,
        join_hints:       str,
        examples_context: str,
        timeout:          int = 60,
    ) -> Dict:
        system = self.pb.build_sql_system_prompt()
        prompt = self.pb.build_repair_prompt(
            question=question, failed_sql=failed_sql, error_msg=error_msg,
            schema_context=schema_context, join_hints=join_hints,
            examples_context=examples_context,
        )
        result = self.llm.generate_json(
            prompt=prompt, system=system, temperature=0.05,
            max_tokens=1024, timeout=timeout,
        )
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "repair failed")}
        return {"success": True, "parsed": result.get("parsed", {}),
                "raw_response": result.get("raw_response", "")}
