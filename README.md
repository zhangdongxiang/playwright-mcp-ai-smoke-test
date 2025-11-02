# Playwright MCP UI 自动化测试项目

基于 Python + Playwright MCP + DeepSeek 的自然语言 UI 自动化测试框架

## 项目特性

- ✅ **自然语言测试用例**：使用中文描述测试步骤，AI 自动执行
- ✅ **多 AI 模型支持**：支持 DeepSeek、通义千问(Qwen)、GitHub Copilot、OpenAI
- ✅ **智能执行引擎**：AI 解析测试用例并执行 Playwright 操作
- ✅ **详细测试报告**：生成包含统计数据、饼图和失败截图的 HTML 报告
- ✅ **失败截图**：自动捕获失败测试用例的截图
- ✅ **测试统计**：完整的测试结果统计和可视化
- ✅ **跨平台支持**：支持 Windows、Linux、Mac 系统

## 项目结构

```
mcp-smoke-test/
├── reports/              # 测试报告目录
│   └── screenshots/      # 失败截图目录
├── testcase/             # 测试用例目录
│   └── test_cases.json   # 测试用例文件
├── log/                  # 日志文件目录
├── utils/                # 工具模块
│   ├── utils.py          # 辅助函数
│   └── report_generator.py  # 报告生成器
├── .env                  # 环境变量配置
├── client.py             # 主运行脚本
├── run.bat               # Windows 批处理启动文件（双击运行）
├── run.sh                # Linux/Mac Shell 启动脚本
├── check_dependencies.py # 依赖检查脚本
├── requirements.txt      # Python 依赖
└── README.md            # 项目说明
```

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器

**Windows:**
```bash
playwright install chromium
```

**Linux/Mac:**
```bash
python3 -m playwright install chromium
# 或
playwright install chromium
```

### 3. 配置环境变量

创建 `.env` 文件（如果还没有），可以选择使用以下任一 AI 服务提供商：

#### 方式一：使用 DeepSeek（默认）

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

#### 方式二：使用通义千问 (Qwen)

```env
AI_PROVIDER=qwen
QWEN_API_KEY=your_qwen_api_key_here
QWEN_MODEL=qwen-turbo
```

#### 方式三：使用 GitHub Copilot

```env
AI_PROVIDER=copilot
COPILOT_API_KEY=your_copilot_api_key_here
COPILOT_BASE_URL=https://api.githubcopilot.com/v1
COPILOT_MODEL=gpt-4
```

#### 方式四：使用 OpenAI

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

> 💡 提示：可以参考 `.env.example` 文件查看完整的配置示例。只需设置你需要的 AI 提供商的配置即可。

## 使用方法

### 1. 编写测试用例

可以在 `testcase/` 文件夹下创建一个或多个 JSON 文件，每个文件可以包含一个或多个测试用例。

**单个测试用例文件示例** (`testcase/test_cases.json`):
```json
[
  {
    "id": "TC001",
    "name": "访问百度首页",
    "description": "打开百度网站首页，验证页面标题包含'百度'",
    "steps": [
      "导航到 https://www.baidu.com",
      "验证页面标题包含'百度'"
    ]
  },
  {
    "id": "TC002",
    "name": "百度搜索功能测试",
    "description": "在百度搜索框中输入'Playwright'并搜索",
    "steps": [
      "导航到 https://www.baidu.com",
      "找到搜索框并输入'Playwright'",
      "点击搜索按钮"
    ]
  }
]
```

**多个测试用例文件**：
- `testcase/smoke_tests.json` - 冒烟测试用例
- `testcase/regression_tests.json` - 回归测试用例
- `testcase/functional_tests.json` - 功能测试用例

运行时，系统会自动扫描 `testcase/` 文件夹下的所有 `.json` 文件并合并执行所有测试用例。

### 2. 运行测试

#### Windows 系统

**方式一：双击运行（推荐）**

直接双击 `run.bat` 文件即可运行测试。批处理文件会自动：
- 检查 Python 环境
- 检查并安装依赖
- 检查并安装 Playwright 浏览器
- 执行测试用例
- 显示测试结果

**方式二：命令行运行**

```bash
python client.py
```

或者使用批处理文件：

```bash
run.bat
```

#### Linux/Mac 系统

**方式一：使用 Shell 脚本（推荐）**

```bash
# 赋予执行权限（首次运行需要）
chmod +x run.sh

# 运行测试
./run.sh
```

**方式二：直接运行 Python 脚本**

```bash
python3 client.py
```

### 3. 查看报告

测试完成后，在 `reports/` 目录下会生成 HTML 报告，直接在浏览器中打开即可。

## 测试用例格式

每个测试用例包含以下字段：

- `id`: 测试用例唯一标识符
- `name`: 测试用例名称
- `description`: 测试用例描述
- `steps`: 测试步骤列表（自然语言描述）

### 支持的测试步骤关键词

- **导航相关**：导航到、打开、访问
- **输入相关**：输入、填写、填入
- **点击相关**：点击、选择
- **验证相关**：验证、检查、确认
- **等待相关**：等待、暂停

## 测试报告

测试报告包含以下内容：

1. **统计卡片**：总测试数、通过数、失败数、总耗时
2. **饼图**：测试结果分布可视化
3. **测试详情**：每个测试用例的详细执行信息
   - 测试步骤执行情况
   - 错误信息（如果有）
   - 失败截图（如果失败）

## 示例

### 示例测试用例

```json
{
  "id": "TC002",
  "name": "百度搜索功能测试",
  "description": "在百度搜索框中输入'Playwright'并搜索，验证搜索结果页面",
  "steps": [
    "导航到 https://www.baidu.com",
    "找到搜索框并输入'Playwright'",
    "点击搜索按钮",
    "等待搜索结果加载",
    "验证搜索结果页面包含相关内容"
  ]
}
```

### 运行示例

```bash
$ python client.py

🤖 DeepSeek: 开始执行测试用例
👤 用户: 开始执行测试: 访问百度首页 (TC001)
✅ 测试完成: 访问百度首页 (5.23秒)
👤 用户: 开始执行测试: 百度搜索功能测试 (TC002)
✅ 测试完成: 百度搜索功能测试 (8.45秒)
📊 测试报告已生成: reports/test_report_20241101_210530.html
```

## 注意事项

1. **API Key 安全**：不要将 `.env` 文件提交到版本控制系统
2. **网络连接**：确保可以访问 DeepSeek API 和测试目标网站
3. **浏览器选择**：默认使用 Chromium，可以在 `client.py` 中修改
4. **截图存储**：失败截图保存在 `reports/screenshots/` 目录

## 故障排除

### 问题：无法连接到 DeepSeek API

**解决方案**：
- 检查 `.env` 文件中的 API Key 是否正确
- 确认网络连接正常
- 验证 API Key 是否有效

### 问题：Playwright 浏览器未安装

**解决方案**：
```bash
playwright install chromium
```

### 问题：测试执行失败但无截图

**解决方案**：
- 检查 `reports/screenshots/` 目录是否存在
- 确认有写入权限

## 技术栈

- **Python 3.8+**
- **Playwright**：浏览器自动化
- **OpenAI SDK**：DeepSeek API 客户端
- **Matplotlib**：图表生成
- **HTML/CSS**：报告渲染

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

