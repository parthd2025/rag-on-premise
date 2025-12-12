@echo off
echo === Starting RAG Chatbot ===

echo Killing old processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting Backend...
cd /d "D:\RAG ON PREMISE\backend"
start "RAG Backend" cmd /k "D:\RAG ON PREMISE\venv\Scripts\activate.bat && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"

timeout /t 10 /nobreak
echo Starting Frontend...
cd /d "D:\RAG ON PREMISE\frontend"
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

