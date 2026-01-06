# ⚡ Instrucciones de Inicio Rápido

Sigue estos pasos para arrancar el sistema y empezar a probarlo.

---

## 📂 1. Ubicación del Proyecto
La carpeta raíz del sistema es:
`c:\Users\user\Desktop\restaurant_inventory_enterprise`

---

## 🚀 2. Comando para Iniciar

### Opción A: PowerShell (Recomendado)
Abre PowerShell en la carpeta del proyecto y ejecuta:
```powershell
.\boot.ps1
```

### Opción B: Símbolo del Sistema (CMD)
Si prefieres usar CMD, pega este comando:
```cmd
powershell -ExecutionPolicy Bypass -File .\boot.ps1
```
*(Este comando cerrará procesos antiguos en el puerto 8000 e iniciará el servidor limpio).*

---

## 🌐 3. Acceso al Sistema
Una vez iniciado, abre tu navegador favorito y entra en:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🔑 4. Usuarios de Prueba
| Rol | Email | Contraseña |
| :--- | :--- | :--- |
| **Administrador** | `admin@restauranteelsol.com` | `admin123` |
| **Gerente** | `manager@restauranteelsol.com` | `manager123` |
| **Personal** | `staff@restauranteelsol.com` | `staff123` |

---

## 🛠️ 5. Comandos Útiles
- **Resetear datos:** Si quieres borrar todo y volver a los datos de ejemplo originales, ejecuta:
  ```powershell
  python seed_db.py
  ```
- **Parar el servidor:** Presiona `Ctrl + C` en la terminal.

---

> [!IMPORTANT]
> Los archivos de ayuda y manuales están guardados en la carpeta `\artifacts` dentro del proyecto.
