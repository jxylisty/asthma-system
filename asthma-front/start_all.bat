@echo off
chcp 65001 >nul
echo ===============================
echo  Asthma Frontend Project
echo ===============================
echo.

cd /d "%~dp0"

if not exist "node_modules" (
    echo [1/2] Installing dependencies...
    echo.
    npm install
    echo.
)

echo [2/2] Starting frontend dev server...
echo.
npm run dev

pause