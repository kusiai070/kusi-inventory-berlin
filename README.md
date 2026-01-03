# Enterprise Restaurant Inventory System (SaaS)

Sistema de gestión de inventarios multi-tenant (SaaS) diseñado para cadenas de restaurantes, con soporte para OCR de facturas, concurrencia transaccional y reportes legales.

![Status](https://img.shields.io/badge/Status-Production-green)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-teal)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)

## 🚀 Características Enterprise

### 🏢 Arquitectura Multi-Tenant (SaaS)
*   **Aislamiento de Datos:** Cada restaurante (Inquilino) tiene sus datos lógicamente separados.
*   **Panel Super Admin:** Interfaz web (`/admin.html`) para dar de alta nuevos clientes (restaurantes) y suspender servicios en caliente.
*   **Roles RBAC:** Sistema de permisos granular (Super Admin, Dueño, Gerente, Personal).

### 🤖 Inteligencia Artificial & Automatización
*   **OCR de Facturas:** Motor Tesseract integrado para escanear facturas (PDF/Imágenes) y actualizar stock automáticamente.
*   **Detección de Anomalías:** Algoritmos para identificar mermas inusuales o robos (Consumo Real vs Teórico).

### 📊 Reportes Legales & Financieros
*   **Motor de Exportación:** Generación de documentos en **PDF** (firmables) y **Excel** (contables) al vuelo.
*   **Tipos de Reportes:** Valoración de Inventario, Rotación de Stock, Mermas, Compras y Consumo.

### 🛡️ Integridad & Seguridad
*   **Concurrencia Transaccional:** Uso de `PostgreSQL` con bloqueos pesimistas (`FOR UPDATE`) para evitar carreras de datos en actualizaciones de stock.
*   **Precisión Decimal:** Todos los cálculos financieros usan tipo de dato `Decimal` (no floats) para contabilidad exacta.
*   **Blindaje Frontend:** Interfaz tolerante a fallos de datos.

## 🛠️ Stack Tecnológico

*   **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0.
*   **Base de Datos:** PostgreSQL 15 (Producción), Redis 7 (Caché).
*   **Infraestructura:** Docker Compose, Tesseract OCR.
*   **Frontend:** Vanilla JS (Optimizado), TailwindCSS, Chart.js.

## 📦 Instalación y Despliegue

### Requisitos Previos
*   Docker y Docker Compose
*   (Opcional) Make

### Despliegue en Producción (Recomendado)

1.  **Clonar repositorio:**
    ```bash
    git clone https://github.com/tu-repo/restaurant-inventory-enterprise.git
    cd restaurant-inventory-enterprise
    ```

2.  **Configurar entorno:**
    ```bash
    # Copiar ejemplo de configuración
    cp .env.example .env
    # En Windows PowerShell: copy .env.example .env
    ```

3.  **Iniciar servicios:**
    ```bash
    docker-compose up -d --build
    ```
    *Esto levantará: API (Puerto 8000), PostgreSQL (5432) y Redis.*

3.  **Acceder al sistema:**
    *   **App Principal:** `http://localhost:8000`
    *   **Panel Super Admin:** `http://localhost:8000/static/admin.html`
    *   **Documentación API:** `http://localhost:8000/docs`

### Configuración Inicial (Seed)

Si despliegas desde cero, puedes ejecutar el script de inicialización para crear restaurantes de prueba:

```bash
docker-compose exec app python backend/scripts/setup_tenants.py
```

Esto creará:
*   **Cafetería Central** (User: `admin@cafeteria_central.com` / `admin123`)
*   **Pizzería Centro** (User: `admin@pizzeria_centro.com` / `admin123`)
*   **Pizzería Norte** (User: `admin@pizzeria_norte.com` / `admin123`)

## 📖 Guía de Uso Rápida

### 1. Gestión de Super Admin
*   Entra a `/static/admin.html`.
*   Usa el botón **"Nuevo Restaurante"** para dar de alta un cliente.
*   Define el nombre, email del administrador y contraseña.
*   El cliente ya puede entrar inmediatamente.

### 2. Carga de Facturas (OCR)
*   Ve a **"Gestión de Facturas"**.
*   Sube una foto o PDF de la factura.
*   El sistema leerá Proveedor, Fecha, Items y Totales.
*   Confirma los datos y el stock se sumará automáticamente.

### 3. Generación de Reportes
*   Ve a **"Reportes"**.
*   Selecciona un rango de fechas.
*   Haz clic en **"Exportar PDF"** para obtener el documento oficial.

## 📂 Estructura del Proyecto

```
/
├── backend/
│   ├── api/            # Endpoints (FastAPI)
│   ├── models/         # Modelos DB (SQLAlchemy)
│   ├── utils/          # Motores (OCR, Reportes, Cálculos)
│   └── scripts/        # Scripts de mantenimiento
├── frontend/           # UI (HTML/JS/CSS)
│   ├── js/             # Lógica cliente
│   └── admin.html      # Panel Super Admin
├── database/           # Migraciones y Schemas
├── docker-compose.yml  # Orquestación
└── Dockerfile          # Definición de contenedor App
```