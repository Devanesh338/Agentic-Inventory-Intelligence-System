@echo off
setlocal enabledelayedexpansion
title AEMIIF - AI Smart Inventory Launcher

echo ==============================================================================
echo           AEMIIF - AI SMART INVENTORY AND PROCUREMENT SYSTEM
echo ==============================================================================
echo.

:: Detect directories cleanly without trailing backslashes
set "CURRENT_DIR=%~dp0"
if "%CURRENT_DIR:~-1%"=="\" set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

if exist "%CURRENT_DIR%\AI SMART INVENTORY\backend" (
    set "PROJECT_DIR=%CURRENT_DIR%\AI SMART INVENTORY"
) else (
    set "PROJECT_DIR=%CURRENT_DIR%"
)

cd /d "%PROJECT_DIR%"
echo [*] Project Directory: "%PROJECT_DIR%"

:: Check Python
set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo [*] Testing Python: "%PYTHON_EXE%"
"%PYTHON_EXE%" --version
if errorlevel 1 (
    echo [ERROR] Python was not found! Please ensure Python 3.11+ is installed in venv or on PATH.
    echo Press any key to exit...
    pause
    exit /b 1
)

:: Check Node and npm
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found on PATH! Please install Node.js 20+.
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm was not found on PATH!
    pause
    exit /b 1
)

:: Check Frontend Dependencies
if exist "%PROJECT_DIR%\frontend\node_modules" goto :deps_ready
echo [*] Installing frontend dependencies - please wait...
cd /d "%PROJECT_DIR%\frontend"
call npm install
cd /d "%PROJECT_DIR%"

:deps_ready
echo.
echo ==============================================================================
echo [*] Starting Services...
echo ==============================================================================
echo.

:: 1. Launch FastAPI Backend in a separate window
echo [*] Starting FastAPI Backend on http://localhost:8000 ...
start "AEMIIF Backend API - Port 8000" /D "%PROJECT_DIR%" cmd /k "%PYTHON_EXE%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

:: 2. Launch React Frontend in a separate window
echo [*] Starting React Frontend on http://localhost:5173 ...
start "AEMIIF React Frontend - Port 5173" /D "%PROJECT_DIR%\frontend" cmd /k npm run dev

:: 3. Launch Streamlit Dashboard in a separate window
echo [*] Starting Streamlit Dashboard on http://localhost:8501 ...
start "AEMIIF Streamlit UI - Port 8501" /D "%PROJECT_DIR%" cmd /k "%PYTHON_EXE%" -m streamlit run app.py --server.port 8501

:: Wait 4 seconds for services to spin up
echo [*] Waiting for services to initialize...
ping 127.0.0.1 -n 5 >nul

:: Open browsers
echo [*] Opening application interfaces in browser...
start http://localhost:5173
start http://localhost:8501

echo.
echo ==============================================================================
echo                     ALL SERVICES ARE RUNNING!
echo ==============================================================================
echo.
echo   - React Frontend:       http://localhost:5173
echo   - Streamlit Dashboard:  http://localhost:8501
echo   - Backend API Docs:     http://localhost:8000/docs
echo   - Backend API Health:   http://localhost:8000/api/v1/health
echo.
echo   [Tip] Keep the service command windows open while using the application.
echo   To stop all services, run stop_project.bat
echo ==============================================================================
echo.
echo Launcher running. Press any key to close this launcher window (services stay running).
pause >nul
