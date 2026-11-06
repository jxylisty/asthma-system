@echo off
chcp 65001 >nul
cd /d "%~dp0"
title DongFang ZhiChuan - StartAll

echo ===============================
echo   DongFang ZhiChuan - Start All
echo ===============================
echo ROOT=%cd%
echo.

rem ========== [0/4] Environment Check ==========
echo [0/4] Checking environment...

verify >nul
where python >nul 2>&1
if not errorlevel 1 goto :python_ok
echo [X] python not found, please install Python 3.10+
pause
exit /b 1
:python_ok

verify >nul
where node >nul 2>&1
if not errorlevel 1 goto :node_ok
echo [X] node not found, please install Node.js 18+
pause
exit /b 1
:node_ok

verify >nul
where npm >nul 2>&1
if not errorlevel 1 goto :npm_ok
echo [X] npm not found
pause
exit /b 1
:npm_ok

if not exist "asthma-core\data\asthma_v2.db" (
    echo [X] Missing database: asthma-core\data\asthma_v2.db
    echo     Download from: https://github.com/jxylisty/asthma-core/releases
    echo     Extract asthma_v2.db.zip into asthma-core\data\
    pause
    exit /b 1
)

echo     [OK] python / node / npm / database
echo.

rem ========== [1/4] Backend Dependencies ==========
echo [1/4] Checking backend dependencies...

rem Check if venv exists and deps are installed
if not exist "asthma-core\.venv\Scripts\python.exe" goto :create_venv

rem Verify deps by importing fastapi (key dependency)
verify >nul
asthma-core\.venv\Scripts\python.exe -c "import fastapi" >nul 2>&1
if not errorlevel 1 goto :backend_done

rem Venv exists but deps missing, install them
echo     Venv exists but deps missing, installing...
goto :install_deps

:create_venv
echo     Creating virtual environment...
pushd "asthma-core"
verify >nul
python -m venv .venv
if errorlevel 1 goto :venv_fail
popd

:install_deps
echo     Installing requirements.txt (first run may be slow, includes RDKit)...
pushd "asthma-core"
verify >nul
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 goto :pip_fail
popd
echo     [OK] Backend dependencies installed
goto :backend_done

:venv_fail
echo [X] Failed to create virtual environment
popd
pause
exit /b 1

:pip_fail
echo [X] pip install failed. Try: conda install -c conda-forge rdkit
popd
pause
exit /b 1

:backend_done
echo     [OK] .venv ready
echo.

rem ========== [2/4] Frontend Dependencies ==========
echo [2/4] Checking frontend dependencies...
if exist "asthma-front\node_modules" goto :frontend_done

echo     Installing npm dependencies (first run may be slow)...
pushd "asthma-front"
verify >nul
call npm install
if errorlevel 1 goto :npm_install_fail
popd
echo     [OK] Frontend dependencies installed
goto :frontend_done

:npm_install_fail
echo [X] npm install failed
popd
pause
exit /b 1

:frontend_done
echo     [OK] node_modules ready
echo.

rem ========== [3/4] Start Backend ==========
echo [3/4] Starting backend (new window)...
start "Asthma Backend [FastAPI :8000]" /D "%cd%\asthma-core" cmd /k ".venv\Scripts\python.exe run.py"

rem ========== [4/4] Start Frontend ==========
echo [4/4] Starting frontend (new window)...
start "Asthma Frontend [Vite :5173]" /D "%cd%\asthma-front" cmd /k "npm run dev"

echo.
echo ===============================
echo   Launch sequence complete
echo ===============================
echo   Backend API :  http://localhost:8000
echo   API Docs   :  http://localhost:8000/docs
echo   Frontend   :  http://localhost:5173
echo.
echo   Close the respective windows to stop services
echo ===============================
echo.
pause
