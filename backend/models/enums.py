import enum

class StockMovementType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"

class WasteType(str, enum.Enum):
    PREPARATION = "preparation"
    EXPIRED = "expired"
    DAMAGED = "damaged"

class CountType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    CATEGORY = "category"

class CountStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
