import json
import re
from llm import LLM
from agents.network_agent import NetworkAgent
from agents.compute_agent import ComputeAgent
from agents.iam_agent import IamAgent

SYSTEM_PROMPT = """
You are the OCI assistant orchestrator. Given a user question, decide which
specialist agents to call and in what order.

You must respond ONLY with a valid JSON object — no explanation, no markdown, no code fences.
Just raw JSON like this:

{
  "steps": [
    {"agent": "network", "question": "...sub-question for network agent..."}
  ],
  "final_synthesis": false
}

Valid agent names: network, compute, iam.
If the question is simple and needs only one agent, return exactly one step.
Do NOT answer the question yourself — only output the JSON plan.
"""


def extract_json(text: str) -> dict | None:
    """
    Tries multiple strategies to extract a JSON object from LLM response text.
    """
    # Strategy 1: inside ```json ... ``` block
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 2: inside ``` ... ``` block (no language tag)
    m = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: first { ... } in the raw text
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return None


class Orchestrator:
    def __init__(self):
        self.llm = LLM()
        self.agents = {
            "network": NetworkAgent(),
            "compute": ComputeAgent(),
            "iam": IamAgent(),
        }

    def run(self, user_question: str) -> str:

        # ── Step 1: Ask LLM to produce an execution plan ──
        plan_resp = self.llm.chat(
            system=SYSTEM_PROMPT,
            history=[{"role": "user", "content": user_question}],
            tools=[],
        )

        raw = plan_resp["text"]
        print(f"\n[orchestrator] raw plan response:\n{raw}\n")

        plan = extract_json(raw)
        if not plan:
            return f"Could not parse plan from orchestrator. Raw response:\n{raw}"

        steps = plan.get("steps", [])
        if not steps:
            return f"Orchestrator returned no steps. Plan was:\n{plan}"

        # ── Step 2: Execute each sub-agent in order ──
        accumulated_context = ""
        results = []

        for step in steps:
            agent_name = step.get("agent", "")
            sub_question = step.get("question", user_question)
            agent = self.agents.get(agent_name)

            if agent is None:
                results.append(f"[{agent_name}] Unknown agent.")
                continue

            print(f"\n→ Delegating to [{agent_name}]: {sub_question}")
            answer = agent.run(sub_question, context=accumulated_context)
            results.append(f"[{agent_name}] {answer}")
            accumulated_context += f"\n{agent_name} findings:\n{answer}\n"

        # ── Step 3: Synthesise final answer if multiple agents were used ──
        if plan.get("final_synthesis") and len(results) > 1:
            synthesis_prompt = (
                f"Original question: {user_question}\n\n"
                f"Findings from specialist agents:\n{accumulated_context}\n\n"
                "Please synthesise a clear, concise final answer for the user."
            )
            final = self.llm.chat(
                system="You are a helpful OCI assistant summarising findings.",
                history=[{"role": "user", "content": synthesis_prompt}],
                tools=[],
            )
            return final["text"]

        return "\n\n".join(results)