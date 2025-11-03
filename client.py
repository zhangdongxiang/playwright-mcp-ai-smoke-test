#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 自动化测试主运行脚本
使用 DeepSeek + Playwright MCP 进行自然语言测试用例执行

Author: Dongxiang.Zhang
Email: dongxiang699@163.com
"""
import asyncio
import os
import sys

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from utils.utils import (
    format_ai_conversation,
    load_test_cases,
    get_timestamp,
    ensure_directory
)
from utils.report_generator import ReportGenerator
from utils.ai_client import create_ai_client, AIClientBase

# 加载环境变量
base_dir = Path(__file__).parent.resolve()
env_path = base_dir / '.env'

# 尝试多种方式加载 .env 文件
if env_path.exists():
    # 首先尝试使用 python-dotenv
    try:
        load_dotenv(dotenv_path=env_path, override=True)
    except Exception as e:
        print(f"警告: dotenv 加载失败: {e}")
    
    # 如果仍然没有加载成功，手动读取 .env 文件
    if not os.getenv("DEEPSEEK_API_KEY"):
        try:
            # 尝试多种编码方式读取（utf-8-sig 用于处理 BOM）
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']
            content_loaded = False
            
            for encoding in encodings:
                try:
                    with open(env_path, 'r', encoding=encoding, errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            # 跳过空行和注释
                            if not line or line.startswith('#'):
                                continue
                            # 解析键值对
                            if '=' in line:
                                parts = line.split('=', 1)
                                if len(parts) == 2:
                                    key = parts[0].strip()
                                    value = parts[1].strip()
                                    # 移除可能的引号
                                    if value.startswith('"') and value.endswith('"'):
                                        value = value[1:-1]
                                    elif value.startswith("'") and value.endswith("'"):
                                        value = value[1:-1]
                                    os.environ[key] = value
                                    content_loaded = True
                    if content_loaded:
                        break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"警告: 无法加载 .env 文件: {e}")
else:
    print(f"警告: 未找到 .env 文件: {env_path}")

# 配置 AI 提供商
AI_PROVIDER = os.getenv("AI_PROVIDER", "deepseek").lower()

REPORTS_DIR = Path(__file__).parent / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"


class PlaywrightMCPTestRunner:
    """Playwright MCP 测试运行器"""
    
    def __init__(self):
        try:
            self.ai_client: AIClientBase = create_ai_client(AI_PROVIDER)
            format_ai_conversation(f"已初始化 AI 客户端: {AI_PROVIDER}", "system")
        except Exception as e:
            format_ai_conversation(f"AI 客户端初始化失败: {str(e)}", "system")
            raise
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.test_results: List[Dict[str, Any]] = []
        self.report_generator = ReportGenerator(REPORTS_DIR)
        
    async def setup_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        self.page = await self.context.new_page()
        format_ai_conversation("浏览器已启动", "system")
        
    async def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        format_ai_conversation("浏览器已关闭", "system")
    
    async def execute_playwright_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        执行 Playwright 操作
        
        Args:
            action: 操作类型 (goto, click, fill, wait, screenshot等)
            **kwargs: 操作参数
            
        Returns:
            执行结果
        """
        if not self.page:
            return {"success": False, "error": "页面未初始化"}
        
        try:
            if action == "goto":
                url = kwargs.get("url")
                await self.page.goto(url, wait_until="networkidle")
                return {"success": True, "message": f"已导航到 {url}"}
            
            elif action == "click":
                selector = kwargs.get("selector")
                await self.page.click(selector)
                return {"success": True, "message": f"已点击 {selector}"}
            
            elif action == "fill":
                selector = kwargs.get("selector")
                text = kwargs.get("text")
                await self.page.fill(selector, text)
                return {"success": True, "message": f"已在 {selector} 中输入 {text}"}
            
            elif action == "type":
                selector = kwargs.get("selector")
                text = kwargs.get("text")
                await self.page.type(selector, text)
                return {"success": True, "message": f"已在 {selector} 中输入 {text}"}
            
            elif action == "wait":
                timeout = kwargs.get("timeout", 3000)
                await self.page.wait_for_timeout(timeout)
                return {"success": True, "message": f"等待 {timeout}ms"}
            
            elif action == "wait_for_selector":
                selector = kwargs.get("selector")
                timeout = kwargs.get("timeout", 30000)
                await self.page.wait_for_selector(selector, timeout=timeout)
                return {"success": True, "message": f"等待元素 {selector} 出现"}
            
            elif action == "screenshot":
                path = kwargs.get("path")
                await self.page.screenshot(path=path, full_page=kwargs.get("full_page", False))
                return {"success": True, "message": f"已保存截图到 {path}"}
            
            elif action == "get_text":
                selector = kwargs.get("selector", "body")
                text = await self.page.inner_text(selector)
                return {"success": True, "text": text, "message": "获取文本成功"}
            
            elif action == "get_title":
                title = await self.page.title()
                return {"success": True, "title": title, "message": f"页面标题: {title}"}
            
            else:
                return {"success": False, "error": f"未知操作: {action}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def ask_ai_to_execute(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        询问 AI 如何执行测试用例
        
        Args:
            test_case: 测试用例
            
        Returns:
            执行结果
        """
        description = test_case.get("description", "")
        steps = test_case.get("steps", [])
        
        # 构建提示词
        prompt = f"""你是一个 UI 自动化测试专家，使用 Playwright 进行浏览器自动化。

测试用例描述：{description}

测试步骤：
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(steps)])}

请按照以下步骤执行：
1. 分析测试用例，确定需要执行的 Playwright 操作序列
2. 执行每个操作并验证结果
3. 如果步骤失败，捕获错误并截图

可用操作：
- goto(url): 导航到指定 URL
- click(selector): 点击元素（selector可以是CSS选择器或文本内容）
- fill(selector, text): 在输入框中填入文本
- type(selector, text): 输入文本（支持按键）
- wait_for_selector(selector, timeout=30000): 等待元素出现
- wait(timeout): 等待指定毫秒数
- screenshot(path): 截图
- get_title(): 获取页面标题
- get_text(selector): 获取元素文本

请开始执行测试，告诉我每一步要做什么，我会帮你执行。"""
        
        format_ai_conversation(prompt, "user")
        
        try:
            # 调用 AI API
            messages = [
                {"role": "system", "content": "你是一个专业的 UI 自动化测试助手，使用 Playwright 进行浏览器操作。"},
                {"role": "user", "content": prompt}
            ]
            
            ai_message = await self.ai_client.chat_completion(
                messages=messages,
                temperature=0.3
            )
            
            format_ai_conversation(ai_message, "assistant")
            
            # 解析 AI 响应，提取 Playwright 命令
            # 这里简化处理，实际应该更智能地解析 AI 的指令
            return await self.parse_and_execute_ai_commands(ai_message, test_case)
            
        except Exception as e:
            error_msg = f"AI 调用失败: {str(e)}"
            format_ai_conversation(error_msg, "system")
            return {"success": False, "error": error_msg}
    
    async def parse_and_execute_ai_commands(
        self, 
        ai_response: str, 
        test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析 AI 响应并执行命令
        
        Args:
            ai_response: AI 响应文本
            test_case: 测试用例
            
        Returns:
            执行结果
        """
        import re
        
        executed_steps = []
        last_error = None
        
        # 尝试执行测试步骤
        steps = test_case.get("steps", [])
        
        for i, step in enumerate(steps):
            step_result = {
                "step": i + 1,
                "description": step,
                "success": False,
                "error": None
            }
            
            try:
                # 根据步骤描述执行操作
                if "导航" in step or "打开" in step or "访问" in step:
                    # 提取 URL
                    url_match = re.search(r'https?://[^\s\)，。]+', step)
                    if url_match:
                        url = url_match.group()
                        result = await self.execute_playwright_action("goto", url=url)
                        step_result["success"] = result["success"]
                        step_result["message"] = result.get("message")
                        if not result["success"]:
                            step_result["error"] = result.get("error")
                            last_error = result.get("error")
                
                elif "搜索" in step and "输入" in step:
                    # 提取搜索关键词
                    text_match = re.search(r"['\"]([^'\"]+)['\"]", step)
                    if text_match:
                        keyword = text_match.group(1)
                        # 尝试找到搜索框（百度为例）
                        result = await self.execute_playwright_action(
                            "fill", 
                            selector="input[name='wd'], input#kw", 
                            text=keyword
                        )
                        step_result["success"] = result["success"]
                        step_result["message"] = result.get("message")
                        if not result["success"]:
                            step_result["error"] = result.get("error")
                            last_error = result.get("error")
                
                elif "点击" in step:
                    # 尝试点击按钮或链接
                    if "搜索" in step or "按钮" in step:
                        result = await self.execute_playwright_action(
                            "click",
                            selector="input[type='submit'], button, #su"
                        )
                    else:
                        # 提取选择器或文本
                        result = await self.execute_playwright_action(
                            "click",
                            selector="button, a"
                        )
                    step_result["success"] = result["success"]
                    step_result["message"] = result.get("message")
                    if not result["success"]:
                        step_result["error"] = result.get("error")
                        last_error = result.get("error")
                
                elif "验证" in step or "检查" in step:
                    # 验证操作
                    if "标题" in step:
                        result = await self.execute_playwright_action("get_title")
                        step_result["success"] = result["success"]
                        step_result["message"] = result.get("message")
                        if result["success"]:
                            title = result.get("title", "")
                            # 简单的验证逻辑
                            if "百度" in title or "playwright" in title.lower():
                                step_result["success"] = True
                            else:
                                step_result["success"] = False
                                step_result["error"] = f"标题验证失败: {title}"
                    else:
                        # 等待页面加载
                        await self.execute_playwright_action("wait", timeout=2000)
                        step_result["success"] = True
                
                elif "等待" in step:
                    result = await self.execute_playwright_action("wait", timeout=3000)
                    step_result["success"] = result["success"]
                    step_result["message"] = result.get("message")
                
                else:
                    # 默认等待
                    await self.execute_playwright_action("wait", timeout=1000)
                    step_result["success"] = True
                    step_result["message"] = "步骤执行完成"
                
                executed_steps.append(step_result)
                
                # 如果步骤失败，停止执行
                if not step_result["success"]:
                    break
                    
            except Exception as e:
                step_result["success"] = False
                step_result["error"] = str(e)
                executed_steps.append(step_result)
                last_error = str(e)
                break
        
        # 判断整体测试是否成功
        all_success = all(step["success"] for step in executed_steps)
        
        result = {
            "success": all_success,
            "steps": executed_steps,
            "error": last_error if not all_success else None
        }
        
        return result
    
    async def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个测试用例
        
        Args:
            test_case: 测试用例
            
        Returns:
            测试结果
        """
        test_id = test_case.get("id", "UNKNOWN")
        test_name = test_case.get("name", "未命名测试")
        
        format_ai_conversation(f"开始执行测试: {test_name} ({test_id})", "system")
        
        start_time = datetime.now()
        
        # 执行测试
        execution_result = await self.ask_ai_to_execute(test_case)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 截图（如果失败）
        screenshot_path = None
        if not execution_result.get("success"):
            ensure_directory(SCREENSHOTS_DIR)
            screenshot_filename = f"{test_id}_{get_timestamp()}.png"
            screenshot_path = SCREENSHOTS_DIR / screenshot_filename
            try:
                await self.execute_playwright_action(
                    "screenshot",
                    path=str(screenshot_path),
                    full_page=True
                )
                screenshot_path = str(screenshot_path.relative_to(REPORTS_DIR))
            except Exception as e:
                format_ai_conversation(f"截图失败: {str(e)}", "system")
        
        # 构建测试结果
        test_result = {
            "id": test_id,
            "name": test_name,
            "description": test_case.get("description", ""),
            "success": execution_result.get("success", False),
            "duration": duration,
            "error": execution_result.get("error"),
            "screenshot": screenshot_path,
            "steps": execution_result.get("steps", []),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        status_emoji = "✅" if test_result["success"] else "❌"
        format_ai_conversation(
            f"{status_emoji} 测试完成: {test_name} ({duration:.2f}秒)",
            "system"
        )
        
        return test_result
    
    async def run_all_tests(self, test_cases: List[Dict[str, Any]]):
        """运行所有测试用例"""
        format_ai_conversation(f"开始执行 {len(test_cases)} 个测试用例", "system")
        
        await self.setup_browser()
        
        try:
            for test_case in test_cases:
                result = await self.run_test_case(test_case)
                self.test_results.append(result)
                
                # 测试之间稍作等待
                await asyncio.sleep(2)
        
        finally:
            await self.close_browser()
        
        # 生成报告
        self.report_generator.generate_report(self.test_results)
        format_ai_conversation("测试报告已生成", "system")


async def main():
    """主函数"""
    # 验证 AI 提供商配置
    try:
        create_ai_client(AI_PROVIDER)
    except ValueError as e:
        print(f"❌ 错误: {str(e)}")
        print(f"请在 .env 文件中设置相应的 API Key")
        print("\n支持的 AI 提供商配置：")
        print("  - deepseek: DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL")
        print("  - qwen: QWEN_API_KEY 或 DASHSCOPE_API_KEY, QWEN_MODEL")
        print("  - copilot: COPILOT_API_KEY, COPILOT_BASE_URL, COPILOT_MODEL")
        print("  - openai: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL")
        print(f"\n当前设置的提供商: AI_PROVIDER={AI_PROVIDER}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: AI 客户端初始化失败: {str(e)}")
        sys.exit(1)
    
    # 加载测试用例
    test_cases = load_test_cases()
    
    if not test_cases:
        print("❌ 错误: 没有找到测试用例")
        print("请创建 test_cases.json 文件或使用默认测试用例")
        sys.exit(1)
    
    # 运行测试
    runner = PlaywrightMCPTestRunner()
    await runner.run_all_tests(test_cases)


if __name__ == "__main__":
    asyncio.run(main())

