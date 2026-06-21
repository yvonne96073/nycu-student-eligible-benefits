"""
Instagram connector：使用 Instagram Graph API 讀取商家帳號貼文。

第一版為 stub。
需要 Instagram Graph API token（INSTAGRAM_ACCESS_TOKEN）。
不使用登入爬蟲，不抓私人帳號或限動。
"""

import logging
import os

from .base import SocialConnector

logger = logging.getLogger(__name__)


class InstagramConnector(SocialConnector):
    """
    合法授權方式：Instagram Graph API。
    只支援已授權的 Instagram Business / Creator 帳號。
    不使用 selenium / playwright 自動登入。
    不抓私人帳號或限時動態。
    """

    @property
    def source_channel(self) -> str:
        return "instagram_api"

    def is_available(self) -> bool:
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        if not token:
            logger.info(
                "[instagram_connector] INSTAGRAM_ACCESS_TOKEN 未設定，跳過 Instagram 來源。"
                "如需啟用，請在 .env 填入 Instagram Graph API token。"
            )
            return False
        return True

    def fetch_recent_posts(self, source: dict) -> list[dict]:
        if not self.is_available():
            return []

        # TODO：呼叫 Instagram Graph API
        # 參考：https://developers.facebook.com/docs/instagram-api/reference/ig-media
        # GET /{ig-user-id}/media?fields=caption,permalink,timestamp&access_token={token}
        # Hashtag search: GET /ig_hashtag_search?user_id={id}&q={hashtag}
        logger.info(
            "[instagram_connector] stub：來源 %s 尚未實作真實 API 呼叫。",
            source.get("id")
        )
        return []

    def normalize_post(self, raw_post: dict, source: dict) -> dict:
        return {
            "text": raw_post.get("caption", ""),
            "tag": "instagram_post",
            "source_url": raw_post.get("permalink", ""),
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_confidence": source.get("source_confidence", "low"),
            "is_nycu_official": source.get("is_nycu_official", False),
            "category_hint": source.get("category_hint", "其他"),
            "source_channel": self.source_channel,
        }
