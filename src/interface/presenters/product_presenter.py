import logging
from typing import Optional

from src.interface.views.product_view import ProductView
from src.application.services import InventoryService
from src.domain.models import Product
from src.domain.exceptions import DomainError

from src.interface.views.variant_view import VariantView
from src.interface.presenters.variant_presenter import VariantPresenter

logger = logging.getLogger(__name__)

class ProductPresenter:
    """
    商品管理畫面的 Presenter (MVP)。
    負責協調 ProductView 與 InventoryService。
    """

    def __init__(self, view: ProductView, service: InventoryService):
        self.view = view
        self.service = service
        self._current_product_id: Optional[int] = None # 用於追蹤當前編輯的商品

        # 綁定 View 的事件
        self.view.set_callbacks(
            on_save=self.handle_save,
            on_delete=self.handle_delete,
            on_select=self.handle_select,
            on_manage_variants=self.open_variant_manager
        )

        # 暫存子視窗的引用，避免被 GC
        self._variant_window_ref = None
        
        # 初始化載入資料
        self.load_products()

    def open_variant_manager(self):
            """開啟變體管理視窗"""
            if not self._current_product_id:
                return

            # 1. 取得當前商品名稱 (為了顯示在標題)
            current_name = self.view.inputs["name"].get()
            
            # 2. 建立視窗 (Toplevel)
            variant_view = VariantView(self.view, current_name)
            
            # 3. 綁定 Presenter
            # 注意：我們直接在方法內實例化，並將引用綁定在 View 上或 self 上
            variant_presenter = VariantPresenter(
                view=variant_view,
                service=self.service,
                product_id=self._current_product_id
            )
            
            # 4. 防止被回收
            self._variant_window_ref = variant_presenter

    def load_products(self):
        """從 Service 載入所有商品並更新 View"""
        try:
            products = self.service.get_all_products()
            self.view.update_product_list(products)
        except Exception as e:
            logger.error(f"載入商品列表失敗: {e}")
            self.view.show_message("錯誤", "無法載入商品列表", is_error=True)

    def handle_select(self, product_id: int):
        """當使用者在列表選擇商品時"""
        try:
            # 使用 Repository 直接查詢 ID (因為列表可能只顯示部分欄位)
            product = self.service.product_repo.get_product_by_id(product_id)
            if product:
                self._current_product_id = product.id
                self.view.set_form_data(product)
        except Exception as e:
            logger.error(f"選取商品失敗: {e}")

    def handle_save(self):
        """處理儲存按鈕 (新增或更新)"""
        data = self.view.get_form_data()
        
        # 1. 簡易驗證
        if not data["name"] or not data["brand"] or not data["base_price"]:
            self.view.show_message("警告", "「品牌」、「名稱」與「售價」為必填欄位", is_error=True)
            return

        try:
            price = float(data["base_price"])
        except ValueError:
            self.view.show_message("錯誤", "售價必須為數字", is_error=True)
            return

        # 2. 建立 Entity 物件
        product = Product(
            id=self._current_product_id, # 如果是 None 則為新增
            name=data["name"],
            brand=data["brand"],
            category=data["category"],
            base_price=price,
            description=data["description"]
        )

        # 3. 呼叫後端
        try:
            if self._current_product_id:
                # 更新模式
                self.service.product_repo.update_product(product)
                self.view.show_message("成功", "商品資料已更新")
            else:
                # 新增模式
                self.service.product_repo.add_product(product)
                self.view.show_message("成功", "新商品已建立")

            # 4. 刷新介面
            self.load_products()
            self.view.clear_form()
            self._current_product_id = None # 重置狀態

        except DomainError as e:
            self.view.show_message("業務錯誤", str(e), is_error=True)
        except Exception as e:
            logger.exception("儲存商品時發生未預期錯誤")
            self.view.show_message("系統錯誤", f"操作失敗: {e}", is_error=True)

    def handle_delete(self):
        """處理刪除按鈕"""
        if not self._current_product_id:
            self.view.show_message("提示", "請先選擇要刪除的商品")
            return

        if not self.view.ask_confirmation("確認刪除", "確定要刪除此商品嗎？\n(這將會一併刪除該商品底下的所有變體與庫存資料！)"):
            return

        try:
            self.service.product_repo.delete_product(self._current_product_id)
            self.view.show_message("成功", "商品已刪除")
            
            self.load_products()
            self.view.clear_form()
            self._current_product_id = None

        except DomainError as e:
            self.view.show_message("錯誤", str(e), is_error=True)
        except Exception as e:
            logger.error(f"刪除商品失敗: {e}")
            self.view.show_message("系統錯誤", "刪除失敗", is_error=True)