import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Optional
from datetime import datetime

from src.domain.models import Document, DocumentItem

class DocumentDetailWindow(tk.Toplevel):
    """
    [彈出視窗] 顯示單據明細
    """
    def __init__(self, master, document: Document):
        super().__init__(master)
        self.title(f"單據詳情 - #{document.id}")
        self.geometry("600x400")
        
        # Header Info
        info_frame = tk.Frame(self, padx=15, pady=15, bg="#f5f5f5")
        info_frame.pack(fill="x")
        
        tk.Label(info_frame, text=f"單號: #{document.id}", font=("Bold", 12), bg="#f5f5f5").grid(row=0, column=0, sticky="w")
        tk.Label(info_frame, text=f"類型: {document.doc_type}", bg="#f5f5f5").grid(row=0, column=1, padx=20, sticky="w")
        tk.Label(info_frame, text=f"日期: {document.doc_date}", bg="#f5f5f5").grid(row=0, column=2, sticky="w")
        
        if document.note:
            tk.Label(info_frame, text=f"備註: {document.note}", fg="gray", bg="#f5f5f5").grid(row=1, column=0, columnspan=3, sticky="w", pady=(5,0))

        # Items Table
        self.tree = ttk.Treeview(self, columns=("Product", "Variant", "Qty", "Price", "Subtotal"), show="headings")
        self.tree.heading("Product", text="商品名稱")
        self.tree.heading("Variant", text="規格")
        self.tree.heading("Qty", text="數量")
        self.tree.heading("Price", text="單價")
        self.tree.heading("Subtotal", text="小計")
        
        self.tree.column("Product", width=150)
        self.tree.column("Variant", width=100)
        self.tree.column("Qty", width=50, anchor="center")
        self.tree.column("Price", width=80, anchor="e")
        self.tree.column("Subtotal", width=80, anchor="e")
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Fill Data
        total = 0
        for item in document.items:
            # 這裡依賴 Repository 有做 join 查詢把 product_name/size/color 帶出來
            # 若 Repository 沒有 populate variant 物件，這裡可能只會顯示 ID
            # 為了 MVP 簡單，我們假設 Repo 回傳的 DocumentItem 物件在 application 層組裝時可能沒有完整 variant 物件
            # 但我們可以透過 item.variant_id 顯示，或者在 Repository 的 SQL Join 裡取值 (推薦後者)
            # 在 Step 2 的 SqliteDocumentRepository.get_document_by_id 我們有做 JOIN
            # 但 DocumentItem dataclass 預設欄位沒有 name/size/color，我們用 getattr 或是擴充 dataclass
            
            # 為了避免修改 dataclass，我們這裡嘗試讀取動態屬性 (row mapping 產生的)
            p_name = getattr(item, 'product_name', '-') # 來自 SQL Alias
            size = getattr(item, 'size', '-')
            color = getattr(item, 'color', '-')
            spec = f"{size}/{color}"
            
            subtotal = item.quantity * item.unit_price
            total += subtotal
            
            self.tree.insert("", "end", values=(p_name, spec, item.quantity, item.unit_price, subtotal))
            
        # Footer
        tk.Label(self, text=f"總金額: ${total:,.2f}", font=("Arial", 12, "bold"), fg="#E91E63").pack(side="right", padx=20, pady=10)


class DocumentListView(tk.Frame):
    """
    [主畫面] 單據歷史查詢列表
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self._on_filter_callback = lambda type: None
        self._on_view_detail_callback = lambda doc_id: None
        
        self._setup_ui()

    def _setup_ui(self):
        # Top Filter Bar
        filter_frame = tk.Frame(self, bg="#eeeeee", padx=10, pady=10)
        filter_frame.pack(fill="x")
        
        tk.Label(filter_frame, text="單據類型篩選:", bg="#eeeeee").pack(side="left")
        
        self.type_cbox = ttk.Combobox(filter_frame, state="readonly", values=["全部 (ALL)", "進貨 (INBOUND)", "銷貨 (OUTBOUND)", "調整 (ADJUST)"])
        self.type_cbox.current(0)
        self.type_cbox.pack(side="left", padx=10)
        self.type_cbox.bind("<<ComboboxSelected>>", self._on_filter_change)

        refresh_btn = tk.Button(filter_frame, text="重新整理", command=lambda: self._on_filter_change(None))
        refresh_btn.pack(side="left")

        # Main List
        cols = ("ID", "Type", "Date", "ItemsCount", "Note")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="單號")
        self.tree.heading("Type", text="類型")
        self.tree.heading("Date", text="日期")
        self.tree.heading("ItemsCount", text="明細數") # 這裡我們可以顯示 item 數量或是總金額(若有)
        self.tree.heading("Note", text="備註")
        
        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Type", width=100, anchor="center")
        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("ItemsCount", width=80, anchor="center")
        self.tree.column("Note", width=300)
        
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double click to view detail
        self.tree.bind("<Double-1>", self._on_item_dbl_click)

    def set_callbacks(self, on_filter, on_view_detail):
        self._on_filter_callback = on_filter
        self._on_view_detail_callback = on_view_detail

    def _on_filter_change(self, event):
        val = self.type_cbox.get()
        # Parse value like "進貨 (INBOUND)" -> "INBOUND"
        if "INBOUND" in val: doc_type = "INBOUND"
        elif "OUTBOUND" in val: doc_type = "OUTBOUND"
        elif "ADJUST" in val: doc_type = "ADJUST"
        else: doc_type = None # ALL
        
        self._on_filter_callback(doc_type)

    def _on_item_dbl_click(self, event):
        selected = self.tree.selection()
        if selected:
            # tree item text is empty, values[0] is ID
            doc_id = self.tree.item(selected[0], "values")[0]
            self._on_view_detail_callback(int(doc_id))

    def update_list(self, documents: List[Document]):
        # Clear
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for doc in documents:
            # 為了效能，列表中不一定有 items 詳情，所以我們只顯示基本資訊
            # 若 Repository 的 get_all_documents 沒有 join items，我們這裡無法顯示 item count 或 total amount
            # 除非我們在 Repository 層做 group by count
            # 這裡暫時顯示 '-' 或依賴 Repo 實作
            self.tree.insert("", "end", values=(
                doc.id, 
                doc.doc_type, 
                doc.doc_date, 
                "-", # 若 doc.items 是空的 (Lazy load) 則無法顯示數量
                doc.note
            ))
            
    def open_detail_window(self, document: Document):
        DocumentDetailWindow(self, document)