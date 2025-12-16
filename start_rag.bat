@echo off
set "PROJECT_ROOT=%~dp0"
:: Remove trailing backslash if present
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

:: Set Hugging Face cache to local directory
set "HF_HOME=%PROJECT_ROOT%\backend\models"
if not exist "%HF_HOME%" mkdir "%HF_HOME%"

echo === Starting RAG Chatbot ===

echo Killing old processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting Backend...
cd /d "%PROJECT_ROOT%\backend"
start "RAG Backend" cmd /k ""%PROJECT_ROOT%\venv\Scripts\python.exe" -m uvicorn api.main:app --host 0.0.0.0 --port 8000"

timeout /t 10 /nobreak
echo Starting Frontend...
cd /d "%PROJECT_ROOT%\frontend"
start "RAG Frontend" cmd /k "npx vite --host"

timeout /t 5 /nobreak
echo.
echo === RAG Chatbot Started ===
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to open the app...
pause >nul
start http://localhost:5173

