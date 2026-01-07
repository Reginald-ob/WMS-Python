class DomainError(Exception):
    """所有業務邏輯異常的基類"""
    pass

class RepositoryError(DomainError):
    """資料存取層發生的通用錯誤 (如: DB 連線失敗)"""
    pass

class EntityNotFoundError(RepositoryError):
    """查詢的實體不存在"""
    pass

class DuplicateEntityError(RepositoryError):
    """實體重複 (如: SKU 已存在)"""
    pass

class BusinessRuleViolation(DomainError):
    """違反業務規則 (如: 負庫存操作)"""
    pass

class OutOfStockError(BusinessRuleViolation):
    """庫存不足異常"""
    pass