import logging
from datetime import date
from tkinter import messagebox
from typing import List, Optional

from src.interface.views.transaction_view import TransactionView
from src.application.services import InventoryService
from src.domain.models import Document, DocumentItem, Product, Variant
from src.domain.exceptions import DomainError

logger = logging.getLogger(__name__)

class TransactionPresenter:
    """
    負責處理「進貨」與「銷貨」的邏輯。
    """

    def __init__(self, view: TransactionView, service: InventoryService, doc_type: str):
        self.view = view
        self.service = service
        self.doc_type = doc_type # 'INBOUND' or 'OUTBOUND'
        
        # 狀態暫存
        self.products: List[Product] = [] 
        self.current_variants: List[Variant] = []
        
        # 綁定事件
        self.view.set_callbacks(
            on_filter_product=self.handle_filter_product,
            on_product_select=self.handle_product_select,
            on_submit=self.handle_submit
        )
        self.view.bind_add_button(self.handle_add_item)

        # 初始化載入所有商品
        self.handle_filter_product("")

    def handle_filter_product(self, keyword: str):
        """
        处理商品過毸/搜尋。
        邏輯方止：
        1. 粗動 Service 進行搜尋 (若 keyword 為空則回傳全部)。
        2. 更新 View 的 Combobox 選項。
        """
        try:
            if not keyword:
                products = self.service.get_all_products()
            else:
                products = self.service.search_products(keyword)
            
            self.products = products
            names = [f"{p.brand} - {p.name}" for p in products]
            self.view.set_product_list(names)
            
        except Exception as e:
            # 搜尋失敗時不彈窗干擾輸入，僅記錄 Log
            logger.error(f"商品篩選失敗: {e}")

    def load_products(self):
        """載入所有商品至下拉選單 (已預先栽作"""
        try:
            self.products = self.service.get_all_products()
            names = [f"{p.brand} - {p.name}" for p in self.products]
            self.view.set_product_list(names)
        except Exception as e:
            logger.error(f"載入商品失敗: {e}")

    def handle_product_select(self, index: int):
        """當使用者選擇商品時，撈取對應變體"""
        try:
            selected_product = self.products[index]
            self.current_variants = self.service.get_variants_for_product(selected_product.id)
            
            # 更新變體選單
            var_names = [v.display_name for v in self.current_variants]
            self.view.set_variant_list(var_names)
            
            # 若是銷貨單，可以考慮自動填入售價 (UX 優化)
            if self.doc_type == 'OUTBOUND':
                self.view.inputs["price"].delete(0, "end")
                self.view.inputs["price"].insert(0, str(selected_product.base_price))
                
        except Exception as e:
            logger.error(f"選取商品連動失敗: {e}")

    def handle_add_item(self):
        """處理「加入清單」按鈕"""
        data = self.view.get_input_data()
        
        # 1. 檢查索引有效性
        p_idx = data["product_idx"]
        v_idx = data["variant_idx"]
        if p_idx < 0 or v_idx < 0:
            return # View 已經有基礎檢查，這裡雙重確認
            
        try:
            qty = int(data["quantity"])
            price = float(data["price"])
            if qty <= 0: raise ValueError
        except ValueError:
            # View 應該已經報錯，這裡略過
            return

        # 2. 取得對應物件
        product = self.products[p_idx]
        variant = self.current_variants[v_idx]
        
        # 3. 準備顯示資料 (Tuple)
        subtotal = qty * price
        display_item = (
            variant.id,           # Hidden ID
            product.name,         # Product Name
            variant.display_name, # Variant Name
            qty,
            price,
            subtotal
        )
        
        # 4. 加入 View
        self.view.add_item_to_tree(display_item)

    def handle_submit(self):
        """處理「送出」按鈕"""
        items_data = self.view.get_all_items()
        if not items_data:
            self.view.master.bell() # 叮一聲
            return

        note = self.view.get_note()
        
        # 1. 建立 Domain Document
        # 由於 Document 需要 List[DocumentItem]，我們先建立 Items
        doc_items = []
        for item in items_data:
            doc_items.append(DocumentItem(
                variant_id=item['variant_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            ))

        document = Document(
            doc_type=self.doc_type,
            doc_date=date.today(), # 這裡簡化為當天，若需補單功能則需 UI 支援選日期
            note=note,
            items=doc_items
        )

        # 2. 呼叫 Service
        try:
            if self.doc_type == 'INBOUND':
                self.service.create_inbound_order(document)
                msg = "進貨單建立成功！"
            elif self.doc_type == 'OUTBOUND':
                self.service.create_outbound_order(document)
                msg = "銷貨單建立成功！\n庫存已扣除。"
            else:
                return

            messagebox.showinfo("成功", msg)
            self.view.clear_all()
            
        except DomainError as e:
            messagebox.showwarning("業務規則錯誤", str(e))
        except Exception as e:
            logger.exception("建立單據失敗")
            messagebox.showerror("系統錯誤", f"操作失敗: {e}")