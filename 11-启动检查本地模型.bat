@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo.
echo   本地模型（按需启动，平时不占内存）
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" src\tools\ensure_ollama.py --status
  echo.
  ".venv\Scripts\python.exe" src\tools\ensure_ollama.py
  echo.
  ".venv\Scripts\python.exe" src\tools\ensure_ollama.py --status
) else (
  python src\tools\ensure_ollama.py --status
)
echo.
pause