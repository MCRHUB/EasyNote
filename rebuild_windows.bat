@echo off
chcp 65001 >nul
echo ================================================
echo   NoteBook - Windows 一键打包
echo   产物: dist\windows\NoteBook.exe
echo ================================================
echo.
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ❌ 未找到 venv\Scripts\python.exe
    pause
    exit /b 1
)

venv\Scripts\python.exe rebuild_windows.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 执行出错
    pause
    exit /b 1
)