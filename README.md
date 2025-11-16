# RisuAI MCP SearXNG Bridge

This repository contains a bridge plugin system that connects **RisuAI** with an **MCP (Model Context Protocol) server** powered by **SearXNG** for advanced web search and crawling capabilities.

## 📦 Components

### 1. MCP Server (`searxng-mcp-crawl/`)
A Python-based MCP server with a plugin architecture that provides:
- **Web Search** via SearXNG
- **Webpage Crawling** and content extraction
- **DateTime** utilities for timezone-aware operations
- **LLM Integration** for external API calls
- **Tool Planning** for intelligent task decomposition

### 2. RisuAI Bridge Plugin (`risuai-mcp-bridge.js`)
A JavaScript plugin for RisuAI that connects to the MCP server, enabling AI characters to:
- Search the web in real-time
- Fetch and analyze webpage content
- Access current date/time information
- Make external LLM API calls

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SearXNG instance running (default: `http://localhost:32768`)
- RisuAI application

### 1. Set Up MCP Server

```bash
cd searxng-mcp-crawl

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env with your settings

# Start the server
python server.py
```

The server will start on `http://0.0.0.0:32769` by default.

### 2. Install RisuAI Plugin

1. Copy `risuai-mcp-bridge.js` to your RisuAI plugins directory
2. In RisuAI, enable the "MCP SearXNG Bridge" plugin
3. Configure the MCP server URL in plugin settings (default: `http://localhost:32769`)

### 3. Usage in RisuAI

#### Initialize the Plugin
```javascript
{
  "command": "init"
}
```

#### Search the Web
```javascript
{
  "command": "search",
  "query": "artificial intelligence news",
  "limit": 10,
  "category": "general"
}
```

#### Fetch Webpage Content
```javascript
{
  "command": "fetch",
  "url": "https://example.com/article",
  "maxLength": 5000
}
```

#### Get Current DateTime
```javascript
{
  "command": "datetime",
  "timezone": "Asia/Seoul"
}
```

#### List Available Tools
```javascript
{
  "command": "tools"
}
```

#### Check Server Status
```javascript
{
  "command": "health"
}
```

## 🔧 MCP Server Configuration

### Environment Variables

Create a `.env` file in the `searxng-mcp-crawl/` directory:

```env
# SearXNG Configuration
SEARXNG_BASE_URL=http://localhost:32768

# Server Configuration
HOST=0.0.0.0
PORT=32769

# Crawler Configuration
CONTENT_MAX_LENGTH=10000
SEARCH_RESULT_LIMIT=10
```

### Available MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `search` | Web search via SearXNG | `query`, `limit`, `category` |
| `fetch_webpage` | Crawl and extract webpage content | `url`/`urls`, `max_length`, `limit` |
| `get_current_datetime` | Get current datetime for timezone | `timezone` |
| `runLLM` | Execute external LLM API calls | `url`, `apiKey`, `model`, `messages` |
| `tool_planner` | Plan tool usage for tasks | `task`, `max_steps` |

## 🧩 Plugin Development

### MCP Server Plugin Structure

```python
from plugin_base import MCPPlugin
from typing import Dict, Any

class MyPlugin(MCPPlugin):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "Description of my tool"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            },
            "required": ["param1"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation here
        return {"success": True, "result": "..."}
```

Save your plugin as `searxng-mcp-crawl/plugins/my_plugin.py` and restart the server.

## 🐛 Debugging

### Check Server Health

```bash
curl http://localhost:32769/health
```

Expected response:
```json
{
  "status": "ok",
  "plugins": 5,
  "available_tools": [
    "get_current_datetime",
    "search",
    "runLLM",
    "fetch_webpage",
    "tool_planner"
  ]
}
```

### Test MCP Protocol

```bash
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

### Server Logs

The server logs all plugin operations and errors. Check the console output for debugging information.

### Common Issues

1. **Connection Refused**: Ensure the MCP server is running on the correct port
2. **SearXNG Errors**: Verify your SearXNG instance is accessible
3. **Plugin Not Found**: Check that plugin files are in `searxng-mcp-crawl/plugins/`
4. **Import Errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`

## 📚 API Reference

### RisuAI Plugin Commands

#### `init` - Initialize Plugin
Establishes connection with MCP server and verifies available tools.

**Request:**
```javascript
{ "command": "init" }
```

**Response:**
```javascript
{
  "success": true,
  "message": "MCP Bridge initialized successfully"
}
```

#### `search` - Web Search
Search the web using SearXNG with customizable parameters.

**Request:**
```javascript
{
  "command": "search",
  "query": "search query",
  "limit": 10,          // Optional, default: 10
  "category": "general"  // Optional, default: "general"
}
```

**Response:**
```javascript
{
  "success": true,
  "query": "search query",
  "results_count": 10,
  "results": [
    {
      "title": "...",
      "url": "...",
      "content": "...",
      "score": 0.95
    }
  ]
}
```

#### `fetch` - Fetch Webpage
Crawl and extract content from web pages.

**Request:**
```javascript
{
  "command": "fetch",
  "url": "https://example.com",  // Single URL
  // OR
  "urls": ["https://example1.com", "https://example2.com"],  // Multiple URLs
  "maxLength": 5000,  // Optional, default: 5000
  "limit": 3          // Optional, default: 3 (for multiple URLs)
}
```

**Response:**
```javascript
{
  "success": true,
  "total_urls": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "success": true,
      "url": "https://example.com",
      "content": "...",
      "content_length": 4532,
      "metadata": {
        "title": "Page Title",
        "description": "...",
        "language": "en"
      }
    }
  ]
}
```

#### `datetime` - Get Current DateTime
Get current date and time for a specific timezone.

**Request:**
```javascript
{
  "command": "datetime",
  "timezone": "Asia/Seoul"  // Optional, default: "UTC"
}
```

**Response:**
```javascript
{
  "success": true,
  "timezone": "Asia/Seoul",
  "datetime": "2025-11-16T21:30:45+09:00",
  "formatted": "2025-11-16 21:30:45 KST",
  "unix_timestamp": 1731761445
}
```

## 🚢 Deployment

### Production Deployment

1. **Using systemd (Linux)**:

Create `/etc/systemd/system/mcp-server.service`:
```ini
[Unit]
Description=MCP SearXNG Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/asdaadas/searxng-mcp-crawl
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
sudo systemctl status mcp-server
```

2. **Using Docker**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY searxng-mcp-crawl/ .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 32769

CMD ["python", "server.py"]
```

Build and run:
```bash
docker build -t mcp-searxng-server .
docker run -d -p 32769:32769 \
  -e SEARXNG_BASE_URL=http://searxng:8080 \
  --name mcp-server \
  mcp-searxng-server
```

3. **Using Docker Compose**:

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "32769:32769"
    environment:
      - SEARXNG_BASE_URL=http://searxng:8080
      - HOST=0.0.0.0
      - PORT=32769
    restart: unless-stopped
    depends_on:
      - searxng

  searxng:
    image: searxng/searxng:latest
    ports:
      - "32768:8080"
    volumes:
      - ./searxng:/etc/searxng
    restart: unless-stopped
```

## 📝 License

- MCP Server: MIT License
- RisuAI Bridge Plugin: MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/damin25soka7/asdaadas.git
cd asdaadas

# Set up Python virtual environment
cd searxng-mcp-crawl
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python server.py
```

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check the debugging section above
- Review server logs for error messages

## 🎯 Roadmap

- [ ] Add authentication/API key support
- [ ] Implement rate limiting
- [ ] Add more plugins (image search, translation, etc.)
- [ ] Create web UI for plugin management
- [ ] Add comprehensive test suite
- [ ] Docker compose setup with SearXNG
- [ ] Performance monitoring and metrics
- [ ] WebSocket support for real-time updates

## 📜 Changelog

### Version 1.0.0 (2025-11-16)
- Initial release
- MCP server with 5 core plugins
- RisuAI bridge plugin
- Basic documentation and examples
