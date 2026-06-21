"""PDF parser：使用 pdfplumber 解析公開 PDF，優先抽文字，遇到表格則抽表格。"""

import io
import logging
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except ImportError:
    _HAS_PDFPLUMBER = False
    logger.warning("pdfplumber 未安裝，PDF 解析功能停用。請執行 pip install pdfplumber")


def _download_pdf(url: str) -> Optional[bytes]:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "").lower()
        if "pdf" not in content_type:
            logger.warning("URL 回傳的 Content-Type 不是 PDF（%s），跳過：%s", content_type, url)
            return None
        return resp.content
    except requests.RequestException as e:
        logger.warning("無法下載 PDF %s：%s", url, e)
        return None


def parse_pdf_bytes(pdf_bytes: bytes, source_url: str = "") -> list[dict]:
    """
    解析 PDF bytes，回傳文字區塊清單。
    有表格時先抽表格；沒有表格時抽純文字段落。
    """
    if not _HAS_PDFPLUMBER:
        return []

    blocks = []
    try:
        pdf_file = pdfplumber.open(io.BytesIO(pdf_bytes))
    except Exception as e:
        logger.warning("無法解析 PDF（檔案可能損壞）：%s", e)
        return []

    with pdf_file as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # 嘗試抽表格
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        cells = [str(c).strip() for c in row if c]
                        text = " | ".join(cells)
                        if len(text) > 5:
                            blocks.append({
                                "text": text,
                                "tag": "table_row",
                                "source_url": source_url,
                                "page": page_num,
                            })
            else:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    line = line.strip()
                    if len(line) > 10:
                        blocks.append({
                            "text": line,
                            "tag": "pdf_text",
                            "source_url": source_url,
                            "page": page_num,
                        })
    return blocks


def parse_pdf_url(url: str) -> list[dict]:
    """下載並解析 PDF URL，回傳文字區塊清單。"""
    pdf_bytes = _download_pdf(url)
    if pdf_bytes is None:
        return []
    return parse_pdf_bytes(pdf_bytes, source_url=url)


def parse_pdf_source(source: dict) -> list[dict]:
    """根據 source 定義解析 PDF。"""
    url = source.get("url", "")
    if not url:
        return []

    logger.info("解析 PDF：%s（%s）", source.get("name"), url)
    blocks = parse_pdf_url(url)
    for b in blocks:
        b["source_id"] = source.get("id")
        b["source_name"] = source.get("name")
        b["source_confidence"] = source.get("source_confidence", "medium")
        b["is_nycu_official"] = source.get("is_nycu_official", False)
        b["category_hint"] = source.get("category_hint", "其他")
    return blocks
