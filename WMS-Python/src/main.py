import logging
import sys
import os
import tkinter as tk
from tkinter import messagebox

# 取得 main.py 所在的目錄 (即 src/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 取得 src 的上一層目錄 (即專案根目錄 WMS-Python/)
project_root = os.path.dirname(current_dir)

# 將專案根目錄加入 Python 搜尋路徑
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import DB_PATH, SCHEMA_PATH
from src.infrastructure.database.db_manager import DatabaseManager
from src.infrastructure.repositories import SqliteProductRepository, SqliteDocumentRepository
from src.application.services import InventoryService
from src.interface.app import MainWindow

# 設定 Log 格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Main")

def main():
    try:
        logger.info("系統啟動中...")

        # 1. Infrastructure Layer (資料庫與儲存庫)
        db_manager = DatabaseManager(DB_PATH)
        
        # 初始化 Schema (若首次執行)
        # 注意：正式環境通常由 migration tool 處理，這裡為了 MVP 方便直接檢查
        db_manager.initialize_schema(SCHEMA_PATH)

        product_repo = SqliteProductRepository(db_manager)
        document_repo = SqliteDocumentRepository(db_manager)

        # 2. Application Layer (業務邏輯服務)
        inventory_service = InventoryService(product_repo, document_repo)

        # 3. UI Layer (視窗介面)
        app = MainWindow(inventory_service)
        
        # 啟動主迴圈
        logger.info("進入 UI 主迴圈")
        app.mainloop()

    except Exception as e:
        logger.exception("系統發生致命錯誤")
        # 如果 UI 已經啟動失敗，嘗試用原生視窗報錯
        try:
            messagebox.showerror("Fatal Error", f"系統無法啟動:\n{e}")
        except:
            print(f"CRITICAL: {e}")
    finally:
        # 確保資源釋放 (如果有)
        pass

if __name__ == "__main__":
    main()