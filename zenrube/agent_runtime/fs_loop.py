# zenrube/agent_runtime/fs_loop.py

import os
import json
from typing import Dict, Any

from zenrube.experts.chatgpt_fs_agent import ChatGPTFsAgent, MCPFilesystemClient


# ---------------------------------------------------------
#  LLM CLIENT (LAZY LOADED)
# ---------------------------------------------------------

_mistral_client = None

def get_llm_client():
    global _mistral_client

    if _mistral_client is not None:
        return _mistral_client

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        class DummyPlanner:
            def plan(self, goal: str, observation: Dict[str, Any]):
                return {
                    "tasks": [],
                    "meta": {
                        "planner": "disabled",
                        "reason": "MISTRAL_API_KEY missing"
                    }
                }
        _mistral_client = DummyPlanner()
        return _mistral_client

    from mistralai import Mistral
    _mistral_client = Mistral(api_key=api_key)
    return _mistral_client


# ---------------------------------------------------------
#  PROMPT BUILDER
# ---------------------------------------------------------

def build_planner_prompt(goal: str, observation: Dict[str, Any]) -> str:
    return f"""
You are the ZenRube FS-Agent filesystem planner.
Return ONLY JSON:

{{
  "tasks": [
    {{
      "op": "list" | "read" | "write" | "delete" | "move",
      "path": "string",
      "content": "string (optional)",
      "dest": "string (optional)"
    }}
  ],
  "meta": {{
    "reason": "string"
  }}
}}

Rules:
- Stay inside /workspaces/ZenRube
- If unsure: list or read
- No markdown. No backticks. JSON ONLY.

GOAL:
{goal}

OBSERVATION:
{json.dumps(observation, indent=2)}
"""


# ---------------------------------------------------------
#  CALL MISTRAL (WITH FENCE CLEANUP)
# ---------------------------------------------------------

def call_fs_planner_llm(goal: str, observation: Dict[str, Any]) -> Dict[str, Any]:
    client = get_llm_client()

    if client.__class__.__name__ == "DummyPlanner":
        return client.plan(goal, observation)

    prompt = build_planner_prompt(goal, observation)

    resp = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=800
    )

    content = resp.choices[0].message.content

    # ---------------------------------------------------------
    # CLEANUP: remove fenced code blocks
    # ---------------------------------------------------------
    raw = content if isinstance(content, str) else json.dumps(content)
    cleaned = raw.strip()

    # Remove ```json ... ```
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

    # Remove stray backticks anywhere
    cleaned = cleaned.replace("```", "").replace("`", "").strip()

    # Attempt JSON load
    try:
        return json.loads(cleaned)
    except Exception:
        return {
            "tasks": [],
            "meta": {
                "reason": "Invalid JSON after cleanup",
                "raw": raw,
                "cleaned": cleaned
            }
        }


# ---------------------------------------------------------
#  FS AGENT LOOP
# ---------------------------------------------------------

class FsAgentLoop:

    def __init__(self, root: str = "/workspaces/ZenRube", max_steps: int = 8):
        self.root = root
        self.max_steps = max_steps
        self.client = MCPFilesystemClient()
        self.agent = ChatGPTFsAgent(self.client, root)

    def run(self, goal: str) -> Dict[str, Any]:
        history = []
        observation: Dict[str, Any] = {}

        for step in range(self.max_steps):

            # 1. Ask planner
            plan = call_fs_planner_llm(goal, observation)
            plan = json.loads(json.dumps(plan))  # JSON-safe

            tasks = plan.get("tasks", [])

            # stop if empty
            if not tasks:
                history.append({
                    "step": step,
                    "plan": plan,
                    "execution": {"ok": True, "note": "No tasks returned"}
                })

                return json.loads(json.dumps({
                    "ok": True,
                    "steps": step + 1,
                    "history": history,
                    "final_state": {"note": "Planner returned no tasks"}
                }))

            # 2. Execute tasks via FS agent
            exec_result = self.agent.handle_plan(tasks)
            exec_result = json.loads(json.dumps(exec_result))  # JSON-safe

            history.append({
                "step": step,
                "plan": plan,
                "execution": exec_result
            })

            observation = exec_result

            # Optional completion flag
            if exec_result.get("ok") and exec_result.get("complete"):
                return json.loads(json.dumps({
                    "ok": True,
                    "steps": step + 1,
                    "history": history,
                    "final_state": exec_result
                }))

        # Max steps reached
        return json.loads(json.dumps({
            "ok": False,
            "steps": self.max_steps,
            "history": history,
            "final_state": {"error": "Max steps reached"}
        }))
