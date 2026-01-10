import sqlite3
import logging
from typing import List, Optional
from src.application.interfaces import IProductRepository
from src.domain.models import Product, Variant
from src.domain.exceptions import RepositoryError, EntityNotFoundError, DuplicateEntityError
from src.infrastructure.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class SqliteProductRepository(IProductRepository):
    """
    SQLite 版本的商品儲存庫實作。
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def add_product(self, product: Product) -> Product:
        query = """
            INSERT INTO products (name, brand, category, base_price, description)
            VALUES (?, ?, ?, ?, ?)
        """
        conn = self.db_manager.get_connection()
        try:
            with conn:
                cursor = conn.execute(query, (
                    product.name,
                    product.brand,
                    product.category,
                    product.base_price,
                    product.description
                ))
                product.id = cursor.lastrowid
                logger.info(f"已新增商品: {product.name} (ID: {product.id})")
                return product
        except sqlite3.Error as e:
            logger.error(f"新增商品失敗: {e}")
            raise RepositoryError(f"資料庫錯誤: {e}")

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        query = "SELECT * FROM products WHERE id = ?"
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(query, (product_id,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_product(row)
            return None
        except sqlite3.Error as e:
            raise RepositoryError(f"查詢商品失敗: {e}")

    def get_all_products(self) -> List[Product]:
        query = "SELECT * FROM products ORDER BY id DESC"
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            return [self._map_row_to_product(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"取得商品列表失敗: {e}")

    def update_product(self, product: Product) -> None:
        if product.id is None:
            raise RepositoryError("無法更新沒有 ID 的商品")
            
        query = """
            UPDATE products 
            SET name = ?, brand = ?, category = ?, base_price = ?, description = ?
            WHERE id = ?
        """
        conn = self.db_manager.get_connection()
        try:
            with conn:
                cursor = conn.execute(query, (
                    product.name,
                    product.brand,
                    product.category,
                    product.base_price,
                    product.description,
                    product.id
                ))
                if cursor.rowcount == 0:
                    raise EntityNotFoundError(f"找不到 ID 為 {product.id} 的商品")
        except sqlite3.Error as e:
            raise RepositoryError(f"更新商品失敗: {e}")

    def delete_product(self, product_id: int) -> None:
        # 注意：schema.sql 設定了 ON DELETE CASCADE，所以刪除 Product 會自動刪除 Variants
        query = "DELETE FROM products WHERE id = ?"
        conn = self.db_manager.get_connection()
        try:
            with conn:
                cursor = conn.execute(query, (product_id,))
                if cursor.rowcount == 0:
                    raise EntityNotFoundError(f"找不到 ID 為 {product_id} 的商品")
                logger.info(f"已刪除商品 ID: {product_id}")
        except sqlite3.Error as e:
            raise RepositoryError(f"刪除商品失敗: {e}")

    def search_products(self, keyword: str) -> List[Product]:
        """
        實作模糊搜尋：
        使用 SQLite 的 LIKE 語法，針對 Name, Brand, Category, Description 進行匹配。
        """
        if not keyword:
            return self.get_all_products()

        # SQL: 只要任一欄位包含關鍵字即符合 (Case-insensitive)
        query = """
            SELECT * FROM products 
            WHERE name LIKE ? 
               OR brand LIKE ? 
               OR category LIKE ?
               OR description LIKE ?
            ORDER BY id DESC
        """
        search_term = f"%{keyword}%"
        params = (search_term, search_term, search_term, search_term)

        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [self._map_row_to_product(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"搜尋商品失敗: {e}")

    # --- Variant Methods ---

    def add_variant(self, variant: Variant) -> Variant:
        query = """
            INSERT INTO variants (product_id, size, color, sku, stock_qty, safety_stock)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        conn = self.db_manager.get_connection()
        try:
            with conn:
                cursor = conn.execute(query, (
                    variant.product_id,
                    variant.size,
                    variant.color,
                    variant.sku,
                    variant.stock_qty,
                    variant.safety_stock
                ))
                variant.id = cursor.lastrowid
                logger.info(f"已新增變體: {variant.display_name} (ID: {variant.id})")
                return variant
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise DuplicateEntityError(f"變體 SKU 或組合重複: {e}")
            raise RepositoryError(f"新增變體失敗: {e}")
        except sqlite3.Error as e:
            raise RepositoryError(f"新增變體失敗: {e}")

    def get_variants_by_product_id(self, product_id: int) -> List[Variant]:
        query = "SELECT * FROM variants WHERE product_id = ?"
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(query, (product_id,))
            rows = cursor.fetchall()
            return [self._map_row_to_variant(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"查詢變體列表失敗: {e}")
    
    def get_variant_by_id(self, variant_id: int) -> Optional[Variant]:
        query = "SELECT * FROM variants WHERE id = ?"
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(query, (variant_id,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_variant(row)
            return None
        except sqlite3.Error as e:
            raise RepositoryError(f"查詢變體失敗: {e}")

    def get_variant_by_sku(self, sku: str) -> Optional[Variant]:
        query = "SELECT * FROM variants WHERE sku = ?"
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(query, (sku,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_variant(row)
            return None
        except sqlite3.Error as e:
            raise RepositoryError(f"依 SKU 查詢失敗: {e}")

    def update_variant(self, variant: Variant) -> None:
        if variant.id is None:
            raise RepositoryError("無法更新沒有 ID 的變體")
            
        query = """
            UPDATE variants 
            SET size = ?, color = ?, sku = ?, stock_qty = ?, safety_stock = ?
            WHERE id = ?
        """
        conn = self.db_manager.get_connection()
        try:
            with conn:
                cursor = conn.execute(query, (
                    variant.size,
                    variant.color,
                    variant.sku,
                    variant.stock_qty,
                    variant.safety_stock,
                    variant.id
                ))
                if cursor.rowcount == 0:
                    raise EntityNotFoundError(f"找不到 ID 為 {variant.id} 的變體")
        except sqlite3.Error as e:
            raise RepositoryError(f"更新變體失敗: {e}")

    # --- Mapping Helpers ---

    def _map_row_to_product(self, row: sqlite3.Row) -> Product:
        """將資料庫 Row 轉換為 Product 物件"""
        return Product(
            id=row['id'],
            name=row['name'],
            brand=row['brand'],
            category=row['category'],
            base_price=row['base_price'],
            description=row['description'],
            created_at=row['created_at']
        )

    def _map_row_to_variant(self, row: sqlite3.Row) -> Variant:
        """將資料庫 Row 轉換為 Variant 物件"""
        return Variant(
            id=row['id'],
            product_id=row['product_id'],
            size=row['size'],
            color=row['color'],
            sku=row['sku'],
            stock_qty=row['stock_qty'],
            safety_stock=row['safety_stock']
        )

from src.application.interfaces import IDocumentRepository, IProductRepository # 更新匯入
from src.domain.models import Document, DocumentItem

class SqliteDocumentRepository(IDocumentRepository):
    """
    SQLite 版本的單據儲存庫實作。
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def add_document(self, document: Document) -> Document:
        """
        新增單據與明細。
        使用 Transaction 確保主檔與明細同時寫入成功，否則全部 rollback。
        """
        conn = self.db_manager.get_connection()
        try:
            with conn: # 開啟交易
                # 1. 寫入單據主檔 (Header)
                header_query = """
                    INSERT INTO documents (doc_type, doc_date, note)
                    VALUES (?, ?, ?)
                """
                cursor = conn.execute(header_query, (
                    document.doc_type,
                    document.doc_date,
                    document.note
                ))
                new_doc_id = cursor.lastrowid
                document.id = new_doc_id

                # 2. 寫入單據明細 (Items)
                item_query = """
                    INSERT INTO document_items (doc_id, variant_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """
                items_data = [
                    (new_doc_id, item.variant_id, item.quantity, item.unit_price)
                    for item in document.items
                ]
                
                # executemany 批次寫入效能較佳
                cursor.executemany(item_query, items_data)
                
                logger.info(f"已建立單據 ID: {new_doc_id} (含 {len(items_data)} 筆明細)")
                return document
                
        except sqlite3.Error as e:
            logger.error(f"新增單據失敗: {e}")
            raise RepositoryError(f"資料庫交易錯誤: {e}")

    def get_document_by_id(self, doc_id: int) -> Optional[Document]:
        conn = self.db_manager.get_connection()
        try:
            # 1. 查詢主檔
            header_query = "SELECT * FROM documents WHERE id = ?"
            cursor = conn.execute(header_query, (doc_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            document = self._map_row_to_document(row)
            
            # 2. 查詢並填入明細
            items_query = """
                SELECT i.*, v.size, v.color, p.name as product_name
                FROM document_items i
                JOIN variants v ON i.variant_id = v.id
                JOIN products p ON v.product_id = p.id
                WHERE i.doc_id = ?
            """
            cursor = conn.execute(items_query, (doc_id,))
            item_rows = cursor.fetchall()
            
            for item_row in item_rows:
                item = DocumentItem(
                    id=item_row['id'],
                    variant_id=item_row['variant_id'],
                    quantity=item_row['quantity'],
                    unit_price=item_row['unit_price']
                )

                item.product_name = item_row['product_name']
                item.size = item_row['size']
                item.color = item_row['color']
                document.add_item(item)
                
                # 這裡我們可以選擇性地填充 item.variant 資訊以便顯示，但核心是 ID
                # document.add_item(item)
                
            return document

        except sqlite3.Error as e:
            raise RepositoryError(f"查詢單據失敗: {e}")

    def get_all_documents(self, doc_type: Optional[str] = None) -> List[Document]:
        conn = self.db_manager.get_connection()
        try:
            query = "SELECT * FROM documents"
            params = []
            
            if doc_type:
                query += " WHERE doc_type = ?"
                params.append(doc_type)
            
            query += " ORDER BY doc_date DESC, id DESC"
            
            cursor = conn.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            # 注意：列表查詢通常只回傳 Header，不預先載入 Items (Lazy Loading) 以節省效能
            # 若 UI 需要顯示詳情，再呼叫 get_document_by_id
            return [self._map_row_to_document(row) for row in rows]
            
        except sqlite3.Error as e:
            raise RepositoryError(f"取得單據列表失敗: {e}")

    def _map_row_to_document(self, row: sqlite3.Row) -> Document:
        return Document(
            id=row['id'],
            doc_type=row['doc_type'],
            doc_date=row['doc_date'], # 注意: SQLite date 讀出來可能是字串，Domain 層可能需要 parse
            note=row['note'],
            created_at=row['created_at']
        )
    
    def delete_document(self, doc_id: int) -> None:
        query = "DELETE FROM documents WHERE id = ?"
        conn = self.db_manager.get_connection()
        try:
            with conn:
                cursor = conn.execute(query, (doc_id,))
                if cursor.rowcount == 0:
                    logger.warning(f"嘗試刪除不存在的單據 ID: {doc_id}")
                else:
                    logger.info(f"已刪除單據 ID: {doc_id}")
        except sqlite3.Error as e:
            logger.error(f"刪除單據失敗: {e}")
            raise RepositoryError(f"資料庫刪除錯誤: {e}")