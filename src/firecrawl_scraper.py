"""
firecrawl_scraper.py：使用 Firecrawl API 抓取 JS 重的網站。

當 FIRECRAWL_API_KEY 有設定時，自動取代 requests-based scraper。
Firecrawl 會渲染 JS、取得完整 DOM 內容，適合 SPA 或動態載入頁面。
沒有 API key 時自動 fallback 到 requests-based scraper。
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

_FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"


def is_available() -> bool:
    return bool(os.getenv("FIRECRAWL_API_KEY", ""))


def firecrawl_scrape(url: str) -> str | None:
    """
    使用 Firecrawl Scrape API 抓取單一 URL，回傳 markdown 格式文字。
    失敗時回傳 None。
    """
    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = requests.post(
            _FIRECRAWL_SCRAPE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "waitFor": 3000,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data.get("data", {}).get("markdown", "")
    except Exception as e:
        logger.warning("Firecrawl scrape 失敗 (%s)：%s", url, e)
    return None


def scrape_source_firecrawl(source: dict) -> list[dict]:
    """
    用 Firecrawl 抓取 source，回傳文字區塊清單。
    格式與 scraper.py 的 scrape_source() 相容。
    """
    url = source.get("url", "")
    if not url:
        return []

    logger.info("Firecrawl 抓取：%s（%s）", source.get("name"), url)
    markdown = firecrawl_scrape(url)
    if not markdown:
        return []

    blocks = []
    for line in markdown.split("\n"):
        line = line.strip()
        if len(line) < 15:
            continue
        blocks.append({
            "text": line,
            "tag": "firecrawl_md",
            "source_url": url,
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_confidence": source.get("source_confidence", "medium"),
            "is_nycu_official": source.get("is_nycu_official", False),
            "category_hint": source.get("category_hint", "其他"),
        })

    return blocks
