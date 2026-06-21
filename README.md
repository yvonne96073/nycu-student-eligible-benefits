# nycu-student-eligible-benefits

NYCU 研究生學生優惠自動搜尋工具。

**使用者條件：** 32 歲、國立陽明交通大學研究生、持學生證。

自動從公開網站、PDF、搜尋結果、合法社群 connector 找出你真的可以用的學生優惠，整理成可同步到 Notion 的格式。

---

## 快速開始

```bash
# 1. 安裝相依套件
pip install -r requirements.txt

# 2. 複製環境變數範本
cp .env.example .env

# 3. 執行 dry-run（抓公開來源，印出結果）
python main.py --dry-run

# 4. 只看「可用」和「可能可用」
python main.py --only-usable

# 5. 同步到 Notion（需先設定 .env）
python main.py --sync-notion

# 6. 只跑指定來源
python main.py --source nycu_partner_stores

# 7. 額外啟用 Threads 來源（需設 THREADS_ACCESS_TOKEN）
python main.py --include-threads

# 8. 啟用所有社群 connector
python main.py --include-social
```

---

## 優惠判斷邏輯

| final_result | 條件 |
|---|---|
| **可用** | 學生身分符合 + 年齡符合或無限制 + 沒排除研究生 + 未過期 |
| **可能可用** | 學生優惠但資格文字不完整，需人工確認 |
| **不可用** | 年齡不符 / 排除研究生 / 限高中以下 / 已過期 |

年齡邊界：「未滿 32 歲」→ 不符合（你剛好 32，嚴格 < 32 不含）。「32 歲以下」→ 符合（含 32）。

Notion 只同步「可用」和「可能可用」，「不可用」只出現在 dry-run 輸出。

---

## 專案結構

```
nycu-student-eligible-benefits/
├── main.py                        # 整合入口，支援 CLI 參數
├── sources.yaml                   # 所有來源設定
├── requirements.txt
├── .env.example                   # 環境變數範本
└── src/
    ├── scraper.py                 # 公開 HTML scraper
    ├── pdf_parser.py              # PDF 解析（pdfplumber）
    ├── search_adapter.py          # Google Search 來源 adapter
    ├── normalize.py               # 統一欄位格式 + 地點分類
    ├── eligibility_filter.py      # 年齡 / 學生身分 / 研究生資格判斷
    ├── dedup.py                   # 穩定 hash 去重
    ├── notion_client.py           # Notion dry-run 與同步
    └── social_connectors/
        ├── base.py                # SocialConnector 抽象類別
        ├── facebook_connector.py  # Meta Graph API（stub）
        ├── instagram_connector.py # Instagram Graph API（stub）
        ├── threads_connector.py   # Threads 三層架構（stub）
        └── dcard_public.py        # Dcard 公開版（experimental）
```

---

## 來源分級

### 第一版可立即自動化（不需 token）

| 來源 | source_type | 說明 |
|---|---|---|
| NYCU 特約商店 | html | nycu.edu.tw 公開頁 |
| NYCU 校內餐廳 | html | 公開餐廳資訊 |
| NYCU 活動公告 | html | 學務處公告 |
| 台北 / 新竹博物館展覽 | html | 公開票價頁 |
| 台北 / 新竹 / 線上搜尋 | google_search | stub，可接 Custom Search API |
| Dcard 優惠版 | dcard_public | experimental，不需 token |

### 需要 API token 的來源

| 來源 | 需要 | 設定方式 |
|---|---|---|
| Facebook | `FACEBOOK_ACCESS_TOKEN` | Meta Graph API |
| Instagram | `INSTAGRAM_ACCESS_TOKEN` | Instagram Graph API |
| Threads | `THREADS_ACCESS_TOKEN` + `THREADS_SEARCH_ENABLED=true` | Meta Threads API |
| Gmail | `GMAIL_ENABLED=true` + OAuth | Gmail API |
| Google Search | `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` | Custom Search JSON API |

**沒有設定 token 的 connector 會自動跳過，不會讓主程式失敗。**

---

## 接 Notion API

1. 前往 [notion.so/my-integrations](https://www.notion.so/my-integrations) 建立 integration
2. 取得 `NOTION_TOKEN`
3. 建立 database，邀請 integration 加入
4. 取得 `NOTION_DATABASE_ID`（URL 中的 32 位 ID）
5. 填入 `.env`，執行 `python main.py --sync-notion`

Notion database 需要建立以下欄位（名稱、類型）：
`名稱`（Title）、`類別`（Select）、`優惠內容`（Text）、`地點分類`（Select）、
`最終結果`（Select）、`判斷理由`（Text）、`來源 URL`（URL）、
`Notion 狀態`（Select）、`Hash`（Text）等。

---

## 跑測試

```bash
python -m pytest tests/ -v
```

60 個測試，涵蓋年齡判斷、學生身分判斷、地點分類、final_result、去重、社群 connector stub。

---

## 下一步建議

1. **接 Google Custom Search API**：在 `.env` 填入 `GOOGLE_API_KEY` 和 `GOOGLE_CSE_ID`，`search_adapter.py` 即可自動呼叫，不需修改程式碼。

2. **接 Notion**：建立 Notion database → 填 token → `python main.py --sync-notion`。

3. **接 Threads API**：申請 [Meta Threads API](https://developers.facebook.com/docs/threads) 存取權限，填入 `THREADS_ACCESS_TOKEN`，在 `threads_connector.py` 實作真實 API 呼叫（stub 已預留位置）。

4. **定時執行**：用 Windows 工作排程器或 cron 定期跑 `python main.py --sync-notion`。

5. **新增來源**：在 `sources.yaml` 加入新的 `html` 或 `google_search` 來源即可，不需修改程式碼。

6. **提升 normalize 精度**：目前以規則擷取優惠內容，可針對 NYCU 官網格式加強 parser。
