# 🚨 ANALISIS_INICIAL_KIMI.md - Auditoría "Verdad Brutal"

**Fecha:** 02/01/2026
**Auditor:** Antigravity (Google Deepmind Team)
**Estado del Código:** 🔴 **ROTO / PELIGROSO** (No apto para producción Enterprise)

---

## 🚦 Semáforo de Estado

| Categoría | Estado | Veredicto |
| :--- | :---: | :--- |
| **Integridad de Datos** | 🔴 | **CRÍTICO**. Pérdida de dinero y stock garantizada. |
| **Seguridad** | 🔴 | **CRÍTICO**. Secretos expuestos código duro. |
| **Arquitectura** | 🟡 | **ACEPTABLE**. Estructura modular decente, pero implementación ingenua. |
| **Frontend** | 🟡 | **BÁSICO**. HTML/JS Vainilla. Funcional pero difícil de escalar. |

---

## 💀 Top 3 Riesgos Críticos (Business Killers)

### 1. El "Efecto Superman 3" (Float en Dinero) 💸
**El Problema:** Kimi definió todos los campos monetarios (`cost_price`, `selling_price`, `total`) como `Float` en `database.py`.
**Por qué es grave:** Los floats tienen errores de precisión (ej: `0.1 + 0.2 = 0.30000000000000004`). En un "Enterprise Inventory", esto causará desajustes contables acumulativos de centavos que descuadrarán la caja y los impuestos.
**Solución:** Migrar todo a `DECIMAL(10, 2)` o `Numeric`.

### 2. Inventario "Fantasma" (Condición de Carrera) 👻
**El Problema:** En `wastes.py` (Línea 103) y `invoices.py`, el stock se actualiza con lógica Python:
```python
product.current_stock -= waste.quantity  # LECTURA y ESCRITURA separadas
db.commit()
```
**Por qué es grave:** Si dos camareros registran una merma o venta simultáneamente (milisegundos de diferencia), ambos leerán el *mismo* stock inicial. El último en escribir sobrescribirá el cambio del primero.
**Resultado:** El inventario físico nunca coincidirá con el del sistema.
**Solución:** Usar actualizaciones atómicas a nivel de BD (`UPDATE products SET stock = stock - X`) o bloqueo de filas (`with_for_update`).

### 3. Puertas Abiertas (Secretos Hardcodeados) 🔓
**El Problema:** Archivo `backend/api/auth.py` (Línea 24):
```python
SECRET_KEY = "your-secret-key-here-change-in-production"
```
**Por qué es grave:** Si esto llega a git (y ya está), cualquiera puede generar tokens JWT falsos y loguearse como Admin.
**Solución:** Cargar estrictamente desde Variables de Entorno (`os.getenv`). Fallar si no existen.

---

## 🛠️ Plan de Refactorización (De "Juguete" a "Enterprise")

Propongo ejecutar esta cirugía en 3 fases estrictas:

### FASE 1: Cimientos de Datos (La Prioridad)
- [ ] **Refactor de Modelos**: Cambiar todos los `Float` monetarios a `DECIMAL`.
- [ ] **Atomicidad**: Reescribir la lógica de actualización de stock en `StockMovement` para usar expresiones SQL en lugar de aritmética Python.
- [ ] **Seguridad Config**: Crear `config.py` y `.env` para sacar secretos del código.

### FASE 2: Lógica Robusta
- [ ] **Validación Estricta**: Asegurar que no se permitan stocks negativos (Constraint Check en DB).
- [ ] **Roles Enums**: Cambiar roles de strings "sueltos" a Enum estricto.

### FASE 3: UI/UX (Futuro)
- [ ] Mantener el frontend HTML simple por ahora, pero conectar la API refactorizada.

---

**CONCLUSIÓN:**
Kimi nos dio un "esqueleto" visualmente correcto pero con osteoporosis en los huesos (la base de datos). **NO se puede construir sobre esto sin arreglar la capa de datos primero.**

### ¿Instrucciones?
Espero tu **OK** para proceder con la **FASE 1: Cimientos de Datos**.
