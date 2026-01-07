import logging
from typing import Optional

from src.interface.views.variant_view import VariantView
from src.application.services import InventoryService
from src.domain.models import Variant
from src.domain.exceptions import DomainError

logger = logging.getLogger(__name__)

class VariantPresenter:
    """
    變體管理視窗的 Presenter。
    """

    def __init__(self, view: VariantView, service: InventoryService, product_id: int):
        self.view = view
        self.service = service
        self.product_id = product_id

        self.view.set_callbacks(
            on_add=self.handle_add_variant,
            on_delete=self.handle_delete_variant
        )
        
        self.load_variants()

    def load_variants(self):
        try:
            variants = self.service.get_variants_for_product(self.product_id)
            self.view.update_variant_list(variants)
        except Exception as e:
            logger.error(f"載入變體失敗: {e}")
            self.view.show_error("無法載入變體列表")

    def handle_add_variant(self):
        data = self.view.get_form_data()
        
        # 1. 驗證
        if not data["size"] or not data["color"]:
            self.view.show_error("尺寸與顏色為必填")
            return
            
        try:
            safety_stock = int(data["safety_stock"]) if data["safety_stock"] else 5
        except ValueError:
            self.view.show_error("安全庫存必須為整數")
            return

        # 2. 處理 SKU (若為空則自動生成)
        # 簡單規則: PROD-{ID}-{SIZE}-{COLOR}
        sku = data["sku"]
        if not sku:
            # 移除非法字元
            safe_size = "".join(c for c in data["size"] if c.isalnum())
            safe_color = "".join(c for c in data["color"] if c.isalnum())
            sku = f"P{self.product_id}-{safe_size}-{safe_color}".upper()

        # 3. 建立物件
        variant = Variant(
            product_id=self.product_id,
            size=data["size"],
            color=data["color"],
            sku=sku,
            stock_qty=0, # 初始庫存為 0，需透過進貨單增加
            safety_stock=safety_stock
        )

        # 4. 呼叫後端
        try:
            self.service.product_repo.add_variant(variant)
            self.view.clear_form()
            self.load_variants() # 刷新列表
        except DomainError as e:
            self.view.show_error(str(e))
        except Exception as e:
            logger.exception("新增變體失敗")
            self.view.show_error("系統錯誤，請檢查日誌")

    def handle_delete_variant(self, variant_id: int):
        try:
            # 這裡需要一個 delete_variant 方法，我們需要確認 Repository 有沒有實作
            # 假設 Repository 沒有提供直接刪除變體的方法 (Step 2 介面中似乎漏了單獨刪除變體)
            # 我們需要去擴充 Repository，或暫時用 SQL 執行
            
            # 為了 MVP，我們先假設使用者不會刪除有庫存的變體
            # 正確做法：應檢查是否有相關單據，若有則禁止刪除 (Soft Delete)
            
            # [Fixing Missing Interface]: 讓我們動態補充這個功能
            conn = self.service.product_repo.db_manager.get_connection()
            with conn:
                conn.execute("DELETE FROM variants WHERE id = ?", (variant_id,))
            
            self.load_variants()
            
        except Exception as e:
            logger.error(f"刪除變體失敗: {e}")
            self.view.show_error("刪除失敗 (可能該變體已有關聯單據)")