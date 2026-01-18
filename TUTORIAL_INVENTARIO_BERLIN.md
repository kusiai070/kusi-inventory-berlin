# 📚 TUTORIAL SISTEMA INVENTARIO RESTAURANTE - GUÍA COMPLETA

> **Versión del Manual:** 1.0 (Enero 2026)  
> **Sistema:** Kusi Inventory Enterprise (Berlin Edition)  
> **Objetivo:** Dominar el control total de tu inventario, desde el ingreso de productos hasta la detección de fraudes.

---

## 🎯 ÍNDICE
1. [Acceso al Sistema](#1-acceso-al-sistema)
2. [Dashboard Principal: Tu Centro de Mando](#2-dashboard-principal)
3. [Gestión de Productos: El Corazón del Sistema](#3-gestión-de-productos)
4. [Registro de Compras y Facturas (OCR)](#4-registro-de-compras-y-facturas-ocr)
5. [Control de Mermas y Desperdicios](#5-control-de-mermasdesperdicios)
6. [Alertas de Stock y Reabastecimiento](#6-alertas-de-stock)
7. [Reportes y Análisis Financiero](#7-reportes-y-análisis)
8. [🛡️ Detección de Anomalías (Anti-Fraude)](#8-detección-de-anomalías-fraudes)
9. [Configuración de Usuarios y Roles](#9-configuración-usuarios)
10. [Solución de Problemas Frecuentes](#10-solución-de-problemas)

---

## 1️⃣ ACCESO AL SISTEMA

### 🔗 ¿Dónde entro?
Accede desde cualquier navegador (Chrome, Edge, Safari) a la siguiente dirección:  
👉 **https://kusi-inventory-berlin.onrender.com**

### 🔑 Tus Llaves de Acceso (Credenciales)
El sistema tiene diferentes niveles de acceso. Usa el que corresponda a tu rol:

| Rol | Correo (Usuario) | Contraseña | ¿Qué puede hacer? |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@RestauranteElSol.com` | `admin123` | Control Total, ver precios, crear usuarios, reportes financieros. |
| **Gerente (Manager)** | `manager@RestauranteElSol.com` | `manager123` | Gestión diaria, inventario, compras, reportes operativos. |
| **Staff/Personal** | `staff@RestauranteElSol.com` | `staff123` | Conteo físico y registro de mermas (sin ver costos sensibles). |

### 👣 Paso a Paso: Tu Primer Ingreso

1.  **Carga la Página:** Verás una pantalla limpia con el logo de "Enterprise Inventory" al centro.
2.  **Ingresa tus Datos:**
    *   En el campo "Correo Electrónico", escribe tu usuario (ej. `admin@RestauranteElSol.com`).
    *   En el campo "Contraseña", escribe tu clave.
    *   *Ojo:* Si estás en un dispositivo seguro, el navegador puede recordar estos datos.
3.  **Click en "Iniciar Sesión":** Pulsa el botón morado grande.
4.  **¡Dentro!** Si los datos son correctos, serás redirigido al Dashboard en menos de 2 segundos.

> **💡 Consejo Pro:** Guarda la página en tus "Favoritos" para acceder rápido cada mañana.

---

## 2️⃣ DASHBOARD PRINCIPAL: Tu Centro de Mando

Al entrar, aterrizas en el **Dashboard**. Piensa en esto como el tablero de tu coche: te dice cómo va el restaurante de un vistazo rápido.

### 🖼️ ¿Qué estoy viendo?

1.  **Barra Lateral (Izquierda):** Es tu menú de navegación. Desde aquí vas a todas partes (Inventario, Facturas, Reportes). Siempre está visible.
2.  **Selector de Restaurante (Arriba Derecha):** Si gestionas varios locales, aquí seleccionas cuál estás viendo (Ej. "Restaurante El Sol").
3.  **Selector de Idioma:** ¿Prefieres Inglés o Alemán? Cámbialo aquí.

### 📊 Las Gráficas Clave

*   **📉 Consumo Semanal:**
    *   *Lo visual:* Una línea que sube y baja mostrando cuánto dinero has gastado en insumos los últimos 7 días.
    *   *Para qué sirve:* Si ves un pico repentino ayer y no tuviste muchas ventas, ¡alerta! Algo pasó (robo, desperdicio masivo, o llegó un pedido grande).

*   **💰 Valor del Inventario (Tarjeta):** Te dice cuánto dinero tienes "parado" en tus estanterías hoy.
*   **⚠️ Alertas de Stock Bajo (Tarjeta):** Te avisa cuántos productos están a punto de acabarse. Si dice "5", corre a la sección de compras.

---

## 3️⃣ GESTIÓN DE PRODUCTOS: El Corazón del Sistema

Aquí es donde vive tu base de datos de ingredientes. Sin esto, no hay control.

### 📍 ¿Cómo llegar?
Click en **"Inventario"** en el menú lateral.

### 🔍 Encontrar un Producto
1.  Verás una barra de búsqueda arriba.
2.  Escribe "Tomate" o "Vodka".
3.  La lista se filtra automáticamente mientras escribes.
4.  También puedes filtrar por **Categoría** (Carnes, Licores, Limpieza) usando el menú desplegable.

### ➕ Crear un Nuevo Producto (Paso a Paso)
1.  Click en el botón azul **"+ Nuevo Producto"** (arriba a la derecha).
2.  Se abre una ventana (modal). Llena los datos:
    *   **Nombre:** Ej. "Aceite de Oliva Extra Virgen".
    *   **Categoría:** Ej. "Abarrotes".
    *   **Unidad:** ¿Cómo lo cuentas? (Litros, Kilos, Botellas, Unidades).
    *   **Stock Mínimo:** *CRÍTICO.* ¿Con cuánto te pones nervioso? Si pones "2", el sistema te avisará cuando te queden 2 botellas.
    *   **Costo Unitario:** Cuánto te cuesta a ti (sin IVA).
3.  Click en **"Guardar"**. ¡Listo!

### ✏️ Editar un Producto
¿Cambió el precio del limón?
1.  Busca "Limón".
2.  Click en el icono de **lápiz** a la derecha del producto.
3.  Cambia el precio.
4.  Guardar.

---

## 4️⃣ REGISTRO DE COMPRAS Y FACTURAS (OCR): Magia Automática

Olvídate de teclear facturas línea por línea. Usamos Inteligencia Artificial para leerlas.

### 📍 ¿Cómo llegar?
Click en **"Facturas OCR"** en el menú.

### 📤 Subir una Factura
1.  Toma una foto clara a la factura de tu proveedor o descarga el PDF.
2.  En la pantalla, verás un recuadro grande punteado que dice **"Arrastra tu factura aquí"**.
3.  Arrestra el archivo o haz click para buscarlo en tu PC.
4.  **Espera:** Una barra de carga aparecerá ("Procesando con IA...").
5.  **Revisión:** El sistema te mostrará qué leyó:
    *   Proveedor detectado.
    *   Fecha y Total.
    *   Items detectados (Ej. "10 Kilos de Harina").
6.  Si todo está OK, dale a **"Confirmar Ingreso"**.
    *   *Automaticamente:* El stock de Harina sube +10. El gasto se registra en reportes.

> **⚠️ Nota de Campo:** La IA es buena, pero no perfecta. Si la foto está borrosa o la factura está arrugada, puede fallar. Revisa siempre los totales antes de confirmar.

---

## 5️⃣ CONTROL DE MERMAS Y DESPERDICIOS

Aquí se registra lo que se tira a la basura. Es doloroso, pero necesario para saber cuánto pierdes.

### 📍 ¿Cómo llegar?
Click en **"Mermas"** (o ícono de basura) en el menú.

### 🗑️ Registrar una Pérdida
1.  Click en **"+ Registrar Merma"**.
2.  **Producto:** Busca "Tomate".
3.  **Cantidad:** "2" (Kilos).
4.  **Motivo:** Aquí sé sincero. Opciones:
    *   *Caducidad* (Se pudrió).
    *   *Error Cocina* (Se quemó, se cayó al piso).
    *   *Cortesía* (Invitación al cliente).
    *   *Robo/Desconocido*.
5.  **Guardar.**

### 📉 ¿Por qué hacer esto?
El sistema resta esos 2 kgs del inventario (para que cuadre el stock real) Y lo anota en el "Reporte de Pérdidas". A fin de mes sabrás cuánto dinero tiraste por "Errores de Cocina".

---

## 6️⃣ ALERTAS DE STOCK

El sistema te cuida las espaldas. No tienes que revisar todo el inventario diario.

### 🔔 ¿Cómo funcionan?
1.  El sistema mira tu **Stock Mínimo** (que configuraste en la sección 3).
2.  Si *Stock Actual* < *Stock Mínimo*:
    *   El producto sale en **Rojo** en la lista de inventario.
    *   Aparece una notificación en el Dashboard: "5 Productos Críticos".

### 📝 Generar Lista de Compra
*(Funcionalidad Pro)*
1.  Ve a inventario.
2.  Filtra por "Estado: Bajo Stock".
3.  Dale a "Exportar" -> "Lista de Compra PDF".
4.  Mándasela a tu proveedor.

---

## 7️⃣ REPORTES Y ANÁLISIS

La verdad sobre tu dinero.

### 📍 ¿Cómo llegar?
Click en **"Reportes"**.

### 📑 Tipos de Reportes
1.  **Inventario Valorizado:** ¿Cuánto vale todo lo que tengo en el almacén hoy? (Ideal para contabilidad).
2.  **Reporte de Mermas:** El "Muro de la Vergüenza". ¿Quién tiró más comida? ¿Qué insumo se pudre más?
3.  **Rotación de Producto:** ¿Qué se mueve más? (Tus productos estrella).
4.  **Historial de Compras:** Evolución de precios. ¿El proveedor te subió el precio del salmón sin avisar? Aquí lo verás.

### 🖨️ Exportar
Todos los reportes tienen un botón **"Descargar Excel"** arriba a la derecha. Úsalo para tus reuniones de cierre de mes.

---

## 8️⃣ 🛡️ DETECCIÓN DE ANOMALÍAS (ANTI-FRAUDE)

Esta es una característica exclusiva "Kusi Berlin". El sistema vigila patrones sospechosos en segundo plano.

### 🕵️ ¿Qué detecta?
*   **Consumos Fantasma:** Si se gastaron 50 Kilos de carne pero solo vendiste 10 hamburguesas.
*   **Precios Inflados:** Si siempre pagas $10 por el aceite y hoy registras una factura a $20.
*   **Mermas Recurrentes:** Si siempre se "rompen" botellas de vino caro los viernes noche.

### 🚨 ¿Dónde lo veo?
Si el sistema detecta algo grave, aparecerá una **"Alerta de Anomalía"** en tu Dashboard con un nivel de riesgo (Alta/Media).
Pincha en la alerta para ver el detalle: *"Posible robo hormiga detectado en Licores - Turno Noche"*.

---

## 9️⃣ CONFIGURACIÓN DE USUARIOS

Solo el **Admin** puede entrar aquí.

### 📍 ¿Cómo llegar?
Click en tu foto de perfil (abajo izquierda) -> **"Gestión de Usuarios"**.

### 👥 Crear Usuario
1.  Click "+ Nuevo Usuario".
2.  Correo y Contraseña temporal.
3.  **Rol:** Elige con cuidado.
    *   Dale *Staff* a los camareros/cocineros (solo conteo).
    *   Dale *Manager* al jefe de cocina/sala.
    *   Guarda *Admin* solo para dueños.

---

## 🔟 SOLUCIÓN DE PROBLEMAS (Troubleshooting)

### 🆘 "Se me olvidó la contraseña"
Por seguridad, el sistema no envía contraseñas por correo. Pide a un **Admin** que entre a la sección de Usuarios y te asigne una nueva contraseña temporal.

### 🆘 "La factura no carga / Da error al subir"
*   Verifica que sea **PDF, JPG o PNG**.
*   ¿Pesa más de 10MB? Intenta comprimirla.
*   ¿Es una foto? Asegúrate de que haya buena luz y no esté borrosa.

### 🆘 "El sistema va lento"
*   Generalmente es tu conexión a internet. Prueba abrir Google. Si Google vuela y Kusi no, contáctanos.
*   Limpia la caché de tu navegador (Control + F5).

### 🆘 "No veo los productos actualizados"
Dale al botón de **"Actualizar"** o recarga la página. A veces, si otro manager hizo cambios, tardan unos segundos en reflejarse en tu pantalla.

---

## ⚠️ PROBLEMAS CONOCIDOS (Versión Beta)
*   **Subida Masiva:** Aún no se pueden subir 50 facturas de golpe. Hay que ir una por una.
*   **Modo Offline:** Si se va internet, no se guardan los cambios. Asegúrate de tener conexión antes de guardar un inventario largo.

## 📞 SOPORTE TÉCNICO
¿Algo se rompió? ¿Tienes una duda existencial sobre el inventario?

*   **Contacto Directo:** Soporte Kusi AI
*   **Horario:** 24/7 (Sistemas críticos)
*   **Email:** soporte@kusiai.com

---

**Kusi Inventory Enterprise**  
*Simplicidad. Control. Rentabilidad.*
