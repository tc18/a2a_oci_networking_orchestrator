import json
from llm import LLM

class BaseAgent:
    """
    A ReAct-style agent loop:
Send question + tools to LLM
If LLM calls a tool → run it → feed result back
Repeat until LLM returns a plain text answer
    """
    name: str = "base"
    system_prompt: str = "You are a helpful OCI assistant."
    tools: list[dict] = []
    tool_map: dict = {}

    def __init__(self):
        self.llm = LLM()
        
    def _filter_tools(self, question: str) -> list[dict]:
        """Only send tools whose name or description matches keywords in the question."""
        keywords = question.lower().split()
        relevant = []
        for tool in self.tools:
            tool_text = (tool["name"] + tool["description"]).lower()
            if any(kw in tool_text for kw in keywords):
                relevant.append(tool)
        # Always return at least 2 tools so the agent has something to work with
        return relevant if len(relevant) >= 2 else self.tools[:3]

    def run(self, question: str, context: str = "") -> str:
        history = [{"role": "user", "content": f"{context}\n\n{question}".strip()}]
        max_steps = 10

        for step in range(max_steps):
            response = self.llm.chat(
                system=self.system_prompt,
                history=history,
                
                # tools=self.tools,
                tools=self._filter_tools(question) # this will only send relevant tools to LLM.
            )

            # No tool calls → final answer
            if not response["tool_calls"]:
                return response["text"]

            # Append assistant's tool-call turn
            history.append({"role": "chatbot", "content": response["text"] or "(calling tools)"})

            # Execute each tool call and collect results
            tool_results = []
            for tc in response["tool_calls"]:
                fn = self.tool_map.get(tc["name"])
                if fn is None:
                    result = {"error": f"Tool '{tc['name']}' not found"}
                else:
                    try:
                        result = fn(**tc["parameters"])
                    except Exception as e:
                        result = {"error": str(e)}

                print(f"  [{self.name}] called {tc['name']}({tc['parameters']}) → {str(result)[:120]}")
                tool_results.append({
                    "call": tc["name"],
                    "outputs": result,
                })

            # Feed tool results back as a user message (Cohere format)
            history.append({
                "role": "tool",
                "content": json.dumps(tool_results),
            })

        return "Max steps reached without a final answer."