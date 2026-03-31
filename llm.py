import json
import re
import oci
from config import OciHelper, GENAI_MAX_TOKENS, COMPARTMENT_OCID

GENAI_MODEL_ID  = "google.gemini-2.5-pro"   # change to any model ID or OCID
GENAI_REGION    = "us-ashburn-1"
GENAI_ENDPOINT  = "https://inference.generativeai.us-ashburn-1.oci.oraclecloud.com"
DEBUG          = True   # set False in production

def _debug(label: str, value):
    if DEBUG:
        print(f"\n[llm DEBUG] {label}:\n{value}\n{'─'*50}")
        
class LLM:
    def __init__(self):
        self.client = OciHelper.get_client("generative_ai", region=GENAI_REGION)

    def chat(self, system: str, history: list[dict], tools: list[dict]) -> dict:
        """
        Sends a conversation to OCI GenAI (Generic API format — works for
        Gemini, Llama, OpenAI, Grok models on OCI).
        Returns: {"text": str, "tool_calls": [...]}
        """

        # ── Build system prompt (inject tool schema if tools provided) ──
        full_system = system or ""
        if tools:
            tool_spec = json.dumps(tools, indent=2)
            full_system += f"""

You have access to the following tools:
{tool_spec}

When you need to call a tool, respond ONLY with a JSON block in this exact format and nothing else:
```json
{{
  "tool_calls": [
    {{"name": "tool_name", "parameters": {{"param1": "value1"}}}}
  ]
}}
```

When you have enough information to answer without calling a tool, respond in plain text only — no JSON.
"""

        _debug("system prompt", full_system)
        _debug("history", json.dumps(history, indent=2))
        
        
        # ── Build message list ──
        messages = []

        if full_system:
            sys_content = oci.generative_ai_inference.models.TextContent()
            sys_content.text = full_system
            sys_msg = oci.generative_ai_inference.models.SystemMessage()
            sys_msg.content = [sys_content]
            messages.append(sys_msg)

        for m in history:
            content = oci.generative_ai_inference.models.TextContent()
            content.text = m["content"]

            if m["role"] in ("user", "tool"):
                msg = oci.generative_ai_inference.models.UserMessage()
            else:
                msg = oci.generative_ai_inference.models.AssistantMessage()

            msg.content = [content]
            messages.append(msg)

        # ── Build request ──
        chat_request = oci.generative_ai_inference.models.GenericChatRequest()
        chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
        chat_request.messages = messages
        chat_request.max_tokens = GENAI_MAX_TOKENS
        chat_request.temperature = 0.3    # low = consistent JSON for tool calls
        chat_request.top_p = 0.9
        chat_request.top_k = 1
        chat_request.frequency_penalty = 0
        chat_request.presence_penalty = 0
        chat_request.is_stream = False

        # ── Build chat details ──
        chat_detail = oci.generative_ai_inference.models.ChatDetails()
        chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
            model_id=GENAI_MODEL_ID
        )
        chat_detail.chat_request = chat_request
        chat_detail.compartment_id = COMPARTMENT_OCID

        # ── Call API ──
        _debug("sending request for model", GENAI_MODEL_ID)
        resp = self.client.chat(chat_detail)
        chat_resp = resp.data.chat_response
        _debug("chat_response type", type(chat_resp))
        _debug("chat_response vars", vars(chat_resp))

        # ── Extract text ──
        text = ""
        try:
            text = chat_resp.choices[0].message.content[0].text
            _debug("extracted via choices[0]", text)
        except (AttributeError, IndexError, TypeError):
            _debug("choices extraction failed", str(e))
            text = getattr(chat_resp, "text", "") or ""
            _debug("fallback text", text)

        # ── Parse tool calls from JSON block if present ──
        tool_calls = []
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            _debug("found json block", json_match.group(1))
            try:
                parsed = json.loads(json_match.group(1))
                if "tool_calls" in parsed:
                    # This is a tool invocation from a sub-agent
                    tool_calls = parsed.get("tool_calls", [])
                    text = ""
                    _debug("parsed as tool_calls", tool_calls)
                else:
                    # This is an orchestrator plan or other JSON — leave text intact
                    text = json_match.group(1)
                    _debug("parsed as plain JSON (not tool_calls), keeping as text", text)
            except json.JSONDecodeError as e:
                _debug("json block parse error", str(e))

        _debug("final return", {"text": text[:200], "tool_calls": tool_calls})
        
        return {
            "text": text,
            "tool_calls": tool_calls,
        }