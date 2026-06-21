"""SocialConnector 抽象基底類別。"""

from abc import ABC, abstractmethod
from typing import Optional


class SocialConnector(ABC):
    """所有社群 connector 的共同介面。"""

    @property
    @abstractmethod
    def source_channel(self) -> str:
        """回傳 source_channel 識別字串，例如 'threads_search'。"""

    @abstractmethod
    def is_available(self) -> bool:
        """
        檢查此 connector 是否可用（例如 API token 已設定）。
        不可用時主程式應跳過，不應拋出例外。
        """

    @abstractmethod
    def fetch_recent_posts(self, source: dict) -> list[dict]:
        """
        抓取最新貼文，回傳 raw post list。
        每筆至少包含 'text'、'url'、'posted_at'（可為 None）。
        如果 is_available() 為 False，應直接回傳 []。
        """

    @abstractmethod
    def normalize_post(self, raw_post: dict, source: dict) -> dict:
        """
        把 raw_post 轉換成統一的 block 格式，
        欄位對齊 scraper.py 的 block dict。
        """

    def get_source_channel(self) -> str:
        return self.source_channel

    def run(self, source: dict) -> list[dict]:
        """對外統一入口：先檢查可用性，再抓取並 normalize。"""
        if not self.is_available():
            import logging
            logging.getLogger(__name__).info(
                "[%s] connector 不可用（可能缺少 API token），跳過來源：%s",
                self.source_channel, source.get("id")
            )
            return []
        raw_posts = self.fetch_recent_posts(source)
        return [self.normalize_post(p, source) for p in raw_posts]
