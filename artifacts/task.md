# Tareas: Auditoría y Refactorización (Inventario Enterprise)

- [x] **Fase 0: Auditoría y Diagnóstico**
    - [x] Explorar estructura de archivos y dependencias <!-- id: 0 -->
    - [x] Análisis de Integridad de Datos (Decimales, Concurrencia, FKs) <!-- id: 1 -->
    - [x] Análisis de Arquitectura (Modularidad, Secretos, Auth) <!-- id: 2 -->
    - [x] Análisis de Calidad de Código (Alucinaciones, UI/Lógica, Mantenibilidad) <!-- id: 3 -->
    - [x] Generar reporte `ANALISIS_INICIAL_KIMI.md` <!-- id: 4 -->

- [x] **Fase 1: Cimientos de Datos (Integridad y Matemáticas)**
    - [x] **DB Models**: Migrar campos monetarios de `Float` a `DECIMAL` en `backend/models/database.py` <!-- id: 5 -->
    - [x] **Pydantic**: Actualizar esquemas de validación en `backend/api/*.py` <!-- id: 6 -->
    - [x] **Atomicidad**: Implementar `StockMovement` granular (evitar race conditions) <!-- id: 7 -->

- [x] **Fase 2: Lógica de Negocio (Robusta)**
    - [x] **Enums**: Implementar Enums para tipos de movimiento y mermas (evitar "strings mágicos") <!-- id: 10 -->
    - [x] **Stock Negativo**: Implementar Checks para prevenir inventario negativo <!-- id: 9 -->

- [x] **Fase 3: Validación y QA**
    - [x] **Script de Prueba**: Script integral ejecutado. (Nota: Concurrencia requiere Postgres) <!-- id: 8 -->

- [x] **Fase 4: Dashboard y UI (Pulido)**
    - [x] **Backend Dashboard**: Refactorizar `dashboard.py` (Enums + Decimales puros) <!-- id: 11 -->
    - [x] **Frontend Audit**: Blindaje de `utils.js` para manejo de Decimales/Strings <!-- id: 12 -->

- [x] **Fase 5: Reportes y Exportación** (PDF/Excel)
- [x] **Fase 6: Infraestructura de Producción** (PostgreSQL + Tesseract)
- [x] **Fase 7: Gestión SaaS** (Admin Panel + Multi-tenancy)
- [x] **Fase 8: UX Móvil y Documentación** (Manual, Presentación y Mobile Count)

<!-- POSTERGADO: Auth y Seguridad (Solo al final) -->
<!-- - Configurar Variables de Entorno (.env) -->
<!-- - Hardening de JWT -->
