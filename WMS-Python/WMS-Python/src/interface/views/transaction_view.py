import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import List, Callable, Dict, Any

class TransactionView(tk.Frame):
    """
    通用單據視圖 (進貨/銷貨共用)。
    採用「購物車」模式：先將項目加入列表，最後一次送出。
    """

    def __init__(self, master, title: str, color_theme: str = "#4CAF50", **kwargs):
        super().__init__(master, **kwargs)
        self.title_text = title
        self.theme_color = color_theme
        
        # Callbacks
        self._on_product_select_callback = lambda pid: None
        self._on_submit_callback = lambda: None
        self._on_filter_product_callback = lambda k: None
        
        self._setup_ui()

    def _setup_ui(self):
        # 格線佈局
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # 列表區自動延展

        # --- 1. 標題區 ---
        header_frame = tk.Frame(self, bg=self.theme_color, pady=10)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        tk.Label(header_frame, text=self.title_text, font=("Microsoft JhengHei", 16, "bold"), bg=self.theme_color, fg="white").pack(side="left", padx=20)
        
        # 日期顯示
        today_str = date.today().strftime("%Y-%m-%d")
        tk.Label(header_frame, text=f"日期: {today_str}", bg=self.theme_color, fg="white").pack(side="right", padx=20)

        # --- 2. 操作區 (新增明細) ---
        input_frame = tk.LabelFrame(self, text="新增明細", padx=10, pady=10)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        self.inputs = {}

        # Row 1: 選擇商品與變體
        tk.Label(input_frame, text="1. 商品檢索:").grid(row=0, column=0, sticky="w")
        
        # A. 模糊搜寻框
        self.prod_filter_entry = tk.Entry(input_frame, width=15)
        self.prod_filter_entry.grid(row=0, column=1, padx=5, pady=5)
        self.prod_filter_entry.insert(0, "輸入關鍵字...")
        self.prod_filter_entry.bind("<FocusIn>", lambda e: self._on_filter_entry_focus_in())
        self.prod_filter_entry.bind("<KeyRelease>", lambda e: self._on_key_release_filter())
        
        tk.Label(input_frame, text="選擇商品:").grid(row=0, column=2, sticky="w")
        # B. 商品下拉选单 (Combobox)
        self.product_cbox = ttk.Combobox(input_frame, state="readonly", width=30)
        self.product_cbox.grid(row=0, column=3, padx=5, pady=5)
        self.product_cbox.bind("<<ComboboxSelected>>", self._on_product_select)

        tk.Label(input_frame, text="2. 選擇規格(變體):").grid(row=0, column=4, sticky="w")
        self.variant_cbox = ttk.Combobox(input_frame, state="readonly", width=25)
        self.variant_cbox.grid(row=0, column=5, padx=5, pady=5)
        
        # Row 2: 數量與價格
        tk.Label(input_frame, text="3. 數量:").grid(row=1, column=0, sticky="w")
        self.inputs["quantity"] = tk.Entry(input_frame, width=10)
        self.inputs["quantity"].grid(row=1, column=1, sticky="w", padx=5, pady=5)

        tk.Label(input_frame, text="4. 單價:").grid(row=1, column=2, sticky="w")
        self.inputs["price"] = tk.Entry(input_frame, width=10)
        self.inputs["price"].grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # 加入按鈕
        add_btn = tk.Button(input_frame, text="↓ 加入清單", command=self._on_add_item_click)
        add_btn.grid(row=1, column=6, padx=10, sticky="ew")

        # --- 3. 列表區 (購物車) ---
        list_frame = tk.Frame(self, padx=10, pady=5)
        list_frame.grid(row=2, column=0, sticky="nsew")

        cols = ("ID", "Product", "Variant", "Qty", "Price", "Subtotal")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="#")
        self.tree.heading("Product", text="商品名稱")
        self.tree.heading("Variant", text="規格")
        self.tree.heading("Qty", text="數量")
        self.tree.heading("Price", text="單價")
        self.tree.heading("Subtotal", text="小計")

        self.tree.column("ID", width=30, anchor="center")
        self.tree.column("Product", width=200)
        self.tree.column("Variant", width=150)
        self.tree.column("Qty", width=60, anchor="center")
        self.tree.column("Price", width=80, anchor="e")
        self.tree.column("Subtotal", width=80, anchor="e")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- 4. 底部結算區 ---
        footer_frame = tk.Frame(self, padx=20, pady=20, bg="#f9f9f9")
        footer_frame.grid(row=3, column=0, sticky="ew")

        # 備註欄
        tk.Label(footer_frame, text="單據備註:", bg="#f9f9f9").pack(side="left")
        self.inputs["note"] = tk.Entry(footer_frame, width=40)
        self.inputs["note"].pack(side="left", padx=10)

        # 送出按鈕
        submit_btn = tk.Button(footer_frame, text="確認送出 (Submit)", bg=self.theme_color, fg="white", font=("Arial", 12, "bold"), height=2, command=self._on_submit_click)
        submit_btn.pack(side="right")
        
        # 移除按鈕
        remove_btn = tk.Button(footer_frame, text="移除選中項目", command=self._on_remove_item_click)
        remove_btn.pack(side="right", padx=10)

        # 總金額
        self.total_lbl = tk.Label(footer_frame, text="總金額: $0", font=("Arial", 14, "bold"), fg="red", bg="#f9f9f9")
        self.total_lbl.pack(side="right", padx=20)

    # --- Events ---
    def set_callbacks(self, on_product_select, on_submit, on_filter_product=None):
        self._on_product_select_callback = on_product_select
        self._on_submit_callback = on_submit
        if on_filter_product:
            self._on_filter_product_callback = on_filter_product

    def _on_product_select(self, event):
        # 取得選中的 Combobox 索引
        current_idx = self.product_cbox.current()
        if current_idx >= 0:
            self._on_product_select_callback(current_idx)
    def _on_filter_entry_focus_in(self):
        """当使用者点击搜寻框时，清空位置文本"""
        if self.prod_filter_entry.get() == "输入关键字...":
            self.prod_filter_entry.delete(0, tk.END)

    def _on_key_release_filter(self):
        """当使用者在搜寻框打字时触发"""
        keyword = self.prod_filter_entry.get().strip()
        self._on_filter_product_callback(keyword)
    def _on_add_item_click(self):
        # 驗證輸入
        p_idx = self.product_cbox.current()
        v_idx = self.variant_cbox.current()
        qty = self.inputs["quantity"].get()
        price = self.inputs["price"].get()

        if p_idx < 0 or v_idx < 0:
            messagebox.showwarning("提示", "請選擇商品與規格")
            return
        
        try:
            qty_val = int(qty)
            price_val = float(price)
            if qty_val <= 0 or price_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "數量必須為正整數，單價必須為數字")
            return

        # 取得顯示文字 (這些邏輯本應在 Presenter，但為了 Grid 顯示方便，我們暫存這裡)
        # 更好的做法是回傳資料給 Presenter，由 Presenter 決定是否加入
        self.master.event_generate("<<AddItem>>", x=0, y=0) # 簡化起見，我們直接操作 Treeview
        # 在 MVP 中，View 不應該決定業務邏輯。我們設計一個 add_item_callback 比較好。
        # 這裡為了簡化，我們將「驗證通過的原始資料」傳給 Presenter 處理
        pass

    def _on_submit_click(self):
        self._on_submit_callback()
    
    def _on_remove_item_click(self):
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected)
            self.update_total_display()

    # --- Public API ---
    
    def set_product_list(self, names: List[str]):
        """設定商品下拉選單"""
        self.product_cbox['values'] = names
        self.product_cbox.set("")
        self.variant_cbox.set("")
        self.variant_cbox['values'] = []

    def set_variant_list(self, variants: List[str]):
        """設定變體下拉選單"""
        self.variant_cbox['values'] = variants
        self.variant_cbox.set("")

    def get_input_data(self) -> Dict[str, Any]:
        """取得當前輸入框的資料 (用於加入明細)"""
        return {
            "product_idx": self.product_cbox.current(),
            "variant_idx": self.variant_cbox.current(),
            "quantity": self.inputs["quantity"].get(),
            "price": self.inputs["price"].get()
        }
        
    def get_note(self) -> str:
        return self.inputs["note"].get()

    def add_item_to_tree(self, display_data: tuple):
        """將驗證後的資料加入 Treeview"""
        # display_data: (variant_id, prod_name, var_name, qty, price, subtotal)
        self.tree.insert("", "end", values=display_data)
        self.update_total_display()
        
        # 清空輸入框以便下一筆
        self.inputs["quantity"].delete(0, tk.END)
        self.inputs["price"].delete(0, tk.END)
        # self.variant_cbox.set("") # 視需求決定是否重置變體

    def get_all_items(self) -> List[dict]:
        """取得 Treeview 中所有資料 (供 Submit 使用)"""
        items = []
        for child in self.tree.get_children():
            values = self.tree.item(child)["values"]
            # values: [variant_id, prod_name, var_name, qty, price, subtotal]
            items.append({
                "variant_id": values[0],
                "quantity": int(values[3]),
                "unit_price": float(values[4])
            })
        return items

    def update_total_display(self):
        """計算並更新總金額"""
        total = 0.0
        for child in self.tree.get_children():
            val = self.tree.item(child)["values"]
            total += float(val[5])
        self.total_lbl.config(text=f"總金額: ${total:,.2f}")

    def clear_all(self):
        """重置整個畫面"""
        self.product_cbox.set("")
        self.variant_cbox.set("")
        self.inputs["quantity"].delete(0, tk.END)
        self.inputs["price"].delete(0, tk.END)
        self.inputs["note"].delete(0, tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_total_display()
    
    def bind_add_button(self, callback):
        self.add_btn_callback = callback
        # 重新綁定按鈕
        # 由於 __init__ 中按鈕已經綁定到 _on_add_item_click，我們在那裡呼叫這個 callback
        pass
    
    # 修正按鈕綁定
    def _on_add_item_click(self):
        if hasattr(self, 'add_btn_callback'):
            self.add_btn_callback()