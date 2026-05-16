# backend/app/agents/response_rewriter_v8.py
"""
Response Rewriter V8 — Groq LLaMA 3.1 8B
Remplace response_rewriter_v7.py (Ollama). Interface identique.
"""
from typing import Dict, List

try:
    from app.agents.prompt_builder_v7 import PromptBuilderV7
    from app.agents.llm_agent_v8      import LLMAgentV8
except ImportError:
    from prompt_builder_v7 import PromptBuilderV7
    from llm_agent_v8      import LLMAgentV8


class ResponseRewriterV8:
    def __init__(self):
        self.pb  = PromptBuilderV7()
        self.llm = LLMAgentV8()

    def rewrite(
        self,
        question: str,
        tenant:   str,
        columns:  List[str],
        rows:     List[Dict],
        timeout:  int = 45,
    ) -> Dict:
        prompt = self.pb.build_rewrite_prompt(
            question=question, tenant=tenant, columns=columns, rows=rows[:20]
        )
        result = self.llm.generate(
            prompt=prompt, system=None, temperature=0.2, max_tokens=512, timeout=timeout
        )
        if not result.get("success"):
            return result
        return {"success": True, "response": result["response"].strip()}
