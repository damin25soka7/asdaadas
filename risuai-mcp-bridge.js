//@name MCP-SearXNG-Bridge
//@display-name MCP SearXNG Bridge
//@version 1.0.0
//@description Bridge plugin to connect RisuAI with MCP SearXNG server for web search and crawling capabilities
//@author damin25soka7
//@arg mcp_server_url string http://localhost:32769

/**
 * RisuAI MCP Bridge Plugin
 * 
 * This plugin connects RisuAI to the MCP (Model Context Protocol) SearXNG server,
 * enabling advanced web search and webpage crawling capabilities.
 * 
 * Available Tools:
 * - search: Web search via SearXNG
 * - fetch_webpage: Crawl and extract webpage content
 * - get_current_datetime: Get current date/time for specific locations
 * - runLLM: Execute external LLM API calls
 * - tool_planner: Intelligent tool selection and planning
 * 
 * @license MIT
 */

const pluginApis = globalThis.__pluginApis__;

// RisuAI API access
const risuAPI = {
    risuFetch: pluginApis.risuFetch,
    nativeFetch: pluginApis.nativeFetch,
    getArg: pluginApis.getArg,
    setArg: pluginApis.setArg,
    getChar: pluginApis.getChar,
    setChar: pluginApis.setChar,
    getDatabase: pluginApis.getDatabase,
    toast: pluginApis.toast,
    log: pluginApis.log,
};

// Plugin configuration
class MCPBridgeConfig {
    static get serverUrl() {
        const url = risuAPI.getArg('mcp_server_url') || 'http://localhost:32769';
        return url.replace(/\/$/, ''); // Remove trailing slash
    }

    static set serverUrl(value) {
        risuAPI.setArg('mcp_server_url', value);
    }
}

// MCP Client for communication with the server
class MCPClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.messageId = 1;
    }

    async callTool(toolName, arguments) {
        try {
            const requestBody = {
                jsonrpc: "2.0",
                id: this.messageId++,
                method: "tools/call",
                params: {
                    name: toolName,
                    arguments: arguments
                }
            };

            risuAPI.log(`[MCP Bridge] Calling tool: ${toolName}`);
            risuAPI.log(`[MCP Bridge] Arguments: ${JSON.stringify(arguments)}`);

            const response = await risuAPI.nativeFetch(this.serverUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(`MCP Error: ${data.error.message}`);
            }

            // Extract content from MCP response
            if (data.result && data.result.content && data.result.content.length > 0) {
                const textContent = data.result.content[0].text;
                return JSON.parse(textContent);
            }

            return data.result;

        } catch (error) {
            risuAPI.log(`[MCP Bridge] Error: ${error.message}`);
            throw error;
        }
    }

    async listTools() {
        try {
            const requestBody = {
                jsonrpc: "2.0",
                id: this.messageId++,
                method: "tools/list"
            };

            const response = await risuAPI.nativeFetch(this.serverUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.result.tools || [];

        } catch (error) {
            risuAPI.log(`[MCP Bridge] Error listing tools: ${error.message}`);
            throw error;
        }
    }

    async checkHealth() {
        try {
            const response = await risuAPI.nativeFetch(`${this.serverUrl}/health`, {
                method: 'GET'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();

        } catch (error) {
            risuAPI.log(`[MCP Bridge] Health check failed: ${error.message}`);
            throw error;
        }
    }
}

// Tool implementations
class MCPTools {
    constructor(client) {
        this.client = client;
    }

    /**
     * Search the web using SearXNG
     * @param {string} query - Search query
     * @param {number} limit - Number of results (default: 10)
     * @param {string} category - Search category (default: general)
     * @returns {Promise<Object>} Search results
     */
    async search(query, limit = 10, category = "general") {
        return await this.client.callTool("search", {
            query,
            limit,
            category
        });
    }

    /**
     * Fetch and extract content from one or multiple webpages
     * @param {string|string[]} url - Single URL or array of URLs
     * @param {number} maxLength - Maximum content length (default: 5000)
     * @param {number} limit - Maximum number of URLs to fetch (default: 3)
     * @returns {Promise<Object>} Webpage content
     */
    async fetchWebpage(url, maxLength = 5000, limit = 3) {
        const args = {
            max_length: maxLength,
            limit: limit
        };

        if (Array.isArray(url)) {
            args.urls = url;
        } else {
            args.url = url;
        }

        return await this.client.callTool("fetch_webpage", args);
    }

    /**
     * Get current date and time for a specific location
     * @param {string} timezone - Timezone (e.g., "Asia/Seoul", "America/New_York")
     * @returns {Promise<Object>} Current datetime info
     */
    async getCurrentDateTime(timezone = "UTC") {
        return await this.client.callTool("get_current_datetime", {
            timezone
        });
    }

    /**
     * Execute an external LLM API call
     * @param {string} url - API endpoint URL
     * @param {string} apiKey - API key
     * @param {string} model - Model name
     * @param {Array} messages - Array of message objects
     * @returns {Promise<Object>} LLM response
     */
    async runLLM(url, apiKey, model, messages) {
        return await this.client.callTool("runLLM", {
            url,
            apiKey,
            model,
            messages
        });
    }

    /**
     * Plan and select appropriate tools for a task
     * @param {string} task - Task description
     * @param {number} maxSteps - Maximum number of steps (default: 5)
     * @returns {Promise<Object>} Tool execution plan
     */
    async planTools(task, maxSteps = 5) {
        return await this.client.callTool("tool_planner", {
            task,
            max_steps: maxSteps
        });
    }
}

// Main plugin class
class MCPBridgePlugin {
    constructor() {
        this.client = null;
        this.tools = null;
        this.initialized = false;
    }

    async initialize() {
        if (this.initialized) {
            return;
        }

        try {
            const serverUrl = MCPBridgeConfig.serverUrl;
            risuAPI.log(`[MCP Bridge] Initializing with server: ${serverUrl}`);

            this.client = new MCPClient(serverUrl);
            this.tools = new MCPTools(this.client);

            // Check server health
            const health = await this.client.checkHealth();
            risuAPI.log(`[MCP Bridge] Server status: ${health.status}`);
            risuAPI.log(`[MCP Bridge] Available plugins: ${health.plugins}`);
            risuAPI.log(`[MCP Bridge] Tools: ${health.available_tools.join(', ')}`);

            this.initialized = true;
            risuAPI.toast('MCP Bridge initialized successfully!', 'success');

        } catch (error) {
            risuAPI.log(`[MCP Bridge] Initialization failed: ${error.message}`);
            risuAPI.toast(`MCP Bridge initialization failed: ${error.message}`, 'error');
            throw error;
        }
    }

    async ensureInitialized() {
        if (!this.initialized) {
            await this.initialize();
        }
    }

    /**
     * Search the web
     */
    async search(query, options = {}) {
        await this.ensureInitialized();
        const limit = options.limit || 10;
        const category = options.category || "general";
        return await this.tools.search(query, limit, category);
    }

    /**
     * Fetch webpage content
     */
    async fetchWebpage(url, options = {}) {
        await this.ensureInitialized();
        const maxLength = options.maxLength || 5000;
        const limit = options.limit || 3;
        return await this.tools.fetchWebpage(url, maxLength, limit);
    }

    /**
     * Get current datetime
     */
    async getCurrentDateTime(timezone = "UTC") {
        await this.ensureInitialized();
        return await this.tools.getCurrentDateTime(timezone);
    }

    /**
     * List available tools
     */
    async listTools() {
        await this.ensureInitialized();
        return await this.client.listTools();
    }

    /**
     * Check server health
     */
    async checkHealth() {
        const client = new MCPClient(MCPBridgeConfig.serverUrl);
        return await client.checkHealth();
    }
}

// Global plugin instance
const mcpBridge = new MCPBridgePlugin();

// Export plugin functions for RisuAI
async function plugin(args) {
    try {
        // Parse arguments
        const command = args.command || 'help';

        switch (command) {
            case 'init':
            case 'initialize':
                await mcpBridge.initialize();
                return {
                    success: true,
                    message: 'MCP Bridge initialized successfully'
                };

            case 'search':
                if (!args.query) {
                    return {
                        success: false,
                        error: 'Query parameter is required for search'
                    };
                }
                const searchResults = await mcpBridge.search(args.query, {
                    limit: args.limit || 10,
                    category: args.category || 'general'
                });
                return searchResults;

            case 'fetch':
            case 'fetchWebpage':
                if (!args.url && !args.urls) {
                    return {
                        success: false,
                        error: 'URL parameter is required for fetch'
                    };
                }
                const fetchResults = await mcpBridge.fetchWebpage(
                    args.url || args.urls,
                    {
                        maxLength: args.maxLength || 5000,
                        limit: args.limit || 3
                    }
                );
                return fetchResults;

            case 'datetime':
            case 'getCurrentDateTime':
                const datetimeResults = await mcpBridge.getCurrentDateTime(
                    args.timezone || 'UTC'
                );
                return datetimeResults;

            case 'tools':
            case 'listTools':
                const tools = await mcpBridge.listTools();
                return {
                    success: true,
                    tools: tools
                };

            case 'health':
            case 'status':
                const health = await mcpBridge.checkHealth();
                return health;

            case 'help':
            default:
                return {
                    success: true,
                    message: 'MCP SearXNG Bridge Plugin',
                    version: '1.0.0',
                    usage: {
                        init: 'Initialize the plugin: {command: "init"}',
                        search: 'Search web: {command: "search", query: "...", limit: 10}',
                        fetch: 'Fetch webpage: {command: "fetch", url: "...", maxLength: 5000}',
                        datetime: 'Get datetime: {command: "datetime", timezone: "Asia/Seoul"}',
                        tools: 'List tools: {command: "tools"}',
                        health: 'Check status: {command: "health"}',
                    },
                    server_url: MCPBridgeConfig.serverUrl
                };
        }

    } catch (error) {
        return {
            success: false,
            error: error.message,
            stack: error.stack
        };
    }
}

// Export for RisuAI
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { plugin, mcpBridge, MCPBridgePlugin };
}
