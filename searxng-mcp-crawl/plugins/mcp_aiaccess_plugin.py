from plugin_base import MCPPlugin
from typing import Dict, Any, List
import httpx
import json


class MCPAIAccessPlugin(MCPPlugin):
    """
    Simple AI Access Plugin - Direct LLM call

    Provides runLLM tool for calling custom LLM APIs.
    Users provide API config (url, apiKey, model) in each call.
    """

    @property
    def name(self) -> str:
        return "runLLM"

    @property
    def description(self) -> str:
        return "Execute LLM API call. Params: url, apiKey, model, messages."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "apiKey": {"type": "string"},
                "model": {"type": "string"},
                "messages": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["url", "apiKey", "model", "messages"],
        }

    @property
    def version(self) -> str:
        return "1.2.0"

    @property
    def author(self) -> str:
        return "damin25soka7"

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LLM API call

        Returns MCP-compatible response (NOT RisuAI plugin format)
        """
        # Extract and validate parameters
        url = arguments.get("url", "").strip()
        api_key = arguments.get("apiKey", "").strip()
        model = arguments.get("model", "").strip()
        messages = arguments.get("messages", [])

        # Validation
        if not url:
            return {"success": False, "message": "Missing required parameter: url"}
        if not api_key:
            return {"success": False, "message": "Missing required parameter: apiKey"}
        if not model:
            return {"success": False, "message": "Missing required parameter: model"}
        if not messages or not isinstance(messages, list):
            return {
                "success": False,
                "message": "Invalid messages: must be non-empty array",
            }

        # Validate message structure
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                return {"success": False, "message": f"Message {i} must be an object"}
            if "role" not in msg or "content" not in msg:
                return {
                    "success": False,
                    "message": f"Message {i} missing role or content",
                }
            if msg["role"] not in ["user", "assistant", "system"]:
                return {
                    "success": False,
                    "message": f'Message {i} invalid role: {msg["role"]}',
                }

        print(f"\n{'='*60}")
        print(f"🤖 runLLM")
        print(f"Model: {model}")
        print(f"URL: {url[:60]}...")
        print(f"Messages: {len(messages)}")
        print(f"{'='*60}")

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000,
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                # Parse OpenAI-compatible response
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    print(f"✅ Success ({len(content)} chars)")
                    print(f"{'='*60}\n")

                    # Return simple object (NOT plugin format)
                    return {
                        "success": True,
                        "message": content,
                        "model_used": model,
                        "tokens": data.get("usage", {}),
                    }

                elif "content" in data:
                    content = data["content"]
                    print(f"✅ Success ({len(content)} chars)")
                    print(f"{'='*60}\n")

                    return {"success": True, "message": content, "model_used": model}

                else:
                    raise ValueError(
                        f"Unexpected API response format: {list(data.keys())}"
                    )

        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:500]
            error_msg = f"HTTP {e.response.status_code}: {error_text}"
            print(f"❌ API Error: {error_msg}")
            print(f"{'='*60}\n")

            return {
                "success": False,
                "message": error_msg,
                "status_code": e.response.status_code,
            }

        except httpx.TimeoutException:
            error_msg = "Request timeout (120s)"
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")

            return {"success": False, "message": error_msg}

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌ Error: {error_msg}")
            print(f"{'='*60}\n")

            return {"success": False, "message": error_msg}
