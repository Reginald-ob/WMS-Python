import os
import sys
from pathlib import Path

# --- 路徑解析核心邏輯 ---
if getattr(sys, 'frozen', False):
    # [打包環境]
    # sys.executable 是 .exe 檔案的絕對路徑
    # 我們取它的目錄作為 ROOT_DIR，這樣 wms.db 就會產生在 exe 旁邊
    ROOT_DIR = os.path.dirname(sys.executable)
    
    # [資源讀取]
    # 對於 schema.sql 這種打包進去的靜態資源，它位於解壓後的暫存目錄 (_MEIPASS)
    # 我們需要另外定義一個 BASE_RESOURCE_DIR
    BASE_RESOURCE_DIR = sys._MEIPASS
else:
    # [開發環境]
    # 維持原本邏輯，以 config.py 所在位置往上推兩層
    ROOT_DIR = str(Path(__file__).parent.parent)
    BASE_RESOURCE_DIR = ROOT_DIR

# --- 資料庫設定 ---
DB_NAME = "wms.db"

# 重要：資料庫要存在 "使用者看得到的目錄" (exe 旁邊)，所以使用 ROOT_DIR
DB_PATH = os.path.join(ROOT_DIR, DB_NAME)

# 重要：Schema 是唯讀的腳本，位於 "程式碼內部" (暫存區)，所以使用 BASE_RESOURCE_DIR
# 這裡的路徑結構要對應 pyinstaller 的 --add-data 參數
# 原本指令是: src/infrastructure/database/schema.sql;src/infrastructure/database
# 所以在暫存區內的路徑結構是 src/infrastructure/database/schema.sql
SCHEMA_PATH = os.path.join(BASE_RESOURCE_DIR, "src", "infrastructure", "database", "schema.sql")

# --- UI 設定 (維持不變) ---
WINDOW_TITLE = "WMS-Python 體育用品庫存管理系統"
WINDOW_SIZE = "1024x768"
THEME_FONT = ("Microsoft JhengHei", 10)
TITLE_FONT = ("Microsoft JhengHei", 12, "bold")
HEADER_FONT = ("Microsoft JhengHei", 16, "bold")