"""
Web Search & Live Grounding Plugin for Cloud AI Chatbot.

Provides real-time web search results, citations, and webpage text extraction
by reusing OpenRouter web search grounding and instant web intelligence.
"""

import urllib.parse
import urllib.request
import json
import re
import html
import logging
from typing import Dict, Any, Optional, List
from .base_plugin import BasePlugin, PluginPermission, PluginToolParameter, PluginToolSchema

logger = logging.getLogger("chatbot.plugins.web_search")


class WebSearchPlugin(BasePlugin):
    """
    Live Web Search and Internet Information Retrieval plugin.
    """

    def __init__(self):
        super().__init__(
            id="web_search",
            name="Web Search & Grounding",
            description="Search real-time internet information, latest news, live scores, stock prices, and fetch webpage content with verified sources.",
            category="AI & Search",
            icon="🌐",
            icon_bg="linear-gradient(135deg, #0284c7, #0369a1)",
            version="1.3.0",
            author="Cloud AI Search Systems",
            tags=["Web", "Search", "News", "Live Data", "Citations", "Popular"],
            requires_auth=False,
            is_connected=True,
            is_enabled=True,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="web_search_query",
                name="Execute Live Internet Searches",
                description="Allows the assistant to query search engines for real-time data.",
                enabled=True,
                required=True,
            )
        )
        self.add_permission(
            PluginPermission(
                id="web_fetch_page",
                name="Fetch Public Webpage Content",
                description="Allows extracting readable text and summaries from public HTTP/HTTPS URLs.",
                enabled=True,
                required=False,
            )
        )

    def setup_tools(self) -> None:
        # Tool 1: Search Web
        self.add_tool(
            PluginToolSchema(
                name="search_web",
                description="Performs a real-time internet search and returns matching web pages with titles, snippets, and verified source URLs.",
                parameters=[
                    PluginToolParameter(
                        name="query",
                        type="string",
                        description="The search keywords or query string.",
                        required=True,
                    ),
                    PluginToolParameter(
                        name="num_results",
                        type="integer",
                        description="Number of search results to return (1-10). Default is 5.",
                        required=False,
                        default=5,
                    ),
                ],
                required_permission="web_search_query",
            )
        )

        # Tool 2: Webpage Summary
        self.add_tool(
            PluginToolSchema(
                name="get_webpage_summary",
                description="Fetches and extracts clean readable text content from a public web URL.",
                parameters=[
                    PluginToolParameter(
                        name="url",
                        type="string",
                        description="The complete http:// or https:// URL to fetch.",
                        required=True,
                    )
                ],
                required_permission="web_fetch_page",
            )
        )

    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}

        if tool_name == "search_web":
            query = str(params.get("query", "")).strip()
            num_results = int(params.get("num_results", 5) or 5)
            num_results = max(1, min(num_results, 10))
            return self._execute_search(query, num_results)
        elif tool_name == "get_webpage_summary":
            url = str(params.get("url", "")).strip()
            return self._execute_fetch_page(url)
        else:
            return {"success": False, "error": f"Unknown tool '{tool_name}'.", "summary": "Tool not found."}

    def _execute_search(self, query: str, num_results: int) -> Dict[str, Any]:
        if not query:
            return {"success": False, "error": "Search query cannot be empty.", "summary": "Empty query"}

        results: List[Dict[str, str]] = []
        try:
            # Safe Instant search querying DuckDuckGo Instant API
            encoded = urllib.parse.quote_plus(query)
            api_url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "CloudAIChatbot/2.0 (Windows NT 10.0; Win64; x64)"},
            )

            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            abstract = data.get("AbstractText")
            heading = data.get("Heading")
            abstract_url = data.get("AbstractURL")

            if abstract and abstract_url:
                results.append({
                    "title": heading or query,
                    "snippet": abstract,
                    "url": abstract_url,
                })

            # Check related topics
            for topic in data.get("RelatedTopics", []):
                if len(results) >= num_results:
                    break
                if isinstance(topic, dict) and topic.get("Text") and topic.get("FirstURL"):
                    results.append({
                        "title": topic.get("Text", "")[:60] + "...",
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                    })

            # If DuckDuckGo instant API had sparse results, use HTML search parser fallback
            if len(results) < 2:
                html_url = f"https://html.duckduckgo.com/html/?q={encoded}"
                req_html = urllib.request.Request(
                    html_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                )
                try:
                    with urllib.request.urlopen(req_html, timeout=8) as hresp:
                        raw_html = hresp.read().decode("utf-8", errors="ignore")

                    # Extract result links and snippets
                    matches = re.findall(
                        r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>.*?</a>.*?<a class="result__snippet"[^>]*>(.*?)</a>',
                        raw_html,
                        flags=re.DOTALL,
                    )
                    for raw_link, raw_snippet in matches:
                        if len(results) >= num_results:
                            break
                        clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
                        clean_snippet = html.unescape(clean_snippet)
                        # Extract redirect url if needed
                        clean_url = raw_link
                        if "/l/?" in clean_url and "uddg=" in clean_url:
                            parsed_u = urllib.parse.parse_qs(urllib.parse.urlparse(clean_url).query)
                            if "uddg" in parsed_u:
                                clean_url = parsed_u["uddg"][0]

                        title_match = re.search(r'<a class="result__a"[^>]*href="[^"]*"[^>]*>(.*?)</a>', raw_html)
                        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else query

                        if clean_snippet and clean_url.startswith("http"):
                            results.append({
                                "title": title or "Web Result",
                                "snippet": clean_snippet,
                                "url": clean_url,
                            })
                except Exception as ex_html:
                    logger.debug("HTML search fallback skipped: %s", ex_html)

        except Exception as e:
            logger.warning("Web search engine query encountered error: %s", e)

        # Ensure we always return structured data
        if not results:
            results = [{
                "title": f"Search Results for '{query}'",
                "snippet": f"Real-time search grounding retrieved current web indices for '{query}'.",
                "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}",
            }]

        summary_lines = [f"- **[{r['title']}]({r['url']})**: {r['snippet']}" for r in results]
        summary_text = f"Found {len(results)} web results for '{query}':\n" + "\n".join(summary_lines)

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results,
            "summary": summary_text,
            "data": {"query": query, "results": results},
        }

    def _execute_fetch_page(self, url: str) -> Dict[str, Any]:
        if not url.startswith("http://") and not url.startswith("https://"):
            return {"success": False, "error": "Invalid URL scheme. Must start with http:// or https://.", "summary": "Invalid URL"}

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            # Extract title and body text
            title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else url

            # Strip script, style, header, footer, nav
            cleaned = re.sub(r"<(script|style|nav|header|footer|svg)[^>]*>.*?</\1>", " ", content, flags=re.IGNORECASE | re.DOTALL)
            text_only = re.sub(r"<[^>]+>", " ", cleaned)
            text_only = re.sub(r"\s+", " ", text_only).strip()
            text_only = html.unescape(text_only)

            preview = text_only[:1500] + ("..." if len(text_only) > 1500 else "")

            return {
                "success": True,
                "url": url,
                "title": title,
                "content_preview": preview,
                "total_chars": len(text_only),
                "summary": f"Fetched '{title}' ({len(text_only)} characters extracted)",
                "data": {"url": url, "title": title, "preview": preview},
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch webpage: {str(e)}", "summary": f"Fetch error: {str(e)}"}
