"""測試去重邏輯。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dedup import dedup, compute_hash


def _item(title: str, url: str = "", merchant: str = "", discount: str = "") -> dict:
    return {
        "title": title,
        "source_url": url,
        "merchant": merchant,
        "discount": discount,
        "source_name": "測試",
        "last_checked_at": "2025-01-01T00:00:00+00:00",
    }


def test_same_url_title_deduped():
    items = [
        _item("NYCU 特約店 8 折", url="https://example.com/a"),
        _item("NYCU 特約店 8 折", url="https://example.com/a"),
    ]
    result = dedup(items)
    assert len(result) == 1, f"期望 1 筆，得到 {len(result)}"


def test_different_url_not_deduped():
    items = [
        _item("NYCU 特約店 8 折", url="https://example.com/a"),
        _item("NYCU 特約店 8 折", url="https://example.com/b"),
    ]
    result = dedup(items)
    assert len(result) == 2, f"期望 2 筆，得到 {len(result)}"


def test_no_url_dedup_by_merchant_discount():
    items = [
        _item("", merchant="星巴克", discount="9折"),
        _item("", merchant="星巴克", discount="9折"),
    ]
    result = dedup(items)
    assert len(result) == 1, f"期望 1 筆，得到 {len(result)}"


def test_hash_stable():
    i1 = _item("NYCU 特約店 8 折", url="https://example.com/a")
    i2 = _item("NYCU 特約店 8 折", url="https://example.com/a")
    assert compute_hash(i1) == compute_hash(i2)


def test_hash_different():
    i1 = _item("A 優惠", url="https://example.com/a")
    i2 = _item("B 優惠", url="https://example.com/b")
    assert compute_hash(i1) != compute_hash(i2)


def test_dedup_sets_hash_field():
    items = [_item("Test", url="https://example.com")]
    result = dedup(items)
    assert "dedup_hash" in result[0]
    assert len(result[0]["dedup_hash"]) == 16


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  ✓ {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {fn.__name__}：{e}")
            failed += 1
    print(f"\n結果：{passed} 通過，{failed} 失敗")
