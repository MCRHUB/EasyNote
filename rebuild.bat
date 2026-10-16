@echo off
chcp 65001 >nul
echo ================================================
echo   NoteBook - 一键重新生成图标 + 打包 + 重建快捷方式
echo ================================================
echo.
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo ❌ 未找到 venv\Scripts\python.exe，请先创建虚拟环境
    pause
    exit /b 1
)
echo 正在执行 rebuild.py ...
echo.
venv\Scripts\python.exe rebuild.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ 执行出错
    pause
    exit /b 1
)