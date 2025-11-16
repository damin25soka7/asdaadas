# RisuAI Plugin Usage Examples

This document provides practical examples of using the MCP SearXNG Bridge plugin in RisuAI.

## Installation

1. **Start the MCP Server**:
   ```bash
   cd searxng-mcp-crawl
   python server.py
   ```

2. **Install the Plugin in RisuAI**:
   - Open RisuAI
   - Go to Settings → Plugins
   - Click "Add Plugin" or "Import Plugin"
   - Select `risuai-mcp-bridge.js`
   - Configure the server URL (default: `http://localhost:32769`)

## Basic Usage Examples

### Example 1: Initialize and Check Status

First, always initialize the plugin and check the server status:

```javascript
// Character: "Let me initialize my web tools..."
{
  "command": "init"
}

// Then check what's available
{
  "command": "health"
}
```

**Expected Response:**
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

### Example 2: Search for Current Information

```javascript
// Character: "I'll search for recent AI developments..."
{
  "command": "search",
  "query": "artificial intelligence breakthroughs 2025",
  "limit": 5,
  "category": "news"
}
```

**Response Structure:**
```json
{
  "success": true,
  "query": "artificial intelligence breakthroughs 2025",
  "results_count": 5,
  "results": [
    {
      "title": "Major AI Breakthrough Announced",
      "url": "https://example.com/article",
      "content": "Summary of the article...",
      "score": 0.95
    }
  ]
}
```

### Example 3: Fetch and Analyze Webpage

```javascript
// Character: "Let me read this article in detail..."
{
  "command": "fetch",
  "url": "https://example.com/interesting-article",
  "maxLength": 3000
}
```

**Response:**
```json
{
  "success": true,
  "total_urls": 1,
  "successful": 1,
  "results": [
    {
      "success": true,
      "url": "https://example.com/interesting-article",
      "content": "Full article text...",
      "content_length": 2847,
      "metadata": {
        "title": "Article Title",
        "description": "Article description",
        "language": "en"
      }
    }
  ]
}
```

### Example 4: Get Current Time for Different Locations

```javascript
// Character: "What time is it in Seoul right now?"
{
  "command": "datetime",
  "timezone": "Asia/Seoul"
}
```

**Response:**
```json
{
  "success": true,
  "timezone": "Asia/Seoul",
  "datetime": "2025-11-16T21:30:45+09:00",
  "formatted": "2025-11-16 21:30:45 KST",
  "unix_timestamp": 1731761445
}
```

## Advanced Usage Scenarios

### Scenario 1: Research Assistant Character

Create a character that helps with research by searching and summarizing information:

**Character Prompt:**
```
You are a helpful research assistant with access to web search and webpage reading capabilities.
When a user asks you to research something, you:
1. Search for relevant information
2. Fetch the most relevant webpages
3. Summarize and analyze the content
4. Provide accurate, cited responses
```

**Example Conversation:**

User: "Can you research the latest developments in quantum computing?"

Character (thinking): 
```javascript
// Step 1: Search for information
{
  "command": "search",
  "query": "quantum computing developments 2025",
  "limit": 5
}
```

Character (after receiving results):
```javascript
// Step 2: Fetch the most relevant article
{
  "command": "fetch",
  "url": "https://top-result-url.com/article",
  "maxLength": 5000
}
```

Character (response): "Based on my research, I found several key developments in quantum computing in 2025..."

### Scenario 2: News Aggregator Character

**Character Prompt:**
```
You are a news curator who keeps users informed about current events.
You can search for news in specific categories and provide summaries.
```

**Example Usage:**

User: "What's happening in technology today?"

Character:
```javascript
{
  "command": "search",
  "query": "technology news today",
  "limit": 10,
  "category": "news"
}
```

### Scenario 3: Time-Aware Character

**Character Prompt:**
```
You are aware of global time zones and can tell users the current time anywhere.
You understand time differences and can schedule things accordingly.
```

**Example Usage:**

User: "When is 3 PM in Tokyo in New York time?"

Character:
```javascript
// First, get Tokyo time
{
  "command": "datetime",
  "timezone": "Asia/Tokyo"
}
```

```javascript
// Then get New York time
{
  "command": "datetime",
  "timezone": "America/New_York"
}
```

### Scenario 4: Multi-Step Research

For complex research tasks involving multiple steps:

```javascript
// Step 1: Search for the topic
{
  "command": "search",
  "query": "climate change impact on agriculture",
  "limit": 5
}

// Step 2: Fetch multiple relevant articles
{
  "command": "fetch",
  "urls": [
    "https://article1.com",
    "https://article2.com",
    "https://article3.com"
  ],
  "limit": 3,
  "maxLength": 4000
}

// Step 3: Search for related statistics
{
  "command": "search",
  "query": "agriculture climate statistics 2025",
  "limit": 3
}
```

## Error Handling

### Example: Handling Search Failures

```javascript
// Search with validation
const searchResult = {
  "command": "search",
  "query": "my search query",
  "limit": 10
};

// Check response
if (searchResult.success === false) {
  // Handle error
  console.error("Search failed:", searchResult.error);
  // Inform user gracefully
  return "I encountered an issue searching. Let me try again...";
}
```

### Example: Handling Connection Issues

```javascript
// Check server health before operations
try {
  const health = {
    "command": "health"
  };
  
  if (health.status !== "ok") {
    return "My web tools are currently unavailable. Please try again later.";
  }
} catch (error) {
  return "I'm having trouble connecting to my web services.";
}
```

## Best Practices

### 1. Initialize Once Per Session
```javascript
// At the start of a conversation
{
  "command": "init"
}
```

### 2. Use Appropriate Limits
```javascript
// For quick searches
{
  "command": "search",
  "query": "...",
  "limit": 3  // Small limit for speed
}

// For comprehensive research
{
  "command": "search",
  "query": "...",
  "limit": 10  // More results
}
```

### 3. Control Content Length
```javascript
// For summaries
{
  "command": "fetch",
  "url": "...",
  "maxLength": 2000  // Brief content
}

// For detailed analysis
{
  "command": "fetch",
  "url": "...",
  "maxLength": 8000  // More content
}
```

### 4. Chain Operations Logically
```javascript
// 1. Search first
search → results

// 2. Then fetch interesting results
fetch → content

// 3. Analyze and respond
analysis → user response
```

## Debugging Tips

### Check Plugin Configuration
```javascript
{
  "command": "help"
}
```

This returns plugin version, available commands, and current configuration.

### Verify Server Connection
```javascript
{
  "command": "health"
}
```

### List Available Tools
```javascript
{
  "command": "tools"
}
```

## Integration with Character Personalities

### Academic/Researcher Personality
- Uses `search` extensively with specific queries
- Fetches full articles with high `maxLength`
- Provides detailed citations

### News Reporter Personality
- Searches with `category: "news"`
- Uses lower `maxLength` for quick summaries
- Focuses on recent, time-sensitive content

### Virtual Assistant Personality
- Uses `datetime` for scheduling
- Makes quick searches with low limits
- Provides concise, actionable information

## Performance Optimization

### For Fast Responses
```javascript
{
  "command": "search",
  "query": "...",
  "limit": 3  // Fewer results
}
```

### For Comprehensive Analysis
```javascript
{
  "command": "fetch",
  "urls": ["url1", "url2", "url3"],
  "maxLength": 5000,
  "limit": 3
}
```

### Batch Operations
```javascript
// Instead of multiple single fetches, use array
{
  "command": "fetch",
  "urls": ["url1", "url2", "url3", "url4", "url5"],
  "limit": 5
}
```

## Common Use Cases

1. **Real-time Information**: Weather, news, stock prices
2. **Research**: Academic papers, documentation, tutorials
3. **Fact-Checking**: Verify information, find sources
4. **Content Discovery**: Find articles, videos, resources
5. **Time Management**: Global time zones, scheduling
6. **Web Scraping**: Extract data from specific websites

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure MCP server is running |
| "Tool not found" | Check server has loaded all plugins |
| "Timeout error" | Increase timeout or reduce content size |
| "Invalid response" | Verify server URL is correct |
| "Empty results" | Check SearXNG is configured and working |

## Security Considerations

- Always validate server URL in plugin settings
- Don't expose API keys in plugin arguments
- Use HTTPS when possible for server connections
- Implement rate limiting for production use

## Next Steps

1. Experiment with different search queries
2. Try fetching various types of web content
3. Combine multiple commands for complex workflows
4. Create custom character personalities using these tools
5. Monitor server logs for debugging and optimization
