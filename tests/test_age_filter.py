"""測試年齡判斷邏輯。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eligibility_filter import check_age


def test_30_under_excluded():
    result, _ = check_age("本優惠限 30 歲以下學生")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_31_under_excluded():
    result, _ = check_age("青年票限 31 歲以下")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_under_32_excluded():
    result, _ = check_age("未滿 32 歲可購買學生票")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_under_31_excluded():
    result, _ = check_age("未滿 31 歲限定優惠")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_18_30_range_excluded():
    result, _ = check_age("適用對象：18～30 歲學生")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_18_31_range_excluded():
    result, _ = check_age("年齡限制：18-31 歲")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_32_under_included():
    result, _ = check_age("32 歲以下學生均可使用")
    assert result == "符合", f"期望 符合，得到 {result}"


def test_under_33_included():
    result, _ = check_age("未滿 33 歲即可憑學生證享折扣")
    assert result == "符合", f"期望 符合，得到 {result}"


def test_18_32_range_included():
    result, _ = check_age("18-32 歲學生優惠")
    assert result == "符合", f"期望 符合，得到 {result}"


def test_no_age_mentioned():
    result, _ = check_age("持有效學生證即可入場")
    assert result == "無年齡限制", f"期望 無年齡限制，得到 {result}"


def test_no_age_mentioned_nycu():
    result, _ = check_age("陽明交大在校學生憑學生證享 8 折優惠")
    assert result == "無年齡限制", f"期望 無年齡限制，得到 {result}"


def test_unlimited_explicit():
    result, _ = check_age("不限年齡，持學生證即享優惠")
    assert result == "符合", f"期望 符合，得到 {result}"


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
