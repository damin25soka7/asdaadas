# Quick Start Guide

Get up and running with the MCP SearXNG Bridge in 5 minutes!

## For RisuAI Users

### Step 1: Start the MCP Server

```bash
cd searxng-mcp-crawl
pip install -r requirements.txt
python server.py
```

You should see:
```
🚀 Extensible MCP Server with Plugin System
Server: http://0.0.0.0:32769
✅ Server ready
```

### Step 2: Install the RisuAI Plugin

1. Open RisuAI
2. Go to **Settings** → **Plugins**
3. Click **Add Plugin** or **Import Plugin**
4. Select `risuai-mcp-bridge.js` from this repository
5. In plugin settings, set server URL to: `http://localhost:32769`

### Step 3: Test It!

Create a character or use an existing one, and try these commands:

```javascript
// Initialize
{
  "command": "init"
}

// Search something
{
  "command": "search",
  "query": "latest AI news",
  "limit": 5
}

// Get current time
{
  "command": "datetime",
  "timezone": "Asia/Seoul"
}
```

## For Developers

### Quick Test

```bash
# Terminal 1: Start server
cd searxng-mcp-crawl
python server.py

# Terminal 2: Run tests
cd searxng-mcp-crawl
python test_server.py
```

### Quick API Test

```bash
# Check health
curl http://localhost:32769/health

# List tools
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Test search
curl -X POST http://localhost:32769 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"search",
      "arguments":{"query":"python","limit":3}
    }
  }'
```

## Docker Quick Start

```bash
# Option 1: Server only
cd searxng-mcp-crawl
docker build -t mcp-server .
docker run -d -p 32769:32769 mcp-server

# Option 2: With SearXNG
cd ..
docker-compose up -d
```

## Troubleshooting

**Server won't start:**
- Check if port 32769 is available: `lsof -i :32769`
- Make sure Python dependencies are installed: `pip install -r requirements.txt`

**RisuAI can't connect:**
- Verify server is running: `curl http://localhost:32769/health`
- Check server URL in plugin settings
- Try `http://127.0.0.1:32769` instead of `localhost`

**No search results:**
- Check if SearXNG is configured (default: `http://localhost:32768`)
- Update `SEARXNG_BASE_URL` in `.env` file

## Next Steps

- Read [RISUAI_USAGE.md](RISUAI_USAGE.md) for detailed examples
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- See [README.md](README.md) for complete documentation

## Need Help?

- GitHub Issues: https://github.com/damin25soka7/asdaadas/issues
- Check server logs for errors
- Run test suite: `python test_server.py`

## Common Use Cases

### Research Assistant
```javascript
{
  "command": "search",
  "query": "quantum computing 2025",
  "limit": 5
}
```

### News Reader
```javascript
{
  "command": "search",
  "query": "technology news today",
  "category": "news",
  "limit": 10
}
```

### Web Content Analyzer
```javascript
{
  "command": "fetch",
  "url": "https://example.com/article",
  "maxLength": 5000
}
```

### Time Zone Helper
```javascript
{
  "command": "datetime",
  "timezone": "America/New_York"
}
```

That's it! You're ready to use the MCP SearXNG Bridge with RisuAI! 🚀
