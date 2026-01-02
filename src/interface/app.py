import tkinter as tk
from tkinter import messagebox
import logging
from typing import Type

from src.application.services import InventoryService
from src.config import WINDOW_TITLE, WINDOW_SIZE, THEME_FONT, HEADER_FONT

from src.interface.views.product_view import ProductView
from src.interface.presenters.product_presenter import ProductPresenter

from src.interface.views.transaction_view import TransactionView
from src.interface.presenters.transaction_presenter import TransactionPresenter

from src.interface.views.document_list_view import DocumentListView
from src.interface.presenters.document_list_presenter import DocumentListPresenter

from src.interface.views.adjustment_view import AdjustmentView
from src.interface.presenters.adjustment_presenter import AdjustmentPresenter

logger = logging.getLogger(__name__)

class MainWindow(tk.Tk):
    """
    主應用程式視窗 (UI Composition Root)
    負責視窗佈局、全域設定以及視窗切換導航。
    """

    def __init__(self, inventory_service: InventoryService):
        super().__init__()

        self.inventory_service = inventory_service

        # 1. 基礎視窗設定
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.option_add("*Font", THEME_FONT)  # 設定全域字型

        # 2. 初始化 UI 佈局
        self._setup_layout()
        self._setup_sidebar()
        
        # 3. 顯示首頁
        self.show_view("HOME")

    def _setup_layout(self):
        """設定 Grid 佈局: 左側選單(固定寬度), 右側內容(自動延展)"""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左側選單區
        self.sidebar_frame = tk.Frame(self, bg="#f0f0f0", width=200, padx=10, pady=10)
        self.sidebar_frame.grid(row=0, column=0, sticky="ns")
        self.sidebar_frame.grid_propagate(False) # 固定寬度

        # 右側內容區
        self.content_frame = tk.Frame(self, bg="white", padx=20, pady=20)
        self.content_frame.grid(row=0, column=1, sticky="nsew")

    def _setup_sidebar(self):
        """建立側邊選單按鈕"""
        title_lbl = tk.Label(self.sidebar_frame, text="WMS 系統", font=HEADER_FONT, bg="#f0f0f0")
        title_lbl.pack(pady=(0, 20))

        # 選單按鈕定義 (Label, ViewKey)
        menu_items = [
            ("首頁總覽", "HOME"),
            ("商品管理", "PRODUCT"),
            ("進貨作業", "INBOUND"),
            ("銷貨作業", "OUTBOUND"),
            ("單據查詢", "HISTORY"),
            ("庫存盤點", "ADJUST"),
        ]

        for text, view_key in menu_items:
            btn = tk.Button(
                self.sidebar_frame, 
                text=text, 
                command=lambda k=view_key: self.show_view(k),
                height=2,
                relief="flat",
                bg="#e0e0e0"
            )
            btn.pack(fill="x", pady=5)

        # 底部版本資訊
        ver_lbl = tk.Label(self.sidebar_frame, text="v1.0.0", bg="#f0f0f0", fg="gray")
        ver_lbl.pack(side="bottom")

    def show_view(self, view_key: str):
        """
        切換右側內容區的畫面
        """
        # 1. 清空當前畫面
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.current_presenter = None
        logger.info(f"導航至頁面: {view_key}")

        # 2. 根據 Key 載入對應 View (工廠模式概念)
        # 注意: 之後實作具體 View 後，會在這裡實例化並傳入 Presenter
        if view_key == "HOME":
            self._render_home_view()
        elif view_key == "PRODUCT":
            self._render_product_view()
        elif view_key == "INBOUND":
            self._render_transaction_view("INBOUND", "進貨作業 (Inbound)", "#4CAF50")
        elif view_key == "OUTBOUND":
            self._render_transaction_view("OUTBOUND", "銷貨作業 (Outbound)", "#FF5722")
        elif view_key == "HISTORY":
            self._render_history_view()
        elif view_key == "ADJUST":
            self._render_adjustment_view()
        else:
            self._render_placeholder(f"未知頁面: {view_key}")

    def _render_home_view(self):
        """簡單的首頁 (Dashboard)"""
        tk.Label(self.content_frame, text="歡迎使用庫存管理系統", font=HEADER_FONT, bg="white").pack(pady=20)
        
        # 顯示簡單統計 (直接呼叫 Service 獲取數據)
        try:
            products = self.inventory_service.get_all_products()
            tk.Label(self.content_frame, text=f"目前商品款式總數: {len(products)}", bg="white").pack()
            
            low_stocks = self.inventory_service.get_low_stock_variants()
            if low_stocks:
                msg = f"⚠️ 警告: 有 {len(low_stocks)} 個變體低於安全庫存！"
                tk.Label(self.content_frame, text=msg, fg="red", bg="white").pack(pady=10)
            else:
                tk.Label(self.content_frame, text="✅ 目前庫存水位正常", fg="green", bg="white").pack(pady=10)

        except Exception as e:
            tk.Label(self.content_frame, text=f"讀取數據失敗: {e}", fg="red", bg="white").pack()

    def _render_product_view(self):
            """渲染商品管理頁面"""
            # 1. 建立 View
            view = ProductView(self.content_frame)
            view.pack(fill="both", expand=True)

            # 2. 建立 Presenter (注入 View 與 Service)
            # 注意: 這裡我們建立了 View 與 Logic 的連結
            presenter = ProductPresenter(view, self.inventory_service)
            
            # 3. 保持引用，防止被回收
            self.current_presenter = presenter

    def _render_transaction_view(self, doc_type: str, title: str, color: str):
        view = TransactionView(self.content_frame, title=title, color_theme=color)
        view.pack(fill="both", expand=True)
        
        presenter = TransactionPresenter(view, self.inventory_service, doc_type=doc_type)
        self.current_presenter = presenter

    def _render_history_view(self):
        view = DocumentListView(self.content_frame)
        view.pack(fill="both", expand=True)
            
        presenter = DocumentListPresenter(view, self.inventory_service)
        self.current_presenter = presenter

    def _render_adjustment_view(self):
        view = AdjustmentView(self.content_frame)
        view.pack(fill="both", expand=True)
        
        presenter = AdjustmentPresenter(view, self.inventory_service)
        self.current_presenter = presenter