@echo off
echo Starting Cloud Migration Optimizer...

cd /d "%~dp0"

echo Creating virtual environment...
python -m venv .venv

echo Installing dependencies...
.venv\Scripts\pip install -r backend\requirements.txt

echo Starting backend on port 5055...
start "Backend" .venv\Scripts\python -m flask --app backend.app:app run --host 127.0.0.1 --port 5055

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Starting frontend on port 8080...
cd frontend
start "Frontend" ..\\.venv\Scripts\python -m http.server 8080 --bind 127.0.0.1

echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:8080

echo Both servers started. Check the opened windows.
pause