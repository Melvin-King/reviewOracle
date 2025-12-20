"""
LLM API 客户端封装
支持 OpenAI 和 Anthropic
"""

import os
from typing import Dict, List, Optional
from openai import OpenAI
import anthropic


class LLMClient:
    """统一的 LLM 客户端接口"""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, 
                 model: str = "gpt-4", temperature: float = 0.3, base_url: Optional[str] = None):
        """
        Args:
            provider: LLM 提供商，"openai", "anthropic", 或 "deepseek"
            api_key: API 密钥，如果为 None 则从环境变量读取
            model: 模型名称
            temperature: 温度参数
            base_url: API 基础 URL（用于 DeepSeek 等自定义端点）
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        
        if api_key is None or api_key == "":
            # 尝试从环境变量读取
            env_key = f"{provider.upper()}_API_KEY"
            api_key = os.getenv(env_key)
        
        # 验证 API key
        if not api_key:
            raise ValueError(
                f"未找到 {provider} API key。请设置环境变量 {provider.upper()}_API_KEY "
                f"或在配置文件中提供 api_key。"
            )
        
        if provider == "openai":
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        elif provider == "deepseek":
            # DeepSeek 使用 OpenAI 兼容的 API
            deepseek_base_url = base_url or "https://api.deepseek.com"
            self.client = OpenAI(api_key=api_key, base_url=deepseek_base_url)
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"不支持的提供商: {provider}。支持: openai, anthropic, deepseek")
    
    def call(self, prompt: str, system_prompt: Optional[str] = None, 
             max_tokens: int = 2000) -> str:
        """
        调用 LLM
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_tokens: 最大 token 数
            
        Returns:
            LLM 响应文本
        """
        if self.provider in ["openai", "deepseek"]:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM 返回了空响应")
            return content
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            if not response.content or len(response.content) == 0:
                raise ValueError("LLM 返回了空响应")
            return response.content[0].text
    
    def batch_call(self, prompts: List[str], system_prompt: Optional[str] = None) -> List[str]:
        """
        批量调用 LLM
        
        Args:
            prompts: 提示列表
            system_prompt: 系统提示
            
        Returns:
            响应列表
        """
        return [self.call(p, system_prompt) for p in prompts]

