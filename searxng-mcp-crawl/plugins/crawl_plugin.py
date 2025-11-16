from plugin_base import MCPPlugin
from typing import Dict, Any, List
from crawler import WebCrawler
import asyncio


class CrawlPlugin(MCPPlugin):
    """
    Advanced Web Crawling Plugin with Auto-Chunking
    """

    def __init__(self):
        try:
            self.crawler = WebCrawler()
            print("   🕷️ CrawlPlugin: Crawler initialized")
        except Exception as e:
            print(f"   ⚠️ CrawlPlugin: Crawler init error: {e}")
            self.crawler = None

    @property
    def name(self) -> str:
        return "fetch_webpage"

    @property
    def description(self) -> str:
        return "Fetch webpage content with auto-chunking. Params: urls, limit=3, max_length=10000."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "urls": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 3},
                "max_length": {"type": "integer", "default": 10000},
            },
        }

    @property
    def version(self) -> str:
        return "3.0.0"

    @property
    def author(self) -> str:
        return "damin25soka7"

    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        if not isinstance(url, str):
            return False
        return url.startswith(("http://", "https://"))

    def _chunk_text(
        self, text: str, chunk_size: int, overlap: int
    ) -> List[Dict[str, Any]]:
        """Internal chunking method - does NOT count as separate step"""
        chunks = []
        start = 0
        chunk_num = 1
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk_content = text[start:end]

            chunks.append(
                {
                    "chunk_number": chunk_num,
                    "content": chunk_content,
                    "start_pos": start,
                    "end_pos": end,
                    "length": len(chunk_content),
                }
            )

            chunk_num += 1
            start = end - overlap

            # Prevent infinite loop
            if start >= end:
                break

        return chunks

    async def fetch_single_url(
        self,
        url: str,
        max_length: int,
        include_metadata: bool,
        timeout: int,
        index: int = 0,
    ) -> Dict[str, Any]:
        """Fetch a single URL with error handling"""
        try:
            print(f"      [{index}] Fetching: {url[:60]}...")

            result = await self.crawler.fetch_webpage(
                url=url, max_length=max_length, timeout=timeout
            )

            if isinstance(result, dict):
                if result.get("success") or "content" in result:
                    content_length = len(result.get("content", ""))
                    print(f"      [{index}] ✅ Success ({content_length:,} chars)")

                    response = {
                        "success": True,
                        "url": url,
                        "content": result.get("content", ""),
                        "content_length": content_length,
                    }

                    if include_metadata:
                        response["metadata"] = {
                            "title": result.get("title", ""),
                            "description": result.get("description", ""),
                            "language": result.get("language", ""),
                            "word_count": len(result.get("content", "").split()),
                        }

                    return response
                else:
                    print(
                        f"      [{index}] ❌ Failed: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "url": url,
                        "error": result.get("error", "Unknown error"),
                    }

            return {"success": False, "url": url, "error": "Invalid response format"}

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"      [{index}] ❌ Exception: {error_msg}")
            return {"success": False, "url": url, "error": error_msg}

    async def fetch_batch(
        self,
        urls: List[str],
        max_length: int,
        include_metadata: bool,
        timeout: int,
        batch_size: int,
    ) -> List[Dict[str, Any]]:
        """Fetch URLs in batches for optimal performance"""
        all_results = []

        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(urls) + batch_size - 1) // batch_size

            print(f"   📦 Batch {batch_num}/{total_batches}: {len(batch)} URLs")

            tasks = [
                self.fetch_single_url(
                    url, max_length, include_metadata, timeout, i + idx + 1
                )
                for idx, url in enumerate(batch)
            ]

            batch_results = await asyncio.gather(*tasks)
            all_results.extend(batch_results)

            if i + batch_size < len(urls):
                await asyncio.sleep(0.5)

        return all_results

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute webpage fetching with automatic chunking
        """
        single_url = arguments.get("url", "").strip()
        url_list = arguments.get("urls", [])
        limit = arguments.get("limit", 3)
        max_length = arguments.get("max_length", 5000)  # Reduced default
        include_metadata = arguments.get("include_metadata", True)
        timeout = arguments.get("timeout", 30)
        batch_size = arguments.get("batch_size", 10)

        # Auto-chunking parameters
        auto_chunk = arguments.get("auto_chunk", True)
        chunk_threshold = arguments.get("chunk_threshold", 30000)  # Reduced threshold
        chunk_size = arguments.get("chunk_size", 15000)  # Reduced chunk size
        chunk_overlap = arguments.get("chunk_overlap", 200)  # Reduced overlap

        # NEW: Response size control
        max_response_chars = arguments.get("max_response_chars", 50000)  # Limit total response

        # Validation
        if not single_url and not url_list:
            return {
                "success": False,
                "error": "Either 'url' or 'urls' parameter is required",
            }

        if single_url and url_list:
            return {
                "success": False,
                "error": "Provide either 'url' or 'urls', not both",
            }

        # Prepare URL list
        if single_url:
            if not self.validate_url(single_url):
                return {"success": False, "error": f"Invalid URL format: {single_url}"}
            urls_to_fetch = [single_url]
        else:
            valid_urls = [url for url in url_list if self.validate_url(url)]
            invalid_urls = [url for url in url_list if not self.validate_url(url)]

            if invalid_urls:
                print(f"   ⚠️ Skipping {len(invalid_urls)} invalid URLs")

            if not valid_urls:
                return {"success": False, "error": "No valid URLs provided"}

            urls_to_fetch = valid_urls[:limit]

        # Clamp parameters
        limit = max(1, min(20, limit))
        max_length = max(100, min(50000, max_length))
        timeout = max(5, min(120, timeout))
        batch_size = max(1, min(20, batch_size))
        chunk_threshold = max(10000, min(200000, chunk_threshold))
        chunk_size = max(5000, min(50000, chunk_size))
        chunk_overlap = max(0, min(2000, chunk_overlap))

        total_urls = len(urls_to_fetch)

        print(f"\n🕷️ fetch_webpage v3.0 (Auto-Chunking)")
        print(f"   URLs to fetch: {total_urls}")
        print(f"   Max length: {max_length:,} chars")
        print(f"   Timeout: {timeout}s")
        print(f"   Batch size: {batch_size}")
        print(f"   Include metadata: {include_metadata}")
        print(f"   Auto-chunk: {auto_chunk} (threshold: {chunk_threshold:,} chars)")

        import time

        start_time = time.time()

        # Fetch URLs
        if total_urls == 1:
            results = [
                await self.fetch_single_url(
                    urls_to_fetch[0], max_length, include_metadata, timeout, 1
                )
            ]
        else:
            results = await self.fetch_batch(
                urls_to_fetch, max_length, include_metadata, timeout, batch_size
            )

        elapsed_time = time.time() - start_time

        # Count successes and failures
        successful = sum(1 for r in results if r.get("success"))
        failed = total_urls - successful

        # Calculate total content size
        total_content_size = sum(
            len(r.get("content", "")) for r in results if r.get("success")
        )

        print(f"\n   📊 Results: {successful} successful, {failed} failed")
        print(f"   📏 Total content: {total_content_size:,} chars")
        print(
            f"   ⏱️ Total time: {elapsed_time:.2f}s ({elapsed_time/total_urls:.2f}s per URL)"
        )

        # Auto-chunking decision
        chunked = False
        chunks = []

        if auto_chunk and total_content_size > chunk_threshold:
            print(
                f"\n   ⚠️ Large content detected ({total_content_size:,} chars > {chunk_threshold:,})"
            )
            print(f"   ✂️ Auto-chunking enabled...")

            # Combine all successful content
            combined_content = "\n\n---PAGE SEPARATOR---\n\n".join(
                [
                    f"[Source: {r['url']}]\n{r.get('content', '')}"
                    for r in results
                    if r.get("success")
                ]
            )

            # Chunk the combined content
            chunks = self._chunk_text(combined_content, chunk_size, chunk_overlap)
            chunked = True

            print(f"   ✂️ Created {len(chunks)} chunks")
            for i, chunk in enumerate(chunks[:3], 1):
                print(f"      Chunk {i}: {chunk['length']:,} chars")
            if len(chunks) > 3:
                print(f"      ... ({len(chunks) - 3} more chunks)")
        else:
            print(
                f"   ℹ️ Content size OK ({total_content_size:,} chars), no chunking needed"
            )

        # CRITICAL: Truncate results to prevent token overflow
        truncated_results = []
        current_size = 0

        for r in results:
            if r.get("success"):
                content = r.get("content", "")
                # Truncate individual content if too large
                if len(content) > max_length:
                    content = content[:max_length] + f"\n...[TRUNCATED: {len(r.get('content', '')) - max_length} chars omitted]"

                # Check if adding this would exceed limit
                if current_size + len(content) > max_response_chars:
                    remaining = max_response_chars - current_size
                    if remaining > 1000:
                        content = content[:remaining] + f"\n...[TRUNCATED: response size limit reached]"
                        truncated_results.append({**r, "content": content, "truncated": True})
                    else:
                        truncated_results.append({
                            "success": True,
                            "url": r["url"],
                            "content": "[OMITTED: response size limit reached]",
                            "content_length": len(r.get("content", "")),
                            "omitted": True
                        })
                    break
                else:
                    truncated_results.append({**r, "content": content})
                    current_size += len(content)
            else:
                truncated_results.append(r)

        # Build response
        response = {
            "success": True,
            "total_urls": total_urls,
            "successful": successful,
            "failed": failed,
            "results": truncated_results,  # Use truncated results
            "total_content_size": total_content_size,
            "response_content_size": current_size,
            "chunked": chunked,
            "performance": {
                "total_time_seconds": round(elapsed_time, 2),
                "avg_time_per_url": round(elapsed_time / total_urls, 2),
                "urls_per_second": round(total_urls / elapsed_time, 2),
            },
            "parameters": {
                "max_length": max_length,
                "include_metadata": include_metadata,
                "timeout": timeout,
                "batch_size": batch_size,
                "auto_chunk": auto_chunk,
                "chunk_threshold": chunk_threshold,
                "max_response_chars": max_response_chars,
            },
        }

        # Add chunk METADATA only (NOT full content) to prevent token overflow
        if chunked:
            # Only include first chunk content, rest are metadata only
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                if i == 0:
                    # First chunk: include content (limited)
                    chunk_metadata.append({
                        "chunk_number": chunk["chunk_number"],
                        "content": chunk["content"][:max_length] if len(chunk["content"]) > max_length else chunk["content"],
                        "length": chunk["length"],
                        "is_first": True
                    })
                else:
                    # Other chunks: metadata only
                    chunk_metadata.append({
                        "chunk_number": chunk["chunk_number"],
                        "length": chunk["length"],
                        "start_pos": chunk["start_pos"],
                        "end_pos": chunk["end_pos"],
                        "content_preview": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
                    })

            response["chunks"] = chunk_metadata
            response["total_chunks"] = len(chunks)
            response["avg_chunk_size"] = sum(c["length"] for c in chunks) // len(chunks)
            response["note"] = "Only first chunk has full content. Other chunks have metadata and preview only to save tokens."

            print(
                f"\n   ✅ Auto-chunking complete: {len(chunks)} chunks (first chunk full, others metadata only)"
            )

        return response
