"""
AI 客户端管理器
支持多种 AI 服务提供商：DeepSeek、通义千问(Qwen)、GitHub Copilot

Author: Dongxiang.Zhang
Email: dongxiang699@163.com
"""
import os
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    import dashscope
    from dashscope import Generation
except ImportError:
    dashscope = None
    Generation = None


class AIClientBase(ABC):
    """AI 客户端基类
    
    Author: Dongxiang.Zhang
    Email: dongxiang699@163.com
    """
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息列表
            model: 模型名称（可选）
            temperature: 温度参数
            
        Returns:
            AI 返回的文本内容
            
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        pass


class DeepSeekClient(AIClientBase):
    """DeepSeek 客户端
    
    Author: Dongxiang.Zhang
    Email: dongxiang699@163.com
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", model: str = "deepseek-chat"):
        if AsyncOpenAI is None:
            raise ImportError("请安装 openai 包: pip install openai")
        
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        调用 DeepSeek API
        
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    async def close(self):
        """关闭客户端连接"""
        await self.client.close()

class QwenClient(AIClientBase):
    """通义千问 (Qwen) 客户端
    
    Author: Dongxiang.Zhang
    Email: dongxiang699@163.com
    """
    
    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        # 兼容 dashscope OpenAI 接口
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("请安装 openai 包: pip install openai")
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model = model

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        调用通义千问 API (OpenAI兼容模式)
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        # OpenAI Python SDK 兼容调用
        completion = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature
        )
        # 返回内容
        return completion.choices[0].message.content


class CopilotClient(AIClientBase):
    """GitHub Copilot 客户端（使用 OpenAI 兼容接口）
    
    Author: Dongxiang.Zhang
    Email: dongxiang699@163.com
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.githubcopilot.com/v1", model: str = "gpt-4"):
        if AsyncOpenAI is None:
            raise ImportError("请安装 openai 包: pip install openai")
        
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        调用 Copilot API
        
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content


class OpenAIClient(AIClientBase):
    """OpenAI 客户端（用于兼容其他 OpenAI 兼容的服务）
    
    Author: Dongxiang.Zhang
    Email: dongxiang699@163.com
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4"):
        if AsyncOpenAI is None:
            raise ImportError("请安装 openai 包: pip install openai")
        
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        调用 OpenAI API
        
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content


def create_ai_client(provider: str = None) -> AIClientBase:
    """
    创建 AI 客户端
    
    Args:
        provider: AI 服务提供商 (deepseek, qwen, copilot, openai)
                  如果为 None，则从环境变量 AI_PROVIDER 读取
        
    Returns:
        AI 客户端实例
        
    Raises:
        ValueError: 如果提供了不支持的提供商或缺少必要的配置
        
    Author: Dongxiang.Zhang
    Email: dongxiang699@163.com
    """
    if provider is None:
        provider = os.getenv("AI_PROVIDER", "deepseek").lower()
    
    provider = provider.lower()
    
    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量")
        
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        return DeepSeekClient(api_key, base_url, model)
    
    elif provider == "qwen":
        api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未设置 QWEN_API_KEY 或 DASHSCOPE_API_KEY 环境变量")
        
        model = os.getenv("QWEN_MODEL", "qwen-turbo")
        return QwenClient(api_key, model)
    
    elif provider == "copilot":
        api_key = os.getenv("COPILOT_API_KEY")
        if not api_key:
            raise ValueError("未设置 COPILOT_API_KEY 环境变量")
        
        base_url = os.getenv("COPILOT_BASE_URL", "https://api.githubcopilot.com/v1")
        model = os.getenv("COPILOT_MODEL", "gpt-4")
        return CopilotClient(api_key, base_url, model)
    
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("未设置 OPENAI_API_KEY 环境变量")
        
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4")
        return OpenAIClient(api_key, base_url, model)
    
    else:
        raise ValueError(f"不支持的 AI 提供商: {provider}。支持的提供商: deepseek, qwen, copilot, openai")