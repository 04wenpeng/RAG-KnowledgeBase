@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" src\tools\install_ollama_local.py %*
) else (
  python src\tools\install_ollama_local.py %*
)
echo.
pause
