"""
Threads connector：三層架構。

第一層：ThreadsSearchMonitor  — 公開關鍵字搜尋
第二層：ThreadsAccountMonitor — 指定公開帳號監測
第三層：ThreadsAPIConnector   — Threads 官方 API（stub）

優先使用 Meta / Threads 官方 API 或合法授權方式。
不使用登入爬蟲，不破解反爬，不抓私人或非公開內容。
token 未設定時跳過，不讓主程式失敗。
"""

import logging
import os

from .base import SocialConnector

logger = logging.getLogger(__name__)


# ── 第一層：Threads Search Monitor ────────────────────────────────────────────

class ThreadsSearchMonitor(SocialConnector):
    """
    使用公開搜尋思路，定期監測關鍵字與公開貼文搜尋結果。

    目前 Threads 尚未開放公開關鍵字搜尋 API。
    需要 THREADS_ACCESS_TOKEN 才能使用 Threads API。
    未設定時跳過，不讓主程式失敗。
    """

    @property
    def source_channel(self) -> str:
        return "threads_search"

    def is_available(self) -> bool:
        enabled = os.getenv("THREADS_SEARCH_ENABLED", "false").lower() == "true"
        token = os.getenv("THREADS_ACCESS_TOKEN", "")
        if not enabled or not token:
            logger.info(
                "[threads_search] 未啟用或 THREADS_ACCESS_TOKEN 未設定，跳過。"
                "如需啟用：在 .env 設定 THREADS_ACCESS_TOKEN 並設 THREADS_SEARCH_ENABLED=true。"
            )
            return False
        return True

    def fetch_recent_posts(self, source: dict) -> list[dict]:
        if not self.is_available():
            return []

        # TODO：Threads Search API（目前尚未公開）
        # 參考：https://developers.facebook.com/docs/threads
        # 當 Threads Search API 正式開放後，在此實作：
        # GET /threads?q={keyword}&fields=text,permalink,timestamp
        keywords = source.get("keywords", [])
        logger.info(
            "[threads_search] stub：來源 %s，關鍵字 %d 組，尚未實作真實 API 呼叫。",
            source.get("id"), len(keywords)
        )
        return []

    def normalize_post(self, raw_post: dict, source: dict) -> dict:
        return {
            "text": raw_post.get("text", ""),
            "tag": "threads_post",
            "source_url": raw_post.get("permalink", ""),
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_confidence": source.get("source_confidence", "medium"),
            "is_nycu_official": source.get("is_nycu_official", False),
            "category_hint": source.get("category_hint", "其他"),
            "source_channel": self.source_channel,
        }


# ── 第二層：Threads Account Monitor ──────────────────────────────────────────

class ThreadsAccountMonitor(SocialConnector):
    """
    監測 sources.yaml 中指定的公開 Threads 帳號。

    需要 THREADS_ACCESS_TOKEN。
    只監測公開帳號，不登入，不抓私人帳號。
    """

    @property
    def source_channel(self) -> str:
        return "threads_account"

    def is_available(self) -> bool:
        token = os.getenv("THREADS_ACCESS_TOKEN", "")
        if not token:
            logger.info(
                "[threads_account] THREADS_ACCESS_TOKEN 未設定，跳過帳號監測。"
            )
            return False
        return True

    def fetch_recent_posts(self, source: dict) -> list[dict]:
        if not self.is_available():
            return []

        account_ids = source.get("account_ids", [])
        # TODO：對每個 account_id 呼叫 Threads Media API
        # GET /{threads-user-id}/threads?fields=text,permalink,timestamp&access_token={token}
        logger.info(
            "[threads_account] stub：來源 %s，帳號 %s，尚未實作真實 API 呼叫。",
            source.get("id"), account_ids
        )
        return []

    def normalize_post(self, raw_post: dict, source: dict) -> dict:
        return {
            "text": raw_post.get("text", ""),
            "tag": "threads_post",
            "source_url": raw_post.get("permalink", ""),
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_confidence": source.get("source_confidence", "medium"),
            "is_nycu_official": source.get("is_nycu_official", False),
            "category_hint": source.get("category_hint", "其他"),
            "source_channel": self.source_channel,
        }


# ── 第三層：Threads API Connector ─────────────────────────────────────────────

class ThreadsAPIConnector(SocialConnector):
    """
    Threads 官方 API Connector（stub）。

    優先使用 Meta / Threads 官方 API 或合法授權方式。
    不使用登入爬蟲，不破解反爬。
    API 權限不足或 token 未設定時跳過，不讓主程式失敗。
    """

    @property
    def source_channel(self) -> str:
        return "threads_api"

    def is_available(self) -> bool:
        token = os.getenv("THREADS_ACCESS_TOKEN", "")
        if not token:
            logger.info(
                "[threads_api] THREADS_ACCESS_TOKEN 未設定，跳過 Threads API connector。"
                "如需啟用，請申請 Meta Threads API 授權並填入 .env。"
            )
            return False
        return True

    def fetch_recent_posts(self, source: dict) -> list[dict]:
        if not self.is_available():
            return []

        # TODO：Threads API 正式接入點
        # 參考：https://developers.facebook.com/docs/threads/posts
        logger.info(
            "[threads_api] stub：來源 %s，尚未實作真實 API 呼叫。",
            source.get("id")
        )
        return []

    def normalize_post(self, raw_post: dict, source: dict) -> dict:
        return {
            "text": raw_post.get("text", ""),
            "tag": "threads_post",
            "source_url": raw_post.get("permalink", ""),
            "source_id": source.get("id"),
            "source_name": source.get("name"),
            "source_confidence": source.get("source_confidence", "medium"),
            "is_nycu_official": source.get("is_nycu_official", False),
            "category_hint": source.get("category_hint", "其他"),
            "source_channel": self.source_channel,
        }


# ── 工廠函式：根據 source_type 選擇正確的 connector ──────────────────────────

def get_threads_connector(source_type: str) -> SocialConnector:
    mapping = {
        "threads_search": ThreadsSearchMonitor,
        "threads_account": ThreadsAccountMonitor,
        "threads_api": ThreadsAPIConnector,
    }
    cls = mapping.get(source_type)
    if cls is None:
        raise ValueError(f"未知的 Threads source_type：{source_type}")
    return cls()
