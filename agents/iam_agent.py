from agents.base import BaseAgent
from tools.iam import TOOLS, TOOL_MAP

class IamAgent(BaseAgent):
    name = "iam"
    system_prompt = (
        "You are an OCI IAM specialist. "
        "Answer questions about policies, groups, users, and compartments"
        "by calling the available tools to inspect the real environment."
    )
    tools = TOOLS
    tool_map = TOOL_MAP