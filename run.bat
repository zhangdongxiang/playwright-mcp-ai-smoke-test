@echo off
chcp 65001 >nul
echo ========================================
echo    Playwright MCP UI 自动化测试
echo ========================================
echo.

REM 获取批处理文件所在目录
cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 或更高版本
    echo.
    pause
    exit /b 1
)

REM 检查并安装项目依赖
python check_dependencies.py
if errorlevel 1 (
    echo.
    echo [错误] 依赖检查或安装失败
    pause
    exit /b 1
)

REM 检查 .env 文件
echo [2/4] 检查环境变量配置...
if not exist ".env" (
    echo [错误] 未找到 .env 文件
    echo 请创建 .env 文件并设置 DEEPSEEK_API_KEY
    echo.
    echo 示例内容:
    echo DEEPSEEK_API_KEY=your_api_key_here
    echo DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
    echo DEEPSEEK_MODEL=deepseek-chat
    pause
    exit /b 1
) else (
    echo [成功] .env 文件存在
)

REM 检查 Playwright 浏览器
echo [3/4] 检查 Playwright 浏览器...
python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); b.close(); p.stop()" >nul 2>&1
if errorlevel 1 (
    echo [警告] Playwright 浏览器未安装，正在安装...
    python -m playwright install chromium >nul 2>&1
    if errorlevel 1 (
        echo [错误] Playwright 浏览器安装失败
        pause
        exit /b 1
    )
    echo [成功] Playwright 浏览器安装完成
) else (
    echo [成功] Playwright 浏览器已就绪
)

REM 运行测试
echo [4/4] 开始运行测试...
echo.
python client.py

REM 检查执行结果
if errorlevel 1 (
    echo.
    echo [错误] 测试执行失败
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo    测试执行完成！
    echo ========================================
    echo.
    echo 测试报告位置: reports\test_report_*.html
    echo.
)

REM 暂停，让用户查看结果
pause

