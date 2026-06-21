"""
merge.py：同一來源（source_url）下多筆產品 block 合併為一筆品牌條目。

合併規則：
  - 同一 source_url 有 >= 3 筆 → 合併
  - title 取來源名稱（source_name）
  - discount 改成「產品 → 價格」清單
  - eligibility 取最佳結果（可用 > 可能可用 > 不可用）
  - 其餘欄位取第一筆
"""

from __future__ import annotations

_RESULT_RANK = {"可用": 0, "可能可用": 1, "不可用": 2}


def _clean_product_name(raw: str) -> str:
    """清理產品名稱中的 Markdown link、HTML、多餘空白。"""
    import re
    raw = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", raw)
    raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = re.sub(r"[#*\\]+", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def _extract_product_line(item: dict) -> str:
    """從一筆 item 產生「產品 → 價格」的摘要行。"""
    raw_title = item.get("title", "")
    title = _clean_product_name(raw_title)
    discount = item.get("discount", "").strip()
    if len(title) > 60:
        title = title[:57] + "..."
    if discount:
        return f"  • {title}：{discount}"
    return f"  • {title}"


def merge_by_source(items: list[dict], min_group: int = 3) -> list[dict]:
    """
    同一 source_url 下超過 min_group 筆的 item 合併為一筆。
    少於 min_group 的保持原樣。
    """
    from collections import OrderedDict

    groups: OrderedDict[str, list[dict]] = OrderedDict()
    for item in items:
        url = item.get("source_url", "") or ""
        if not url:
            groups.setdefault("__no_url__", []).append(item)
            continue
        groups.setdefault(url, []).append(item)

    result = []
    for url, group in groups.items():
        if url == "__no_url__" or len(group) < min_group:
            result.extend(group)
            continue

        # 合併
        best = min(group, key=lambda i: _RESULT_RANK.get(i.get("final_result", "不可用"), 9))

        product_lines = [_extract_product_line(i) for i in group]
        product_summary = "\n".join(product_lines)

        merged = dict(best)
        merged["title"] = best.get("source_name", "") or best.get("title", "")
        merged["discount"] = f"共 {len(group)} 項優惠：\n{product_summary}"
        merged["_merged_count"] = len(group)
        merged["final_result"] = best.get("final_result", "可能可用")
        merged["reason"] = best.get("reason", "")

        result.append(merged)

    return result
