#!/bin/bash

# 设置编码和错误处理
set -e  # 遇到错误立即退出
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "   Playwright MCP UI 自动化测试"
echo "========================================"
echo ""

# 检查 Python 是否安装
echo "[1/4] 检查 Python 环境..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}[错误] 未检测到 Python，请先安装 Python 3.8 或更高版本${NC}"
    echo ""
    exit 1
fi

# 确定 Python 命令
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}[成功]${NC} $PYTHON_VERSION"

# 检查并安装项目依赖
echo ""
echo "[2/4] 检查项目依赖..."
if [ ! -f "check_dependencies.py" ]; then
    echo -e "${RED}[错误] 未找到 check_dependencies.py 文件${NC}"
    exit 1
fi

$PYTHON_CMD check_dependencies.py
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[错误] 依赖检查或安装失败${NC}"
    exit 1
fi

# 检查 .env 文件
echo ""
echo "[3/4] 检查环境变量配置..."
if [ ! -f ".env" ]; then
    echo -e "${RED}[错误] 未找到 .env 文件${NC}"
    echo "请创建 .env 文件并设置 DEEPSEEK_API_KEY"
    echo ""
    echo "示例内容:"
    echo "DEEPSEEK_API_KEY=your_api_key_here"
    echo "DEEPSEEK_BASE_URL=https://api.deepseek.com/v1"
    echo "DEEPSEEK_MODEL=deepseek-chat"
    exit 1
else
    echo -e "${GREEN}[成功]${NC} .env 文件存在"
fi

# 检查 Playwright 浏览器
echo ""
echo "[4/4] 检查 Playwright 浏览器..."
$PYTHON_CMD -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch(headless=True).close()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[警告]${NC} Playwright 浏览器未安装，正在安装..."
    if command -v playwright &> /dev/null; then
        playwright install chromium
    else
        $PYTHON_CMD -m playwright install chromium
    fi
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误]${NC} Playwright 浏览器安装失败"
        exit 1
    fi
    echo -e "${GREEN}[成功]${NC} Playwright 浏览器安装完成"
else
    echo -e "${GREEN}[成功]${NC} Playwright 浏览器已就绪"
fi

# 运行测试
echo ""
echo "[5/5] 开始运行测试..."
echo ""
$PYTHON_CMD client.py

# 检查执行结果
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[错误]${NC} 测试执行失败"
    exit 1
else
    echo ""
    echo "========================================"
    echo -e "    ${GREEN}测试执行完成！${NC}"
    echo "========================================"
    echo ""
    echo "测试报告位置: reports/test_report_*.html"
    echo ""
fi

