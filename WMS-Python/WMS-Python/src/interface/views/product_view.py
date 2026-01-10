import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Any, Callable

from src.domain.models import Product

class ProductView(tk.Frame):
    """
    商品管理畫面的 View (被動視圖)。
    負責 UI 佈局、顯示資料表、取得使用者輸入。
    """

    def __init__(self, master: tk.Widget, **kwargs):
        super().__init__(master, **kwargs)
        
        # 定義回呼函數 (由 Presenter 注入)
        self._on_save_callback: Callable[[], None] = lambda: None
        self._on_delete_callback: Callable[[], None] = lambda: None
        self._on_select_callback: Callable[[int], None] = lambda id: None
        self._on_manage_variants_callback: Callable[[], None] = lambda: None
        self._on_search_callback: Callable[[str], None] = lambda k: None

        self._setup_ui()

    def _setup_ui(self):
        """建立 Grid 佈局: 左列表 (Treeview), 右表單 (Form)"""
        self.grid_columnconfigure(0, weight=3) # 列表佔較多空間
        self.grid_columnconfigure(1, weight=2) # 表單區
        self.grid_rowconfigure(0, weight=1)

        # --- 1. 左側列表區 ---
        list_frame = tk.Frame(self, bg="#f0f0f0", padx=10, pady=10)
        list_frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(list_frame, text="商品列表", font=("Microsoft JhengHei", 12, "bold")).pack(anchor="w")

        # [New] 搜尋列 Frame
        search_frame = tk.Frame(list_frame, bg="#f0f0f0")
        search_frame.pack(fill="x", pady=(0, 5))

        tk.Label(search_frame, text="🔍 搜尋商品:", bg="#f0f0f0").pack(side="left")
        
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        # 綁定 Enter 鍵觸發搜尋
        self.search_entry.bind("<Return>", lambda e: self._on_search_click())

        search_btn = tk.Button(search_frame, text="搜尋", command=self._on_search_click)
        search_btn.pack(side="left")

        reset_btn = tk.Button(search_frame, text="重置", command=self._on_reset_click)
        reset_btn.pack(side="left", padx=2)

        # 原本只有 tk.Label，現在改為 Frame 容器以容納按鈕
        title_frame = tk.Frame(list_frame, bg="#f0f0f0")
        title_frame.pack(fill="x", pady=(0, 5))

        # 匯入csv按鈕
        self.import_btn = tk.Button(title_frame, text="📂 匯入 CSV", bg="#FF9800", fg="white", 
                                            font=("Microsoft JhengHei", 9),
                                            command=self._on_import_click)
        self.import_btn.pack(side="right")

        # Treeview 設定
        cols = ("ID", "Brand", "Name", "Price")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Brand", text="品牌")
        self.tree.heading("Name", text="商品名稱")
        self.tree.heading("Price", text="基準價")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Brand", width=100)
        self.tree.column("Name", width=200)
        self.tree.column("Price", width=80, anchor="e")

        # 捲軸
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 綁定選擇事件
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # --- 2. 右側表單區 ---
        form_frame = tk.Frame(self, bg="white", padx=20, pady=20, relief="groove", bd=1)
        form_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        tk.Label(form_frame, text="商品詳細資料", font=("Microsoft JhengHei", 12, "bold"), bg="white").pack(anchor="w", pady=(0, 20))

        # 表單欄位容器
        fields_frame = tk.Frame(form_frame, bg="white")
        fields_frame.pack(fill="x")

        self.inputs = {}
        
        # 輔助函數: 快速建立標籤與輸入框
        def create_field(label_text, key, row):
            tk.Label(fields_frame, text=label_text, bg="white").grid(row=row, column=0, sticky="w", pady=5)
            entry = tk.Entry(fields_frame)
            entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
            fields_frame.grid_columnconfigure(1, weight=1)
            self.inputs[key] = entry

        create_field("品牌 (Brand):", "brand", 0)
        create_field("商品名稱 (Name):", "name", 1)
        create_field("分類 (Category):", "category", 2)
        create_field("基準售價 (Price):", "base_price", 3)
        create_field("描述 (Desc):", "description", 4)

        # 按鈕區
        btn_frame = tk.Frame(form_frame, bg="white", pady=20)
        btn_frame.pack(fill="x", side="bottom")

        self.save_btn = tk.Button(btn_frame, text="儲存 / 新增", bg="#4CAF50", fg="white", command=self._on_save_click)
        self.save_btn.pack(side="left", fill="x", expand=True, padx=5)

        # [新增按鈕] 管理變體
        self.variant_btn = tk.Button(btn_frame, text="管理變體 (SKU)", bg="#2196F3", fg="white", command=self._on_manage_variants_click)
        self.variant_btn.pack(side="left", fill="x", expand=True, padx=5)
        # 預設禁用，直到選擇商品
        self.variant_btn.config(state="disabled")

        self.del_btn = tk.Button(btn_frame, text="刪除商品", bg="#F44336", fg="white", command=self._on_delete_click)
        self.del_btn.pack(side="left", fill="x", expand=True, padx=5)
        
        self.clear_btn = tk.Button(btn_frame, text="清空重填", command=self.clear_form)
        self.clear_btn.pack(side="left", fill="x", expand=True, padx=5)

    # --- 事件轉發 (Event Forwarding) ---

    def set_callbacks(self, on_save, on_delete, on_select, on_manage_variants=None, on_import=None, on_search=None):
        self._on_save_callback = on_save
        self._on_delete_callback = on_delete
        self._on_select_callback = on_select
        if on_manage_variants:
            self._on_manage_variants_callback = on_manage_variants
        if on_import:
            self._on_import_callback = on_import
        if on_search:
            self._on_search_callback = on_search

    def _on_manage_variants_click(self):
        self._on_manage_variants_callback()

    def _on_save_click(self):
        self._on_save_callback()

    def _on_delete_click(self):
        self._on_delete_callback()

    def _on_search_click(self):
        keyword = self.search_entry.get().strip()
        self._on_search_callback(keyword)

    def _on_reset_click(self):
        self.search_entry.delete(0, tk.END)
        self._on_search_callback("")  # 空字串代表查詢全部

    def _on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            item_id = selected_items[0]
            # treeview 的 values 順序對應 columns，第一個是 ID
            values = self.tree.item(item_id, "values")
            if values:
                product_id = int(values[0])
                self._on_select_callback(product_id)

    # --- 公開介面 (Public API for Presenter) ---

    def update_product_list(self, products: List[Product]):
        """更新左側列表"""
        # 清空舊資料
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 填入新資料
        for p in products:
            self.tree.insert("", "end", values=(p.id, p.brand, p.name, p.base_price))

    def get_form_data(self) -> dict:
        """取得目前表單輸入值"""
        return {k: v.get().strip() for k, v in self.inputs.items()}

    def set_form_data(self, product: Product):
        """將商品物件填入表單"""
        self.clear_form()
        self.inputs["brand"].insert(0, product.brand)
        self.inputs["name"].insert(0, product.name)
        self.inputs["category"].insert(0, product.category or "")
        self.inputs["base_price"].insert(0, str(product.base_price))
        self.inputs["description"].insert(0, product.description or "")
        self.variant_btn.config(state="normal")# 啟用按鈕

    def clear_form(self):
        """清空表單"""
        for entry in self.inputs.values():
            entry.delete(0, tk.END)
        # 取消 Treeview 選擇
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())
        
        self.variant_btn.config(state="disabled") # 禁用按鈕

    def show_message(self, title: str, message: str, is_error: bool = False):
        if is_error:
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)
            
    def ask_confirmation(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)
    


    # 按鈕點擊事件
    def _on_import_click(self):
        if hasattr(self, '_on_import_callback'):
            self._on_import_callback()

    # 提供選擇檔案的對話框 (由 Presenter 呼叫)
    def ask_open_csv_file(self) -> str:
        """打開檔案選擇器，回傳檔案路徑，若取消則回傳空字串"""
        file_path = filedialog.askopenfilename(
            title="選擇商品匯入檔",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        return file_path