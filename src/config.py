import os
from pathlib import Path

# 專案根目錄
ROOT_DIR = Path(__file__).parent.parent

# 資料庫設定
DB_NAME = "wms.db"
DB_PATH = os.path.join(ROOT_DIR, DB_NAME)
SCHEMA_PATH = os.path.join(ROOT_DIR, "src", "infrastructure", "database", "schema.sql")

# UI 設定
WINDOW_TITLE = "WMS-Python 體育用品庫存管理系統"
WINDOW_SIZE = "1024x768"
THEME_FONT = ("Microsoft JhengHei", 10)
TITLE_FONT = ("Microsoft JhengHei", 12, "bold")
HEADER_FONT = ("Microsoft JhengHei", 16, "bold")