# 🕵️ Detección de Anomalías: Estadística Z-Score (MVP)

> **Estado:** Implementado (v1.0)
> **Método:** Estadística Robusta (Desviación Estándar)
> **Dependencias:** Ninguna (Python Standard Lib + SQLAlchemy)

## 🎯 Objetivo
Detectar fraudes, robos o errores en el registro de mermas (desperdicios) analizando el historial de comportamiento de cada producto.

## 🧮 Cómo funciona (Matemática)
El sistema utiliza el puntaje **Z-Score** para determinar qué tan lejos está un nuevo reporte del promedio histórico.

Formula:
```math
Z = \frac{x - \mu}{\sigma}
```
Donde:
*   `x`: Cantidad reportada (kg/unidades)
*   `μ`: Promedio de los últimos 30 días
*   `σ`: Desviación estándar histórica

### Umbrales de Alerta
| Z-Score | Severidad | Acción |
| :--- | :--- | :--- |
| > 3.0 | **CRÍTICA** | Alerta Inmediata. Desviación extrema (>99.7% probabilidad). |
| > 2.0 | **ALTA** | Anomalía fuerte. Revisión recomendada. |
| > 1.5 | **MEDIA** | Sospechoso. Monitorizar. |
| < 1.5 | NORMAL | Comportamiento habitual. |

## 🏗️ Arquitectura
1.  **Motor:** `backend/utils/anomaly_detector.py`
    *   Calcula estadísticas en tiempo real.
    *   No bloquea la petición principal (try/except wrapper).
2.  **Integración:** `backend/api/wastes.py`
    *   Intercepta cada `POST /wastes`.
    *   Inyecta el análisis antes de confirmar la transacción.
3.  **Alertas:** Tabla `alerts` en PostgreSQL.
    *   Queda registro persistente para el Dashboard.

## 🚀 Próximos Pasos (Roadmap IA)
*   [ ] Análisis de horarios (Detectar robos nocturnos).
*   [ ] Correlación con Ventas (¿Merma sube cuando ventas bajan?).
*   [ ] Isolation Forest (Para patrones no lineales).

---
*Implementado por Antigravity - Enero 2026*
