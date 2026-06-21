"""
Facebook connector：使用 Meta Graph API 讀取公開粉專貼文。

第一版為 stub。
需要 Meta Graph API token（FACEBOOK_ACCESS_TOKEN）。
不使用登入爬蟲，不抓私人社團。
"""

import logging
import os

from .base import SocialConnector

logger = logging.getLogger(__name__)


class FacebookConnector(SocialConnector):
    """
    合法授權方式：Meta Graph API。
    不使用 selenium / playwright 自動登入。
    不抓私人社團或需要登入才能看到的內容。
    """

    @property
    def source_channel(self) -> str:
        return "facebook_api"

    def is_available(self) -> bool:
        token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
        if not token:
            logger.info(
                "[facebook_connector] FACEBOOK_ACCESS_TOKEN 未設定，跳過 Facebook 來源。"
                "如需啟用，請在 .env 填入 Meta Graph API token。"
            )
            return False
        return True

    def fetch_recent_posts(self, source: dict) -> list[dict]:
        if not self.is_available():
            return []

        # TODO：呼叫 Meta Graph API
        # 參考：https://developers.facebook.com/docs/graph-api/reference/page/feed/
        # GET /{page-id}/feed?fields=message,permalink_url,created_time&access_token={token}
        logger.info(
            "[facebook_connector] stub：來源 %s 尚未實作真實 API 呼叫。",
            source.get("id")
        )
        return []

    def normalize_post(self, raw_post: dict, source: dict) -> dict:
        return {
            "text": raw_post.get("message", ""),
            "tag": "facebook_post",
            "source_url": raw_post.get("permalink_url", ""),
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_confidence": source.get("source_confidence", "low"),
            "is_nycu_official": source.get("is_nycu_official", False),
            "category_hint": source.get("category_hint", "其他"),
            "source_channel": self.source_channel,
        }
