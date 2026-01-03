@echo off
echo ===================================================
echo   KUSI SAAS ENTERPRISE - INICIANDO SERVIDORES
echo ===================================================
echo.
echo [1/3] Verificando Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker no esta instalado o no se encuentra en el PATH.
    echo Por favor instala Docker Desktop y vuelve a intentarlo.
    pause
    exit /b
)

echo [2/3] Levantando contenedores (Base de Datos + App)...
echo Esto puede tardar unos segundos...
docker-compose up -d

echo.
echo [3/3] LISTO! El sistema esta corriendo.
echo.
echo ===================================================
echo   PANEL PRINCIPAL: http://localhost:8000
echo   SUPER ADMIN:     http://localhost:8000/static/admin.html
echo ===================================================
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause
