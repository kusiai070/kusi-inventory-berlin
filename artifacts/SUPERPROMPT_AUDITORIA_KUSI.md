# 🔍 SUPERPROMPT: Auditoría Técnica y QA Enterprise (KusiSaaS)

Este prompt debe activarse ANTES de cualquier commit importante o despliegue. Detecta errores que los humanos (y otros modelos) suelen pasar por alto.

---

## 🎯 OBJETIVO
Garantizar que el código es robusto, escalable, no tiene redundancias y está listo para ser desplegado en cualquier entorno (Local o Docker/Cloud).

## 🕵️ DIRECTIVAS DE AUDITORÍA (PASO A PASO)

### 1. Verificación de Dependencias (El "Fallo Docker")
- **Sync Check**: Revisa el archivo `requirements.txt` y compáralo con TODOS los `import` del código. 
- **Missing Deps**: Informa si falta alguna librería (ej: `werkzeug`, `email-validator`, `python-jose`) que ya esté en el código pero no en la lista de instalación.

### 2. Integridad de Rutas y Estáticos
- **Path Reliability**: Verifica el uso de `os.path` o `pathlib`. Asegura que las rutas a carpetas de `frontend`, `static` o `uploads` sean robustas y funcionen tanto en local como dentro de una estructura de servidor (multi-nivel). Prohibir rutas hardcodeadas absolutas del PC local.

### 3. Calidad de Código y Redundancia
- **Líneas Duplicadas**: Busca bloques de código o argumentos repetidos accidentalmente (ej: `restaurant_id=restaurant_id` dos veces en una llamada).
- **Importaciones Huérfanas**: Detecta `NameError` potenciales (ej: usar `Query` de FastAPI sin haberlo importado).

### 4. Rendimiento y Concurrencia
- **Race Conditions**: Identifica actualizaciones de stock o balances que no usen `atomic updates` o `select_for_update()`.
- **N+1 Queries**: Busca bucles `for` que hagan consultas a la base de datos en cada iteración. Exige `join` o `eager loading`.

### 5. Estándares Enterprise
- **Tipado**: Asegurar uso de Pydantic para validación de entrada/salida.
- **Logs**: Verificar que no haya `print()` en producción; exigir el uso de la librería `logging`.
- **Manejo de Errores**: Todo endpoint debe tener bloques `try/except` que devuelvan códigos HTTP correctos (404, 400, 500) con mensajes claros.

---

## 🚩 FORMATO DE DEVOLUCIÓN
Para cada fallo técnico, responde con:
1. **Gravedad**: [BLOQUEANTE | ADVERTENCIA | OPTIMIZACIÓN]
2. **Diagnóstico**: Qué está mal técnicamente.
3. **Solución**: Código corregido y limpio.
