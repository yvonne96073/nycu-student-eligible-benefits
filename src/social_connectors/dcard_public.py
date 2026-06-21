"""
Dcard public connector（experimental）。

只處理 Dcard 公開版面或公開搜尋結果，不登入，不抓需要帳號才能看的內容。
此 connector 標記為 experimental，Dcard 公開 API 穩定性不保證。
"""

import logging

import requests
from bs4 import BeautifulSoup

from .base import SocialConnector

logger = logging.getLogger(__name__)

DCARD_API_POSTS = "https://www.dcard.tw/service/api/v2/posts"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.dcard.tw/",
}


class DcardPublicConnector(SocialConnector):
    """
    Experimental：使用 Dcard 非官方公開 API 讀取優惠版文章。
    不登入，只讀公開版面（/f/deal 等）。
    如果 API 不穩定或被限制，此 connector 會跳過，不讓主程式失敗。
    """

    @property
    def source_channel(self) -> str:
        return "dcard_public"

    def is_available(self) -> bool:
        return True  # 不需要 token，但 experimental

    def fetch_recent_posts(self, source: dict) -> list[dict]:
        forum = "deal"  # Dcard 優惠版
        try:
            resp = requests.get(
                DCARD_API_POSTS,
                params={"forumAlias": forum, "limit": 30},
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            posts = resp.json()
            return posts if isinstance(posts, list) else []
        except Exception as e:
            logger.warning(
                "[dcard_public] 抓取失敗（experimental，可能受限制）：%s", e
            )
            return []

    def normalize_post(self, raw_post: dict, source: dict) -> dict:
        post_id = raw_post.get("id", "")
        return {
            "text": raw_post.get("title", "") + " " + raw_post.get("excerpt", ""),
            "tag": "dcard_post",
            "source_url": f"https://www.dcard.tw/f/deal/p/{post_id}" if post_id else "",
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_confidence": "low",  # experimental，信心度低
            "is_nycu_official": False,
            "category_hint": source.get("category_hint", "綜合"),
            "source_channel": self.source_channel,
        }
