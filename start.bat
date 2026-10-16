@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem ============================================================
rem  一键静默启动脚本
rem  - 首次运行: 创建 venv + 安装依赖
rem  - 后续运行: pythonw 后台启动 + 自动关闭自身窗口
rem  - 用户只看到 PyWebView 桌面窗口, 没有任何控制台
rem ============================================================

set "VENV_DIR=venv"
set "PYW=%VENV_DIR%\Scripts\pythonw.exe"
set "MAIN=main.py"

rem ---- 1. 首次运行: 创建 venv ----
if not exist "%PYW%" (
    if not exist "%VENV_DIR%\Scripts\activate.bat" (
        echo [首次运行] 创建虚拟环境...
        python -m venv %VENV_DIR%
        if errorlevel 1 (
            echo [错误] 创建失败, 请先安装 Python 3.9+
            pause
            exit /b 1
        )
    )
)

rem ---- 2. 检查依赖 ----
call "%VENV_DIR%\Scripts\activate.bat"
python -c "import flask, webview" 2>nul
if errorlevel 1 (
    echo [首次运行] 安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

rem ---- 3. 正式启动: pythonw 后台运行, 立即关闭本 bat ----
start "" "%PYW%" "%MAIN%"
exit /b