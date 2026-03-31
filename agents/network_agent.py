from agents.base import BaseAgent
from tools.network import TOOLS, TOOL_MAP, slim_tools

class NetworkAgent(BaseAgent):
    name = "network"
    system_prompt = (
        "You are an OCI network specialist. "
        "When asked about network paths, VCNs, subnets, route tables, DRGs, "
        "security lists, or NSGs — use the available tools to inspect the real "
        "OCI environment and give a clear, step-by-step answer.\n\n "
        "IMPORTANT: OCI API calls always require compartment OCIDs, never names. "
        "If you only have a compartment name, call list_compartments first to get "
        "the OCID, then use that OCID in subsequent calls.\n\n"
        "When tracing a route between two IPs, check: source subnet route table → "
        "DRG attachment → DRG route table → destination VCN route table → "
        "security lists/NSGs at destination."
    )
    tools = slim_tools(TOOLS)
    tool_map = TOOL_MAP