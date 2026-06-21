"""測試 final_result 判斷邏輯。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eligibility_filter import determine_final_result, apply_eligibility
from src.normalize import normalize_block


def _make_item(text: str, is_nycu: bool = False) -> dict:
    block = {
        "text": text,
        "tag": "p",
        "source_url": "https://example.com",
        "source_id": "test",
        "source_name": "測試",
        "source_confidence": "high",
        "is_nycu_official": is_nycu,
        "category_hint": "其他",
    }
    item = normalize_block(block)
    item["is_nycu_official"] = is_nycu
    return apply_eligibility(item)


def test_fully_eligible():
    item = _make_item("大專院校學生持有效學生證即可，無年齡限制")
    assert item["final_result"] == "可用", f"期望 可用，得到 {item['final_result']}｜理由：{item['reason']}"


def test_graduate_explicit():
    item = _make_item("研究生及大學生均可憑學生證享 8 折")
    assert item["final_result"] == "可用", f"期望 可用，得到 {item['final_result']}｜理由：{item['reason']}"


def test_nycu_official_student():
    item = _make_item("本校學生持學生證享優惠", is_nycu=True)
    assert item["final_result"] == "可用", f"期望 可用，得到 {item['final_result']}｜理由：{item['reason']}"


def test_ambiguous_student_requirement():
    item = _make_item("學生優惠，詳情請洽服務台")
    assert item["final_result"] in ("可能可用", "可用"), \
        f"期望 可能可用 或 可用，得到 {item['final_result']}｜理由：{item['reason']}"


def test_age_unknown_no_exclude():
    item = _make_item("學生票 NT$150，憑學生證購買")
    assert item["final_result"] in ("可用", "可能可用"), \
        f"期望 可用 或 可能可用，得到 {item['final_result']}｜理由：{item['reason']}"


def test_age_excluded():
    item = _make_item("青年票限 30 歲以下，持學生證購買")
    assert item["final_result"] == "不可用", f"期望 不可用，得到 {item['final_result']}｜理由：{item['reason']}"


def test_undergrad_only_excluded():
    item = _make_item("限大學部學生，研究生不適用")
    assert item["final_result"] == "不可用", f"期望 不可用，得到 {item['final_result']}｜理由：{item['reason']}"


def test_location_unknown_not_deleted():
    # 地點不明，但資格符合 → 不應直接刪除，應為可用或可能可用
    item = _make_item("大專院校學生均可享 8 折，無年齡限制")
    assert item["final_result"] in ("可用", "可能可用"), \
        f"地點不明時不應刪除，得到 {item['final_result']}｜location_scope: {item['location_scope']}"


def test_expired():
    result, reason = determine_final_result("符合", "符合", "2020-01-01")
    assert result == "不可用", f"期望 不可用（已過期），得到 {result}"
    assert "過期" in reason


def test_not_expired():
    result, reason = determine_final_result("符合", "符合", "2099-12-31")
    assert result == "可用", f"期望 可用，得到 {result}"


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
