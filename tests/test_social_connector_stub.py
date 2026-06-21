"""
測試社群 connector stub 行為。

確認：
1. token 未設定時 is_available() 回傳 False
2. run() 回傳 []，不拋出例外
3. source_channel 回傳正確識別字串
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 確保 env 沒有 token（測試環境）
for k in ["FACEBOOK_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN", "THREADS_ACCESS_TOKEN"]:
    os.environ.pop(k, None)
os.environ["THREADS_SEARCH_ENABLED"] = "false"

from src.social_connectors.facebook_connector import FacebookConnector
from src.social_connectors.instagram_connector import InstagramConnector
from src.social_connectors.threads_connector import (
    ThreadsSearchMonitor, ThreadsAccountMonitor, ThreadsAPIConnector,
    get_threads_connector,
)
from src.social_connectors.dcard_public import DcardPublicConnector

_DUMMY_SOURCE = {
    "id": "test_source",
    "name": "測試來源",
    "source_confidence": "medium",
    "is_nycu_official": False,
    "category_hint": "其他",
    "keywords": ["學生優惠"],
    "account_ids": [],
}


def test_facebook_no_token_unavailable():
    conn = FacebookConnector()
    assert not conn.is_available()


def test_facebook_run_returns_empty():
    conn = FacebookConnector()
    result = conn.run(_DUMMY_SOURCE)
    assert result == []


def test_facebook_channel():
    assert FacebookConnector().source_channel == "facebook_api"


def test_instagram_no_token_unavailable():
    conn = InstagramConnector()
    assert not conn.is_available()


def test_instagram_run_returns_empty():
    conn = InstagramConnector()
    result = conn.run(_DUMMY_SOURCE)
    assert result == []


def test_instagram_channel():
    assert InstagramConnector().source_channel == "instagram_api"


def test_threads_search_unavailable():
    conn = ThreadsSearchMonitor()
    assert not conn.is_available()


def test_threads_search_run_empty():
    conn = ThreadsSearchMonitor()
    result = conn.run(_DUMMY_SOURCE)
    assert result == []


def test_threads_account_unavailable():
    conn = ThreadsAccountMonitor()
    assert not conn.is_available()


def test_threads_api_unavailable():
    conn = ThreadsAPIConnector()
    assert not conn.is_available()


def test_get_threads_connector_factory():
    conn = get_threads_connector("threads_search")
    assert isinstance(conn, ThreadsSearchMonitor)
    conn2 = get_threads_connector("threads_account")
    assert isinstance(conn2, ThreadsAccountMonitor)
    conn3 = get_threads_connector("threads_api")
    assert isinstance(conn3, ThreadsAPIConnector)


def test_dcard_channel():
    assert DcardPublicConnector().source_channel == "dcard_public"


def test_dcard_available():
    # Dcard 不需要 token，應該 is_available() = True
    assert DcardPublicConnector().is_available()


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
