from __future__ import annotations
import os
from typing import Dict, Any, Optional
from .schemas import AIPlan, AIAction, AISignalSetup


class AIAgent:
    """
    Lightweight AI Orchestrator using OpenAI-compatible API (e.g., Ollama).
    Produces a structured plan of actions. Safe-by-default: only proposes.
    """

    def __init__(self,
                 model: Optional[str] = None,
                 api_base: Optional[str] = None,
                 api_key: Optional[str] = None):
        self.model = model or os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
        self.api_base = api_base or os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/v1')
        # For OpenAI client, any non-empty api_key is required; use dummy if Ollama.
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', os.getenv('OLLAMA_API_KEY', 'ollama'))
        try:
            from openai import OpenAI
            self.client = OpenAI(base_url=self.api_base, api_key=self.api_key)
        except Exception:
            self.client = None

    def propose_actions(self, snapshot: Dict[str, Any], system_policy: Optional[str] = None) -> Optional[AIPlan]:
        if not self.client:
            return None

        system_prompt = system_policy or (
            "You are a trading assistant. Output a JSON object strictly matching the schema. "
            "Never place orders directly; only propose actions with confidence and reasons."
        )

        user_content = (
            "Snapshot JSON with features per timeframe and current price. "
            "Decide if to open/modify/close positions. Prefer NO_OP unless strong confluence."
        )

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                    {"role": "user", "content": json_dumps_safe(snapshot)[:6000]},
                ],
                temperature=0.2,
            )
            text = (resp.choices[0].message.content or '').strip()
            # Try parse JSON
            import json
            data = None
            try:
                data = json.loads(text)
            except Exception:
                # try to extract code block
                if '```' in text:
                    chunk = text.split('```')
                    for block in chunk:
                        try:
                            data = json.loads(block)
                            break
                        except Exception:
                            continue
            if not isinstance(data, dict):
                return None
            plan = AIPlan.model_validate(data)
            return plan
        except Exception:
            return None


def json_dumps_safe(obj: Any) -> str:
    import json
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return json.dumps({"error": "unserializable"})

