import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import List, Callable, Dict, Any

from src.domain.models import Product

class AdjustmentView(tk.Frame):
    """
    庫存盤點視圖 (Inventory Adjustment)。
    修正: 使用字典映射取代字串解析，移除 UI 上的 ID 顯示。
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 內部狀態: 用於儲存 "顯示名稱" -> "商品ID" 的對照表
        self.product_map: Dict[str, int] = {}
        
        # Callbacks
        self._on_filter_product_callback = lambda k: None
        self._on_product_select_callback = lambda pid: None
        self._on_variant_select_callback = lambda idx: None 
        self._on_submit_callback = lambda: None
        
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- 1. 標題區 ---
        header_frame = tk.Frame(self, bg="#607D8B", pady=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        tk.Label(header_frame, text="庫存盤點 / 調整 (Adjustment)", font=("Microsoft JhengHei", 16, "bold"), bg="#607D8B", fg="white").pack(side="left", padx=20)
        tk.Label(header_frame, text=f"日期: {date.today()}", bg="#607D8B", fg="white").pack(side="right", padx=20)

        # --- 2. 操作區 ---
        input_frame = tk.LabelFrame(self, text="盤點輸入", padx=10, pady=10)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # Row 0: 商品檢索與選擇
        tk.Label(input_frame, text="1. 商品檢索:").grid(row=0, column=0, sticky="w")
        
        self.prod_filter_entry = tk.Entry(input_frame, width=15)
        self.prod_filter_entry.grid(row=0, column=1, padx=5)
        self.prod_filter_entry.insert(0, "輸入關鍵字...")
        self.prod_filter_entry.bind("<FocusIn>", lambda e: self.prod_filter_entry.delete(0, tk.END))
        self.prod_filter_entry.bind("<KeyRelease>", self._on_key_release_filter)

        tk.Label(input_frame, text="選擇商品:").grid(row=0, column=2, sticky="w")
        self.product_cbox = ttk.Combobox(input_frame, state="readonly", width=30)
        self.product_cbox.grid(row=0, column=3, padx=5, pady=5)
        self.product_cbox.bind("<<ComboboxSelected>>", self._on_product_select)

        tk.Label(input_frame, text="2. 選擇規格:").grid(row=0, column=4, sticky="w")
        self.variant_cbox = ttk.Combobox(input_frame, state="readonly", width=25)
        self.variant_cbox.grid(row=0, column=5, padx=5, pady=5)
        self.variant_cbox.bind("<<ComboboxSelected>>", self._on_variant_select)

        # Row 1: 庫存數據 (唯讀) 與 輸入
        tk.Label(input_frame, text="系統庫存:", fg="gray").grid(row=1, column=0, sticky="w", pady=10)
        self.sys_qty_var = tk.StringVar(value="-")
        tk.Label(input_frame, textvariable=self.sys_qty_var, font=("Arial", 10, "bold"), fg="blue").grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(input_frame, text="3. 實際盤點數:", font=("Bold", 10)).grid(row=1, column=2, sticky="w")
        self.actual_qty_entry = tk.Entry(input_frame, width=10, bg="#FFF8E1")
        self.actual_qty_entry.grid(row=1, column=3, sticky="w", padx=5)

        add_btn = tk.Button(input_frame, text="計算差異並加入 ↓", command=self._on_add_item_click)
        add_btn.grid(row=1, column=4, columnspan=2, padx=10, sticky="ew")

        # --- 3. 調整清單 ---
        list_frame = tk.Frame(self, padx=10, pady=5)
        list_frame.grid(row=2, column=0, sticky="nsew")

        cols = ("ID", "Product", "Variant", "SystemQty", "ActualQty", "Diff")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="#")
        self.tree.heading("Product", text="商品名稱")
        self.tree.heading("Variant", text="規格")
        self.tree.heading("SystemQty", text="系統庫存")
        self.tree.heading("ActualQty", text="實際盤點")
        self.tree.heading("Diff", text="差異調整數")

        self.tree.column("ID", width=30, anchor="center")
        self.tree.column("Product", width=200)
        self.tree.column("Variant", width=150)
        self.tree.column("SystemQty", width=80, anchor="center")
        self.tree.column("ActualQty", width=80, anchor="center")
        self.tree.column("Diff", width=100, anchor="center")
        
        self.tree.tag_configure("negative", foreground="red")
        self.tree.tag_configure("positive", foreground="green")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- 4. 底部 ---
        footer_frame = tk.Frame(self, padx=20, pady=20, bg="#f9f9f9")
        footer_frame.grid(row=3, column=0, sticky="ew")

        tk.Label(footer_frame, text="盤點備註:", bg="#f9f9f9").pack(side="left")
        self.note_entry = tk.Entry(footer_frame, width=50)
        self.note_entry.pack(side="left", padx=10)

        submit_btn = tk.Button(footer_frame, text="確認庫存修正 (Submit Adjustment)", bg="#607D8B", fg="white", font=("Arial", 12, "bold"), height=2, command=self._on_submit_click)
        submit_btn.pack(side="right")
        
        remove_btn = tk.Button(footer_frame, text="移除項目", command=self._on_remove_item)
        remove_btn.pack(side="right", padx=10)

    # --- Events & Public API ---

    def set_callbacks(self, on_filter_product, on_product_select, on_variant_select, on_submit):
        self._on_filter_product_callback = on_filter_product
        self._on_product_select_callback = on_product_select
        self._on_variant_select_callback = on_variant_select
        self._on_submit_callback = on_submit

    def _on_key_release_filter(self, event):
        keyword = self.prod_filter_entry.get().strip()
        self._on_filter_product_callback(keyword)

    def _on_product_select(self, event):
        """
        修正: 透過 product_map 查詢 ID，不再依賴字串解析。
        """
        val = self.product_cbox.get()
        if val in self.product_map:
            prod_id = self.product_map[val]
            self._on_product_select_callback(prod_id)

    def _on_variant_select(self, event):
        idx = self.variant_cbox.current()
        if idx >= 0: self._on_variant_select_callback(idx)

    def _on_add_item_click(self):
        try:
            actual = int(self.actual_qty_entry.get())
            if actual < 0: raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "實際盤點數必須為非負整數")
            return
            
        if not self.product_cbox.get() or self.variant_cbox.current() < 0:
            messagebox.showwarning("提示", "請選擇商品與規格")
            return

        if hasattr(self, 'add_item_handler'):
            self.add_item_handler()

    def bind_add_button(self, handler):
        self.add_item_handler = handler

    def _on_submit_click(self):
        self._on_submit_callback()
    
    def _on_remove_item(self):
        selected = self.tree.selection()
        if selected: self.tree.delete(selected)

    # --- Setters / Getters ---

    def update_product_combo(self, products: List[Product]):
        """
        更新下拉選單與 ID 映射表。
        格式: "Brand Name" (不含 ID)
        """
        self.product_map = {}
        display_list = []
        
        for p in products:
            display_str = f"{p.brand} {p.name}"
            self.product_map[display_str] = p.id
            display_list.append(display_str)
            
        self.product_cbox['values'] = display_list
        
        if display_list:
            self.product_cbox.current(0)
            self._on_product_select(None)
        else:
            self.product_cbox.set("")
            self.variant_cbox.set("")
            self.variant_cbox['values'] = []

    def set_variant_list(self, names: List[str]):
        self.variant_cbox['values'] = names
        self.variant_cbox.set("")
        self.sys_qty_var.set("-")
        if names:
            self.variant_cbox.current(0)
            self._on_variant_select(None)

    def update_system_stock_display(self, qty: int):
        self.sys_qty_var.set(str(qty))

    def get_input_data(self):
        return {
            "prod_str": self.product_cbox.get(),
            "v_idx": self.variant_cbox.current(),
            "actual_qty": int(self.actual_qty_entry.get())
        }

    def add_item_to_tree(self, display_data: tuple, diff: int):
        tag = "positive" if diff >= 0 else "negative"
        self.tree.insert("", "end", values=display_data, tags=(tag,))
        self.actual_qty_entry.delete(0, tk.END)

    def get_all_items(self) -> List[dict]:
        items = []
        for child in self.tree.get_children():
            val = self.tree.item(child)["values"]
            items.append({
                "variant_id": val[0],
                "quantity": int(val[5])
            })
        return items

    def get_note(self) -> str:
        return self.note_entry.get()

    def clear_all(self):
        self.product_cbox.set("")
        self.variant_cbox.set("")
        self.sys_qty_var.set("-")
        self.actual_qty_entry.delete(0, tk.END)
        self.note_entry.delete(0, tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)