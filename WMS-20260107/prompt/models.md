# Role (角色)
資深開發者 (Goose)

# Context (背景)

我們正在實作 `單據查詢`該頁面中的新功能，要你參照下面提供的代碼，僅對document_list_view.py檔案做修改，目的是修改UI 視圖的代碼 (src/interface/views/document_list_view.py)，我們需要在 彈出視窗 (Detail Window) 增加按鈕，並將事件傳遞回去。

# ... (Imports)
class DocumentDetailWindow(tk.Toplevel):
    def __init__(self, master, document: Document, on_delete: Callable[[int], None] = None): # [修改] 新增 on_delete 參數
        super().__init__(master)
        self.document = document
        self.on_delete = on_delete
        
        # ... (保留 Header Info 代碼)
        # ... (保留 Items Table 代碼)
        
        # [新增] 底部操作區
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(side="bottom", fill="x", padx=10)

        # 刪除按鈕 (紅色)
        del_btn = tk.Button(btn_frame, text="🗑 刪除此單據", bg="#D32F2F", fg="white", 
                            command=self._on_delete_click)
        del_btn.pack(side="left")

        # 關閉按鈕
        close_btn = tk.Button(btn_frame, text="關閉", command=self.destroy)
        close_btn.pack(side="right")

    def _on_delete_click(self):
        if self.on_delete:
            self.on_delete(self.document.id)

class DocumentListView(tk.Frame):
    # ... (保留 __init__)

    # [修改] 新增 on_delete 參數
    def set_callbacks(self, on_filter, on_view_detail, on_delete=None):
        self._on_filter_callback = on_filter
        self._on_view_detail_callback = on_view_detail
        self._on_delete_callback = on_delete # [新增]

    # [修改] 開啟視窗時傳入 callback
    def open_detail_window(self, document: Document):
        # 傳入 self._on_delete_callback
        DocumentDetailWindow(self, document, on_delete=self._on_delete_callback)