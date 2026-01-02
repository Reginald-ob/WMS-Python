import logging
from datetime import date
from typing import List

from src.interface.views.adjustment_view import AdjustmentView
from src.application.services import InventoryService
from src.domain.models import Product, Variant, Document, DocumentItem
from src.domain.exceptions import DomainError

logger = logging.getLogger(__name__)

class AdjustmentPresenter:
    def __init__(self, view: AdjustmentView, service: InventoryService):
        self.view = view
        self.service = service
        
        self.products: List[Product] = []
        self.current_variants: List[Variant] = []
        self.selected_variant: Variant = None # 暫存當前選中的變體物件

        self.view.set_callbacks(
            on_product_select=self.handle_product_select,
            on_variant_select=self.handle_variant_select,
            on_submit=self.handle_submit
        )
        self.view.bind_add_button(self.handle_add_item)
        
        self.load_products()

    def load_products(self):
        try:
            self.products = self.service.get_all_products()
            names = [f"{p.brand} - {p.name}" for p in self.products]
            self.view.set_product_list(names)
        except Exception as e:
            logger.error(f"盤點頁面載入商品失敗: {e}")

    def handle_product_select(self, idx: int):
        try:
            product = self.products[idx]
            self.current_variants = self.service.get_variants_for_product(product.id)
            var_names = [v.display_name for v in self.current_variants]
            self.view.set_variant_list(var_names)
            self.selected_variant = None # 重置
        except Exception as e:
            logger.error(f"連動變體失敗: {e}")

    def handle_variant_select(self, idx: int):
        try:
            # 這裡必須重新從 DB 撈取「最新」庫存，避免快取舊資料
            # 雖然 current_variants 有資料，但那是 load_products 時的快照嗎?
            # 視 get_variants_for_product 實作而定。為了安全，依 ID 再查一次。
            variant_preview = self.current_variants[idx]
            fresh_variant = self.service.product_repo.get_variant_by_id(variant_preview.id)
            
            if fresh_variant:
                self.selected_variant = fresh_variant
                self.view.update_system_stock_display(fresh_variant.stock_qty)
            else:
                self.view.update_system_stock_display(0) # Error case
                
        except Exception as e:
            logger.error(f"查詢庫存失敗: {e}")

    def handle_add_item(self):
        if not self.selected_variant:
            return

        try:
            data = self.view.get_input_data()
            actual_qty = data['actual_qty']
            system_qty = self.selected_variant.stock_qty
            
            # [核心邏輯] 差異 = 實際 - 系統
            # 例: 系統10, 實際8 -> 差 -2 (需扣除2)
            # 例: 系統10, 實際12 -> 差 +2 (需增加2)
            diff = actual_qty - system_qty
            
            if diff == 0:
                self.view.master.bell() # 沒差異通常不用調整，但如果使用者堅持也可以
                # 這裡我們允許加入，紀錄「盤點確認無誤」
            
            # 顯示
            prod_name = self.products[data['p_idx']].name
            var_name = self.selected_variant.display_name
            
            display_item = (
                self.selected_variant.id,
                prod_name,
                var_name,
                system_qty,
                actual_qty,
                diff
            )
            
            self.view.add_item_to_tree(display_item, diff)
            
        except Exception as e:
            logger.error(f"加入盤點清單錯誤: {e}")

    def handle_submit(self):
        items_data = self.view.get_all_items()
        if not items_data:
            return

        # 建立單據
        doc_items = []
        for item in items_data:
            # item['quantity'] 其實是 diff
            # 如果 diff 是 0，是否要寫入單據？
            # 寫入 0 的明細可以作為「已盤點且無誤」的紀錄，建議保留。
            doc_items.append(DocumentItem(
                variant_id=item['variant_id'],
                quantity=item['quantity'],
                unit_price=0 # 調整單通常無單價，或可設為成本價 (MVP 設 0)
            ))

        document = Document(
            doc_type='ADJUST',
            doc_date=date.today(),
            note=self.view.get_note(),
            items=doc_items
        )

        try:
            self.service.create_adjustment_order(document)
            self.view.clear_all()
            # 重置暫存
            self.selected_variant = None
            
            from tkinter import messagebox
            messagebox.showinfo("成功", "庫存盤點調整已完成！")
            
        except DomainError as e:
            logger.warning(f"盤點業務錯誤: {e}")
            messagebox.showwarning("警告", str(e))
        except Exception as e:
            logger.exception("盤點送出失敗")
            messagebox.showerror("錯誤", "系統發生錯誤")