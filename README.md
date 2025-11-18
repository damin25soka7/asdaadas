# MCP Chatbot Integration Project

A comprehensive reference implementation for integrating Model Context Protocol (MCP) into chatbot applications.

## 📖 Overview

This repository demonstrates how to build and integrate MCP (Model Context Protocol) servers with chatbot applications, providing a complete working example with the `searxng-mcp-crawl` server and detailed integration documentation.

### What's Included

- **MCP Server Implementation**: A fully functional MCP server with plugin architecture
- **Plugin Examples**: Multiple tool implementations (search, crawl, AI planning, LLM execution)
- **Integration Guides**: Comprehensive documentation for integrating MCP into any chatbot
- **Architecture Documentation**: Deep dive into MCP architecture and design patterns
- **Multiple Languages**: Documentation in English and Korean

## 🚀 Quick Start

### 1. Start the MCP Server

```bash
cd searxng-mcp-crawl
pip install -r requirements.txt
python server.py
```

The server will start on `http://localhost:32769`

### 2. Test the Server

```bash
# Check health
curl http://localhost:32769/health

# List available tools
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Call a tool
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"search",
      "arguments":{"query":"Python programming","limit":5}
    }
  }'
```

### 3. Integrate with Your Chatbot

See the integration guides for detailed instructions:
- [English Integration Guide](./MCP_INTEGRATION_GUIDE.md)
- [Korean Integration Guide (한국어)](./MCP_INTEGRATION_GUIDE_KR.md)

## 📚 Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| [MCP Integration Guide](./MCP_INTEGRATION_GUIDE.md) | Complete guide to integrating MCP into chatbots (English) |
| [MCP 통합 가이드](./MCP_INTEGRATION_GUIDE_KR.md) | MCP 챗봇 통합 가이드 (한국어) |
| [MCP Architecture](./MCP_ARCHITECTURE.md) | Deep dive into architecture and implementation details |
| [Server README](./searxng-mcp-crawl/README.md) | MCP server documentation and API reference |

### Key Topics Covered

1. **Understanding MCP**
   - What is Model Context Protocol?
   - Why use MCP in chatbots?
   - Key benefits and features

2. **Server Implementation**
   - How MCP servers work
   - Plugin system architecture
   - Creating custom tools/plugins
   - Hot reloading capabilities

3. **Chatbot Integration**
   - Integration patterns (simple, medium, advanced)
   - Tool discovery and execution
   - AI-powered tool planning
   - Error handling and fallbacks

4. **Platform-Specific Integration**
   - Web-based chatbots (JavaScript/TypeScript)
   - Desktop applications (Electron)
   - Mobile apps (React Native)
   - Terminal/CLI chatbots (Python)

5. **Advanced Topics**
   - Performance optimization
   - Security best practices
   - Caching strategies
   - Rate limiting
   - Parallel execution

## 🔧 Available Tools

The MCP server comes with several built-in tools:

### 🔍 search
Search the web using SearXNG with customizable parameters.
```json
{
  "query": "Python programming",
  "limit": 10,
  "category": "general"
}
```

### 🌐 fetch_webpage
Crawl and extract content from webpages.
```json
{
  "urls": ["https://example.com"],
  "limit": 3,
  "max_length": 5000
}
```

### 🧠 tool_planner
AI-powered planning for complex multi-step operations.
```json
{
  "user_query": "Find latest Python news and summarize",
  "planner_llm_config": {
    "url": "https://api.openai.com/v1/chat/completions",
    "apiKey": "sk-...",
    "model": "gpt-4"
  },
  "max_steps": 5
}
```

### 🤖 runLLM
Execute LLM calls as a tool.
```json
{
  "messages": [
    {"role": "user", "content": "Summarize this text: ..."}
  ]
}
```

### 📅 get_current_datetime
Get current date and time with timezone support.
```json
{
  "cities": ["New York", "London", "Tokyo"],
  "format": "iso"
}
```

## 🏗️ Architecture

```
┌─────────────────┐
│   Chatbot UI    │  (Your chatbot application)
└────────┬────────┘
         │ HTTP/SSE
         ▼
┌─────────────────┐
│  MCP Server     │  (searxng-mcp-crawl)
├─────────────────┤
│ Plugin Manager  │  (Dynamic plugin loading)
├─────────────────┤
│   Plugins:      │
│   • search      │  (Web search)
│   • crawl       │  (Web crawling)
│   • planner     │  (AI planning)
│   • runLLM      │  (LLM execution)
│   • datetime    │  (Time/date)
└─────────────────┘
```

## 🎯 Use Cases

### 1. Research Assistant
```
User: "Find the latest research on quantum computing and summarize the key findings"

Plan:
1. search: query="quantum computing research 2024", limit=10
2. fetch_webpage: urls=[top 3 results], max_length=8000
3. runLLM: messages=[system prompt + extracted content]
→ Returns comprehensive summary
```

### 2. News Aggregator
```
User: "What's happening in tech today?"

Plan:
1. search: query="tech news today", category="news", limit=15
2. runLLM: Categorize and summarize news items
→ Returns organized news digest
```

### 3. Content Analyzer
```
User: "Analyze the content of example.com"

Plan:
1. fetch_webpage: urls=["example.com"]
2. runLLM: Analyze content structure, topics, sentiment
→ Returns detailed analysis
```

## 🔌 Creating Custom Plugins

Add your own tools in just a few steps:

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
        return "My custom tool. Params: input_text"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_text": {"type": "string"}
            },
            "required": ["input_text"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        input_text = arguments.get("input_text")
        
        # Your logic here
        result = process(input_text)
        
        return {
            "success": True,
            "result": result
        }
```

The plugin will be automatically discovered and loaded when the server starts!

## 🌍 Multi-Language Support

Documentation is available in multiple languages:

- **English**: [MCP_INTEGRATION_GUIDE.md](./MCP_INTEGRATION_GUIDE.md)
- **한국어 (Korean)**: [MCP_INTEGRATION_GUIDE_KR.md](./MCP_INTEGRATION_GUIDE_KR.md)

## 🔗 Related Projects

- [LobeChat](https://github.com/lobehub/lobe-chat) - Modern chatbot framework with MCP support
- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP specification
- [Anthropic MCP](https://www.anthropic.com/news/model-context-protocol) - MCP announcement and resources

## 📊 Project Structure

```
.
├── MCP_INTEGRATION_GUIDE.md      # Complete integration guide (English)
├── MCP_INTEGRATION_GUIDE_KR.md   # 통합 가이드 (한국어)
├── MCP_ARCHITECTURE.md            # Architecture deep dive
├── searxng-mcp-crawl/             # MCP server implementation
│   ├── server.py                  # Main server
│   ├── plugin_manager.py          # Plugin system
│   ├── plugin_base.py             # Plugin base class
│   ├── config.py                  # Configuration
│   ├── crawler.py                 # Web crawling utilities
│   ├── plugins/                   # Tool plugins
│   │   ├── search_plugin.py
│   │   ├── crawl_plugin.py
│   │   ├── tool_planner_plugin.py
│   │   ├── mcp_aiaccess_plugin.py
│   │   └── datetime_plugin.py
│   ├── requirements.txt           # Python dependencies
│   └── README.md                  # Server documentation
└── LBI-0.35.0-pre17_개조.js      # Example chatbot integration
```

## 🤝 Contributing

Contributions are welcome! Here are some ways you can contribute:

1. **Add New Plugins**: Create tools for specific use cases
2. **Improve Documentation**: Fix typos, add examples, translate to other languages
3. **Report Issues**: Found a bug? Let us know!
4. **Share Integration Examples**: Show how you integrated MCP into your chatbot

## 💡 FAQ

### Q: Can I use this with any chatbot?
**A:** Yes! MCP is designed to be chatbot-agnostic. The documentation includes integration examples for web, desktop, mobile, and terminal chatbots.

### Q: Do I need SearXNG for the search tool?
**A:** No, the search tool has a fallback mock mode for testing without SearXNG.

### Q: How do I add authentication?
**A:** See the [Security Architecture](./MCP_ARCHITECTURE.md#security-architecture) section for examples.

### Q: Can I use multiple MCP servers?
**A:** Yes! You can run multiple MCP servers and connect to different ones for different tools.

### Q: Is this production-ready?
**A:** The code is a reference implementation. For production, add authentication, rate limiting, monitoring, and proper error handling.

## 📝 License

This project is provided as-is for educational and reference purposes.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) specification
- [Anthropic](https://www.anthropic.com/) for pioneering MCP
- [LobeChat](https://github.com/lobehub/lobe-chat) for MCP implementation inspiration
- SearXNG project for the search engine

---

**Built with ❤️ for the AI chatbot community**

For questions, feedback, or discussions, please open an issue on GitHub.
