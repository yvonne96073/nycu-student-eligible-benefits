"""
normalize.py：把各種來源的 raw block 整理成統一欄位格式。

採規則與關鍵字切出初步資料，不追求完美，以覆蓋率優先。
"""

import re
from datetime import datetime, timezone


# ── 關聯性過濾：只保留可能跟優惠 / 學生 / 票價相關的文字區塊 ─────────────────

# 「折扣 / 優惠」類關鍵字 — 至少要命中一個才算有可能是優惠資訊
_BENEFIT_KEYWORDS = [
    "優惠", "折扣", "折", "免費", "半價", "特價", "促銷",
    "學生票", "學生價", "票價", "門票", "入場費",
    "特約", "合約", "配合",
    "NT$", "discount", "off",
]

# 「學生 / 身分」類關鍵字 — 用來加分，但不能單獨成立
_IDENTITY_KEYWORDS = [
    "學生", "學生證", "研究生", "在校",
    "student", "大專",
]

# 排除：明顯是導覽列、選單、footer 的片段
_NOISE_PATTERNS = [
    r"^:::.*側邊選單",
    r"^:::.*網站導覽",
    r"回首頁",
    r"^下方選單",
    r"隱私權.*政策",
    r"瀏覽人次",
    r"^關於.*單位簡介",
    r"^Copyright",
    r"^©",
]
_NOISE_RE = re.compile("|".join(_NOISE_PATTERNS), re.IGNORECASE)


def is_relevant(text: str) -> bool:
    """
    檢查文字區塊是否可能與學生優惠相關。
    需要同時有「優惠」面向 + 最少 20 字，並且不是導覽列雜訊。
    短 block（< 80 字）需要同時包含身分關鍵字才保留，避免純產品列表灌水。
    """
    if len(text) < 20:
        return False
    if _NOISE_RE.search(text):
        return False
    lower = text.lower()
    has_benefit = any(kw.lower() in lower for kw in _BENEFIT_KEYWORDS)
    if not has_benefit:
        return False
    has_identity = any(kw.lower() in lower for kw in _IDENTITY_KEYWORDS)
    if len(text) < 80 and not has_identity:
        return False
    return True


# ── 地點分類規則 ──────────────────────────────────────────────────────────────

_LOCATION_RULES = [
    (
        "NYCU 校區周邊",
        [
            "陽明交大", "陽明交通大學", "nycu", "交大",
            "光復校區", "博愛校區", "六家校區", "陽明校區",
            "光復路", "大學路",  # 新竹交大周邊常見路名
        ],
    ),
    (
        "台北",
        [
            "台北", "臺北", "信義區", "中山區", "松山區", "大安區",
            "士林區", "北投區", "萬華區", "南港區", "文山區", "中正區",
            "大同區", "內湖區", "木柵", "天母", "表演藝術中心",
        ],
    ),
    (
        "新竹",
        [
            "新竹", "竹北", "東區", "北區",  # 新竹市區
        ],
    ),
    (
        "全台",
        ["全台", "全臺", "全門市", "全台適用", "全臺適用", "全國"],
    ),
    (
        "線上",
        ["線上", "官網", "線上申請", "線上購票", "online", "app", "網站", "網路"],
    ),
]


def classify_location(text: str) -> tuple[str, str]:
    """
    從文字推論地點。
    回傳 (location_raw, location_scope)。
    NYCU 校區優先於台北 / 新竹，避免「交大光復校區」被分到新竹一般地區。
    """
    lower = text.lower()
    for scope, keywords in _LOCATION_RULES:
        for kw in keywords:
            if kw.lower() in lower:
                # 取匹配到的原始片段作為 location_raw
                idx = lower.find(kw.lower())
                raw = text[max(0, idx - 5): idx + len(kw) + 10].strip()
                return raw, scope
    return "", "不明"


# ── 優惠欄位擷取 ──────────────────────────────────────────────────────────────

_DISCOUNT_PATTERNS = [
    r"[0-9]+\s*折",                # 8折、85折
    r"[0-9]+\s*%\s*off",          # 20% off
    r"優惠[：:]\s*.{2,30}",
    r"折扣[：:]\s*.{2,30}",
    r"學生票[：:].{2,30}",
    r"學生價[：:].{2,30}",
    r"NT\$?\s*[0-9,]+",           # NT$200
    r"[0-9,]+\s*元",              # 200元
    r"免費",
    r"半價",
]
_DISCOUNT_RE = re.compile("|".join(_DISCOUNT_PATTERNS), re.IGNORECASE)


def extract_discount(text: str) -> str:
    m = _DISCOUNT_RE.search(text)
    return m.group(0).strip() if m else ""


# ── 日期擷取 ──────────────────────────────────────────────────────────────────

_DATE_RE = re.compile(
    r"(\d{4})[/\-.年](\d{1,2})[/\-.月](\d{1,2})"
)

# 優惠期限相關的上下文關鍵字（日期前後 20 字內需出現）
_DEADLINE_CONTEXT = re.compile(
    r"(?:活動(?:日期|時間|期間)|優惠(?:期間|期限|截止)|有效(?:期間|期限|日期)"
    r"|使用期限|兌換期限|適用期間|即日起|期間限定|限時"
    r"|至|到|止|截止|結束|期滿"
    r"|~|～|–|—|-)",
    re.IGNORECASE,
)

# 文章 metadata 日期（應排除）
_META_DATE_CONTEXT = re.compile(
    r"(?:更新日期|發布日期|發佈日期|資料截止|資料更新|最後更新"
    r"|發布單位|分類|撰文|編輯|作者|發文"
    r"|場館優化進度|進度說明)",
    re.IGNORECASE,
)


def extract_dates(text: str) -> tuple[str, str]:
    """
    從文字中擷取優惠期限日期，回傳 (start_date, end_date)，格式 YYYY-MM-DD。

    只在日期前後 30 字內有期限相關關鍵字時才採用。
    排除文章更新日期、發布日期等 metadata。
    """
    dates = []
    for m in _DATE_RE.finditer(text):
        # 取日期前後 30 字的 context
        start = max(0, m.start() - 30)
        end = min(len(text), m.end() + 30)
        context = text[start:end]

        # 排除文章 metadata 日期
        if _META_DATE_CONTEXT.search(context):
            continue

        # 只保留有期限 context 的日期，或者出現「至」「~」等連接兩個日期的 pattern
        if _DEADLINE_CONTEXT.search(context):
            y, mo_s, d_s = m.group(1), m.group(2), m.group(3)
            mo, d = int(mo_s), int(d_s)
            if 1 <= mo <= 12 and 1 <= d <= 31:
                dates.append(f"{y}-{mo_s.zfill(2)}-{d_s.zfill(2)}")

    if not dates:
        return "", ""
    if len(dates) == 1:
        return dates[0], ""
    return dates[0], dates[-1]


# ── 主要正規化函式 ─────────────────────────────────────────────────────────────

def normalize_block(block: dict) -> dict:
    """
    把 raw block dict 轉成統一的優惠欄位 dict。
    欄位對應 spec 中定義的 data model。
    """
    text = block.get("text", "")
    source_url = block.get("source_url", "")
    now_iso = datetime.now(timezone.utc).isoformat()

    location_raw, location_scope = classify_location(text)
    discount = extract_discount(text)
    start_date, end_date = extract_dates(text)

    return {
        "title": _guess_title(text, block),
        "category": block.get("category_hint", "其他"),
        "merchant": "",          # 由 eligibility_filter 或人工補充
        "discount": discount,
        "location_raw": location_raw,
        "location_scope": location_scope,
        "eligibility_text": text[:500],   # 保留原文前 500 字供判斷
        "student_requirement": "",        # 由 eligibility_filter 填入
        "age_limit_text": "",             # 由 eligibility_filter 填入
        "age_result": "",
        "graduate_student_result": "",
        "final_result": "",
        "reason": "",
        "required_document": "",
        "start_date": start_date,
        "end_date": end_date,
        "source_name": block.get("source_name", ""),
        "source_url": source_url,
        "source_channel": block.get("source_channel", _infer_channel(block)),
        "source_confidence": block.get("source_confidence", "medium"),
        "is_nycu_official": block.get("is_nycu_official", False),
        "last_checked_at": now_iso,
        "notion_status": "待確認",
        "_raw_text": text,  # 保留原始文字，供 eligibility_filter 使用
    }


def _clean_title(raw: str) -> str:
    """清理 title 中的 Markdown link、HTML tag、多餘空白。"""
    # [![alt](url)](url) → alt
    raw = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", raw)
    # [text](url) → text
    raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)
    # <tag ...> </tag>
    raw = re.sub(r"<[^>]+>", "", raw)
    # 多餘空白
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def _guess_title(text: str, block: dict) -> str:
    """從 block 資訊猜測優惠標題。"""
    if block.get("title"):
        return _clean_title(block["title"][:100])
    return _clean_title(text[:60])


def _infer_channel(block: dict) -> str:
    tag = block.get("tag", "")
    source_id = block.get("source_id", "")
    if "pdf" in tag:
        return "pdf"
    if "search" in tag or "search" in source_id:
        return "google_search"
    return "official_web"
