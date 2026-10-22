@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
".venv\Scripts\python.exe" "src\web.py" --port 8000 --host 0.0.0.0 >> "server.log" 2>&1