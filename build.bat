@echo off
chcp 65001 >nul
title NoteBook - 打包为 Windows exe

rem ============================================================
rem  一键打包脚本
rem  - 使用 PyInstaller 把项目打包成独立 exe
rem  - 产物在 dist\NoteBook.exe
rem  - 用户电脑不需要安装 Python
rem ============================================================

cd /d "%~dp0"

echo ==========================================
echo    NoteBook 一键打包工具
echo ==========================================
echo.

rem ---- 1. 激活虚拟环境 ----
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [错误] 未找到 venv，请先运行 start.bat 初始化
    pause
    exit /b 1
)

rem ---- 2. 安装 PyInstaller ----
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [提示] 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

rem ---- 3. 清理旧构建 ----
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "NoteBook.spec" del /q NoteBook.spec

rem ---- 4. 开始打包 ----
echo.
echo [打包中] 请耐心等待，首次打包约需 1-3 分钟...
echo.

pyinstaller build.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请查看上方日志
    pause
    exit /b 1
)

rem ---- 5. 完成 ----
echo.
echo ==========================================
echo    打包完成！
echo    产物: dist\NoteBook.exe
echo.
echo    双击即可运行，无需 Python 环境
echo    建议连同 uploads\ 和 notebook.db 一起分发
echo ==========================================
echo.

if exist "dist\NoteBook.exe" (
    for %%A in ("dist\NoteBook.exe") do echo    exe 大小: %%~zA 字节
)

pause