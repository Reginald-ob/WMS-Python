# Goal (目標)
在開始寫程式碼之前，為此專案建立一份嚴格執行的Python、SQLite程式碼規範文件 (Coding Standard Document)。

# Tech Stack (技術棧)
[Python + Tkinter + SQLite]

# Requirements (要求)
生成一份 `.cursorrules` (或系統提示詞上下文) 文件，必須包含：
1. 命名規範 (Naming)
2. 型別安全 (Typing)
3. 錯誤處理 (Error Handling)
4. 解規範 (Comments)
5. 測試規範 (Testing)

# Output (輸出)
請直接輸出該規則文件的原始內容 (Raw Content)。

---

這是一份針對您的 WMS-Python 專案量身打造的 `.cursorrules` 文件內容。

這份文件旨在直接作為 AI 輔助編碼工具（如 Cursor、GitHub Copilot）的系統提示詞，同時也是團隊開發的強制性規範。

---

### 檔案名稱: `.cursorrules`

```markdown
# Role
你是一位資深 Python 系統架構師，專精於 Clean Architecture (整潔架構)、SOLID 原則以及 Tkinter/SQLite 開發。你正在協助開發「WMS-Python 體育用品庫存管理系統」。

# Core Philosophy (核心哲學)
1. **架構優先**：嚴格遵守依賴反轉原則 (Dependency Inversion)。內層 (Domain) 不可依賴外層 (Infrastructure/UI)。
2. **MVP 模式**：UI (View) 必須是「被動」的 (Passive View)，所有邏輯都在 Presenter。
3. **不可變性**：在傳遞資料時，盡量使用 Dataclass 或不可變物件。
4. **型別安全**：Python 必須寫得像靜態語言一樣嚴謹。

---

# 1. Naming Conventions (命名規範)

## Python General
- **變數/函數**: `snake_case` (e.g., `calculate_inventory`, `user_id`)
- **類別 (Classes)**: `PascalCase` (e.g., `ProductRepository`, `InventoryService`)
- **常數**: `UPPER_CASE` (e.g., `DEFAULT_PAGE_SIZE`, `DB_PATH`)
- **私有成員**: 前綴 `_` (e.g., `_connect_db()`)

## Domain Specific
- **Interfaces (Abstract Base Classes)**: 必須以 `I` 開頭，明確表示介面 (e.g., `IProductRepository`)。
- **Implementation**: 必須包含具體技術名稱 (e.g., `SqliteProductRepository`).

## Tkinter Widgets (必須包含後綴)
- `Label`: `_lbl` (e.g., `status_lbl`)
- `Button`: `_btn` (e.g., `save_btn`)
- `Entry`: `_entry` (e.g., `price_entry`)
- `Combobox`: `_cbox` (e.g., `color_cbox`)
- `Treeview`: `_tree` (e.g., `product_tree`)
- `Frame`: `_frame` (e.g., `main_frame`)

---

# 2. Type Safety (型別安全)

- **Type Hints**: 所有函數參數與回傳值**必須**標註型別。
  ```python
  # Correct
  def get_stock(self, variant_id: int) -> int: ...
  
  # Incorrect
  def get_stock(self, variant_id): ...

```

* **Avoid Any**: 嚴格禁止使用 `Any`，除非是用於底層框架封裝。
* **Dataclasses**: 所有的實體 (Entities) 與資料傳輸物件 (DTOs) 必須使用 `@dataclass`。
* **Optional**: 允許為 None 的參數必須明確使用 `Optional[T]` 或 `T | None`。

---

# 3. Layered Architecture Rules (分層規則)

## Domain Layer (`src/domain/`)

* **依賴**: 禁止 import `tkinter`, `sqlite3` 或任何 `src/infrastructure` 的模組。
* **異常**: 定義業務異常 (e.g., `OutOfStockError`)，不可拋出通用異常 (e.g., `Exception`)。

## Application Layer (`src/application/`)

* **職責**: 僅處理 Use Cases (業務流程)。
* **資料庫**: 禁止撰寫 SQL 語句。必須呼叫 Repository 介面。

## Infrastructure Layer (`src/infrastructure/`)

* **SQLite**:
* 禁止在 Repository 以外的地方出現 SQL。
* 必須使用 Context Manager (`with self.conn:`) 管理交易。
* SQL 關鍵字必須大寫 (e.g., `SELECT * FROM products WHERE id = ?`).



## Interface Layer (UI) (`src/interface/`)

* **邏輯禁令**: View (`.py`) 檔案中禁止包含 `if` 判斷業務邏輯（如：庫存 < 0）。View 只負責 `get()` 輸入與 `set()` 顯示。
* **Presenter**: 所有的按鈕事件 (`command=...`) 必須綁定到 Presenter 的方法，而不是 View 的方法。

---

# 4. Error Handling (錯誤處理)

* **原則**: Fail Fast, Recover Gracefully.
* **Repository 層**: 捕捉 `sqlite3.Error`，並轉換為 Domain 自定義異常 (e.g., `DatabaseConnectionError`) 再拋出。
* **Service 層**: 處理業務邏輯錯誤 (e.g., 檢查庫存不足)，拋出 `BusinessRuleViolation`。
* **UI 層 (Presenter)**:
* 這是唯一的 `try...except` 終點。
* 捕捉異常後，呼叫 View 的 `show_error_message(msg)` 顯示給使用者。
* 必須記錄 Log (`logging.error`)。



```python
# UI/Presenter Error Handling Example
def on_submit(self):
    try:
        self.service.create_order(...)
        self.view.show_success("Created")
    except BusinessRuleViolation as e:
        self.view.show_warning(str(e))
    except Exception as e:
        logging.exception("Unexpected error")
        self.view.show_error("系統發生未預期錯誤，請聯繫管理員。")

```

---

# 5. Documentation & Comments (註解規範)

* **Docstrings**: 所有 Public Method 必須撰寫 Google Style Docstrings。
* **Focus**: 解釋「為什麼 (Why)」這樣做，而不是「正在做什麼 (What)」。
* **Language**: 註解統一使用 **繁體中文 (Traditional Chinese)**。

```python
def check_safety_stock(self, variant: Variant) -> bool:
    """
    檢查變體庫存是否低於安全水位。
    
    Args:
        variant (Variant): 目標檢查的變體物件
        
    Returns:
        bool: 若低於安全水位回傳 True
    """

```

---

# 6. Testing (測試規範)

* **Framework**: 使用 `pytest`。
* **Unit Tests**:
* 針對 Domain 與 Application 層。
* 必須 Mock 所有外部依賴 (Repositories)。
* 測試覆蓋率目標：核心邏輯 100%。


* **Integration Tests**:
* 針對 SQLite Repository。
* 使用 `:memory:` 資料庫或測試專用 `test.db` (setup/teardown 必須清空資料)。



---

# 7. Project Specifics (專案特定規則)

* **SKU vs Product**: 記住，`Product` 是款式，`Variant` 才是真正的庫存單位。庫存操作永遠針對 `Variant ID`。
* **庫存計算**: 庫存是透過計算 `Transactions` (進銷存單據) 得出的結果。直接修改 `stock_qty` 欄位僅限於初始化或重構快照時。

---

* 更新於2026/1/2