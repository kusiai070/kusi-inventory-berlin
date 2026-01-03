# 🛡️ Auditoría de Ciberseguridad: KusiSaaS Enterprise v1.0

**Fecha:** 03/01/2026
**Auditor:** Antigravity (Senior Security Auditor)
**Estado:** 🔴 **NO APTO PARA PRODUCCIÓN (BLOQUEADO)**

---

## 1. Superficie de Ataque
El sistema, al ser un SaaS multi-tenant expuesto a Internet, presenta los siguientes puntos de entrada:
*   **API REST (FastAPI):** Gestión de inventarios, reportes y administración.
*   **Motor OCR (Tesseract):** Procesamiento de archivos externos (JPG, PDF).
*   **Panel Super Admin:** Control de inquilinos (tenants).
*   **Capa de Autenticación:** Validación de tokens JWT.

---

## 2. Hallazgos Críticos (Riesgo Extremo)

### 🚨 V-C1: Secreto de JWT Hardcodeado
*   **Ubicación:** `backend/api/auth.py` (Línea 24)
*   **Análisis:** La clave para firmar tokens es una cadena estática en el código.
*   **Impacto:** Cualquier atacante con acceso al código puede generar sus propios tokens con rol `super_admin`, obteniendo acceso total a los datos de todos los restaurantes.

### 🚨 V-C2: Bypass de Seguridad "Backdoor" en Administrador
*   **Ubicación:** `backend/api/admin.py` (Líneas 50-53)
*   **Análisis:** El middleware de administrador valida si el `current_user.id == 1` para otorgar privilegios.
*   **Impacto:** Fallo masivo de lógica. Un usuario legítimo de un restaurante que reciba el ID 1 por secuencia de base de datos tendrá control sobre todo el SaaS.

### 🚨 V-C3: Política CORS Laxa
*   **Ubicación:** `backend/api/main.py` (Líneas 46-51)
*   **Análisis:** Se permite cualquier origen (`"*"`) con envío de credenciales.
*   **Impacto:** Exposición a ataques CSRF que permiten robar sesiones de usuarios activos.

---

## 3.Hallazgos Medios (Riesgo Significativo)

### ⚠️ V-M1: Ausencia de Rate Limiting
*   **Análisis:** El endpoint `/api/auth/login` permite intentos infinitos de contraseña.
*   **Impacto:** Riesgo de fuerza bruta exitosa contra cuentas de administrador.

### ⚠️ V-M2: Denegación de Servicio vía OCR
*   **Análisis:** No hay cuotas de tamaño o tiempo para el procesamiento OCR.
*   **Impacto:** "PDF Bombs" pueden saturar la CPU del contenedor, dejando el servicio inoperativo para todos los inquilinos.

---

## 4. Escenarios de Ataque Realistas

1.  **Exfiltración entre Inquilinos (IDOR):**
    Un dueño del "Restaurante A" modifica una ID de objeto en la API para ver los costes de compra del "Restaurante B", obteniendo información comercial confidencial de su competencia.

2.  **Secuestro de Tenant:**
    Un atacante usa el bypass del ID 1 para loguearse como administrador global y suspender las cuentas de restaurantes competidores para dañar su operativa.

---

## 5. Mitigaciones Obligatorias (Action Plan)

1.  **Variables de Entorno:** Mover `SECRET_KEY` y `DATABASE_URL` a archivos `.env`.
2.  **Autorización Estricta:** Reemplazar el chequeo de `ID == 1` por una validación estricta de roles y scopes en el token.
3.  **Aislamiento Global:** Inyectar automáticamente el `restaurant_id` en todas las consultas de base de datos para prevenir fugas accidentales.
4.  **Rate Limiting:** Implementar límites por IP en endpoints de autenticación.

---

**Veredicto Final:**
El sistema es funcionalmente brillante pero requiere un refuerzo de seguridad (Hardening) antes de recibir tráfico real de clientes externos.
