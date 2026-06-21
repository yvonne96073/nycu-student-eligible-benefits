"""
main.py：整合所有模組，執行學生優惠搜尋 pipeline。

用法：
  python main.py --dry-run            跑所有公開來源，印出結果
  python main.py --only-usable        只印出「可用」和「可能可用」
  python main.py --sync-notion        同步可用 / 可能可用到 Notion
  python main.py --source SOURCE_ID   只跑指定來源
  python main.py --include-social     額外啟用所有社群 connector
  python main.py --include-threads    額外啟用 Threads 來源
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 讓 src 目錄可被 import
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper import scrape_source
from src.firecrawl_scraper import is_available as firecrawl_available, scrape_source_firecrawl
from src.pdf_parser import parse_pdf_source
from src.search_adapter import fetch_search_results
from src.normalize import normalize_block, is_relevant
from src.eligibility_filter import apply_eligibility
from src.dedup import dedup, compute_hash
from src.merge import merge_by_source
from src import notion_client as nc

from src.social_connectors.facebook_connector import FacebookConnector
from src.social_connectors.instagram_connector import InstagramConnector
from src.social_connectors.threads_connector import get_threads_connector
from src.social_connectors.dcard_public import DcardPublicConnector

# ── 設定 ────────────────────────────────────────────────────────────────────

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

SOURCES_YAML = Path(__file__).parent / "sources.yaml"

_SOCIAL_CHANNELS = {
    "facebook_api", "instagram_api",
    "threads_search", "threads_account", "threads_api",
    "dcard_public",
}
_THREADS_CHANNELS = {"threads_search", "threads_account", "threads_api"}


# ── 來源載入 ─────────────────────────────────────────────────────────────────

def load_sources() -> list[dict]:
    with open(SOURCES_YAML, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


# ── Pipeline ─────────────────────────────────────────────────────────────────

def process_source(source: dict) -> list[dict]:
    """對單一 source 執行 fetch → normalize → eligibility。"""
    st = source.get("source_type", "")
    blocks = []

    if st == "html":
        if firecrawl_available():
            blocks = scrape_source_firecrawl(source)
        else:
            blocks = scrape_source(source)
    elif st == "pdf":
        blocks = parse_pdf_source(source)
    elif st == "google_search":
        blocks = fetch_search_results(source)
    elif st in _THREADS_CHANNELS:
        conn = get_threads_connector(st)
        blocks = conn.run(source)
    elif st == "facebook_api":
        blocks = FacebookConnector().run(source)
    elif st == "instagram_api":
        blocks = InstagramConnector().run(source)
    elif st == "dcard_public":
        blocks = DcardPublicConnector().run(source)
    elif st == "gmail_newsletter":
        logger.info("[gmail_newsletter] 預留介面，尚未實作，跳過：%s", source.get("id"))
    else:
        logger.info("未知 source_type '%s'，跳過：%s", st, source.get("id"))

    results = []
    for block in blocks:
        if not is_relevant(block.get("text", "")):
            continue
        normalized = normalize_block(block)
        normalized["dedup_hash"] = compute_hash(normalized)
        filtered = apply_eligibility(normalized)
        results.append(filtered)

    return results


def run_pipeline(
    sources: list[dict],
    include_social: bool = False,
    include_threads: bool = False,
    only_source_id: str = "",
) -> list[dict]:
    all_items = []

    for source in sources:
        if not source.get("enabled", True):
            continue

        if only_source_id and source.get("id") != only_source_id:
            continue

        st = source.get("source_type", "")

        # 社群來源：需明確 flag 才啟用
        if st in _SOCIAL_CHANNELS:
            if not include_social:
                if include_threads and st in _THREADS_CHANNELS:
                    pass  # 允許
                else:
                    continue

        items = process_source(source)
        all_items.extend(items)
        logger.info(
            "來源 [%s] 完成，取得 %d 筆", source.get("id"), len(items)
        )

    deduped = dedup(all_items)
    return merge_by_source(deduped)


# ── 輸出格式 ──────────────────────────────────────────────────────────────────

_SORT_KEY_SCOPE = {
    "台北": 0, "新竹": 0, "NYCU 校區周邊": 0, "線上": 0,
    "全台": 1,
    "不明": 2,
}
_SORT_KEY_RESULT = {"可用": 0, "可能可用": 1, "不可用": 2}


def sort_items(items: list[dict]) -> list[dict]:
    def key(i):
        r = _SORT_KEY_RESULT.get(i.get("final_result", "不可用"), 9)
        s = _SORT_KEY_SCOPE.get(i.get("location_scope", "不明"), 3)
        return (r, s)
    return sorted(items, key=key)


def print_results(items: list[dict], only_usable: bool = False) -> None:
    sorted_items = sort_items(items)

    groups = {"可用": [], "可能可用": [], "不可用": []}
    for item in sorted_items:
        r = item.get("final_result", "不可用")
        if r in groups:
            groups[r].append(item)

    def _sep():
        print("─" * 60)

    def _print_item_detail(item, brief=False):
        print(f"  優惠名稱：{item.get('title', '')}")
        discount = item.get("discount", "（未擷取）")
        if "\n" in discount:
            print(f"  優惠內容：")
            for line in discount.split("\n"):
                print(f"    {line}")
        else:
            print(f"  優惠內容：{discount}")
        print(f"  地點分類：{item.get('location_scope', '不明')}")
        if not brief:
            print(f"  需要證件：{item.get('required_document', '不明')}")
            if item.get("end_date"):
                print(f"  有效期限：{item.get('start_date', '')} ~ {item.get('end_date', '')}")
            print(f"  判斷理由：{item.get('reason', '')}")
        else:
            print(f"  需要確認：{item.get('reason', '')}")
        print(f"  來源網址：{item.get('source_url', '')}")

    if groups["可用"]:
        print("\n" + "=" * 60)
        print("【可用】共 {} 筆".format(len(groups["可用"])))
        print("=" * 60)
        for item in groups["可用"]:
            _sep()
            _print_item_detail(item)

    if groups["可能可用"]:
        print("\n" + "=" * 60)
        print("【可能可用】共 {} 筆".format(len(groups["可能可用"])))
        print("=" * 60)
        for item in groups["可能可用"]:
            _sep()
            _print_item_detail(item, brief=True)

    if not only_usable and groups["不可用"]:
        print("\n" + "=" * 60)
        print("【不可用】共 {} 筆（僅供 dry-run 參考）".format(len(groups["不可用"])))
        print("=" * 60)
        for item in groups["不可用"]:
            _sep()
            print(f"  優惠名稱：{item.get('title', '')}")
            print(f"  不可用原因：{item.get('reason', '')}")
            print(f"  來源網址：{item.get('source_url', '')}")
            print(f"  來源渠道：{item.get('source_channel', '')}")

    total = len(items)
    usable = len(groups["可用"])
    maybe = len(groups["可能可用"])
    print(f"\n📋 總計：{total} 筆  |  可用：{usable}  |  可能可用：{maybe}  |  不可用：{len(groups['不可用'])}")


# ── JSON 輸出 ─────────────────────────────────────────────────────────────────

_JSON_FIELDS = [
    "title", "category", "discount", "location_scope",
    "required_document", "start_date", "end_date",
    "final_result", "reason", "source_url", "source_name",
    "source_confidence", "is_nycu_official", "_merged_count",
]


def export_json(items: list[dict], output_path: str) -> None:
    """輸出可用 + 可能可用的 item 為 JSON，供前端網站使用。"""
    from datetime import date

    today = date.today().isoformat()
    exported = []
    for item in sort_items(items):
        r = item.get("final_result", "不可用")
        if r == "不可用":
            continue
        # 再次檢查過期
        end = item.get("end_date", "")
        if end and end < today:
            continue
        row = {k: item.get(k, "") for k in _JSON_FIELDS}
        row["_merged_count"] = item.get("_merged_count", 1)
        exported.append(row)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(exported),
        "items": exported,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("JSON 已輸出：%s（%d 筆）", output_path, len(exported))


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NYCU 學生優惠自動搜尋工具")
    parser.add_argument("--dry-run", action="store_true",
                        help="跑公開來源並印出結果（預設行為）")
    parser.add_argument("--only-usable", action="store_true",
                        help="只印出「可用」和「可能可用」")
    parser.add_argument("--sync-notion", action="store_true",
                        help="同步可用 / 可能可用到 Notion")
    parser.add_argument("--source", type=str, default="",
                        help="只跑指定 source_id")
    parser.add_argument("--include-social", action="store_true",
                        help="包含 Facebook / Instagram / Threads / Dcard 等社群 connector")
    parser.add_argument("--include-threads", action="store_true",
                        help="只額外啟用 Threads 來源")
    parser.add_argument("--output-json", type=str, default="",
                        help="輸出 JSON 到指定路徑（供網站使用）")
    args = parser.parse_args()

    logger.info("載入來源設定...")
    sources = load_sources()
    logger.info("共 %d 個來源", len(sources))

    logger.info("執行 pipeline...")
    items = run_pipeline(
        sources,
        include_social=args.include_social,
        include_threads=args.include_threads,
        only_source_id=args.source,
    )
    logger.info("Pipeline 完成，共 %d 筆（去重後）", len(items))

    if args.output_json:
        export_json(items, args.output_json)

    if args.sync_notion:
        print_results(items, only_usable=args.only_usable)
        logger.info("同步到 Notion...")
        nc.sync_items(items, dry_run=False)
    else:
        print_results(items, only_usable=args.only_usable)
        logger.info("Notion dry-run 輸出：")
        nc.sync_items(items, dry_run=True)


if __name__ == "__main__":
    main()
