@echo off
echo ===================================================
echo   KUSI SAAS ENTERPRISE - INICIANDO SISTEMA
echo ===================================================
echo.
echo Iniciando boot.ps1 (Gestion de puertos y arranque)...
powershell -ExecutionPolicy Bypass -File "boot.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Algo salio mal al iniciar.
    pause
)
