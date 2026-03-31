from llm import LLM

llm = LLM()

# Test 1: plain conversation
resp = llm.chat(
    system="You are a helpful OCI assistant.",
    history=[{"role": "user", "content": "Say hello and tell me what model you are."}],
    tools=[],
)
print("=== Plain response ===")
print(resp["text"])

# Test 2: tool call
resp = llm.chat(
    system="You are an OCI network assistant.",
    history=[{"role": "user", "content": "List all VCNs in the tenancy."}],
    tools=[{
        "name": "list_vcns",
        "description": "List all VCNs in a compartment.",
        "parameters": {
            "compartment_id": {"type": "str", "description": "Compartment OCID", "required": False}
        }
    }],
)
print("\n=== Tool call response ===")
print("text:", resp["text"])
print("tool_calls:", resp["tool_calls"])