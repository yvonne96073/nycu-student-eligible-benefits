"""
notion_client.py：Notion dry-run 與同步。

支援：
  - dry_run 模式：只印出將要同步的資料，不真的寫入
  - create_page：建立新頁面
  - update_page：更新現有頁面（by dedup_hash）
  - search_by_hash：查詢是否已存在
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from notion_client import Client as NotionSDKClient
    _HAS_NOTION = True
except ImportError:
    _HAS_NOTION = False
    logger.warning("notion-client 未安裝，Notion 同步功能停用。請執行 pip install notion-client")


def _get_client() -> Optional[object]:
    token = os.getenv("NOTION_TOKEN", "")
    if not token:
        logger.warning("NOTION_TOKEN 未設定，無法連線 Notion。")
        return None
    if not _HAS_NOTION:
        return None
    return NotionSDKClient(auth=token)


def _build_properties(item: dict) -> dict:
    """把優惠 dict 轉成 Notion page properties 格式。"""
    def text(val: str) -> dict:
        return {"rich_text": [{"text": {"content": str(val or "")[:2000]}}]}

    def title(val: str) -> dict:
        return {"title": [{"text": {"content": str(val or "")[:500]}}]}

    def select(val: str) -> dict:
        return {"select": {"name": str(val or "不明")}}

    def date_prop(val: str) -> dict:
        if val:
            try:
                return {"date": {"start": val}}
            except Exception:
                pass
        return {"date": None}

    return {
        "名稱": title(item.get("title", "")),
        "類別": select(item.get("category", "其他")),
        "優惠內容": text(item.get("discount", "")),
        "地點原文": text(item.get("location_raw", "")),
        "地點分類": select(item.get("location_scope", "不明")),
        "資格文字": text(item.get("eligibility_text", "")[:500]),
        "學生身分要求": select(item.get("student_requirement", "不明")),
        "年齡限制": text(item.get("age_limit_text", "")),
        "年齡判斷": select(item.get("age_result", "不明")),
        "研究生判斷": select(item.get("graduate_student_result", "不明")),
        "最終結果": select(item.get("final_result", "可能可用")),
        "判斷理由": text(item.get("reason", "")),
        "需要證件": select(item.get("required_document", "不明")),
        "開始日期": date_prop(item.get("start_date", "")),
        "結束日期": date_prop(item.get("end_date", "")),
        "來源名稱": text(item.get("source_name", "")),
        "來源 URL": {"url": item.get("source_url") or None},
        "來源渠道": select(item.get("source_channel", "official_web")),
        "來源可信度": select(item.get("source_confidence", "medium")),
        "Notion 狀態": select(item.get("notion_status", "待確認")),
        "Hash": text(item.get("dedup_hash", "")),
    }


def search_by_hash(client, database_id: str, hash_val: str) -> Optional[str]:
    """查詢 Notion database 中是否已有相同 hash，回傳 page_id 或 None。"""
    try:
        result = client.databases.query(
            database_id=database_id,
            filter={
                "property": "Hash",
                "rich_text": {"equals": hash_val},
            },
        )
        pages = result.get("results", [])
        if pages:
            return pages[0]["id"]
    except Exception as e:
        logger.warning("Notion search 失敗：%s", e)
    return None


def create_page(client, database_id: str, item: dict) -> Optional[str]:
    """在 Notion database 中建立新頁面，回傳 page_id 或 None。"""
    try:
        page = client.pages.create(
            parent={"database_id": database_id},
            properties=_build_properties(item),
        )
        return page["id"]
    except Exception as e:
        logger.warning("Notion create_page 失敗：%s", e)
        return None


def update_page(client, page_id: str, item: dict) -> bool:
    """更新 Notion 現有頁面。"""
    try:
        client.pages.update(
            page_id=page_id,
            properties=_build_properties(item),
        )
        return True
    except Exception as e:
        logger.warning("Notion update_page 失敗：%s", e)
        return False


def sync_items(items: list[dict], dry_run: bool = True) -> None:
    """
    同步優惠清單到 Notion。
    dry_run=True 時只印出，不真的寫入。
    只同步 final_result 為「可用」或「可能可用」的項目。
    """
    eligible = [i for i in items if i.get("final_result") in ("可用", "可能可用")]

    if dry_run:
        logger.info("=== Notion Dry-run：共 %d 筆（可用 + 可能可用）===", len(eligible))
        for item in eligible:
            logger.info(
                "[%s] %s | %s | %s | %s",
                item.get("final_result"),
                item.get("title", "")[:40],
                item.get("location_scope", ""),
                item.get("discount", ""),
                item.get("source_url", ""),
            )
        return

    database_id = os.getenv("NOTION_DATABASE_ID", "")
    if not database_id:
        logger.error("NOTION_DATABASE_ID 未設定，無法同步 Notion。")
        return

    client = _get_client()
    if client is None:
        return

    created = updated = skipped = 0
    for item in eligible:
        h = item.get("dedup_hash", "")
        existing_id = search_by_hash(client, database_id, h) if h else None

        if existing_id:
            if update_page(client, existing_id, item):
                updated += 1
            else:
                skipped += 1
        else:
            if create_page(client, database_id, item):
                created += 1
            else:
                skipped += 1

    logger.info("Notion 同步完成：新增 %d，更新 %d，跳過 %d", created, updated, skipped)
