from agents.base import BaseAgent
from tools.compute import TOOLS, TOOL_MAP

class ComputeAgent(BaseAgent):
    name = "compute"
    system_prompt = (
        "You are an OCI compute specialist. "
        "Answer questions about instances, shapes, VNICs, and IP addresses "
        "by calling the available tools to inspect the real environment."
    )
    tools = TOOLS
    tool_map = TOOL_MAP