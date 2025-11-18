# MCP (Model Context Protocol) Integration Guide

## 📚 Table of Contents

1. [Overview](#overview)
2. [What is MCP?](#what-is-mcp)
3. [Architecture](#architecture)
4. [How MCP Servers Work](#how-mcp-servers-work)
5. [Plugin System](#plugin-system)
6. [Creating Custom MCP Tools](#creating-custom-mcp-tools)
7. [Integrating MCP into Chatbots](#integrating-mcp-into-chatbots)
8. [Example Implementation](#example-implementation)
9. [Porting to Other Chatbots](#porting-to-other-chatbots)
10. [Best Practices](#best-practices)

---

## Overview

This guide explains how to integrate Model Context Protocol (MCP) into chatbot applications, using the `searxng-mcp-crawl` server as a reference implementation. MCP provides a standardized way for AI assistants to interact with external tools and data sources.

## What is MCP?

**Model Context Protocol (MCP)** is a protocol that enables AI models to:
- Discover available tools dynamically
- Call external functions with structured parameters
- Receive structured responses
- Maintain context across multiple tool calls

### Key Benefits:
- **Extensibility**: Easy to add new capabilities via plugins
- **Standardization**: Consistent interface for tool integration
- **Modularity**: Tools can be developed and deployed independently
- **Dynamic Discovery**: Chatbots can discover available tools at runtime

---

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Chatbot UI    │
│  (e.g., LBI)    │
└────────┬────────┘
         │ HTTP/SSE
         ▼
┌─────────────────┐
│  MCP Server     │
│  (server.py)    │
├─────────────────┤
│ Plugin Manager  │
├─────────────────┤
│   Plugins:      │
│   • search      │
│   • crawl       │
│   • runLLM      │
│   • planner     │
│   • datetime    │
└─────────────────┘
```

### Communication Flow

1. **Initialize**: Chatbot connects to MCP server and gets capabilities
2. **Tool Discovery**: Chatbot requests list of available tools
3. **Tool Execution**: Chatbot calls specific tools with parameters
4. **Response**: MCP server executes plugin and returns structured result

---

## How MCP Servers Work

### 1. Server Setup (`server.py`)

The MCP server is built with Starlette and supports two communication methods:

#### HTTP POST (Simple Request/Response)
```python
POST / HTTP/1.1
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
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

#### Server-Sent Events (SSE) for Streaming
```python
GET / HTTP/1.1
Accept: text/event-stream
```

### 2. Core MCP Methods

| Method | Purpose | Parameters |
|--------|---------|------------|
| `initialize` | Establish connection | `protocolVersion` |
| `notifications/initialized` | Confirm initialization | None |
| `tools/list` | Get available tools | None |
| `tools/call` | Execute a tool | `name`, `arguments` |
| `ping` | Health check | None |

### 3. Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": true, \"data\": ...}"
      }
    ]
  }
}
```

---

## Plugin System

### Plugin Architecture

The MCP server uses a plugin-based architecture where each tool is a separate plugin:

```
plugins/
├── search_plugin.py       # Web search tool
├── crawl_plugin.py        # Webpage crawler
├── tool_planner_plugin.py # AI-powered planning
├── datetime_plugin.py     # Date/time utilities
└── mcp_aiaccess_plugin.py # LLM execution
```

### Plugin Base Class

Every plugin inherits from `MCPPlugin`:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class MCPPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (unique identifier)"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for AI"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON Schema for input validation"""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool logic"""
        pass
    
    @property
    def version(self) -> str:
        return "1.0.0"
```

### Plugin Manager

The `PluginManager` class:
- Auto-discovers plugins in the `plugins/` directory
- Loads plugins dynamically at startup
- Provides plugin listing and execution
- Supports hot-reloading

```python
class PluginManager:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, MCPPlugin] = {}
        self.load_plugins()
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins as MCP tools"""
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "inputSchema": plugin.input_schema
            }
            for plugin in self.plugins.values()
        ]
    
    async def execute_plugin(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a plugin by name"""
        if name not in self.plugins:
            return {"error": f"Tool '{name}' not found"}
        
        plugin = self.plugins[name]
        return await plugin.execute(arguments)
```

---

## Creating Custom MCP Tools

### Example: Simple Calculator Plugin

```python
from plugin_base import MCPPlugin
from typing import Dict, Any

class CalculatorPlugin(MCPPlugin):
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform basic math operations. Params: operation (add/subtract/multiply/divide), a, b"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"]
                },
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        operation = arguments.get("operation")
        a = arguments.get("a")
        b = arguments.get("b")
        
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return {"success": False, "error": "Division by zero"}
                result = a / b
            else:
                return {"success": False, "error": "Invalid operation"}
            
            return {
                "success": True,
                "operation": operation,
                "a": a,
                "b": b,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### Plugin Development Checklist

- ✅ Inherit from `MCPPlugin`
- ✅ Implement all required properties (`name`, `description`, `input_schema`)
- ✅ Implement `execute()` method
- ✅ Use async/await for I/O operations
- ✅ Return structured JSON responses
- ✅ Include error handling
- ✅ Add proper logging
- ✅ Validate input parameters
- ✅ Keep plugins focused and single-purpose

---

## Integrating MCP into Chatbots

### Step 1: Initialize MCP Connection

```javascript
// Example: JavaScript/TypeScript chatbot client
class MCPClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.tools = [];
    }
    
    async initialize() {
        // Send initialize request
        const response = await fetch(this.serverUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: 1,
                method: 'initialize',
                params: {
                    protocolVersion: '2024-11-05',
                    capabilities: {},
                    clientInfo: {
                        name: 'my-chatbot',
                        version: '1.0.0'
                    }
                }
            })
        });
        
        return await response.json();
    }
    
    async listTools() {
        const response = await fetch(this.serverUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: 2,
                method: 'tools/list',
                params: {}
            })
        });
        
        const data = await response.json();
        this.tools = data.result.tools;
        return this.tools;
    }
    
    async callTool(toolName, arguments) {
        const response = await fetch(this.serverUrl, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: Date.now(),
                method: 'tools/call',
                params: {
                    name: toolName,
                    arguments: arguments
                }
            })
        });
        
        const data = await response.json();
        return JSON.parse(data.result.content[0].text);
    }
}
```

### Step 2: Use Tools in Conversation

```javascript
// Initialize MCP client
const mcp = new MCPClient('http://localhost:32769');
await mcp.initialize();
await mcp.listTools();

// Use search tool
const searchResult = await mcp.callTool('search', {
    query: 'Model Context Protocol',
    limit: 10
});

// Use crawl tool
const crawlResult = await mcp.callTool('fetch_webpage', {
    urls: ['https://example.com'],
    limit: 1
});

// Use LLM tool
const llmResult = await mcp.callTool('runLLM', {
    messages: [
        {role: 'user', content: 'Summarize this: ...'}
    ]
});
```

### Step 3: Integrate with AI Model

```javascript
// Example: Integrating MCP tools with AI conversation
async function handleUserMessage(userMessage, conversationHistory) {
    // 1. Add user message to history
    conversationHistory.push({
        role: 'user',
        content: userMessage
    });
    
    // 2. Get list of available tools
    const tools = await mcp.listTools();
    
    // 3. Send to AI with tool descriptions
    const aiResponse = await callAI({
        messages: conversationHistory,
        tools: tools,
        tool_choice: 'auto'
    });
    
    // 4. If AI wants to use a tool
    if (aiResponse.tool_calls) {
        for (const toolCall of aiResponse.tool_calls) {
            const toolResult = await mcp.callTool(
                toolCall.function.name,
                JSON.parse(toolCall.function.arguments)
            );
            
            // Add tool result to conversation
            conversationHistory.push({
                role: 'tool',
                name: toolCall.function.name,
                content: JSON.stringify(toolResult)
            });
        }
        
        // Get final AI response with tool results
        return await callAI({
            messages: conversationHistory
        });
    }
    
    return aiResponse;
}
```

---

## Example Implementation

### Complete Integration Example

This example shows how the `LBI` chatbot integrates with the MCP server:

```javascript
// LBI Chatbot MCP Integration
class LBIChatbot {
    constructor(config) {
        this.mcpServerUrl = config.mcpServerUrl || 'http://localhost:32769';
        this.mcpClient = null;
        this.availableTools = [];
    }
    
    async initialize() {
        // Initialize MCP connection
        this.mcpClient = new MCPClient(this.mcpServerUrl);
        await this.mcpClient.initialize();
        
        // Discover available tools
        this.availableTools = await this.mcpClient.listTools();
        console.log(`Discovered ${this.availableTools.length} MCP tools`);
    }
    
    async processMessage(userInput) {
        // 1. Determine if tools are needed
        const needsTools = this.analyzeNeedsTools(userInput);
        
        if (!needsTools) {
            return await this.generateResponse(userInput);
        }
        
        // 2. Use AI to select and plan tool usage
        const planResult = await this.mcpClient.callTool('tool_planner', {
            user_query: userInput,
            planner_llm_config: {
                url: this.aiProviderUrl,
                apiKey: this.aiApiKey,
                model: this.aiModel
            },
            max_steps: 5
        });
        
        if (!planResult.success) {
            return await this.generateResponse(userInput);
        }
        
        // 3. Execute plan steps
        const executionResults = [];
        for (const step of planResult.plan) {
            const result = await this.mcpClient.callTool(
                step.tool,
                step.arguments
            );
            executionResults.push({
                step: step.step,
                tool: step.tool,
                result: result
            });
        }
        
        // 4. Generate final response with tool results
        return await this.generateResponseWithContext(
            userInput,
            executionResults
        );
    }
    
    analyzeNeedsTools(input) {
        // Check if user query requires external tools
        const toolKeywords = [
            'search', 'find', 'lookup', 'what is', 'who is',
            'fetch', 'get', 'retrieve', 'download',
            'current', 'latest', 'now', 'today'
        ];
        
        const lowerInput = input.toLowerCase();
        return toolKeywords.some(keyword => lowerInput.includes(keyword));
    }
    
    async generateResponseWithContext(input, toolResults) {
        // Combine tool results into context
        const context = toolResults.map(tr => 
            `Tool: ${tr.tool}\nResult: ${JSON.stringify(tr.result, null, 2)}`
        ).join('\n\n');
        
        // Generate AI response with tool context
        return await this.callAI({
            messages: [
                {
                    role: 'system',
                    content: 'You are a helpful assistant. Use the tool results provided to answer accurately.'
                },
                {
                    role: 'user',
                    content: `Context from tools:\n${context}\n\nUser question: ${input}`
                }
            ]
        });
    }
}
```

---

## Porting to Other Chatbots

### Can This Be Ported to Other Chatbots?

**Yes!** The MCP architecture is designed to be chatbot-agnostic. Here's how to port it:

### For Web-Based Chatbots

1. **Add MCP Client Library**
   - Implement HTTP client for MCP protocol
   - Support both POST and SSE communication methods
   - Handle JSON-RPC 2.0 format

2. **Tool Discovery at Runtime**
   ```javascript
   // On chatbot initialization
   const tools = await mcp.listTools();
   // Store tools for later use
   ```

3. **Integrate Tool Calls**
   - Detect when AI model wants to call a tool
   - Execute tool via MCP
   - Feed results back to AI

### For Desktop Chatbots (e.g., Electron)

```javascript
// In main process
const { app } = require('electron');
const MCPClient = require('./mcp-client');

let mcpClient;

app.on('ready', async () => {
    mcpClient = new MCPClient('http://localhost:32769');
    await mcpClient.initialize();
    
    // Expose to renderer process
    ipcMain.handle('mcp-call-tool', async (event, toolName, args) => {
        return await mcpClient.callTool(toolName, args);
    });
});
```

### For Mobile Apps (React Native)

```javascript
import axios from 'axios';

class MCPMobileClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
    }
    
    async callTool(toolName, arguments) {
        try {
            const response = await axios.post(this.serverUrl, {
                jsonrpc: '2.0',
                id: Date.now(),
                method: 'tools/call',
                params: { name: toolName, arguments }
            });
            
            return JSON.parse(response.data.result.content[0].text);
        } catch (error) {
            console.error('MCP call failed:', error);
            return { success: false, error: error.message };
        }
    }
}
```

### For Terminal/CLI Chatbots (Python)

```python
import requests
import json

class MCPTerminalClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.session = requests.Session()
    
    def initialize(self):
        response = self.session.post(self.server_url, json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'terminal-bot', 'version': '1.0'}
            }
        })
        return response.json()
    
    def call_tool(self, tool_name, arguments):
        response = self.session.post(self.server_url, json={
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {'name': tool_name, 'arguments': arguments}
        })
        
        data = response.json()
        return json.loads(data['result']['content'][0]['text'])

# Usage
mcp = MCPTerminalClient('http://localhost:32769')
mcp.initialize()

# Search example
result = mcp.call_tool('search', {'query': 'Python', 'limit': 5})
print(result)
```

### Integration Checklist for Any Chatbot

- ✅ HTTP client for JSON-RPC 2.0 protocol
- ✅ Initialize connection on startup
- ✅ Discover tools dynamically
- ✅ Convert tool schemas to AI model format
- ✅ Execute tools when AI requests them
- ✅ Handle tool errors gracefully
- ✅ Pass tool results back to AI
- ✅ Support streaming (optional, for long operations)

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Tool logic here
        result = await self.perform_operation(arguments)
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Internal error: {str(e)}"}
```

### 2. Input Validation

Validate all inputs according to schema:

```python
def validate_arguments(self, arguments):
    query = arguments.get("query", "").strip()
    if not query:
        raise ValueError("Query parameter is required")
    
    limit = arguments.get("limit", 10)
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
```

### 3. Logging

Add comprehensive logging:

```python
print(f"\n🔍 {self.name}")
print(f"   Query: {query}")
print(f"   Parameters: {params}")
print(f"   ✅ Success: {len(results)} results")
```

### 4. Performance

- Use async/await for I/O operations
- Implement caching where appropriate
- Set reasonable timeouts
- Limit response sizes

### 5. Security

- Validate all inputs
- Sanitize user-provided data
- Use environment variables for secrets
- Implement rate limiting
- Use HTTPS in production

### 6. Documentation

Document each tool clearly:

```python
@property
def description(self) -> str:
    return """
    Search web via SearXNG.
    
    Parameters:
    - query (required): Search query string
    - limit (optional, default=10): Number of results (1-50)
    - category (optional, default='general'): Search category
    
    Returns:
    {
        "success": bool,
        "results": [...],
        "results_count": int
    }
    """
```

### 7. Testing

Test plugins thoroughly:

```python
# test_plugin.py
import pytest
from plugins.search_plugin import SearchPlugin

@pytest.mark.asyncio
async def test_search_basic():
    plugin = SearchPlugin()
    result = await plugin.execute({
        "query": "test query",
        "limit": 5
    })
    
    assert result["success"] == True
    assert "results" in result
    assert len(result["results"]) <= 5

@pytest.mark.asyncio
async def test_search_validation():
    plugin = SearchPlugin()
    result = await plugin.execute({"query": ""})
    
    assert result["success"] == False
    assert "error" in result
```

---

## Conclusion

The MCP (Model Context Protocol) provides a powerful, extensible way to add capabilities to chatbots:

- **Standardized**: Uses JSON-RPC 2.0 protocol
- **Modular**: Plugin-based architecture
- **Dynamic**: Tools can be added without restarting
- **Universal**: Can be integrated into any chatbot platform
- **Scalable**: Supports multiple tools and complex workflows

The `searxng-mcp-crawl` server demonstrates a complete implementation that can serve as a template for your own MCP-enabled applications.

For more examples and reference implementations, see:
- `server.py` - MCP server implementation
- `plugin_manager.py` - Plugin loading and management
- `plugins/` - Example tool implementations
- `LBI-0.35.0-pre17_개조.js` - Chatbot integration example

---

## Additional Resources

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Anthropic MCP Documentation](https://www.anthropic.com/news/model-context-protocol)
- [LobeChat MCP Integration](https://github.com/lobehub/lobe-chat)

---

*Last Updated: November 2024*
