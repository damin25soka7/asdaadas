# SearXNG MCP Crawl Server

An extensible MCP (Model Context Protocol) server with a plugin-based architecture for AI chatbot integration.

## 🚀 Features

- **Pluggable Architecture**: Easily add new tools by creating plugins
- **Dynamic Tool Discovery**: Chatbots can discover available tools at runtime
- **MCP Protocol**: Implements the Model Context Protocol (JSON-RPC 2.0)
- **Multiple Communication Methods**: HTTP POST and Server-Sent Events (SSE)
- **Hot Reloading**: Reload plugins without restarting the server
- **Web Search**: SearXNG integration for web searches
- **Web Crawling**: Fetch and extract content from webpages
- **AI Planning**: Intelligent tool selection and execution planning
- **LLM Integration**: Execute LLM calls as a tool

## 📦 Installation

1. **Install dependencies:**

```bash
cd searxng-mcp-crawl
pip install -r requirements.txt
```

2. **Configure environment (optional):**

Create a `.env` file:

```env
# SearXNG Configuration
SEARXNG_BASE_URL=http://localhost:32768

# Server Configuration
HOST=0.0.0.0
PORT=32769

# Crawler Settings
CONTENT_MAX_LENGTH=10000
SEARCH_RESULT_LIMIT=10
```

3. **Start the server:**

```bash
python server.py
```

The server will start on `http://0.0.0.0:32769` by default.

## 🔌 Available Tools (Plugins)

### 1. **search** - Web Search
Search the web using SearXNG.

**Parameters:**
- `query` (string, required): Search query
- `limit` (integer, optional): Number of results (default: 10, max: 50)
- `category` (string, optional): Search category (default: "general")
- `language` (string, optional): Language filter (default: "auto")
- `time_range` (string, optional): Time filter (e.g., "day", "week", "month")
- `safe_search` (integer, optional): Safe search level (default: 1)

**Example:**
```json
{
  "name": "search",
  "arguments": {
    "query": "Model Context Protocol",
    "limit": 10,
    "category": "general"
  }
}
```

### 2. **fetch_webpage** - Web Crawling
Fetch and extract content from webpages.

**Parameters:**
- `urls` (array, required): List of URLs to fetch
- `limit` (integer, optional): Maximum number of URLs to process (default: 5)
- `max_length` (integer, optional): Maximum content length per page (default: 10000)
- `timeout` (integer, optional): Request timeout in seconds (default: 30)
- `auto_chunk` (boolean, optional): Automatically chunk large content (default: false)

**Example:**
```json
{
  "name": "fetch_webpage",
  "arguments": {
    "urls": ["https://example.com"],
    "limit": 3,
    "max_length": 5000
  }
}
```

### 3. **tool_planner** - AI-Powered Planning
Create intelligent execution plans using LLM.

**Parameters:**
- `user_query` (string, required): User's query to plan for
- `planner_llm_config` (object, required): LLM configuration
  - `url` (string): LLM API endpoint
  - `apiKey` (string): API key
  - `model` (string): Model name
- `max_steps` (integer, optional): Maximum plan steps (default: 5)
- `complexity` (string, optional): Planning complexity ("simple", "moderate", "detailed")
- `preferred_tools` (array, optional): Tools to prefer in the plan
- `avoid_tools` (array, optional): Tools to avoid in the plan

**Example:**
```json
{
  "name": "tool_planner",
  "arguments": {
    "user_query": "Find the latest Python news and summarize",
    "planner_llm_config": {
      "url": "https://api.openai.com/v1/chat/completions",
      "apiKey": "sk-...",
      "model": "gpt-4"
    },
    "max_steps": 3
  }
}
```

### 4. **runLLM** - LLM Execution
Execute LLM calls directly.

**Parameters:**
- `messages` (array, required): Chat messages
- Additional parameters depend on the LLM provider configuration

**Example:**
```json
{
  "name": "runLLM",
  "arguments": {
    "messages": [
      {"role": "user", "content": "Summarize this text: ..."}
    ]
  }
}
```

### 5. **get_current_datetime** - Date/Time
Get current date and time information.

**Parameters:**
- `cities` (array, optional): List of cities for timezone info
- `format` (string, optional): Output format

**Example:**
```json
{
  "name": "get_current_datetime",
  "arguments": {
    "cities": ["New York", "London", "Tokyo"],
    "format": "iso"
  }
}
```

## 📡 MCP Protocol

### Initialize Connection

```http
POST / HTTP/1.1
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "my-client",
      "version": "1.0.0"
    }
  }
}
```

### List Available Tools

```http
POST / HTTP/1.1
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "search",
        "description": "Search web via SearXNG...",
        "inputSchema": {...}
      },
      ...
    ]
  }
}
```

### Call a Tool

```http
POST / HTTP/1.1
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "query": "Python MCP",
      "limit": 10
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": true, \"results\": [...]}"
      }
    ]
  }
}
```

### Server-Sent Events (SSE)

For streaming responses:

```http
GET / HTTP/1.1
Accept: text/event-stream
```

## 🔧 Creating Custom Plugins

### Step 1: Create Plugin File

Create a new file in the `plugins/` directory:

```python
# plugins/my_plugin.py
from plugin_base import MCPPlugin
from typing import Dict, Any

class MyPlugin(MCPPlugin):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "My custom tool. Params: param1, param2."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer", "default": 10}
            },
            "required": ["param1"]
        }
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def author(self) -> str:
        return "Your Name"
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        param1 = arguments.get("param1")
        param2 = arguments.get("param2", 10)
        
        try:
            # Your tool logic here
            result = f"Processed {param1} with {param2}"
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### Step 2: Test Your Plugin

The plugin will be automatically loaded when the server starts. Test it:

```bash
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "my_tool",
      "arguments": {
        "param1": "test",
        "param2": 20
      }
    }
  }'
```

### Step 3: Hot Reload (Optional)

Reload plugins without restarting:

```bash
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "plugins/reload",
    "params": {}
  }'
```

## 🏗️ Architecture

```
server.py
├── PluginManager (plugin_manager.py)
│   ├── Load plugins from plugins/
│   ├── List available tools
│   └── Execute plugin methods
│
└── HTTP/SSE Endpoints
    ├── POST / - Direct JSON-RPC calls
    ├── GET / - SSE connection
    ├── POST /message/{id} - SSE messages
    └── GET /health - Health check

plugins/
├── plugin_base.py - Base class for all plugins
├── search_plugin.py - Web search tool
├── crawl_plugin.py - Web crawler tool
├── tool_planner_plugin.py - AI planning tool
├── mcp_aiaccess_plugin.py - LLM execution tool
└── datetime_plugin.py - Date/time tool

crawler.py - Web crawling utilities
config.py - Server configuration
```

## 🧪 Testing

### Test Server Health

```bash
curl http://localhost:32769/health
```

Response:
```json
{
  "status": "ok",
  "plugins": 5,
  "available_tools": ["search", "fetch_webpage", "tool_planner", "runLLM", "get_current_datetime"]
}
```

### Test Tool Discovery

```bash
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Test Search Tool

```bash
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "query": "Python programming",
        "limit": 5
      }
    }
  }'
```

## 🔒 Security Considerations

- **Input Validation**: All plugins validate their inputs
- **Rate Limiting**: Consider implementing rate limiting in production
- **Authentication**: Add authentication for production deployments
- **HTTPS**: Use HTTPS in production environments
- **Secrets Management**: Use environment variables for API keys
- **CORS**: Configure CORS appropriately for web clients

## 📚 Integration Examples

### JavaScript/TypeScript

See [MCP_INTEGRATION_GUIDE.md](../MCP_INTEGRATION_GUIDE.md) for complete examples.

### Python

```python
import requests
import json

class MCPClient:
    def __init__(self, server_url):
        self.server_url = server_url
    
    def call_tool(self, tool_name, arguments):
        response = requests.post(self.server_url, json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {
                'name': tool_name,
                'arguments': arguments
            }
        })
        return json.loads(response.json()['result']['content'][0]['text'])

# Usage
client = MCPClient('http://localhost:32769')
result = client.call_tool('search', {'query': 'Python', 'limit': 5})
print(result)
```

## 🛠️ Development

### Requirements

- Python 3.8+
- starlette
- uvicorn
- httpx
- beautifulsoup4
- html5lib
- python-dotenv

### Running in Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server with auto-reload
uvicorn server:app --reload --host 0.0.0.0 --port 32769
```

## 📄 License

This project is part of the asdaadas repository.

## 🤝 Contributing

To add a new plugin:

1. Create a new file in `plugins/` directory
2. Inherit from `MCPPlugin` base class
3. Implement required methods
4. Test your plugin
5. Submit a pull request

## 📖 Additional Documentation

- [Complete MCP Integration Guide](../MCP_INTEGRATION_GUIDE.md) (English)
- [MCP 통합 가이드](../MCP_INTEGRATION_GUIDE_KR.md) (Korean)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)

## 🆘 Troubleshooting

### Server won't start
- Check if port 32769 is already in use
- Verify all dependencies are installed
- Check `config.py` for correct settings

### SearXNG connection fails
- Verify SearXNG is running on the configured URL
- Check `SEARXNG_BASE_URL` in `.env`
- The server will fall back to mock results if SearXNG is unavailable

### Plugin not loading
- Ensure plugin file is in `plugins/` directory
- Check that class inherits from `MCPPlugin`
- Look for syntax errors in plugin code
- Check server logs for error messages

## 📞 Support

For questions or issues, please open an issue on the GitHub repository.

---

Built with ❤️ using Python, Starlette, and the Model Context Protocol
