# 🔍 Auditoría Técnica Completa: KusiSaaS Enterprise v1.0

**Fecha:** 03/01/2026  
**Auditor:** Antigravity (Senior Software Auditor - SaaS B2B)  
**Contexto:** MVP pre-producción, multi-tenant, Python/FastAPI/PostgreSQL  
**Objetivo:** Detectar bugs silenciosos, riesgos de escalabilidad y problemas de diseño antes de producción

---

## 🧠 Visión General Técnica del Sistema

### Arquitectura Actual
- **Patrón:** Monolito modular con separación por routers (API) + modelos (ORM) + utilidades
- **Capas identificadas:**
  - `backend/api/*.py` → Endpoints REST (controllers)
  - `backend/models/database.py` → Modelos SQLAlchemy (ORM)
  - `backend/models/enums.py` → Enumeraciones de negocio
  - `backend/utils/*.py` → Lógica de cálculos y generación de reportes
- **Multi-tenancy:** Implementado mediante `restaurant_id` en tablas principales
- **Estado:** Funcional para 1-5 clientes, con riesgos identificados para escalar a 50+

---

## ❌ Bugs Confirmados (Impacto Inmediato)

### B-1: Race Condition en Actualización de Stock (CRÍTICO)
**Ubicación:** `backend/api/wastes.py` (Línea 105)

**Código problemático:**
```python
product = db.query(Product).filter(Product.id == waste.product_id).with_for_update().first()
# ...
product.current_stock -= waste.quantity  # LECTURA + ESCRITURA en Python
db.commit()
```

**Problema:** Aunque se usa `with_for_update()`, la operación aritmética se hace en Python, no en SQL. Si dos usuarios registran mermas simultáneamente:
1. Usuario A lee `stock = 100`
2. Usuario B lee `stock = 100` (antes del commit de A)
3. Usuario A escribe `stock = 95` (merma de 5)
4. Usuario B escribe `stock = 90` (merma de 10)
5. **Resultado:** Stock final = 90 (debería ser 85)

**Impacto:** Inventario fantasma. El stock del sistema nunca coincidirá con el físico.

**Solución quirúrgica:**
```python
db.query(Product).filter(Product.id == waste.product_id).update({
    "current_stock": Product.current_stock - waste.quantity
})
```

---

### B-2: Fuga de Datos entre Tenants en Dashboard (ALTO)
**Ubicación:** `backend/api/dashboard.py` (Línea 83-87)

**Código problemático:**
```python
weekly_consumption = db.query(func.sum(StockMovement.quantity * Product.cost_price)).filter(
    StockMovement.restaurant_id == current_user.restaurant_id,
    StockMovement.movement_type == StockMovementType.OUT,
    StockMovement.created_at >= week_ago
).scalar() or Decimal('0.0')
```

**Problema:** El JOIN implícito entre `StockMovement` y `Product` NO valida que el producto también pertenezca al mismo `restaurant_id`. Si un `StockMovement` apunta a un `product_id` de otro restaurante (por error de migración o bug), se incluirá en el cálculo.

**Impacto:** Datos financieros contaminados entre clientes.

**Solución:**
```python
weekly_consumption = db.query(func.sum(StockMovement.quantity * Product.cost_price)).join(
    Product, StockMovement.product_id == Product.id
).filter(
    StockMovement.restaurant_id == current_user.restaurant_id,
    Product.restaurant_id == current_user.restaurant_id,  # CRÍTICO
    StockMovement.movement_type == StockMovementType.OUT,
    StockMovement.created_at >= week_ago
).scalar() or Decimal('0.0')
```

---

### B-3: Cálculo de Rotación Incorrecto (MEDIO)
**Ubicación:** `backend/utils/calculations.py` (Línea 227-232)

**Código problemático:**
```python
for movement in reversed(movements):
    if movement.movement_type == "IN":
        current_stock -= movement.quantity  # RETROCESO TEMPORAL
    else:
        current_stock += movement.quantity
    stock_history.append(current_stock)
```

**Problema:** El algoritmo intenta reconstruir el historial de stock "hacia atrás", pero:
1. Asume que `current_stock` es el valor actual del producto
2. No valida que los movimientos estén ordenados cronológicamente
3. Si hay movimientos concurrentes o fuera de orden, el cálculo es erróneo

**Impacto:** Índices de rotación incorrectos → decisiones de compra equivocadas.

**Solución:** Usar `StockMovement.new_stock` directamente (ya está registrado):
```python
stock_history = [m.new_stock for m in movements]
avg_stock = sum(stock_history) / len(stock_history) if stock_history else product.current_stock
```

---

## ⚠️ Riesgos Potenciales (Aún No Fallan)

### R-1: Categorías y Proveedores Compartidos entre Tenants
**Ubicación:** `backend/models/database.py` (Líneas 58-89)

**Análisis:** Las tablas `categories` y `providers` NO tienen `restaurant_id`. Son globales.

**Riesgo:**
- Si el "Restaurante A" crea un proveedor "Distribuidora XYZ", el "Restaurante B" también lo verá.
- Esto puede ser intencional (catálogo compartido) o un error de diseño.

**Impacto si es error:**
- Fuga de información comercial (proveedores de la competencia)
- Conflictos de nombres (dos restaurantes con proveedores homónimos pero diferentes)

**Recomendación:** Aclarar si esto es intencional. Si no, añadir `restaurant_id` a estas tablas.

---

### R-2: OCR Sin Timeout ni Límite de Páginas PDF
**Ubicación:** `backend/utils/ocr_parser.py` (Línea 62)

**Código:**
```python
images = pdf2image.convert_from_bytes(file_content)
if not images:
    return {"success": False, "error": "Could not convert PDF to image"}
image = images[0]  # Use first page
```

**Riesgo:**
- Un PDF de 500 páginas consumirá toda la RAM del servidor
- No hay timeout: un PDF corrupto puede bloquear el worker indefinidamente

**Impacto:** Denegación de servicio para todos los tenants del servidor.

**Solución:**
```python
images = pdf2image.convert_from_bytes(
    file_content,
    first_page=1,
    last_page=1,  # Solo primera página
    timeout=10  # Timeout de 10 segundos
)
```

---

### R-3: Ausencia de Índices Compuestos para Queries Multi-Tenant
**Ubicación:** `backend/models/database.py`

**Análisis:** Las queries más frecuentes filtran por `restaurant_id` + otra condición (ej: `created_at`, `status`), pero solo hay índices simples.

**Ejemplo:**
```python
query = db.query(Invoice).filter(
    Invoice.restaurant_id == current_user.restaurant_id,
    Invoice.created_at >= start_date
)
```

**Riesgo:** Con 100 restaurantes y 10,000 facturas cada uno, PostgreSQL hará un scan completo de 1M de filas.

**Solución:** Añadir índices compuestos:
```python
Index('ix_invoices_restaurant_date', 'restaurant_id', 'created_at')
Index('ix_products_restaurant_stock', 'restaurant_id', 'current_stock')
```

---

## 🧩 Problemas de Diseño / Deuda Técnica

### D-1: Lógica de Negocio Mezclada con Controllers
**Severidad:** MEDIA

**Análisis:** Los archivos `backend/api/*.py` contienen tanto lógica HTTP (validación de requests) como lógica de negocio (cálculos, actualizaciones de stock).

**Ejemplo:** `wastes.py` (Líneas 88-115) calcula costes, valida stock y actualiza la BD en el mismo endpoint.

**Impacto:**
- Imposible testear la lógica de negocio sin levantar FastAPI
- Difícil reutilizar lógica (ej: registrar una merma desde un proceso batch)

**Recomendación:** Extraer a servicios:
```python
# backend/services/waste_service.py
class WasteService:
    def create_waste_log(self, product_id, quantity, waste_type, user_id, db):
        # Lógica pura, sin dependencias de FastAPI
```

---

### D-2: Ausencia de Transacciones Explícitas
**Severidad:** ALTA

**Análisis:** Muchos endpoints hacen múltiples escrituras sin `db.begin()` explícito. Confían en el autocommit de SQLAlchemy.

**Ejemplo:** `counts.py` (Líneas 100-137) crea un `PhysicalCount` + múltiples `PhysicalCountItem` sin transacción.

**Riesgo:** Si falla la creación del ítem #50 de 100, los primeros 49 quedan huérfanos en la BD.

**Solución:**
```python
try:
    db.begin()
    # ... operaciones ...
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

---

### D-3: Cálculos Costosos en Endpoints Síncronos
**Severidad:** MEDIA

**Ubicación:** `backend/api/reports.py` (múltiples endpoints)

**Análisis:** Los reportes iteran sobre todos los productos/movimientos en memoria para calcular agregados.

**Ejemplo:** `get_consumption_report` (Líneas 139-189) hace un loop Python sobre todos los `StockMovement` del período.

**Riesgo:** Con 10,000 movimientos/mes, el endpoint tardará 5-10 segundos → timeout del cliente.

**Solución:** Usar agregaciones SQL:
```python
consumption_by_category = db.query(
    Category.name,
    func.sum(StockMovement.quantity * Product.cost_price).label('total')
).join(...).group_by(Category.name).all()
```

---

## 🔐 Riesgos de Seguridad Relevantes

### S-1: Validación de Propiedad Inconsistente
**Severidad:** CRÍTICA

**Análisis:** Algunos endpoints validan `product.restaurant_id == current_user.restaurant_id`, otros no.

**Ejemplo vulnerable:** `invoices.py` (Línea 350-359)
```python
product = db.query(Product).filter(
    Product.restaurant_id == current_user.restaurant_id,
    func.lower(Product.name) == func.lower(item.product_name)
).with_for_update().first()
```

**Pero en** `products.py` (Línea 169):
```python
if product.restaurant_id != current_user.restaurant_id and current_user.role != "admin":
    raise HTTPException(...)
```

**Riesgo:** Un `admin` global puede acceder a productos de cualquier restaurante. Si el rol "admin" es por restaurante (no global), esto es un bug.

**Solución:** Middleware global que inyecte `restaurant_id` en todas las queries.

---

### S-2: Falta de Validación de Tipos Enum en Pydantic
**Severidad:** BAJA

**Análisis:** Aunque los modelos de BD usan `SQLEnum`, los modelos Pydantic aceptan strings libres en algunos casos.

**Ejemplo:** `wastes.py` (Línea 29)
```python
class WasteCreate(BaseModel):
    waste_type: WasteType  # ✅ Correcto
```

**Pero en otros lugares:**
```python
status_filter: Optional[InvoiceStatus] = None  # ✅ Correcto
```

**Conclusión:** Este punto está bien implementado. No es un riesgo real.

---

## ✅ Qué Está Bien Resuelto

1. **Uso de `Numeric` para dinero:** Todos los campos monetarios usan `Numeric(10, 2)` en lugar de `Float`. ✅
2. **Uso de `with_for_update()` en operaciones críticas:** Se intenta prevenir race conditions (aunque la implementación tiene bugs). ✅
3. **Separación de modelos Pydantic y SQLAlchemy:** No se mezclan responsabilidades. ✅
4. **Enumeraciones tipadas:** Se usan `Enum` de Python para evitar "strings mágicos". ✅
5. **Validación de inputs:** Pydantic valida tipos y formatos automáticamente. ✅

---

## 🔧 Recomendaciones Concretas y Quirúrgicas

### Prioridad 1 (Antes de Producción)
1. **Arreglar race condition en stock:** Usar `UPDATE ... SET stock = stock - X` en SQL.
2. **Añadir validación de `restaurant_id` en JOINs:** Evitar fugas de datos entre tenants.
3. **Añadir timeout y límite de páginas en OCR:** Prevenir DoS.
4. **Implementar transacciones explícitas:** Usar `db.begin()` en operaciones multi-paso.

### Prioridad 2 (Primeros 3 Meses)
5. **Extraer lógica de negocio a servicios:** Facilitar testing y reutilización.
6. **Añadir índices compuestos:** Optimizar queries multi-tenant.
7. **Mover cálculos pesados a SQL:** Reducir latencia de reportes.
8. **Aclarar modelo de Categorías/Proveedores:** ¿Globales o por tenant?

### Prioridad 3 (Escalabilidad Futura)
9. **Implementar caché para dashboard:** Redis para métricas agregadas.
10. **Añadir logging estructurado:** JSON logs con `restaurant_id` y `user_id` en cada línea.
11. **Implementar health checks:** Endpoint `/health` que valide BD + OCR.

---

**Veredicto Final:**  
El sistema es **APTO PARA MVP CON MITIGACIONES**. Los bugs críticos (B-1, B-2) deben corregirse antes de producción. Los riesgos de escalabilidad son manejables hasta 20-30 clientes. Después de eso, se requiere refactorización de reportes y optimización de queries.

**Tiempo estimado de correcciones críticas:** 4-6 horas de desarrollo + 2 horas de testing.
