"""
VMDP Gemini 提供者 - Google Gemini 2.5 Flash 实现

该模块实现了 MusicAIProvider 抽象基类，提供对 Google Gemini API 的调用封装。
支持 Gemini 2.5 Flash 模型，用于音乐 Prompt 的智能处理。

使用新的 google.genai 包（原 google.generativeai 已弃用）
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from .llm_base import (
    BatchProcessingResult,
    ModelCapability,
    ModelConfig,
    MusicAIProvider,
    ProcessingResult,
    PromptContent,
    ProviderFactory,
    ProviderType,
    provider_decorator,
)
from .security import CircuitBreaker, CircuitBreakerRegistry


GEMINI_SYSTEM_PROMPT = """你是一个专业的音乐 Prompt 分析师。你的任务是将英文音乐 Prompt 转换为标准化的 VMDP 格式。

请按以下步骤处理：
1. 将英文内容翻译为中文，保持专业术语的准确性
2. 根据 Prompt 内容推断合适的 DSP 参数（BPM、调性、能量等级等）
3. 生成适合抖音平台的中文标签
4. 提供一条专业的音频处理建议

输出格式必须是严格的 JSON，包含以下字段：
{
    "title_zh": "中文标题",
    "prompt_zh": "中文 Prompt 翻译",
    "douyin_tags": ["标签1", "标签2", "标签3"],
    "dsp_params": {
        "bpm": 120,
        "key": "C Major",
        "energy_level": "medium",
        "frequency_center": "200Hz-2kHz",
        "dynamics_range": "Wide (40dB)"
    },
    "gem_suggestion": "专业的音频处理建议"
}"""


GEMINI_SUPPORTED_MODELS = [
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]

DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"


@provider_decorator("gemini")
class GeminiProvider(MusicAIProvider):
    """
    Google Gemini 提供者实现
    
    实现了 MusicAIProvider 抽象基类，提供对 Google Gemini API 的调用封装。
    支持 Gemini 2.5 Flash 模型，具备以下特性：
    
    - 自动 JSON 解析与验证
    - 熔断器保护
    - 速率限制支持
    - 批量处理优化
    - 健康检查
    
    Example:
        >>> provider = GeminiProvider(api_key="your-api-key")
        >>> provider.initialize()
        >>> content = PromptContent(
        ...     title="Epic Cinematic",
        ...     prompt_text="Epic orchestral music...",
        ...     tags=["cinematic", "epic"]
        ... )
        >>> result = provider.process_single(content)
        >>> print(result.data)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
        rate_limiter: Optional[Any] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        """
        初始化 Gemini 提供者
        
        Args:
            api_key: Google API Key，如未提供则从环境变量 GEMINI_API_KEY 获取
            model_config: 模型配置
            rate_limiter: 速率限制器
            circuit_breaker: 熔断器实例，如未提供则自动创建
        """
        super().__init__(
            api_key=api_key,
            model_config=model_config,
            rate_limiter=rate_limiter
        )
        
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None
        self._model = None
        self._logger = logging.getLogger(f"GeminiProvider.{id(self)}")
        
        if model_config is None:
            self._model_config = ModelConfig(
                model_name=DEFAULT_MODEL,
                max_tokens=8192,
                temperature=0.7,
                top_p=0.95,
                timeout=60.0,
                max_retries=3,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.JSON_OUTPUT,
                    ModelCapability.LONG_CONTEXT,
                ]
            )
        
        self._circuit_breaker = circuit_breaker or CircuitBreakerRegistry().get_or_create(
            name="gemini",
            failure_threshold=5,
            recovery_timeout=120.0,
            logger=self._logger
        )
        
        # Free Tier 用户：5秒/次 请求间隔
        self._min_request_interval = 5.0  # 5秒
        self._last_request_time = 0.0
    
    @property
    def provider_type(self) -> ProviderType:
        """返回提供者类型"""
        return ProviderType.GEMINI
    
    @property
    def supported_models(self) -> List[str]:
        """返回支持的模型列表"""
        return GEMINI_SUPPORTED_MODELS
    
    def initialize(self) -> None:
        """
        初始化 Gemini 客户端
        
        使用新的 google.genai 包
        
        Raises:
            ValueError: API Key 无效
            ImportError: google-genai 未安装
        """
        if self._is_initialized:
            return
        
        if not self._api_key:
            raise ValueError(
                "API Key 未提供。请设置 GEMINI_API_KEY 环境变量或传入 api_key 参数。"
            )
        
        try:
            # 使用新的 google.genai 包
            from google import genai
            from google.genai import types
            
            self._client = genai.Client(api_key=self._api_key)
            self._types = types
            
            self._is_initialized = True
            self._logger.info(
                f"Gemini 提供者初始化成功，模型: {self._model_config.model_name}"
            )
            
        except ImportError as e:
            raise ImportError(
                "未安装 google-genai 库。"
                "请运行: pip install google-genai"
            ) from e
        except Exception as e:
            self._logger.error(f"Gemini 初始化失败: {e}")
            raise
    
    def process_batch(
        self,
        contents: List[PromptContent],
        config: Optional[ModelConfig] = None,
        **kwargs
    ) -> BatchProcessingResult:
        """
        批量处理 Prompt 内容
        
        Args:
            contents: 待处理的 Prompt 内容列表
            config: 可选的模型配置
            **kwargs: 额外参数
            
        Returns:
            BatchProcessingResult: 批量处理结果
        """
        if not self._is_initialized:
            self.initialize()
        
        valid_contents = self._validate_batch(contents)
        if not valid_contents:
            self._logger.warning("批量处理：没有有效内容")
            return BatchProcessingResult(results=[])
        
        results = []
        for content in valid_contents:
            result = self.process_single(content, config, **kwargs)
            results.append(result)
        
        return BatchProcessingResult(results=results)
    
    def process_single(
        self,
        content: PromptContent,
        config: Optional[ModelConfig] = None,
        **kwargs
    ) -> ProcessingResult:
        """
        处理单个 Prompt 内容
        
        Args:
            content: 待处理的 Prompt 内容
            config: 可选的模型配置
            **kwargs: 额外参数
            
        Returns:
            ProcessingResult: 处理结果
        """
        if not self._is_initialized:
            self.initialize()
        
        if not self._validate_content(content):
            return ProcessingResult(
                success=False,
                error="内容验证失败：标题或 Prompt 文本为空",
                provider=self.provider_type,
                model=self._model_config.model_name
            )
        
        self._apply_rate_limit()
        
        start_time = time.time()
        config = config or self._model_config
        
        try:
            with self._circuit_breaker:
                result = self._call_gemini_with_retry(content, config)
                result.latency_ms = (time.time() - start_time) * 1000
                return result
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self._logger.error(f"处理失败: {error_msg}")
            
            return ProcessingResult(
                success=False,
                error=error_msg,
                latency_ms=latency_ms,
                model=self._model_config.model_name,
                provider=self.provider_type
            )
    
    def _call_gemini_with_retry(
        self,
        content: PromptContent,
        config: ModelConfig
    ) -> ProcessingResult:
        """
        调用 Gemini API（带手动重试）
        
        Free Tier 重试策略：
        - 最多重试 3 次
        - 等待时间：5秒 -> 10秒 -> 20秒（指数退避）
        """
        max_retries = 3
        base_wait = 5.0  # 基础等待 5 秒
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                prompt = self._build_prompt(content)
                
                # 使用新的 google.genai API
                response = self._client.models.generate_content(
                    model=config.model_name,
                    contents=prompt,
                    config=self._types.GenerateContentConfig(
                        temperature=config.temperature,
                        top_p=config.top_p,
                        max_output_tokens=config.max_tokens,
                        system_instruction=GEMINI_SYSTEM_PROMPT,
                    )
                )
                
                response_text = response.text
                parsed_data = self._parse_response(response_text)
                
                tokens_used = self._estimate_tokens(prompt, response_text)
                
                if attempt > 0:
                    self._logger.info(f"第 {attempt + 1} 次重试成功")
                
                return ProcessingResult(
                    success=True,
                    data=parsed_data,
                    tokens_used=tokens_used,
                    model=self._model_config.model_name,
                    provider=self.provider_type
                )
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = base_wait * (2 ** attempt)  # 5, 10, 20
                    self._logger.warning(
                        f"API 调用失败 (尝试 {attempt + 1}/{max_retries}): {e}. "
                        f"等待 {wait_time} 秒后重试..."
                    )
                    time.sleep(wait_time)
                else:
                    self._logger.error(f"所有重试均失败: {e}")
        
        # 所有重试都失败了
        raise last_error if last_error else Exception("未知错误")
    
    def _apply_rate_limit(self) -> None:
        """应用速率限制 - Free Tier: 5秒/次"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            self._logger.debug(f"Free Tier 限流：等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
        
        if self._rate_limiter:
            self._rate_limiter.acquire()
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 服务是否健康
        """
        try:
            if not self._is_initialized:
                self.initialize()
            
            test_content = PromptContent(
                title="Test",
                prompt_text="Test prompt",
                tags=["test"]
            )
            
            result = self.process_single(test_content)
            return result.success
            
        except Exception as e:
            self._logger.error(f"健康检查失败: {e}")
            return False
    
    def _build_prompt(self, content: PromptContent) -> str:
        """
        构建发送给 Gemini 的 Prompt
        
        Args:
            content: Prompt 内容
            
        Returns:
            str: 构建好的 Prompt 字符串
        """
        return f"""输入内容：
标题：{content.title}
Prompt：{content.prompt_text}
标签：{', '.join(content.tags)}
点赞数：{content.upvotes}

请输出 JSON 格式的结果。"""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析 Gemini 响应
        
        使用正则表达式提取 JSON，支持 Markdown 代码块格式。
        
        Args:
            response_text: Gemini 返回的原始文本
            
        Returns:
            Dict: 解析后的数据
            
        Raises:
            ValueError: 无法解析 JSON
        """
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                raise ValueError(f"响应中未找到有效的 JSON: {response_text[:200]}")
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            self._logger.error(f"JSON 解析失败: {e}")
            raise ValueError(f"JSON 解析失败: {e}") from e
        
        required_fields = ["title_zh", "prompt_zh", "douyin_tags", "dsp_params", "gem_suggestion"]
        for field in required_fields:
            if field not in data:
                self._logger.warning(f"缺少必要字段: {field}")
        
        return data
    
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """
        估算 Token 使用量
        
        使用简单的字符计数估算，实际值可能有出入。
        
        Args:
            prompt: 输入 Prompt
            response: 输出响应
            
        Returns:
            int: 估算的 Token 数量
        """
        char_count = len(prompt) + len(response)
        return char_count // 4
    
    def set_model(self, model_name: str) -> None:
        """
        切换模型
        
        Args:
            model_name: 模型名称
            
        Raises:
            ValueError: 模型不支持
        """
        if model_name not in self.supported_models:
            raise ValueError(
                f"不支持的模型: {model_name}。"
                f"支持的模型: {self.supported_models}"
            )
        
        self._model_config.model_name = model_name
        self._logger.info(f"已切换到模型: {model_name}")


ProviderFactory.register("gemini", GeminiProvider)
