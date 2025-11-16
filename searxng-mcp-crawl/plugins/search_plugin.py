from plugin_base import MCPPlugin
from typing import Dict, Any, List
from crawler import WebCrawler


class SearchPlugin(MCPPlugin):
    """
    Advanced Web Search Plugin with SearXNG

    Features:
    - Customizable result limit (1-50)
    - Search categories (general, news, images, etc.)
    - Language filtering
    - Time range filtering
    - Safe search toggle
    """

    def __init__(self):
        self.crawler = WebCrawler()

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search web via SearXNG. Params: query, limit=10, category=general."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
                "category": {"type": "string", "default": "general"},
            },
            "required": ["query"],
        }

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def author(self) -> str:
        return "damin25soka7"

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute web search with customizable parameters

        Args:
            query: Search query string
            limit: Number of results (1-50, default: 10)
            category: Search category (default: general)
            language: Language preference (default: auto)
            time_range: Filter by time (default: none)
            safe_search: Safe search level (default: 1)

        Returns:
            {
                "success": bool,
                "query": str,
                "results_count": int,
                "results": [...],
                "parameters": {...}
            }
        """
        query = arguments.get("query", "").strip()
        limit = arguments.get("limit", 10)
        category = arguments.get("category", "general")
        language = arguments.get("language", "auto")
        time_range = arguments.get("time_range", "")
        safe_search = arguments.get("safe_search", 1)

        # Validation
        if not query:
            return {
                "success": False,
                "error": "Query parameter is required and cannot be empty",
            }

        # Clamp limit to valid range (reduced max to prevent token overflow)
        limit = max(1, min(15, limit))  # Max 15 results to save tokens

        print(f"\n🔍 search")
        print(f"   Query: {query}")
        print(f"   Limit: {limit}")
        print(f"   Category: {category}")
        if language != "auto":
            print(f"   Language: {language}")
        if time_range:
            print(f"   Time range: {time_range}")
        print(f"   Safe search: {safe_search}")

        try:
            # Call crawler with parameters
            results = await self.crawler.search_searxng(
                query=query,
                limit=limit,
                category=category,
                language=language,
                time_range=time_range,
                safe_search=safe_search,
            )

            # Check if results were successful
            if isinstance(results, dict) and results.get("success") is False:
                print(f"   ❌ Search failed: {results.get('error', 'Unknown error')}")
                return results

            # Extract result count
            result_list = (
                results if isinstance(results, list) else results.get("results", [])
            )
            result_count = len(result_list)

            print(f"   ✅ Found {result_count} results")

            return {
                "success": True,
                "query": query,
                "results_count": result_count,
                "results": result_list,
                "parameters": {
                    "limit": limit,
                    "category": category,
                    "language": language,
                    "time_range": time_range,
                    "safe_search": safe_search,
                },
            }

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"   ❌ Error: {error_msg}")

            return {"success": False, "error": error_msg, "query": query}
