from llm import LLM
from agents.network_agent import NetworkAgent
from agents.compute_agent import ComputeAgent
from agents.iam_agent import IamAgent

SYSTEM_PROMPT = """
You are the OCI assistant orchestrator. Given a user question, decide which
specialist agents to call and in what order. You must respond ONLY with a JSON
plan like:

{
  "steps": [
    {"agent": "network", "question": "...sub-question for network agent..."},
    {"agent": "compute", "question": "...sub-question for compute agent..."}
  ],
  "final_synthesis": true
}

Valid agent names: network, compute, iam.
If the question is simple and only needs one agent, return one step.
Do NOT answer the question yourself — only plan.
"""

class Orchestrator:
    def __init__(self):
        self.llm = LLM()
        self.agents = {
            "network": NetworkAgent(),
            "compute": ComputeAgent(),
            "iam": IamAgent(),
        }

    def run(self, user_question: str) -> str:
        import json, re

        # Step 1: Ask LLM to produce an execution plan
        plan_resp = self.llm.chat(
            system=SYSTEM_PROMPT,
            history=[{"role": "user", "content": user_question}],
            tools=[],
        )

        # Extract JSON from response
        raw = plan_resp["text"]
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return f"Could not parse plan from orchestrator:\n{raw}"

        plan = json.loads(match.group())
        steps = plan.get("steps", [])

        # Step 2: Execute each sub-agent in order, accumulate context
        accumulated_context = ""
        results = []

        for step in steps:
            agent_name = step["agent"]
            sub_question = step["question"]
            agent = self.agents.get(agent_name)

            if agent is None:
                results.append(f"[{agent_name}] Unknown agent.")
                continue

            print(f"\n→ Delegating to [{agent_name}]: {sub_question}")
            answer = agent.run(sub_question, context=accumulated_context)
            results.append(f"[{agent_name}] {answer}")
            accumulated_context += f"\n{agent_name} findings:\n{answer}\n"

        # Step 3: Synthesise final answer
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