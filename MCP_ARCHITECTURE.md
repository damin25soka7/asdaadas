# MCP Architecture & Implementation Details

## Overview

This document provides in-depth technical details about the Model Context Protocol (MCP) architecture and how it's implemented in this project.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Communication Patterns](#communication-patterns)
3. [Plugin System Deep Dive](#plugin-system-deep-dive)
4. [Tool Planning and Execution](#tool-planning-and-execution)
5. [Integration Patterns](#integration-patterns)
6. [Performance Considerations](#performance-considerations)
7. [Security Architecture](#security-architecture)

---

## Architecture Overview

### System Components

```
┌────────────────────────────────────────────────────────────────┐
│                        Chatbot Client                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   UI Layer   │  │ AI Provider  │  │ MCP Client   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                 │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │                  │                  │ HTTP/SSE
          └──────────────────┴──────────────────┼─────────────────
                                                 │
┌────────────────────────────────────────────────┼─────────────────┐
│                    MCP Server                  │                 │
│  ┌─────────────────────────────────────────────┼──────────────┐ │
│  │              HTTP/SSE Handler               │              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────▼──────────┐  │ │
│  │  │ POST /      │  │ GET /       │  │ POST /message   │  │ │
│  │  │ (JSON-RPC)  │  │ (SSE)       │  │ (SSE Messages)  │  │ │
│  │  └─────┬───────┘  └─────┬───────┘  └──────┬──────────┘  │ │
│  └────────┼──────────────────┼──────────────────┼─────────────┘ │
│           │                  │                  │                │
│  ┌────────▼──────────────────▼──────────────────▼─────────────┐ │
│  │              MCP Protocol Handler                          │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Methods:                                             │ │ │
│  │  │  • initialize                                        │ │ │
│  │  │  • notifications/initialized                         │ │ │
│  │  │  • tools/list                                        │ │ │
│  │  │  • tools/call                                        │ │ │
│  │  │  • ping                                              │ │ │
│  │  │  • plugins/reload                                    │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────┬─────────────────────────────── │
│                                │                                │
│  ┌─────────────────────────────▼─────────────────────────────┐ │
│  │               Plugin Manager                              │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ • Auto-discovery from plugins/ directory            │ │ │
│  │  │ • Dynamic loading and instantiation                 │ │ │
│  │  │ • Plugin lifecycle management                       │ │ │
│  │  │ • Hot reload capability                             │ │ │
│  │  │ • Tool listing and execution                        │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────┬───────────────────────────── │
│                                 │                               │
│  ┌──────────────────────────────▼──────────────────────────┐  │
│  │                    Plugin Instances                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │  Search  │ │  Crawl   │ │ Planner  │ │  runLLM  │  │  │
│  │  │  Plugin  │ │  Plugin  │ │  Plugin  │ │  Plugin  │  │  │
│  │  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘  │  │
│  │        │            │            │            │         │  │
│  └────────┼────────────┼────────────┼────────────┼─────────┘  │
│           │            │            │            │             │
└───────────┼────────────┼────────────┼────────────┼─────────────┘
            │            │            │            │
            ▼            ▼            ▼            ▼
┌───────────────────────────────────────────────────────────────┐
│                    External Services                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ SearXNG  │  │   Web    │  │   LLM    │  │   API    │    │
│  │  Search  │  │  Sites   │  │ Provider │  │ Services │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Step 1: Chatbot determines if tools are needed       │
│  • Keyword analysis                                  │
│  • Intent detection                                  │
│  • Context awareness                                 │
└──────┬───────────────────────────────────────────────┘
       │
       ▼ [If tools needed]
┌──────────────────────────────────────────────────────┐
│ Step 2: Initialize MCP connection (if not already)   │
│  • POST /initialize                                  │
│  • Establish protocol version                        │
│  • Exchange capabilities                             │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Step 3: Discover available tools                     │
│  • POST /tools/list                                  │
│  • Receive tool schemas                              │
│  • Cache tool definitions                            │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Step 4a: Direct tool call (simple cases)             │
│  • POST /tools/call                                  │
│  • Single tool execution                             │
│  OR                                                   │
│ Step 4b: Use tool_planner (complex cases)            │
│  • POST /tools/call tool_planner                     │
│  • AI creates multi-step plan                        │
│  • Returns optimized execution sequence              │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Step 5: Execute plan (if using planner)              │
│  • For each step in plan:                            │
│    - POST /tools/call                                │
│    - Collect results                                 │
│    - Pass to next step if needed                     │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ Step 6: Generate final response                      │
│  • Combine tool results                              │
│  • Send to AI provider                               │
│  • Format response for user                          │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│ User Output │
└─────────────┘
```

---

## Communication Patterns

### Pattern 1: Simple Request-Response (HTTP POST)

Best for: Single tool calls, synchronous operations

```
Client                                    Server
  │                                         │
  │  POST / (initialize)                    │
  ├────────────────────────────────────────>│
  │                                         │
  │  200 OK (capabilities)                  │
  │<────────────────────────────────────────┤
  │                                         │
  │  POST / (tools/list)                    │
  ├────────────────────────────────────────>│
  │                                         │
  │  200 OK (tool list)                     │
  │<────────────────────────────────────────┤
  │                                         │
  │  POST / (tools/call: search)            │
  ├────────────────────────────────────────>│
  │                                         │
  │       [Server executes search]          │
  │                                         │
  │  200 OK (search results)                │
  │<────────────────────────────────────────┤
  │                                         │
```

### Pattern 2: Server-Sent Events (SSE)

Best for: Long-running operations, streaming responses, multiple tool calls

```
Client                                    Server
  │                                         │
  │  GET / (Accept: text/event-stream)      │
  ├────────────────────────────────────────>│
  │                                         │
  │  event: endpoint                        │
  │  data: /message/{connection_id}         │
  │<────────────────────────────────────────┤
  │                                         │
  │  POST /message/{id} (initialize)        │
  ├────────────────────────────────────────>│
  │                                         │
  │  data: {initialize response}            │
  │<────────────────────────────────────────┤
  │                                         │
  │  POST /message/{id} (tools/call)        │
  ├────────────────────────────────────────>│
  │                                         │
  │       [Server executes tool]            │
  │                                         │
  │  data: {partial result 1}               │
  │<────────────────────────────────────────┤
  │  data: {partial result 2}               │
  │<────────────────────────────────────────┤
  │  data: {final result}                   │
  │<────────────────────────────────────────┤
  │                                         │
```

### JSON-RPC 2.0 Message Format

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "method-name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "data": "result-data"
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "additional-error-info"
  }
}
```

---

## Plugin System Deep Dive

### Plugin Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│ Server Startup                                           │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ PluginManager.__init__()                                 │
│  • Initialize plugins directory path                     │
│  • Create empty plugins dictionary                       │
│  • Call load_plugins()                                   │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ load_plugins()                                           │
│  1. Scan plugins/ directory                              │
│  2. For each .py file (except __*):                      │
│     a. Import module dynamically                         │
│     b. Find classes inheriting MCPPlugin                 │
│     c. Instantiate plugin                                │
│     d. Inject PluginManager reference (if supported)     │
│     e. Add to plugins dictionary                         │
│  3. Log loaded plugins                                   │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ Runtime Operation                                        │
│  • list_plugins() - Return tool definitions              │
│  • execute_plugin() - Execute tool by name               │
│  • reload_plugins() - Hot reload all plugins             │
└──────────────────────────────────────────────────────────┘
```

### Plugin Interface Contract

Every plugin must implement:

```python
class MCPPlugin(ABC):
    # Required Properties
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique tool identifier
        - Must be lowercase
        - No spaces (use underscores)
        - Should be descriptive
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description for AI
        - Explain what the tool does
        - List key parameters
        - Mention important constraints
        """
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        JSON Schema for input validation
        - Use standard JSON Schema format
        - Mark required fields
        - Provide defaults where appropriate
        - Add descriptions for clarity
        """
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool logic
        - Validate inputs
        - Perform operation
        - Return structured result
        - Handle errors gracefully
        
        Returns:
            {
                "success": bool,
                "data": Any,  # or specific fields
                "error": str  # if success=False
            }
        """
        pass
    
    # Optional Properties
    @property
    def version(self) -> str:
        """Plugin version (semver recommended)"""
        return "1.0.0"
    
    @property
    def author(self) -> str:
        """Plugin author"""
        return "Unknown"
    
    @property
    def enabled(self) -> bool:
        """Whether plugin is enabled"""
        return True
```

### Plugin Best Practices

1. **Single Responsibility**
   - Each plugin should do one thing well
   - Complex operations should be split into multiple plugins

2. **Error Handling**
   ```python
   async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
       try:
           # Validate inputs
           self.validate_arguments(arguments)
           
           # Execute operation
           result = await self.perform_operation(arguments)
           
           # Return success
           return {"success": True, "data": result}
           
       except ValueError as e:
           # Validation errors
           return {"success": False, "error": f"Invalid input: {str(e)}"}
       
       except TimeoutError as e:
           # Timeout errors
           return {"success": False, "error": "Operation timed out"}
       
       except Exception as e:
           # Unexpected errors
           logging.error(f"Plugin {self.name} error: {str(e)}")
           return {"success": False, "error": "Internal plugin error"}
   ```

3. **Async Operations**
   ```python
   # Good - Non-blocking I/O
   async def execute(self, arguments):
       async with httpx.AsyncClient() as client:
           response = await client.get(url)
       return {"success": True, "data": response.text}
   
   # Bad - Blocking I/O
   def execute(self, arguments):
       response = requests.get(url)  # Blocks the event loop!
       return {"success": True, "data": response.text}
   ```

4. **Resource Management**
   ```python
   class MyPlugin(MCPPlugin):
       def __init__(self):
           self.client = None
       
       async def execute(self, arguments):
           if not self.client:
               self.client = httpx.AsyncClient()
           
           try:
               result = await self.client.get(url)
               return {"success": True, "data": result}
           finally:
               # Cleanup if needed
               pass
   ```

---

## Tool Planning and Execution

### tool_planner Plugin Architecture

The `tool_planner` plugin is a meta-tool that uses AI to create execution plans:

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ tool_planner receives:                                  │
│  • user_query: "Find Python news and summarize"         │
│  • planner_llm_config: {url, apiKey, model}             │
│  • max_steps: 5                                          │
│  • context: (optional)                                   │
└─────┬───────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│ Get available tools from PluginManager                  │
│  • Filters out tool_planner itself                      │
│  • Applies avoid_tools filter                           │
│  • Returns compact tool descriptions                     │
└─────┬───────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│ Build planning prompt                                   │
│  Query: {user_query}                                    │
│  Tools: {compact tool list}                             │
│  Rules:                                                  │
│    - Use between {min_steps} and {max_steps} steps      │
│    - Complexity: {complexity}                            │
│    - Tool parameter hints                                │
└─────┬───────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│ Call dedicated planner LLM                              │
│  • Separate from main chatbot LLM                       │
│  • Optimized for planning tasks                         │
│  • Returns JSON execution plan                           │
└─────┬───────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│ Parse and validate plan                                 │
│  • Clean JSON response (remove markdown, comments)      │
│  • Validate structure                                    │
│  • Check tool availability                               │
│  • Verify step count constraints                         │
└─────┬───────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│ Return execution plan                                   │
│  {                                                       │
│    "success": true,                                      │
│    "main_query": "...",                                  │
│    "plan": [                                             │
│      {                                                   │
│        "step": 1,                                        │
│        "tool": "search",                                 │
│        "arguments": {"query": "...", "limit": 10},       │
│        "purpose": "Find relevant articles"               │
│      },                                                  │
│      {                                                   │
│        "step": 2,                                        │
│        "tool": "fetch_webpage",                          │
│        "arguments": {"urls": ["..."], "limit": 3},       │
│        "purpose": "Extract full content"                 │
│      },                                                  │
│      {                                                   │
│        "step": 3,                                        │
│        "tool": "runLLM",                                 │
│        "arguments": {"messages": [...]},                 │
│        "purpose": "Summarize findings"                   │
│      }                                                   │
│    ],                                                    │
│    "total_steps": 3                                      │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
```

### Plan Execution in Chatbot

```javascript
// After receiving plan from tool_planner
async function executePlan(plan) {
    const results = [];
    
    for (const step of plan.plan) {
        console.log(`Executing step ${step.step}: ${step.tool}`);
        
        // Execute tool via MCP
        const result = await mcpClient.callTool(
            step.tool,
            step.arguments
        );
        
        // Store result
        results.push({
            step: step.step,
            tool: step.tool,
            purpose: step.purpose,
            result: result
        });
        
        // Optional: Check if step failed and handle
        if (!result.success) {
            console.error(`Step ${step.step} failed:`, result.error);
            // Decide whether to continue or abort
        }
    }
    
    return results;
}
```

---

## Integration Patterns

### Pattern 1: Direct Integration (Simple)

```javascript
// For simple chatbots with basic tool needs
class SimpleChatbot {
    async handleMessage(userInput) {
        // Direct tool call without planning
        if (userInput.includes('search')) {
            const query = extractQuery(userInput);
            const result = await mcp.callTool('search', {query, limit: 10});
            return formatResponse(result);
        }
        
        // Regular AI response
        return await ai.generate(userInput);
    }
}
```

### Pattern 2: AI-Assisted Tool Selection (Medium)

```javascript
// Chatbot lets AI decide which tools to use
class SmartChatbot {
    async handleMessage(userInput, history) {
        // Get available tools
        const tools = await mcp.listTools();
        
        // Let AI decide tool usage
        const aiResponse = await ai.generate({
            messages: history,
            tools: tools,
            tool_choice: 'auto'
        });
        
        // Execute tool calls
        if (aiResponse.tool_calls) {
            for (const call of aiResponse.tool_calls) {
                const result = await mcp.callTool(call.name, call.arguments);
                history.push({role: 'tool', content: JSON.stringify(result)});
            }
            
            // Get final response
            return await ai.generate({messages: history});
        }
        
        return aiResponse;
    }
}
```

### Pattern 3: Intelligent Planning (Advanced)

```javascript
// Uses tool_planner for complex multi-step operations
class AdvancedChatbot {
    async handleMessage(userInput, history) {
        // Determine complexity
        const complexity = this.analyzeComplexity(userInput);
        
        if (complexity === 'simple') {
            // Use Pattern 2
            return await this.simpleToolCall(userInput);
        }
        
        // Create execution plan
        const plan = await mcp.callTool('tool_planner', {
            user_query: userInput,
            planner_llm_config: this.plannerConfig,
            max_steps: 5,
            complexity: 'moderate'
        });
        
        if (!plan.success) {
            return await this.fallbackResponse(userInput);
        }
        
        // Execute plan
        const results = await this.executePlan(plan.plan);
        
        // Generate final response with context
        return await ai.generate({
            messages: [
                {role: 'system', content: 'Use tool results to answer'},
                {role: 'user', content: userInput},
                {role: 'assistant', content: JSON.stringify(results)}
            ]
        });
    }
}
```

---

## Performance Considerations

### 1. Connection Pooling

```python
# Good - Reuse HTTP client
class MyPlugin(MCPPlugin):
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100)
        )
    
    async def execute(self, arguments):
        # Reuse self.client for all requests
        response = await self.client.get(url)
```

### 2. Caching

```python
from functools import lru_cache
import time

class CachedPlugin(MCPPlugin):
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def execute(self, arguments):
        # Generate cache key
        cache_key = f"{arguments.get('query')}:{arguments.get('limit')}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        # Fetch fresh data
        result = await self.fetch_data(arguments)
        
        # Cache result
        self.cache[cache_key] = (result, time.time())
        
        return result
```

### 3. Rate Limiting

```python
import asyncio
from collections import deque

class RateLimitedPlugin(MCPPlugin):
    def __init__(self):
        self.requests = deque()
        self.max_per_minute = 60
    
    async def execute(self, arguments):
        # Rate limit check
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] < now - 60:
            self.requests.popleft()
        
        # Check limit
        if len(self.requests) >= self.max_per_minute:
            wait_time = 60 - (now - self.requests[0])
            await asyncio.sleep(wait_time)
        
        # Record request
        self.requests.append(now)
        
        # Execute
        return await self.perform_operation(arguments)
```

### 4. Parallel Execution

```javascript
// Execute independent tools in parallel
async function executePlanOptimized(plan) {
    const results = [];
    
    // Group steps by dependencies
    const batches = groupByDependencies(plan.plan);
    
    for (const batch of batches) {
        // Execute batch in parallel
        const batchResults = await Promise.all(
            batch.map(step => 
                mcp.callTool(step.tool, step.arguments)
            )
        );
        
        results.push(...batchResults);
    }
    
    return results;
}
```

---

## Security Architecture

### 1. Input Validation

```python
async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    # Type validation
    query = arguments.get("query")
    if not isinstance(query, str):
        return {"success": False, "error": "Query must be a string"}
    
    # Length validation
    if len(query) > 1000:
        return {"success": False, "error": "Query too long (max 1000 chars)"}
    
    # Content validation
    if contains_sql_injection(query):
        return {"success": False, "error": "Invalid query content"}
    
    # Sanitize
    query = sanitize_input(query)
    
    # Proceed with execution
    ...
```

### 2. Authentication

```python
# In server.py
async def authenticate(request):
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    if not verify_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return True

# Add to routes
@app.route('/')
async def handle_request(request):
    await authenticate(request)
    # Process request
    ...
```

### 3. Rate Limiting

```python
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests=100, window=60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
    
    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < self.window
            ]
        else:
            self.requests[client_ip] = []
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )
        
        # Record request
        self.requests[client_ip].append(now)
        
        # Continue
        response = await call_next(request)
        return response
```

### 4. Secure Configuration

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Never hardcode secrets
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable required")

# Validate configuration
if not API_KEY.startswith('sk-'):
    raise ValueError("Invalid API key format")

# Use secure defaults
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',')
if not ALLOWED_ORIGINS:
    print("Warning: ALLOWED_ORIGINS not set, defaulting to localhost only")
    ALLOWED_ORIGINS = ['http://localhost:*']
```

---

## Conclusion

This architecture provides:
- **Flexibility**: Plugin system allows easy extension
- **Scalability**: Async operations and connection pooling
- **Security**: Multiple layers of validation and authentication
- **Intelligence**: AI-powered planning for complex tasks
- **Reliability**: Error handling and graceful degradation

For implementation examples, see the `searxng-mcp-crawl` directory and the integration guides.

---

*Last Updated: November 2024*
