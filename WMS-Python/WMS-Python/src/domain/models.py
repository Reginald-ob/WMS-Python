from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date

@dataclass
class Product:
    """
    商品款式 (Product)
    代表抽象的產品概念，例如「Nike Air Zoom」。
    """
    name: str
    brand: str
    base_price: float
    category: Optional[str] = None
    description: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class Variant:
    """
    庫存變體 (Variant)
    代表實際的庫存單位 (SKU)，例如「Nike Air Zoom - 紅色 - US 9.5」。
    """
    product_id: int
    size: str
    color: str
    sku: str = ""  # 若為空字串，系統後續可自動生成
    stock_qty: int = 0
    safety_stock: int = 5
    id: Optional[int] = None
    
    @property
    def display_name(self) -> str:
        """回傳顯示用的完整規格名稱"""
        return f"{self.size} / {self.color}"

    def is_low_stock(self) -> bool:
        """判斷是否低於安全庫存"""
        return self.stock_qty <= self.safety_stock

@dataclass
class DocumentItem:
    """單據明細項"""
    variant_id: int
    quantity: int
    unit_price: float
    id: Optional[int] = None
    # 關聯物件 (Optional, 僅供 UI 顯示方便使用，不寫入 DB)
    variant: Optional[Variant] = None

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price

@dataclass
class Document:
    """進銷存單據 (Header)"""
    doc_type: str  # 'INBOUND', 'OUTBOUND', 'ADJUST'
    doc_date: date
    items: List[DocumentItem] = field(default_factory=list)
    note: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None

    def add_item(self, item: DocumentItem) -> None:
        self.items.append(item)

    @property
    def total_amount(self) -> float:
        return sum(item.subtotal for item in self.items)