"""
dedup.py：避免重複優惠。

去重邏輯：
  - 優先用 source_url + title
  - 若沒有 title，用 merchant + discount + source_name
  - 產生 stable hash
  - 同一筆再次出現時，更新 last_checked_at，不新增重複資料
"""

import hashlib
from datetime import datetime, timezone


def _normalize_text(s: str) -> str:
    """去除多餘空白、統一大小寫，用於 hash 前的正規化。"""
    import re
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


_TRACKING_PARAMS = {"srsltid", "fbclid", "gclid", "utm_source", "utm_medium",
                     "utm_campaign", "utm_term", "utm_content", "ref", "mc_cid", "mc_eid"}


def _normalize_url(url: str) -> str:
    """正規化 URL：統一小寫 scheme+host，移除 tracking 參數和 trailing slash。"""
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    url = url.strip()
    if "://" not in url:
        return url
    p = urlparse(url)
    # 移除 tracking 參數
    qs = {k: v for k, v in parse_qs(p.query, keep_blank_values=True).items()
          if k.lower() not in _TRACKING_PARAMS}
    clean_query = urlencode(qs, doseq=True)
    normalized = urlunparse((
        p.scheme.lower(), p.netloc.lower(), p.path, p.params, clean_query, ""
    ))
    return normalized.rstrip("/")


def _make_key(item: dict) -> str:
    """產生用於去重的 key 字串（正規化後）。"""
    url = _normalize_url(item.get("source_url") or "")
    title = _normalize_text(item.get("title") or "")[:80]

    if url and title:
        return f"{url}|{title}"

    merchant = _normalize_text(item.get("merchant") or "")
    discount = _normalize_text(item.get("discount") or "")[:50]
    source = _normalize_text(item.get("source_name") or "")
    return f"{merchant}|{discount}|{source}"


def compute_hash(item: dict) -> str:
    """產生 stable hash（sha256 前 16 字）。"""
    key = _make_key(item)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def dedup(items: list[dict]) -> list[dict]:
    """
    對一批 item 做去重。
    同 hash 的 item 只保留一筆，並把最新的 last_checked_at 更新進去。
    """
    seen: dict[str, dict] = {}
    now_iso = datetime.now(timezone.utc).isoformat()

    for item in items:
        h = compute_hash(item)
        item["dedup_hash"] = h

        if h not in seen:
            seen[h] = item
        else:
            # 已存在：只更新 last_checked_at
            seen[h]["last_checked_at"] = now_iso

    return list(seen.values())
