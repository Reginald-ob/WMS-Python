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
        
        # 用來追蹤當前正在編輯的變體 ID (若為 None 表示在新增模式)
        self._selected_variant_id: Optional[int] = None

        self.view.set_callbacks(
            on_add=self.handle_add_variant,
            on_update=self.handle_update_variant,
            on_delete=self.handle_delete_variant,
            on_select=self.handle_select_variant
        )
        
        self.load_variants()
        
    def load_variants(self):
        try:
            variants = self.service.get_variants_for_product(self.product_id)
            self.view.update_variant_list(variants)
        except Exception as e:
            logger.error(f"載入變體失敗: {e}")
            self.view.show_error("無法載入變體列表")

    def handle_select_variant(self, variant_id: int):
        """當使用者在列表中選擇變體時觸發"""
        try:
            self._selected_variant_id = variant_id
            
            # 從 Repo 取得最新資料 (避免列表資料過時)
            # 注意: 這裡直接存取 product_repo，符合專案現有模式
            variant = self.service.product_repo.get_variant_by_id(variant_id)
            
            if variant:
                self.view.set_form_data(variant)
            else:
                self.view.show_error("該變體已不存在")
                self.load_variants() # 刷新列表
                
        except Exception as e:
            logger.exception("選取變體失敗")

    def handle_add_variant(self):
        data = self.view.get_form_data()
        
        if not self._validate_input(data):
            return

        # 處理 SKU
        sku = data["sku"]
        if not sku:
            sku = self._generate_sku(data["size"], data["color"])

        try:
            variant = Variant(
                product_id=self.product_id,
                size=data["size"],
                color=data["color"],
                sku=sku,
                stock_qty=0, 
                safety_stock=int(data["safety_stock"])
            )

            self.service.product_repo.add_variant(variant)
            self.view.clear_form()
            self._selected_variant_id = None # 重置選擇
            self.load_variants()
            
        except DomainError as e:
            self.view.show_error(str(e))
        except Exception as e:
            logger.exception("新增變體失敗")
            self.view.show_error(f"新增失敗: {e}")

    def handle_update_variant(self):
        """處理更新變體 (SKU/Metadata)"""
        if self._selected_variant_id is None:
            return

        data = self.view.get_form_data()
        if not self._validate_input(data):
            return

        try:
            # 構建更新物件
            # 注意: stock_qty 傳入 0 也不影響，因為 Service 層會保護庫存
            variant = Variant(
                id=self._selected_variant_id,
                product_id=self.product_id,
                size=data["size"],
                color=data["color"],
                sku=data["sku"], # 允許更新 SKU
                safety_stock=int(data["safety_stock"]),
                stock_qty=0 # Placeholder
            )

            # 呼叫 Service (這是我們在 Step 2 實作的方法)
            self.service.update_variant(variant)
            
            self.view.show_info("更新成功")
            self.view.clear_form()
            self._selected_variant_id = None
            self.load_variants()

        except DomainError as e:
            self.view.show_error(str(e))
        except Exception as e:
            logger.exception("更新變體失敗")
            self.view.show_error(f"更新失敗: {e}")

    def handle_delete_variant(self, variant_id: int):
        try:
            # MVP 權宜之計: 直接執行 SQL 刪除 (若架構完整應移至 Repo)
            conn = self.service.product_repo.db_manager.get_connection()
            with conn:
                conn.execute("DELETE FROM variants WHERE id = ?", (variant_id,))
            
            self.load_variants()
            self.view.clear_form() # 若剛好選中被刪除的，需清空
            self._selected_variant_id = None
            
        except Exception as e:
            logger.error(f"刪除變體失敗: {e}")
            self.view.show_error("刪除失敗 (可能該變體已有關聯單據)")

    # --- Helpers ---
    def _validate_input(self, data) -> bool:
        if not data["size"] or not data["color"]:
            self.view.show_error("尺寸與顏色為必填")
            return False
        try:
            int(data["safety_stock"])
        except ValueError:
            self.view.show_error("安全庫存必須為整數")
            return False
        return True

    def _generate_sku(self, size, color) -> str:
        safe_size = "".join(c for c in size if c.isalnum())
        safe_color = "".join(c for c in color if c.isalnum())
        return f"P{self.product_id}-{safe_size}-{safe_color}".upper()