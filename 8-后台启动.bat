@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" src\tools\start_daemon.py 8000
) else (
  python src\tools\start_daemon.py 8000
)
start "" "http://127.0.0.1:8000/"
echo.
pause
