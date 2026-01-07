import logging
from typing import List, Optional
from datetime import date

from src.domain.models import Product, Variant, Document, DocumentItem
from src.domain.exceptions import EntityNotFoundError, BusinessRuleViolation, OutOfStockError
from src.application.interfaces import IProductRepository, IDocumentRepository

logger = logging.getLogger(__name__)

class InventoryService:
    """
    庫存管理服務 (Application Service)
    負責協調商品庫存與單據的業務流程。
    """

    def __init__(
        self, 
        product_repo: IProductRepository, 
        document_repo: IDocumentRepository
    ):
        self.product_repo = product_repo
        self.document_repo = document_repo

    # --- 商品與變體查詢 (Query) ---

    def get_all_products(self) -> List[Product]:
        return self.product_repo.get_all_products()

    def get_variants_for_product(self, product_id: int) -> List[Variant]:
        return self.product_repo.get_variants_by_product_id(product_id)

    def get_low_stock_variants(self) -> List[Variant]:
        """
        取得所有低於安全庫存水位的變體。
        (這是一個跨 Aggregate 的查詢，適合放在 Service 層)
        """
        # 注意: 如果資料量大，建議在 Repository 層實作 SQL 篩選 (WHERE stock_qty <= safety_stock)
        # 這裡為了 MVP 簡單化，先撈出所有變體再過濾 (Python Filter)
        all_products = self.product_repo.get_all_products()
        low_stock_list = []
        
        for product in all_products:
            variants = self.product_repo.get_variants_by_product_id(product.id)
            for variant in variants:
                if variant.is_low_stock():
                    # 為了顯示方便，我們可以手動將 product info 注入 variant (雖然有點 Dirty，但對 UI 很有用)
                    # 或者回傳一個專門的 DTO (Data Transfer Object)
                    low_stock_list.append(variant)
        
        return low_stock_list

    # --- 交易流程 (Transactions) ---

    def create_inbound_order(self, document: Document) -> Document:
        """
        建立進貨單 (Inbound)
        邏輯: 
        1. 儲存單據
        2. 增加對應變體的庫存
        """
        if document.doc_type != 'INBOUND':
            raise BusinessRuleViolation("單據類型必須為 INBOUND")

        # 1. 儲存單據
        saved_doc = self.document_repo.add_document(document)
        
        # 2. 更新庫存 (增加)
        for item in saved_doc.items:
            variant = self.product_repo.get_variant_by_id(item.variant_id)
            if not variant:
                logger.error(f"變體 ID {item.variant_id} 不存在，跳過庫存更新")
                continue
            
            # 業務邏輯: 進貨 = 原庫存 + 進貨量
            variant.stock_qty += item.quantity
            self.product_repo.update_variant(variant)
            
        logger.info(f"進貨單 {saved_doc.id} 完成，庫存已更新。")
        return saved_doc

    def create_outbound_order(self, document: Document) -> Document:
        """
        建立銷貨單 (Outbound)
        邏輯:
        1. 檢查所有項目的庫存是否充足 (Fail Fast)
        2. 儲存單據
        3. 扣減庫存
        """
        if document.doc_type != 'OUTBOUND':
            raise BusinessRuleViolation("單據類型必須為 OUTBOUND")

        # Step 1: 預先檢查庫存 (Pre-check)
        # 避免發生「第1個商品扣成功，第2個商品庫存不足」導致的數據不一致
        for item in document.items:
            variant = self.product_repo.get_variant_by_id(item.variant_id)
            if not variant:
                raise EntityNotFoundError(f"變體 ID {item.variant_id} 不存在")
            
            if variant.stock_qty < item.quantity:
                raise OutOfStockError(
                    f"庫存不足: {variant.display_name} (庫存: {variant.stock_qty}, 需求: {item.quantity})"
                )

        # Step 2: 儲存單據
        saved_doc = self.document_repo.add_document(document)

        # Step 3: 實際扣庫存
        for item in saved_doc.items:
            variant = self.product_repo.get_variant_by_id(item.variant_id)
            # 業務邏輯: 銷貨 = 原庫存 - 銷貨量
            variant.stock_qty -= item.quantity
            self.product_repo.update_variant(variant)

        logger.info(f"銷貨單 {saved_doc.id} 完成，庫存已扣除。")
        return saved_doc

    def create_adjustment_order(self, document: Document) -> Document:
        """
        建立庫存調整單 (Adjustment) (例如盤點差異)
        邏輯:
        調整單的 quantity 代表「差異數」。
        正數 = 盤盈 (增加庫存)
        負數 = 盤虧 (減少庫存)
        """
        if document.doc_type != 'ADJUST':
            raise BusinessRuleViolation("單據類型必須為 ADJUST")

        saved_doc = self.document_repo.add_document(document)

        for item in saved_doc.items:
            variant = self.product_repo.get_variant_by_id(item.variant_id)
            if not variant:
                continue
            
            # 業務邏輯: 直接加總 (quantity 可正可負)
            # 例如: 庫存10, 盤點為8 (少了2) -> quantity = -2 -> 10 + (-2) = 8
            new_qty = variant.stock_qty + item.quantity
            
            if new_qty < 0:
                raise BusinessRuleViolation(f"調整後庫存不能為負數: {variant.display_name}")

            variant.stock_qty = new_qty
            self.product_repo.update_variant(variant)

        logger.info(f"調整單 {saved_doc.id} 完成。")
        return saved_doc
    
    # --- 查詢與報表 (Queries) ---

    def get_documents(self, doc_type: Optional[str] = None) -> List[Document]:
        """查詢單據列表 (只回傳 Header，不含 Items 以節省效能)"""
        return self.document_repo.get_all_documents(doc_type)

    def get_document_detail(self, doc_id: int) -> Optional[Document]:
        """查詢單據完整內容 (包含 Items)"""
        return self.document_repo.get_document_by_id(doc_id)
    
    def delete_document(self, doc_id: int) -> None:
        """
        刪除單據並回滾庫存。
        策略: 嚴格檢查 (Strict Check)。若回滾導致負庫存則禁止刪除。
        """
        # 1. 取得單據內容
        doc = self.document_repo.get_document_by_id(doc_id)
        if not doc:
            raise EntityNotFoundError(f"單據 ID {doc_id} 不存在")

        # 2. 計算回滾對庫存的影響 (Pre-calculation)
        # 我們使用 map 來累加每個變體的變動量 (impact)，避免多次讀寫
        impacts = {} # Dict[variant_id, change_amount]

        for item in doc.items:
            change = 0
            if doc.doc_type == 'INBOUND':
                # 原本是增加，回滾就是減少
                change = -item.quantity
            elif doc.doc_type == 'OUTBOUND':
                # 原本是減少，回滾就是增加
                change = item.quantity
            elif doc.doc_type == 'ADJUST':
                # 原本是 +qty (可能負)，回滾就是 -qty
                change = -item.quantity
            
            impacts[item.variant_id] = impacts.get(item.variant_id, 0) + change

        # 3. 嚴格檢查 (Strict Check)
        # 在執行任何修改前，先確認所有變體回滾後都不會 < 0
        for vid, change in impacts.items():
            if change < 0: # 只有扣庫存才需要檢查
                variant = self.product_repo.get_variant_by_id(vid)
                if not variant: continue 
                
                final_qty = variant.stock_qty + change
                if final_qty < 0:
                    raise BusinessRuleViolation(
                        f"庫存不足，請先補單並備註。\n"
                        f"商品: {variant.display_name}\n"
                        f"當前: {variant.stock_qty}, 回滾需扣: {abs(change)}"
                    )

        # 4. 執行回滾更新
        for vid, change in impacts.items():
            if change == 0: continue
            variant = self.product_repo.get_variant_by_id(vid)
            if variant:
                variant.stock_qty += change
                self.product_repo.update_variant(variant)

        # 5. 最後刪除單據
        self.document_repo.delete_document(doc_id)
        logger.info(f"單據 {doc_id} 刪除成功，庫存已回滾。")

        # [新增] 刪除單據與庫存回滾邏輯
    def delete_document(self, doc_id: int) -> None:
        """
        刪除單據並回滾庫存。
        策略: 嚴格檢查 (Strict Check)。若回滾導致負庫存則禁止刪除。
        """
        # 1. 取得單據內容
        doc = self.document_repo.get_document_by_id(doc_id)
        if not doc:
            raise EntityNotFoundError(f"單據 ID {doc_id} 不存在")

        # 2. 計算回滾對庫存的影響 (Pre-calculation)
        # 我們使用 map 來累加每個變體的變動量 (impact)，避免多次讀寫
        impacts = {} # Dict[variant_id, change_amount]

        for item in doc.items:
            change = 0
            if doc.doc_type == 'INBOUND':
                # 原本是增加，回滾就是減少
                change = -item.quantity
            elif doc.doc_type == 'OUTBOUND':
                # 原本是減少，回滾就是增加
                change = item.quantity
            elif doc.doc_type == 'ADJUST':
                # 原本是 +qty (可能負)，回滾就是 -qty
                change = -item.quantity
            
            impacts[item.variant_id] = impacts.get(item.variant_id, 0) + change

        # 3. 嚴格檢查 (Strict Check)
        # 在執行任何修改前，先確認所有變體回滾後都不會 < 0
        for vid, change in impacts.items():
            if change < 0: # 只有扣庫存才需要檢查
                variant = self.product_repo.get_variant_by_id(vid)
                if not variant: continue 
                
                final_qty = variant.stock_qty + change
                if final_qty < 0:
                    raise BusinessRuleViolation(
                        f"庫存不足，請先補單並備註。\n"
                        f"商品: {variant.display_name}\n"
                        f"當前: {variant.stock_qty}, 回滾需扣: {abs(change)}"
                    )

        # 4. 執行回滾更新
        for vid, change in impacts.items():
            if change == 0: continue
            variant = self.product_repo.get_variant_by_id(vid)
            if variant:
                variant.stock_qty += change
                self.product_repo.update_variant(variant)

        # 5. 最後刪除單據
        self.document_repo.delete_document(doc_id)
        logger.info(f"單據 {doc_id} 刪除成功，庫存已回滾。")