"""公開 HTML scraper：使用 requests + BeautifulSoup 抓取公開網頁。"""

import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}
TIMEOUT = 15  # seconds


def fetch_html(url: str, timeout: int = TIMEOUT) -> Optional[str]:
    """抓取 URL 的原始 HTML，失敗時回傳 None。"""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return resp.text
    except requests.RequestException as e:
        logger.warning("無法抓取 %s：%s", url, e)
        return None


def extract_text_blocks(html: str, source_url: str = "") -> list[dict]:
    """
    從 HTML 擷取有意義的文字區塊，回傳 list[dict]。

    每個 dict 包含：
      - text: 清理後的文字
      - tag: 原始 HTML tag
      - source_url: 來源 URL
    """
    soup = BeautifulSoup(html, "lxml")

    # 移除 script / style / nav / footer 雜訊
    for tag in soup(["script", "style", "nav", "footer", "head"]):
        tag.decompose()

    blocks = []
    for tag in soup.find_all(["p", "li", "td", "th", "h1", "h2", "h3", "h4", "div"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) < 15:
            continue
        blocks.append({"text": text, "tag": tag.name, "source_url": source_url})

    return blocks


def scrape_source(source: dict) -> list[dict]:
    """
    根據 sources.yaml 中的 source 定義抓取 HTML，回傳文字區塊清單。
    source_type 必須是 'html'。
    """
    url = source.get("url", "")
    if not url:
        logger.info("來源 %s 沒有 URL，跳過", source.get("id"))
        return []

    logger.info("抓取 HTML：%s（%s）", source.get("name"), url)
    html = fetch_html(url)
    if html is None:
        return []

    blocks = extract_text_blocks(html, source_url=url)
    # 把 source 的 metadata 注入每個 block，方便後續處理
    for b in blocks:
        b["source_id"] = source.get("id")
        b["source_name"] = source.get("name")
        b["source_confidence"] = source.get("source_confidence", "medium")
        b["is_nycu_official"] = source.get("is_nycu_official", False)
        b["category_hint"] = source.get("category_hint", "其他")

    return blocks
