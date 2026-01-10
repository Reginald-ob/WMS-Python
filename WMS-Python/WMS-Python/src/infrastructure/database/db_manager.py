import sqlite3
import os
import logging
from typing import Optional
from pathlib import Path
import sys

# 設定 logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# [新增] 資源路徑解析函式
def resource_path(relative_path):
    """取得資源的絕對路徑，兼容開發環境與 PyInstaller 打包後的環境"""
    try:
        # PyInstaller 建立的暫存資料夾
        base_path = sys._MEIPASS
    except Exception:
        # 一般開發環境
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class DatabaseManager:
    def __init__(self, db_path: str, schema_path: str = None):
        self.db_path = db_path
        # 若未提供 schema_path，預設為相對路徑，並透過 resource_path 轉換
        if schema_path is None:
            # 注意: 這裡的路徑要與 add-data 的目標結構對應
            raw_path = os.path.join("src", "infrastructure", "database", "schema.sql")
            self.schema_path = resource_path(raw_path)
        else:
            self.schema_path = resource_path(schema_path)

class DatabaseManager:
    """
    負責 SQLite 資料庫的連線管理與初始化。
    使用 Singleton 模式或依賴注入確保連線統一。
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        """
        取得資料庫連線物件。
        如果連線不存在或已關閉，則重新建立。
        """
        if self._connection is None:
            try:
                # 確保目錄存在
                db_dir = os.path.dirname(self.db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir)
                
                self._connection = sqlite3.connect(self.db_path)
                
                # 設定 Row factory 以便透過欄位名稱存取資料 (dict-like)
                self._connection.row_factory = sqlite3.Row
                
                # 強制啟用外鍵約束 (SQLite 預設關閉)
                self._connection.execute("PRAGMA foreign_keys = ON;")
                
                logger.info(f"成功連線至資料庫: {self.db_path}")
            except sqlite3.Error as e:
                logger.error(f"資料庫連線失敗: {e}")
                raise e
        
        return self._connection

    def close(self):
        """關閉連線"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("資料庫連線已關閉")

    def initialize_schema(self, schema_file_path: str):
        """
        讀取 schema.sql 並初始化資料庫表格。
        """
        conn = self.get_connection()
        try:
            with open(schema_file_path, 'r', encoding='utf-8') as f:
                schema_script = f.read()
            
            with conn:
                conn.executescript(schema_script)
            
            logger.info("資料庫綱要 (Schema) 初始化完成")
        except FileNotFoundError:
            logger.error(f"找不到 Schema 檔案: {schema_file_path}")
            raise
        except sqlite3.Error as e:
            logger.error(f"初始化 Schema 失敗: {e}")
            raise

# 簡易測試 (開發用，實際執行會由 main.py 呼叫)
if __name__ == "__main__":
    # 假設路徑結構: src/infrastructure/database/
    current_dir = Path(__file__).parent
    schema_path = current_dir / "schema.sql"
    db_path = "wms_test.db"  # 測試用資料庫
    
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_schema(str(schema_path))
    db_manager.close()
    
    # 刪除測試檔
    if os.path.exists(db_path):
        os.remove(db_path)
        print("測試資料庫已清除")