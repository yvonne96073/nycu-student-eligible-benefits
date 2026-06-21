"""
eligibility_filter.py：判斷每筆優惠是否符合使用者資格。

使用者條件：
  - 學校：NYCU
  - 身分：研究生 / 在校學生
  - 年齡：32 歲

判斷結果：可用 / 可能可用 / 不可用
"""

import re
from typing import Literal

USER_AGE = 32

# ── 年齡關鍵字 ────────────────────────────────────────────────────────────────

# 明確不符合（上限 < 32）
_AGE_EXCLUDE_PATTERNS = [
    r"(?:未滿|小於|低於)\s*3[012]\s*歲",        # 未滿30/31/32歲（32歲也不符合，因為 < 32）
    r"(?:30|31)\s*歲\s*(?:以下|以內|含以下)",   # 30歲以下、31歲以下
    r"18\s*[~～\-–—至]\s*3[01]\s*歲",           # 18-30、18-31、18至30歲
    r"青年票.*?(?:30|31)\s*歲",
    r"(?:30|31)\s*歲.*?青年",
]

# 明確符合（上限 >= 33，或不限年齡）
_AGE_INCLUDE_PATTERNS = [
    r"(?:未滿|小於|低於)\s*(?:3[3-9]|[4-9][0-9])\s*歲",   # 未滿33歲以上才符合
    r"(?:3[2-9]|[4-9][0-9])\s*歲\s*(?:以下|以內|含以下)",  # 32歲以下等（含 32 → 符合）
    r"18\s*[~～\-–—至]\s*(?:3[2-9]|[4-9][0-9])\s*歲",      # 18-32以上、18至35歲
    r"不限年齡",
    r"無年齡限制",
]

# ── 學生身分關鍵字 ────────────────────────────────────────────────────────────

# 明確不可用（排除研究生或只限特定族群）
_STUDENT_EXCLUDE_PATTERNS = [
    r"限大學部",
    r"限大學生.*?不含研究生",
    r"大學部.*?不含研究生",
    r"限高中(?:職)?(?:以下|生)",
    r"限國中(?:小|以下|生)",
    r"限小學",
    r"限兒童",
    r"兒童票",
    r"高中(?:職)?以下",
]

# 明確可用（含研究生或本校學生）
_STUDENT_INCLUDE_PATTERNS = [
    r"研究生",
    r"大學(?:生)?及研究生",
    r"大專院校(?:學生)?",
    r"在校學生",
    r"本校學生",
    r"NYCU\s*student",
    r"陽明交大(?:學生)?",
    r"國立陽明交通大學(?:學生)?",
    r"交大(?:學生)?",
    r"持(?:有效)?學生證",
    r"有效學生證",
    r"國中以上.*?學生",
    r"學生票",  # 通常含研究生，但下面標為「可能可用」
]

# 含糊的學生優惠（只說「學生」，沒排除也沒明確含研究生）
_STUDENT_AMBIGUOUS_PATTERNS = [
    r"學生優惠",
    r"學生價",
    r"學生証",
    r"學生身分",
    r"[^大]學生[^證票]",  # 「學生」但不是「大學生」「學生證」「學生票」
]

# ── NYCU 相關 ─────────────────────────────────────────────────────────────────

_NYCU_PATTERNS = [
    r"nycu", r"陽明交大", r"陽明交通大學", r"交大(?!通部)", r"光復校區",
    r"六家校區", r"博愛校區", r"陽明校區", r"本校學生", r"nycu\.edu\.tw",
]

# ── 證件 ──────────────────────────────────────────────────────────────────────

_DOCUMENT_MAP = {
    r"學生證": "學生證",
    r"在學證明": "在學證明",
    r"身分證": "身分證",
    r"學生手冊": "學生手冊",
}


# ── 輔助函式 ──────────────────────────────────────────────────────────────────

def _match_any(text: str, patterns: list[str]) -> bool:
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def _infer_required_document(text: str) -> str:
    for pattern, doc in _DOCUMENT_MAP.items():
        if re.search(pattern, text, re.IGNORECASE):
            return doc
    return "不明"


# ── 核心判斷 ──────────────────────────────────────────────────────────────────

def check_age(text: str) -> tuple[str, str]:
    """
    回傳 (age_result, age_limit_text)。
    age_result: 符合 / 不符合 / 無年齡限制 / 不明
    """
    # 先找年齡相關文字片段
    age_text_match = re.search(r".{0,10}(?:歲|青年|年齡).{0,20}", text)
    age_limit_text = age_text_match.group(0).strip() if age_text_match else ""

    if _match_any(text, _AGE_EXCLUDE_PATTERNS):
        return "不符合", age_limit_text
    if _match_any(text, _AGE_INCLUDE_PATTERNS):
        return "符合", age_limit_text
    if age_limit_text:
        return "不明", age_limit_text
    return "無年齡限制", ""


def check_student(text: str, is_nycu_official: bool = False) -> tuple[str, str]:
    """
    回傳 (graduate_student_result, student_requirement)。
    graduate_student_result: 符合 / 不符合 / 不明
    student_requirement: NYCU學生 / 一般學生 / 研究生 / 不明
    """
    if _match_any(text, _STUDENT_EXCLUDE_PATTERNS):
        return "不符合", "限定族群（排除研究生或限高中以下）"

    is_nycu = is_nycu_official or _match_any(text, _NYCU_PATTERNS)
    has_include = _match_any(text, _STUDENT_INCLUDE_PATTERNS)
    has_ambiguous = _match_any(text, _STUDENT_AMBIGUOUS_PATTERNS)

    if is_nycu and (has_include or re.search(r"學生", text)):
        req = "NYCU學生"
        return "符合", req

    if re.search(r"研究生", text, re.IGNORECASE):
        return "符合", "研究生"

    if has_include:
        # 「學生票」含糊，但沒排除研究生 → 可能可用
        if re.search(r"學生票", text):
            return "不明", "一般學生（學生票，未確認是否含研究生）"
        return "符合", "一般學生"

    if has_ambiguous:
        return "不明", "一般學生（未確認是否含研究生）"

    return "不明", "不明"


def determine_final_result(
    age_result: str,
    graduate_student_result: str,
    end_date: str,
) -> tuple[str, str]:
    """
    回傳 (final_result, reason)。
    final_result: 可用 / 可能可用 / 不可用
    """
    from datetime import date

    # 過期判斷
    if end_date:
        try:
            exp = date.fromisoformat(end_date)
            if exp < date.today():
                return "不可用", f"優惠已過期（{end_date}）"
        except ValueError:
            pass

    # 不可用條件
    if age_result == "不符合":
        return "不可用", "年齡不符合（超過年齡上限）"
    if graduate_student_result == "不符合":
        return "不可用", "身分不符合（明確排除研究生或限特定族群）"

    # 可用條件：全部明確符合
    if (
        graduate_student_result == "符合"
        and age_result in ("符合", "無年齡限制")
    ):
        return "可用", "學生身分符合，年齡符合或無年齡限制，研究生未被排除"

    # 否則為「可能可用」
    reasons = []
    if graduate_student_result == "不明":
        reasons.append("學生資格文字不夠清楚，未確認是否含研究生")
    if age_result == "不明":
        reasons.append("年齡限制資訊不明確")
    reason = "；".join(reasons) if reasons else "資格條件不完整，需進一步確認"
    return "可能可用", reason


# ── 對外主函式 ────────────────────────────────────────────────────────────────

def apply_eligibility(item: dict) -> dict:
    """
    輸入已 normalize 的 dict，補入資格判斷欄位後回傳。
    """
    text = item.get("_raw_text", "") or item.get("eligibility_text", "")
    is_nycu = item.get("is_nycu_official", False)

    age_result, age_limit_text = check_age(text)
    graduate_result, student_req = check_student(text, is_nycu)
    final_result, reason = determine_final_result(
        age_result, graduate_result, item.get("end_date", "")
    )
    required_doc = _infer_required_document(text)

    item["age_result"] = age_result
    item["age_limit_text"] = age_limit_text
    item["graduate_student_result"] = graduate_result
    item["student_requirement"] = student_req
    item["final_result"] = final_result
    item["reason"] = reason
    item["required_document"] = required_doc

    return item
