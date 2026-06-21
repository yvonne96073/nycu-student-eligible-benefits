"""
搜尋來源 adapter：管理搜尋類型來源。

優先使用 Firecrawl（FIRECRAWL_API_KEY），
備援使用 Google Custom Search JSON API（GOOGLE_API_KEY + GOOGLE_CSE_ID），
都沒有時印出 stub 提示。
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

_GOOGLE_SEARCH_BASE = "https://www.google.com/search?q={query}&hl=zh-TW"
_FIRECRAWL_SEARCH_URL = "https://api.firecrawl.dev/v1/search"


def build_search_urls(source: dict) -> list[dict]:
    """組成 Google 搜尋 URL stub 清單（fallback 用）。"""
    keywords = source.get("keywords", [])
    results = []
    for kw in keywords:
        encoded = kw.replace(" ", "+")
        url = _GOOGLE_SEARCH_BASE.format(query=encoded)
        results.append({
            "keyword": kw,
            "url": url,
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_confidence": source.get("source_confidence", "medium"),
            "is_nycu_official": source.get("is_nycu_official", False),
            "category_hint": source.get("category_hint", "綜合"),
        })
    return results


# ── Firecrawl 搜尋 ───────────────────────────────────────────────────────────

def _firecrawl_search(query: str, api_key: str, limit: int = 5) -> list[dict]:
    """呼叫 Firecrawl Search API，回傳搜尋結果清單。"""
    try:
        resp = requests.post(
            _FIRECRAWL_SEARCH_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "limit": limit,
                "scrapeOptions": {
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data.get("data", [])
    except Exception as e:
        logger.warning("Firecrawl 搜尋失敗 (%s)：%s", query, e)
    return []


def _firecrawl_fetch(source: dict) -> list[dict]:
    """使用 Firecrawl 搜尋所有 keywords，回傳 block 清單。"""
    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    keywords = source.get("keywords", [])
    blocks = []

    for kw in keywords:
        logger.info("  Firecrawl 搜尋：%s", kw)
        results = _firecrawl_search(kw, api_key, limit=5)
        if not results:
            logger.warning("  Firecrawl 搜尋「%s」無結果", kw)
        for item in results:
            # Firecrawl 回傳格式：{url, title, description, markdown?}
            text = item.get("markdown") or item.get("description") or ""
            if not text:
                continue
            blocks.append({
                "text": text[:2000],  # 限制長度避免過大
                "tag": "search_result",
                "source_url": item.get("url", ""),
                "title": item.get("title", ""),
                "source_id": source.get("id"),
                "source_name": source.get("name"),
                "source_confidence": source.get("source_confidence", "medium"),
                "is_nycu_official": source.get("is_nycu_official", False),
                "category_hint": source.get("category_hint", "綜合"),
                "keyword": kw,
                "source_channel": "google_search",
            })

    return blocks


# ── Google Custom Search JSON API ────────────────────────────────────────────

def _google_cse_fetch(source: dict) -> list[dict]:
    """使用 Google Custom Search JSON API 搜尋。"""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    cse_id = os.getenv("GOOGLE_CSE_ID", "")
    keywords = source.get("keywords", [])
    blocks = []

    for kw in keywords:
        try:
            params = {
                "key": api_key, "cx": cse_id, "q": kw, "hl": "zh-TW", "num": 10,
            }
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params, timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                blocks.append({
                    "text": item.get("snippet", ""),
                    "tag": "search_result",
                    "source_url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "source_id": source.get("id"),
                    "source_name": source.get("name"),
                    "source_confidence": source.get("source_confidence", "medium"),
                    "is_nycu_official": source.get("is_nycu_official", False),
                    "category_hint": source.get("category_hint", "綜合"),
                    "keyword": kw,
                    "source_channel": "google_search",
                })
        except Exception as e:
            logger.warning("Google CSE 呼叫失敗 (%s, %s)：%s", source.get("id"), kw, e)

    return blocks


# ── 對外主函式 ────────────────────────────────────────────────────────────────

def fetch_search_results(source: dict) -> list[dict]:
    """
    搜尋來源主入口。優先順序：
    1. Firecrawl（FIRECRAWL_API_KEY）
    2. Google Custom Search（GOOGLE_API_KEY + GOOGLE_CSE_ID）
    3. Stub（印出搜尋 URL）
    """
    keywords = source.get("keywords", [])
    if not keywords:
        logger.info("來源 %s 沒有 keywords，跳過", source.get("id"))
        return []

    # 1. Firecrawl
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")
    if firecrawl_key:
        logger.info("[Firecrawl] 搜尋來源：%s（%d 組關鍵字）", source.get("name"), len(keywords))
        return _firecrawl_fetch(source)

    # 2. Google CSE
    google_key = os.getenv("GOOGLE_API_KEY", "")
    google_cse = os.getenv("GOOGLE_CSE_ID", "")
    if google_key and google_cse:
        logger.info("[Google CSE] 搜尋來源：%s（%d 組關鍵字）", source.get("name"), len(keywords))
        return _google_cse_fetch(source)

    # 3. Stub
    logger.info(
        "[搜尋來源 stub] %s：需要 FIRECRAWL_API_KEY 或 GOOGLE_API_KEY + GOOGLE_CSE_ID。",
        source.get("name")
    )
    urls = build_search_urls(source)
    for u in urls:
        logger.info("  stub: %s → %s", u["keyword"], u["url"])
    return []
