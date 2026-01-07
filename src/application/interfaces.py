from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models import Product, Variant

class IProductRepository(ABC):
    """
    商品儲存庫介面 (Interface)
    定義對 Product 與 Variant 的存取操作。
    """

    @abstractmethod
    def add_product(self, product: Product) -> Product:
        """新增商品款式，回傳帶有 ID 的完整物件"""
        pass

    @abstractmethod
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """依 ID 查詢商品"""
        pass

    @abstractmethod
    def get_all_products(self) -> List[Product]:
        """取得所有商品列表"""
        pass

    @abstractmethod
    def update_product(self, product: Product) -> None:
        """更新商品資訊"""
        pass

    @abstractmethod
    def delete_product(self, product_id: int) -> None:
        """刪除商品 (注意: 需考慮是否連動刪除變體)"""
        pass

    # --- Variant (變體) 相關操作 ---
    
    @abstractmethod
    def add_variant(self, variant: Variant) -> Variant:
        """新增變體"""
        pass

    @abstractmethod
    def get_variant_by_id(self, variant_id: int) -> Optional[Variant]:
        """依 ID 查詢變體"""
        pass

    @abstractmethod
    def get_variants_by_product_id(self, product_id: int) -> List[Variant]:
        """取得特定商品底下的所有變體"""
        pass

    @abstractmethod
    def update_variant(self, variant: Variant) -> None:
        """更新變體 (包含庫存數量變更)"""
        pass
    
    @abstractmethod
    def get_variant_by_sku(self, sku: str) -> Optional[Variant]:
        """依 SKU 查詢變體"""
        pass

from src.domain.models import Document, DocumentItem # 確保已匯入

class IDocumentRepository(ABC):
    """
    單據儲存庫介面 (Interface)
    負責處理進銷存單據 (Document) 與其明細 (DocumentItem) 的持久化。
    """

    @abstractmethod
    def add_document(self, document: Document) -> Document:
        """
        新增單據 (包含寫入所有明細項目)。
        注意：此操作應為原子性交易 (Atomic Transaction)。
        """
        pass

    @abstractmethod
    def get_document_by_id(self, doc_id: int) -> Optional[Document]:
        """依 ID 取得完整單據 (包含明細)"""
        pass

    @abstractmethod
    def get_all_documents(self, doc_type: Optional[str] = None) -> List[Document]:
        """
        取得單據列表。
        
        Args:
            doc_type: 若提供，僅篩選特定類型的單據 (如 'INBOUND')
        """
        pass

    @abstractmethod
    def delete_document(self, doc_id: int) -> None:
        """刪除單據 (資料庫層級刪除)"""
        pass