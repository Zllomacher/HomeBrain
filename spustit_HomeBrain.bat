@echo off
chcp 65001 > nul
title HomeBrain Server

echo ========================================================
echo   🧠 Spouštím HomeBrain — Rodinný správce dokumentů
echo ========================================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [CHYBA] Virtuální prostředí venv nebylo nalezeno!
    echo Spusťte nejdříve: python -m venv venv a pip install -r requirements.txt
    pause
    exit /b 1
)

echo [OK] Spouštím server na http://localhost:8000 ...
echo [INFO] Pro ukončení serveru stiskněte Ctrl+C.
echo.

:: Otevření prohlížeče po 2 sekundách
start "" cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:8000"

:: Spuštění Uvicorn serveru
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
