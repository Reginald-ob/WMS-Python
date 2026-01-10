## 🚀 使用範例 (Usage Example)

本系統採用模組化設計。由於專案結構依賴於 `src` 套件，請確保在**專案根目錄**下執行程式。

### 啟動應用程式

透過 Python 直接執行入口點腳本：

```bash
# 確保位於專案根目錄 (WMS-Python/)
python src/main.py

```

在Visual Studio`main.py`，運行後`main.py`會自動初始化資料庫 schema 並注入依賴 (Dependency Injection)，最後啟動 GUI 介面。

## ⚙️ 配置 (Configuration)

本專案主要設定檔位於 `src/config.py`。目前不需額外的 `.env` 檔案，所有路徑皆採相對路徑設計。

| 變數名稱 | 預設值 | 說明 |
| --- | --- | --- |
| `DB_NAME` | `wms.db` | SQLite 資料庫檔案名稱 |
| `DB_PATH` | `ROOT_DIR/wms.db` | 資料庫完整路徑，預設位於專案根目錄 |
| `SCHEMA_PATH` | `src/infrastructure/database/schema.sql` | 資料庫初始化 SQL 腳本路徑 |
| `WINDOW_TITLE` | `WMS-Python ...` | 應用程式視窗標題 |
| `WINDOW_SIZE` | `1024x768` | 預設視窗大小 |

若需修改資料庫位置或 UI 字型設定，請直接編輯 `src/config.py`。

## 📦 依賴 (Dependencies)

### 核心依賴 (Core)

本專案堅持 MVP 原則，核心邏輯僅使用 Python 3.10+ **標準函式庫 (Standard Library)**，無需安裝額外套件即可運行：

* `tkinter`: 用戶介面 (UI)
* `sqlite3`: 資料庫驅動
* `logging`: 系統日誌
* `dataclasses`: 資料實體定義

### 開發與打包 (Dev & Build)

若需執行測試或打包為執行檔，需安裝以下套件：

* `pytest`: 執行單元測試
* `pyinstaller`: 打包 .exe 檔案

安裝開發依賴：

```bash
pip install pyinstaller pytest

```

## 🛠 疑難排解 (Troubleshooting)

以下列出系統常見錯誤與對應的代碼層級原因：

### 1. 系統無法啟動 (Fatal Error)

* **現象**：跳出 "Fatal Error" 視窗，顯示 `ModuleNotFoundError`。
* **原因**：執行路徑錯誤，導致 Python 找不到 `src` 模組。
* **解法**：請確保您是在 `WMS-Python` 根目錄下執行 `python src/main.py`，而非進入 `src` 資料夾後執行。`main.py` 內已包含路徑修正邏輯以減輕此問題。

### 2. 變體 SKU 重複 (DuplicateEntityError)

* **現象**：新增變體時失敗，Log 顯示 `IntegrityError`。
* **原因**：資料庫中已存在相同的 `sku` 編碼。Repository 層會捕捉 SQLite 的 `UNIQUE constraint failed` 並拋出 `DuplicateEntityError`。
* **解法**：請確認變體的 SKU 是唯一的，或留空讓系統自動生成。

### 3. 庫存不足警告 (OutOfStockError)

* **現象**：建立銷貨單時失敗。
* **原因**：Service 層在寫入前會預先檢查庫存 (`Pre-check`)。若 `variant.stock_qty < item.quantity`，會觸發 `OutOfStockError` 並中止交易。
* **解法**：請先建立「進貨單 (INBOUND)」或「調整單 (ADJUST)」以補足庫存。

## 📦 打包指令 (Pyinstaller)
```bash
pyinstaller --noconsole --onefile --name="SportWMS" --paths="." --add-data "src/infrastructure/database/schema.sql;src/infrastructure/database" --icon=NONE src/main.py
```

* 更新於2026/1/2

