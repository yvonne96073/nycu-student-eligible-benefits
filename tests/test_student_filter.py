"""測試學生身分判斷邏輯。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eligibility_filter import check_student


def test_valid_student_card():
    result, _ = check_student("持有效學生證即可享優惠")
    assert result in ("符合", "不明"), f"期望 符合 或 不明，得到 {result}"


def test_university_students():
    result, _ = check_student("大專院校學生均適用")
    assert result == "符合", f"期望 符合，得到 {result}"


def test_graduate_student():
    result, _ = check_student("本優惠適用研究生")
    assert result == "符合", f"期望 符合，得到 {result}"


def test_undergraduate_only_excluded():
    result, _ = check_student("限大學部學生")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_high_school_excluded():
    result, _ = check_student("限高中以下學生")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_children_excluded():
    result, _ = check_student("兒童票限 12 歲以下")
    assert result == "不符合", f"期望 不符合，得到 {result}"


def test_nycu_official_student():
    result, _ = check_student("本校學生持學生證享 8 折", is_nycu_official=True)
    assert result == "符合", f"期望 符合，得到 {result}"


def test_nycu_text_student():
    result, _ = check_student("陽明交大學生憑學生證即可")
    assert result == "符合", f"期望 符合，得到 {result}"


def test_ambiguous_student():
    result, _ = check_student("學生優惠，詳情請洽服務台")
    assert result in ("不明", "符合"), f"期望 不明 或 符合，得到 {result}"


def test_student_ticket_ambiguous():
    # 「學生票」含糊，沒排除研究生但也沒明確包含
    result, req = check_student("學生票 NT$150，一般票 NT$250")
    assert result in ("不明", "符合"), f"期望 不明 或 符合，得到 {result}"


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
