import logging
import csv
import os
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
            on_select=self.handle_select,            on_search=self.handle_search,            on_manage_variants=self.open_variant_manager,
            on_import=self.handle_import_csv  # 匯入csv事件
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

    def handle_search(self, keyword: str):
        """處理搜尋請求"""
        try:
            # 若關鍵字為空，則載入全部
            if not keyword:
                products = self.service.get_all_products()
            else:
                products = self.service.search_products(keyword)
            
            self.view.update_product_list(products)
        except Exception as e:
            logger.error(f"搜尋商品失敗: {e}")
            self.view.show_message("錯誤", f"搜尋失敗: {e}", is_error=True)

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

    def handle_import_csv(self):
            """處理 CSV 批量匯入"""
            file_path = self.view.ask_open_csv_file()
            if not file_path:
                return

            # 暫存解析後的物件列表
            parsed_products = []
            
            # Phase 1: 讀取與驗證 (All-or-Nothing)
            try:
                # 使用 utf-8-sig 以支援 Excel 存出的 CSV (去除 BOM)
                # 若使用者是 Excel 繁體中文環境存的 CSV 可能是 big5，這裡預設用 utf-8
                with open(file_path, mode='r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.reader(f)
                    
                    # 略過表頭 (Header)
                    try:
                        next(reader) 
                    except StopIteration:
                        self.view.show_message("錯誤", "檔案內容為空", is_error=True)
                        return

                    # 開始逐行讀取
                    for line_num, row in enumerate(reader, start=2):
                        # 檢查欄位數量 (至少 5 欄: Brand, Name, Category, Price, Desc)
                        if len(row) < 5:
                            raise ValueError(f"第 {line_num} 行格式錯誤：欄位數量不足 (需至少5欄)")
                        
                        brand = row[0].strip()
                        name = row[1].strip()
                        category = row[2].strip()
                        price_str = row[3].strip()
                        desc = row[4].strip()

                        # 必填驗證
                        if not brand or not name or not price_str:
                            raise ValueError(f"第 {line_num} 行資料錯誤：品牌、名稱與售價為必填")

                        # 數值驗證
                        try:
                            base_price = float(price_str)
                        except ValueError:
                            raise ValueError(f"第 {line_num} 行資料錯誤：售價「{price_str}」不是有效的數字")

                        # 建立物件 (暫不設定 ID)
                        product = Product(
                            id=None,
                            brand=brand,
                            name=name,
                            category=category,
                            base_price=base_price,
                            description=desc
                        )
                        parsed_products.append(product)

            except UnicodeDecodeError:
                self.view.show_message("編碼錯誤", "無法讀取檔案，請確保 CSV 為 UTF-8 編碼。", is_error=True)
                return
            except ValueError as e:
                # 捕捉驗證錯誤，中斷並通知
                self.view.show_message("匯入失敗", str(e), is_error=True)
                return
            except Exception as e:
                logger.error(f"CSV 讀取未預期錯誤: {e}")
                self.view.show_message("系統錯誤", f"讀取檔案時發生錯誤: {e}", is_error=True)
                return

            # Phase 2: 檢查重複並寫入 (Skip Duplicates)
            try:
                # 為了效率，先取得所有現有商品，建立 (Brand, Name) 的集合
                existing_products = self.service.get_all_products()
                existing_keys = {(p.brand, p.name) for p in existing_products}
                
                added_count = 0
                skipped_list = []

                for new_prod in parsed_products:
                    # 檢查重複
                    if (new_prod.brand, new_prod.name) in existing_keys:
                        skipped_list.append(f"{new_prod.brand} - {new_prod.name}")
                        continue
                    
                    # 寫入資料庫
                    self.service.product_repo.add_product(new_prod)
                    added_count += 1
                
                # Phase 3: 結果報告
                msg = f"匯入作業完成！\n\n✅ 成功新增: {added_count} 筆"
                
                if skipped_list:
                    # 若重複項目太多，只顯示前 10 筆
                    display_skipped = skipped_list[:10]
                    more_count = len(skipped_list) - 10
                    
                    skip_msg = "\n".join(display_skipped)
                    if more_count > 0:
                        skip_msg += f"\n...及其他 {more_count} 筆"
                        
                    msg += f"\n⚠️ 跳過 {len(skipped_list)} 筆重複資料 (需手動修改):\n----------------\n{skip_msg}"
                
                self.view.show_message("匯入結果", msg)
                
                # 刷新列表
                self.load_products()

            except Exception as e:
                logger.error(f"匯入儲存過程錯誤: {e}")
                self.view.show_message("儲存失敗", f"寫入資料庫時發生錯誤: {e}", is_error=True)