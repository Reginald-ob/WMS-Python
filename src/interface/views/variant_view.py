import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Dict

from src.domain.models import Variant

class VariantView(tk.Toplevel):
    """
    變體管理子視窗 (Popup)。
    負責顯示特定商品的變體列表，並提供新增/刪除功能。
    """

    def __init__(self, master, product_name: str):
        super().__init__(master)
        
        self.title(f"管理變體 - {product_name}")
        self.geometry("800x600")
        self.grab_set() # 設為模態視窗 (Modal)，鎖定焦點
        
        # 定義回呼函數
        self._on_add_callback: Callable[[], None] = lambda: None
        self._on_delete_callback: Callable[[int], None] = lambda id: None
        
        self._setup_ui()

    def _setup_ui(self):
        # 版面配置: 上方列表，下方新增表單
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

        # --- 2. 新增變體表單 ---
        form_frame = tk.LabelFrame(self, text="新增變體", padx=10, pady=10)
        form_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        self.inputs = {}

        # 第一排輸入
        tk.Label(form_frame, text="尺寸 (Size):").grid(row=0, column=0, sticky="w")
        self.inputs["size"] = tk.Entry(form_frame, width=15)
        self.inputs["size"].grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="顏色 (Color):").grid(row=0, column=2, sticky="w")
        self.inputs["color"] = tk.Entry(form_frame, width=15)
        self.inputs["color"].grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="安全水位:").grid(row=0, column=4, sticky="w")
        self.inputs["safety_stock"] = tk.Entry(form_frame, width=10)
        self.inputs["safety_stock"].insert(0, "5") # 預設值
        self.inputs["safety_stock"].grid(row=0, column=5, padx=5, pady=5)

        # 第二排輸入
        tk.Label(form_frame, text="SKU (選填):").grid(row=1, column=0, sticky="w")
        self.inputs["sku"] = tk.Entry(form_frame, width=25)
        self.inputs["sku"].grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        tk.Label(form_frame, text="(若留空則系統自動生成)", fg="gray").grid(row=1, column=3, columnspan=2, sticky="w")

        # 按鈕區
        btn_frame = tk.Frame(form_frame, pady=10)
        btn_frame.grid(row=2, column=0, columnspan=6, sticky="ew")

        add_btn = tk.Button(btn_frame, text="+ 新增變體", bg="#4CAF50", fg="white", command=self._on_add_click)
        add_btn.pack(side="right", padx=5)

        del_btn = tk.Button(btn_frame, text="- 刪除選中", bg="#F44336", fg="white", command=self._on_delete_click)
        del_btn.pack(side="left", padx=5)

    # --- Events ---
    def set_callbacks(self, on_add: Callable, on_delete: Callable):
        self._on_add_callback = on_add
        self._on_delete_callback = on_delete

    def _on_add_click(self):
        self._on_add_callback()

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
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for v in variants:
            self.tree.insert("", "end", values=(
                v.id, v.size, v.color, v.sku, v.stock_qty, v.safety_stock
            ))

    def get_form_data(self) -> Dict[str, str]:
        return {k: v.get().strip() for k, v in self.inputs.items()}

    def clear_form(self):
        self.inputs["size"].delete(0, tk.END)
        self.inputs["color"].delete(0, tk.END)
        self.inputs["sku"].delete(0, tk.END)
        # safety_stock 保留預設值或不清除，視需求而定

    def show_error(self, message: str):
        messagebox.showerror("錯誤", message)