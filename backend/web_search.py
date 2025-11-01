from duckduckgo_search import ddg
import logging

logger = logging.getLogger(__name__)

def web_search(query, max_results=3):
    """
    Perform a lightweight web search using DuckDuckGo (no API key required).
    Returns a list of dicts: {"title","snippet","url","source":"web"}.
    """
    try:
        results = ddg(query, max_results=max_results)
        if not results:
            return []
        out = []
        for r in results:
            out.append({
                "title": r.get("title"),
                "snippet": r.get("body") or r.get("snippet") or "",
                "url": r.get("href") or r.get("url"),
                "source": "web"
            })
        logger.info("web_search: query=%s returned=%d", query, len(out))
        return out
    except Exception as e:
        logger.exception("web_search failed: %s", e)
        return []
