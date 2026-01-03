# Plan Fase 2: Lógica de Negocio Robusta

**Objetivo:** Eliminar "Strings Mágicos" y prevenir estados inválidos (Stock Negativo).

## 1. Implementación de Enums (`backend/models/enums.py`)
Crear un archivo centralizado para definiciones constantes. Esto evita errores de dedo (ej: escribir "In" en lugar de "IN").

```python
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
```

## 2. Refactorización de Modelos (`backend/models/database.py`)
- Importar los Enums.
- Modificar las columnas `String` para usar `Enum` de SQLAlchemy (o validar en aplicación si SQLite da problemas, pero definirlos es clave).

## 3. Refactorización de API (`backend/api/*.py`)
- Reemplazar strings literales `"IN"`, `"preparation"`, etc., por las constantes del Enum.
- Actualizar modelos Pydantic para validar que los inputs sean miembros del Enum.

## 4. Validación de Stock (`backend/api/*.py`)
- **Regla:** El stock no debería ser negativo.
- **Acción:** En `wastes.py` y `products.py`, añadir validación explícita:
  ```python
  if product.current_stock - quantity < 0:
      raise HTTPException(400, "Insufficient stock")
  ```
  *(Nota: Ya existe algo básico, pero lo haremos robusto y consistente).*

## Orden de Ejecución
1. Crear `backend/models/enums.py`
2. Actualizar `database.py` (imports)
3. Refactorizar `wastes.py`, `products.py`, `invoices.py`, `counts.py`.
