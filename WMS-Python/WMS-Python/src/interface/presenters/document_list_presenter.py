import logging
from typing import Optional

from src.interface.views.document_list_view import DocumentListView
from src.application.services import InventoryService

logger = logging.getLogger(__name__)

class DocumentListPresenter:
    """
    單據歷史查詢的 Presenter
    """

    def __init__(self, view: DocumentListView, service: InventoryService):
        self.view = view
        self.service = service
        
        self.view.set_callbacks(
            on_filter=self.load_documents,
            on_view_detail=self.open_document_detail
        )
        
        # 預設載入全部
        self.load_documents()

    def load_documents(self, doc_type: Optional[str] = None):
        """依類型載入單據列表"""
        try:
            docs = self.service.get_documents(doc_type)
            self.view.update_list(docs)
        except Exception as e:
            logger.error(f"載入單據列表失敗: {e}")
            # 可以考慮顯示錯誤訊息框

    def open_document_detail(self, doc_id: int):
        """開啟單據詳情"""
        try:
            # 必須重新呼叫 Service 取得完整單據 (包含 Items)
            doc = self.service.get_document_detail(doc_id)
            if doc:
                self.view.open_detail_window(doc)
            else:
                logger.warning(f"找不到單據 ID: {doc_id}")
        except Exception as e:
            logger.error(f"開啟單據詳情失敗: {e}")