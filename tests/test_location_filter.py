"""測試地點分類邏輯。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.normalize import classify_location


def test_taipei_xinyi():
    _, scope = classify_location("台北市信義區展演活動")
    assert scope == "台北", f"期望 台北，得到 {scope}"


def test_tpac():
    _, scope = classify_location("臺北表演藝術中心學生票")
    assert scope == "台北", f"期望 台北，得到 {scope}"


def test_hsinchu_east():
    _, scope = classify_location("新竹市東區餐廳優惠")
    assert scope == "新竹", f"期望 新竹，得到 {scope}"


def test_nycu_campus():
    _, scope = classify_location("陽明交通大學光復校區活動")
    assert scope == "NYCU 校區周邊", f"期望 NYCU 校區周邊，得到 {scope}"


def test_nycu_abbrev():
    _, scope = classify_location("NYCU 學生可免費入場")
    assert scope == "NYCU 校區周邊", f"期望 NYCU 校區周邊，得到 {scope}"


def test_nationwide():
    _, scope = classify_location("全台門市均適用，持學生證即享 9 折")
    assert scope == "全台", f"期望 全台，得到 {scope}"


def test_online():
    _, scope = classify_location("線上申請，官網購票享學生優惠")
    assert scope == "線上", f"期望 線上，得到 {scope}"


def test_no_location():
    raw, scope = classify_location("持有效學生證即可享優惠")
    assert scope == "不明", f"期望 不明，得到 {scope}"


def test_nycu_beats_hsinchu():
    # 「交大光復校區」應該被分到 NYCU 校區周邊，而不是新竹
    _, scope = classify_location("交大光復校區附近餐廳學生優惠")
    assert scope == "NYCU 校區周邊", f"期望 NYCU 校區周邊，得到 {scope}"


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
