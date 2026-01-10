import csv
import sqlite3
from src.config import DB_PATH

def export_data_for_analysis(db_path=DB_PATH, output_file="wms_analysis_export.csv"):
    """
    導出全量交易數據供 Excel 分析。
    包含：單據日期、類型、品牌、商品、規格、數量、單價、當前庫存(快照)。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 核心 SQL：將分散的資料表 Join 成一張分析大表
    # 特別注意：這裡同時拉出了 'unit_price' (交易價) 用於計算毛利
    query = """
    SELECT 
        d.doc_date AS 日期,
        d.doc_type AS 單據類型,
        p.brand AS 品牌,
        p.name AS 商品名稱,
        v.sku AS SKU,
        v.size AS 尺寸,
        v.color AS 顏色,
        di.quantity AS 交易數量,
        di.unit_price AS 交易單價,
        (di.quantity * di.unit_price) AS 交易總額,
        v.stock_qty AS 當前庫存快照
    FROM document_items di
    JOIN documents d ON di.doc_id = d.id
    JOIN variants v ON di.variant_id = v.id
    JOIN products p ON v.product_id = p.id
    ORDER BY d.doc_date DESC, d.id DESC
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 取得欄位名稱
        headers = [description[0] for description in cursor.description]
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
            
        print(f"成功導出數據至: {output_file} (共 {len(rows)} 筆)")
        
    except Exception as e:
        print(f"導出失敗: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    export_data_for_analysis()