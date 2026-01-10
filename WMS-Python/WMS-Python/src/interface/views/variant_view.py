import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Dict, Optional

from src.domain.models import Variant

class VariantView(tk.Toplevel):
    """
    變體管理子視窗 (Popup)。
    負責顯示特定商品的變體列表，並提供新增/刪除/修改功能。
    """

    def __init__(self, master, product_name: str):
        super().__init__(master)
        
        self.title(f"管理變體 - {product_name}")
        self.geometry("800x600")
        self.grab_set() # 設為模態視窗 (Modal)
        
        # 定義回呼函數
        self._on_add_callback: Callable[[], None] = lambda: None
        self._on_update_callback: Callable[[], None] = lambda: None  # New
        self._on_delete_callback: Callable[[int], None] = lambda id: None
        self._on_select_callback: Callable[[int], None] = lambda id: None # New
        
        self._setup_ui()

    def _setup_ui(self):
        # 版面配置: 上方列表，下方表單
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- 1. 變體列表 (唯讀) ---
        list_frame = tk.LabelFrame(self, text="現有變體列表", padx=10, pady=10)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        cols = ("ID", "Size", "Color", "SKU", "Stock", "Safety")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Size", text="尺寸")
        self.tree.heading("Color", text="顏色")
        self.tree.heading("SKU", text="SKU 編碼")
        self.tree.heading("Stock", text="當前庫存")
        self.tree.heading("Safety", text="安全水位")

        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Size", width=80, anchor="center")
        self.tree.column("Color", width=80, anchor="center")
        self.tree.column("SKU", width=150)
        self.tree.column("Stock", width=80, anchor="e")
        self.tree.column("Safety", width=80, anchor="e")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # [New] 綁定選擇事件
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # --- 2. 編輯/新增變體表單 ---
        self.form_frame = tk.LabelFrame(self, text="編輯 / 新增變體", padx=10, pady=10)
        self.form_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        self.inputs = {}

        # 第一排輸入
        tk.Label(self.form_frame, text="尺寸 (Size):").grid(row=0, column=0, sticky="w")
        self.inputs["size"] = tk.Entry(self.form_frame, width=15)
        self.inputs["size"].grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.form_frame, text="顏色 (Color):").grid(row=0, column=2, sticky="w")
        self.inputs["color"] = tk.Entry(self.form_frame, width=15)
        self.inputs["color"].grid(row=0, column=3, padx=5, pady=5)

        tk.Label(self.form_frame, text="安全水位:").grid(row=0, column=4, sticky="w")
        self.inputs["safety_stock"] = tk.Entry(self.form_frame, width=10)
        self.inputs["safety_stock"].insert(0, "5")
        self.inputs["safety_stock"].grid(row=0, column=5, padx=5, pady=5)

        # 第二排輸入
        tk.Label(self.form_frame, text="SKU (選填):").grid(row=1, column=0, sticky="w")
        self.inputs["sku"] = tk.Entry(self.form_frame, width=25)
        self.inputs["sku"].grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        
        self.hint_lbl = tk.Label(self.form_frame, text="(若留空則系統自動生成)", fg="gray")
        self.hint_lbl.grid(row=1, column=3, columnspan=2, sticky="w")

        # 按鈕區
        btn_frame = tk.Frame(self.form_frame, pady=10)
        btn_frame.grid(row=2, column=0, columnspan=6, sticky="ew")

        # [Modified] 按鈕組
        self.add_btn = tk.Button(btn_frame, text="+ 新增變體", bg="#4CAF50", fg="white", command=self._on_add_click)
        self.add_btn.pack(side="right", padx=5)

        self.update_btn = tk.Button(btn_frame, text="💾 儲存修改", bg="#2196F3", fg="white", command=self._on_update_click)
        self.update_btn.pack(side="right", padx=5)
        self.update_btn.config(state="disabled") # 預設禁用

        self.cancel_btn = tk.Button(btn_frame, text="清空/取消", command=self.clear_form)
        self.cancel_btn.pack(side="right", padx=5)

        self.del_btn = tk.Button(btn_frame, text="- 刪除選中", bg="#F44336", fg="white", command=self._on_delete_click)
        self.del_btn.pack(side="left", padx=5)

    # --- Events ---
    def set_callbacks(self, on_add, on_update, on_delete, on_select):
        self._on_add_callback = on_add
        self._on_update_callback = on_update # New
        self._on_delete_callback = on_delete
        self._on_select_callback = on_select # New

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            # 取得該列的第一個值 (ID)
            variant_id = int(self.tree.item(selected[0], "values")[0])
            self._on_select_callback(variant_id)

    def _on_add_click(self):
        self._on_add_callback()

    def _on_update_click(self):
        self._on_update_callback()

    def _on_delete_click(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請先選擇要刪除的變體")
            return
        
        variant_id = int(self.tree.item(selected[0], "values")[0])
        if messagebox.askyesno("確認刪除", "確定要刪除此變體嗎？\n(注意：這將刪除該變體的庫存記錄)"):
            self._on_delete_callback(variant_id)

    # --- Public API ---
    def update_variant_list(self, variants: List[Variant]):
        # 記住當前選擇 (UX 優化)
        selected_id = None
        if self.tree.selection():
            selected_id = self.tree.item(self.tree.selection()[0], "values")[0]

        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for v in variants:
            item = self.tree.insert("", "end", values=(
                v.id, v.size, v.color, v.sku, v.stock_qty, v.safety_stock
            ))
            # 嘗試恢復選擇
            if str(v.id) == str(selected_id):
                self.tree.selection_set(item)

    def get_form_data(self) -> Dict[str, str]:
        return {k: v.get().strip() for k, v in self.inputs.items()}

    def set_form_data(self, variant: Variant):
        """將變體資料填入表單 (進入編輯模式)"""
        # 1. 清空舊資料
        self.inputs["size"].delete(0, tk.END)
        self.inputs["color"].delete(0, tk.END)
        self.inputs["sku"].delete(0, tk.END)
        self.inputs["safety_stock"].delete(0, tk.END)

        # 2. 填入新資料
        self.inputs["size"].insert(0, variant.size)
        self.inputs["color"].insert(0, variant.color)
        self.inputs["sku"].insert(0, variant.sku)
        self.inputs["safety_stock"].insert(0, str(variant.safety_stock))

        # 3. 切換按鈕狀態
        self.add_btn.config(state="disabled")     # 編輯模式下禁止新增
        self.update_btn.config(state="normal")    # 啟用更新
        self.form_frame.config(text=f"編輯變體 (ID: {variant.id})") # 更新標題提示

    def clear_form(self):
        """清空表單並回到新增模式"""
        self.inputs["size"].delete(0, tk.END)
        self.inputs["color"].delete(0, tk.END)
        self.inputs["sku"].delete(0, tk.END)
        self.inputs["safety_stock"].delete(0, tk.END)
        self.inputs["safety_stock"].insert(0, "5") # 恢復預設值

        # 切換回新增模式
        self.add_btn.config(state="normal")
        self.update_btn.config(state="disabled")
        self.form_frame.config(text="新增變體")
        
        # 取消列表選擇
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def show_error(self, message: str):
        messagebox.showerror("錯誤", message)
    
    def show_info(self, message: str):
        messagebox.showinfo("成功", message)