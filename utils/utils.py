"""
工具模块 - 辅助函数
"""
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


def format_ai_conversation(message: str, role: str = "assistant") -> None:
    """
    格式化打印 AI 对话
    
    Args:
        message: 消息内容
        role: 角色 (user/assistant/system)
    """
    import sys
    import io
    
    prefix_map = {
        "user": "👤 用户",
        "assistant": "🤖 DeepSeek",
        "system": "⚙️ 系统"
    }
    prefix = prefix_map.get(role, "❓ 未知")
    
    # 处理 Windows 控制台编码问题
    try:
        print(f"\n{prefix}: {message}\n")
    except UnicodeEncodeError:
        # 如果编码失败，移除 emoji 重试
        simple_prefix_map = {
            "user": "[用户]",
            "assistant": "[DeepSeek]",
            "system": "[系统]"
        }
        simple_prefix = simple_prefix_map.get(role, "[未知]")
        print(f"\n{simple_prefix}: {message}\n")


def load_test_cases(testcase_dir: str = "testcase") -> List[Dict[str, Any]]:
    """
    加载测试用例（支持多个 JSON 文件）
    
    Args:
        testcase_dir: 测试用例目录路径（相对于项目根目录）
        
    Returns:
        测试用例列表（合并所有 JSON 文件中的用例）
    """
    testcase_path = Path(__file__).parent.parent / testcase_dir
    
    # 如果目录不存在，返回默认测试用例
    if not testcase_path.exists() or not testcase_path.is_dir():
        return get_default_test_cases()
    
    # 获取所有 JSON 文件
    json_files = list(testcase_path.glob("*.json"))
    
    if not json_files:
        # 如果没有找到 JSON 文件，返回默认测试用例
        return get_default_test_cases()
    
    all_test_cases = []
    
    # 遍历所有 JSON 文件并加载
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                test_cases = json.load(f)
                # 如果文件内容是列表，直接扩展
                if isinstance(test_cases, list):
                    all_test_cases.extend(test_cases)
                # 如果是字典且包含 test_cases 键，提取列表
                elif isinstance(test_cases, dict) and 'test_cases' in test_cases:
                    all_test_cases.extend(test_cases['test_cases'])
                else:
                    # 单个测试用例，包装成列表
                    all_test_cases.append(test_cases)
            
            format_ai_conversation(
                f"已加载测试用例文件: {json_file.name} ({len(test_cases) if isinstance(test_cases, list) else 1} 个用例)",
                "system"
            )
        except json.JSONDecodeError as e:
            format_ai_conversation(
                f"警告: 无法解析测试用例文件 {json_file.name}: {e}",
                "system"
            )
        except Exception as e:
            format_ai_conversation(
                f"警告: 加载测试用例文件 {json_file.name} 时出错: {e}",
                "system"
            )
    
    if not all_test_cases:
        # 如果所有文件都加载失败，返回默认测试用例
        format_ai_conversation("所有测试用例文件加载失败，使用默认测试用例", "system")
        return get_default_test_cases()
    
    format_ai_conversation(
        f"总共加载 {len(all_test_cases)} 个测试用例（来自 {len(json_files)} 个文件）",
        "system"
    )
    
    return all_test_cases


def save_test_cases(test_cases: List[Dict[str, Any]], file_path: str = "testcase/test_cases.json") -> None:
    """
    保存测试用例
    
    Args:
        test_cases: 测试用例列表
        file_path: 保存路径（相对于项目根目录）
    """
    test_cases_path = Path(__file__).parent.parent / file_path
    # 确保目录存在
    test_cases_path.parent.mkdir(parents=True, exist_ok=True)
    with open(test_cases_path, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)


def get_default_test_cases() -> List[Dict[str, Any]]:
    """
    获取默认测试用例（示例）
    
    Returns:
        默认测试用例列表
    """
    return [
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
            "name": "搜索功能测试",
            "description": "在百度搜索框中输入'Playwright'并搜索，验证搜索结果页面",
            "steps": [
                "导航到 https://www.baidu.com",
                "找到搜索框并输入'Playwright'",
                "点击搜索按钮",
                "等待搜索结果加载",
                "验证搜索结果页面包含相关内容"
            ]
        }
    ]


def parse_playwright_commands(ai_response: str) -> List[Dict[str, Any]]:
    """
    从 AI 响应中解析 Playwright 命令
    
    Args:
        ai_response: AI 返回的文本
        
    Returns:
        解析后的命令列表
    """
    commands = []
    lines = ai_response.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 简单的命令解析逻辑（可根据实际情况改进）
        if '导航' in line or 'goto' in line.lower() or 'navigate' in line.lower():
            # 提取 URL
            import re
            url_match = re.search(r'https?://[^\s\)]+', line)
            if url_match:
                commands.append({
                    "action": "goto",
                    "url": url_match.group()
                })
        elif '点击' in line or 'click' in line.lower():
            # 提取选择器或文本
            if '按钮' in line or 'button' in line.lower():
                commands.append({
                    "action": "click",
                    "selector": "button"
                })
            else:
                commands.append({
                    "action": "click",
                    "selector": line
                })
        elif '输入' in line or 'type' in line.lower() or 'fill' in line.lower():
            commands.append({
                "action": "type",
                "text": line
            })
        elif '等待' in line or 'wait' in line.lower():
            commands.append({
                "action": "wait",
                "timeout": 5000
            })
    
    return commands


def get_timestamp() -> str:
    """
    获取当前时间戳字符串
    
    Returns:
        格式化的时间戳
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_directory(path: str) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path 对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

