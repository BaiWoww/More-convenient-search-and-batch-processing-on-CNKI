@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   CNKI 论文检索助手 - 构建工具
echo ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 安装依赖
echo [1/4] 安装 Python 依赖...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo       完成

:: 安装 Playwright 浏览器
echo [2/4] 安装 Playwright Chromium 浏览器...
playwright install chromium
if %errorlevel% neq 0 (
    echo [警告] Chromium 安装失败，程序运行时可手动安装
)
echo       完成

:: 创建图标 (如果不存在)
if not exist assets (
    mkdir assets
)

:: 构建 EXE
echo [3/4] 使用 PyInstaller 打包...
pyinstaller build.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

:: 完成
echo [4/4] 构建完成!
echo.
echo ============================================
echo   输出目录: dist\CNKI_Desktop\
echo   可执行文件: dist\CNKI_Desktop\CNKI_Desktop.exe
echo ============================================
echo.
echo 注意: 首次运行 exe 时，如果未安装 Chromium 浏览器，
echo       程序会自动提示安装。
echo.
pause
