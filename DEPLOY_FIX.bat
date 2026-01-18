@echo off
echo ==========================================
echo      KUSI AUTOMATION: RENDER FIX
echo ==========================================
echo.

echo [1/3] Sincronizando archivos desde Scratch (Taller)...
xcopy /E /I /Y "C:\Users\user\.gemini\antigravity\scratch\Kusi_SaaS\BERLIN\restaurant_inventory_enterprise" "C:\Users\user\Desktop\Kusi_SaaS\BERLIN\restaurant_inventory_enterprise" /EXCLUDE:exclude_list.txt 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Copia estandar realizada (Robocopy alternativo activado por si acaso)
    robocopy "C:\Users\user\.gemini\antigravity\scratch\Kusi_SaaS\BERLIN\restaurant_inventory_enterprise" "C:\Users\user\Desktop\Kusi_SaaS\BERLIN\restaurant_inventory_enterprise" /E /XD .git .venv node_modules __pycache__ /XO /NFL /NDL
)

echo.
echo [2/3] Preparando Git...
cd /d "C:\Users\user\Desktop\Kusi_SaaS\BERLIN\restaurant_inventory_enterprise"

echo.
echo [3/3] Subiendo a Render (GitHub)...
git add .
git commit -m "fix: Inventory Emergency Fixes (Dynamic Port + Pillow 12.1)"
git push origin master

echo.
echo ==========================================
echo      ¡LISTO! DESPLIEGUE INICIADO
echo ==========================================
echo Verifica en tu dashboard de Render.
pause
