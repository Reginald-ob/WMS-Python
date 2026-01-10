import logging
from datetime import date
from typing import List, Optional
import tkinter.messagebox as messagebox # 明確引入 messagebox

from src.interface.views.adjustment_view import AdjustmentView
from src.application.services import InventoryService
from src.domain.models import Product, Variant, Document, DocumentItem
from src.domain.exceptions import DomainError

logger = logging.getLogger(__name__)

class AdjustmentPresenter:
    def __init__(self, view: AdjustmentView, service: InventoryService):
        self.view = view
        self.service = service
        
        self.current_variants: List[Variant] = []
        self.selected_variant: Optional[Variant] = None 

        self.view.set_callbacks(
            on_filter_product=self.handle_filter_product,
            on_product_select=self.handle_product_select,
            on_variant_select=self.handle_variant_select,
            on_submit=self.handle_submit
        )
        self.view.bind_add_button(self.handle_add_item)
        
        # 初始載入所有商品
        self.handle_filter_product("")

    # ... (handle_filter_product, handle_product_select, handle_variant_select 維持不變) ...

    def handle_filter_product(self, keyword: str):
        try:
            if not keyword:
                products = self.service.get_all_products()
            else:
                products = self.service.search_products(keyword)
            self.view.update_product_combo(products)
        except Exception as e:
            logger.error(f"商品篩選失敗: {e}")

    def handle_product_select(self, product_id: int):
        try:
            self.current_variants = self.service.get_variants_for_product(product_id)
            var_names = [v.display_name for v in self.current_variants]
            self.view.set_variant_list(var_names)
            self.selected_variant = None 
        except Exception as e:
            logger.error(f"連動變體失敗: {e}")

    def handle_variant_select(self, idx: int):
        try:
            if idx < 0 or idx >= len(self.current_variants):
                return
            variant_preview = self.current_variants[idx]
            fresh_variant = self.service.product_repo.get_variant_by_id(variant_preview.id)
            if fresh_variant:
                self.selected_variant = fresh_variant
                self.view.update_system_stock_display(fresh_variant.stock_qty)
            else:
                self.view.update_system_stock_display(0)
        except Exception as e:
            logger.error(f"查詢庫存失敗: {e}")

    def handle_add_item(self):
        """
        [FIX] 修正按鈕無反應的問題：增加錯誤提示與狀態檢查
        """
        # 1. 檢查是否已選中變體 (防止靜默失敗)
        if not self.selected_variant:
            messagebox.showwarning("提示", "請確認已選擇有效的商品規格 (Variant)")
            return

        try:
            # 2. 取得資料
            data = self.view.get_input_data()
            actual_qty = data['actual_qty']
            system_qty = self.selected_variant.stock_qty
            
            # 計算差異: 實際 - 系統
            diff = actual_qty - system_qty
            
            # 顯示資訊 (View 已移除 ID，直接使用 prod_str)
            prod_display = data['prod_str'] 
            var_name = self.selected_variant.display_name
            
            display_item = (
                self.selected_variant.id,
                prod_display,
                var_name,
                system_qty,
                actual_qty,
                diff
            )
            
            # 3. 更新 UI
            self.view.add_item_to_tree(display_item, diff)
            
        except Exception as e:
            # [FIX] 發生錯誤時必須彈窗，否則使用者會以為按鈕壞了
            logger.exception("加入盤點清單失敗")
            messagebox.showerror("錯誤", f"無法加入清單: {e}")

    def handle_submit(self):
        items_data = self.view.get_all_items()
        if not items_data:
            messagebox.showwarning("提示", "盤點清單是空的")
            return

        doc_items = []
        for item in items_data:
            doc_items.append(DocumentItem(
                variant_id=item['variant_id'],
                quantity=item['quantity'], # Diff
                unit_price=0 
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
            self.selected_variant = None
            
            messagebox.showinfo("成功", "庫存盤點調整已完成！")
            
            # 重置搜尋
            self.view.prod_filter_entry.delete(0, "end")
            self.view.prod_filter_entry.insert(0, "輸入關鍵字...")
            self.handle_filter_product("")
            
        except DomainError as e:
            logger.warning(f"盤點業務錯誤: {e}")
            messagebox.showwarning("警告", str(e))
        except Exception as e:
            logger.exception("盤點送出失敗")
            messagebox.showerror("錯誤", f"系統發生錯誤: {e}")