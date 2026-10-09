@echo off
title AEMIIF - Stop Project Services
echo ==============================================================================
echo                 Stopping AEMIIF Project Services...
echo ==============================================================================
echo.

echo [*] Stopping Python / Uvicorn / Streamlit processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM uvicorn.exe /T 2>nul

echo [*] Stopping Node.js / Vite processes...
taskkill /F /IM node.exe /T 2>nul

echo.
echo [*] All services have been stopped.
ping 127.0.0.1 -n 3 >nul
exit /b 0
