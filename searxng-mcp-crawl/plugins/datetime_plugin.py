from plugin_base import MCPPlugin
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime, timezone
import asyncio

class DateTimePlugin(MCPPlugin):
    """
    World Time API Plugin - Get accurate time for multiple cities using WorldTimeAPI
    """

    def __init__(self):
        self.base_url = "https://worldtimeapi.org/api/timezone"

        # City to timezone mapping
        self.city_timezone_map = {
            # Asia
            "seoul": "Asia/Seoul",
            "tokyo": "Asia/Tokyo",
            "beijing": "Asia/Shanghai",
            "shanghai": "Asia/Shanghai",
            "singapore": "Asia/Singapore",
            "hong kong": "Asia/Hong_Kong",
            "taipei": "Asia/Taipei",
            "bangkok": "Asia/Bangkok",
            "mumbai": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
            "dubai": "Asia/Dubai",

            # Europe
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "moscow": "Europe/Moscow",
            "rome": "Europe/Rome",
            "madrid": "Europe/Madrid",
            "amsterdam": "Europe/Amsterdam",
            "zurich": "Europe/Zurich",

            # Americas
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles",
            "chicago": "America/Chicago",
            "toronto": "America/Toronto",
            "vancouver": "America/Vancouver",
            "sao paulo": "America/Sao_Paulo",
            "mexico city": "America/Mexico_City",

            # Oceania
            "sydney": "Australia/Sydney",
            "melbourne": "Australia/Melbourne",
            "auckland": "Pacific/Auckland",

            # UTC
            "utc": "UTC",
            "gmt": "Europe/London",
        }

        print("   🕐 DateTimePlugin: WorldTimeAPI initialized")

    @property
    def name(self) -> str:
        return "get_current_datetime"

    @property
    def description(self) -> str:
        return "Get current time for cities. Default: Seoul. Params: cities (array)."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["Seoul"]
                }
            },
            "required": []
        }

    @property
    def version(self) -> str:
        return "3.1.0"

    @property
    def author(self) -> str:
        return "damin25soka7"

    def get_timezone_for_city(self, city: str) -> Optional[str]:
        """Get timezone identifier for a city name"""
        city_lower = city.lower().strip()

        # Direct match
        if city_lower in self.city_timezone_map:
            return self.city_timezone_map[city_lower]

        # Partial match
        for city_key, tz in self.city_timezone_map.items():
            if city_lower in city_key or city_key in city_lower:
                return tz

        # If it looks like a timezone path, use it directly
        if "/" in city:
            return city

        return None

    async def fetch_timezone_data(self, timezone_id: str, timeout: int = 10) -> Dict[str, Any]:
        """Fetch timezone data from WorldTimeAPI"""
        url = f"{self.base_url}/{timezone_id}"

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()
                return {
                    "success": True,
                    "data": data
                }

        except httpx.TimeoutException:
            return {"success": False, "error": f"Request timed out for {timezone_id}"}

        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code} for {timezone_id}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def format_timezone_response(self, city: str, data: Dict[str, Any], include_details: bool) -> Dict[str, Any]:
        """Format the API response into a clean structure"""
        result = {
            "city": city,
            "timezone": data.get("timezone", "Unknown"),
            "datetime": data.get("datetime", ""),
            "abbreviation": data.get("abbreviation", ""),
            "utc_offset": data.get("utc_offset", ""),
        }

        # Parse datetime for readable format
        if "datetime" in data:
            try:
                dt_str = data["datetime"]
                # Extract just the time part for quick reading
                if "T" in dt_str:
                    date_part, time_part = dt_str.split("T")
                    time_clean = time_part.split(".")[0] if "." in time_part else time_part.split("+")[0].split("-")[0]
                    result["date"] = date_part
                    result["time"] = time_clean
                    result["readable"] = f"{date_part} {time_clean}"
            except:
                pass

        if include_details:
            result["day_of_week"] = data.get("day_of_week", 0)
            result["day_of_year"] = data.get("day_of_year", 0)
            result["week_number"] = data.get("week_number", 0)
            result["dst"] = data.get("dst", False)
            result["dst_offset"] = data.get("dst_offset", 0)
            result["unixtime"] = data.get("unixtime", 0)

        return result

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current date and time for specified cities
        """
        # Default to Seoul if no cities specified
        cities = arguments.get("cities", ["Seoul"])
        if not cities:
            cities = ["Seoul"]

        include_details = arguments.get("include_details", True)
        timeout = arguments.get("timeout", 10)

        print(f"\n🕐 get_current_datetime")
        print(f"   Cities: {', '.join(cities)}")

        results = {}
        errors = []

        # Fetch data for each city
        for city in cities:
            timezone_id = self.get_timezone_for_city(city)

            if not timezone_id:
                errors.append(f"Unknown city: {city}")
                print(f"      ❌ Unknown: {city}")
                continue

            print(f"      🌐 Fetching {city} ({timezone_id})...")

            response = await self.fetch_timezone_data(timezone_id, timeout)

            if response["success"]:
                formatted = self.format_timezone_response(city, response["data"], include_details)
                results[city] = formatted
                print(f"      ✅ {city}: {formatted.get('readable', 'N/A')} ({formatted.get('abbreviation', '')})")
            else:
                errors.append(f"{city}: {response['error']}")
                print(f"      ❌ {city}: {response['error']}")

        # Build final response
        response = {
            "success": len(results) > 0,
            "request_time_utc": datetime.now(timezone.utc).isoformat(),
            "total_requested": len(cities),
            "total_success": len(results),
            "results": results
        }

        if errors:
            response["errors"] = errors

        # Summary for tool planner
        if results:
            summary_parts = []
            for city, data in results.items():
                summary_parts.append(f"{city}: {data.get('readable', 'N/A')} {data.get('abbreviation', '')}")
            response["summary"] = " | ".join(summary_parts)

        print(f"\n   ✅ Complete: {len(results)}/{len(cities)} cities")

        return response