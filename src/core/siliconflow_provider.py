"""
VMDP SiliconFlow 提供者 - Qwen2.5-72B 极速炼金模式

使用 SiliconFlow API (兼容 OpenAI 格式) 调用 Qwen/Qwen2.5-72B-Instruct 模型
免费层频率限制宽松，支持极速处理
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


# 精简版 System Prompt - 强制 JSON 输出
SILICONFLOW_SYSTEM_PROMPT = """You are a music prompt analyzer. Return ONLY valid JSON. No prose, no explanations.

Example output:
{
    "title_zh": "中文标题",
    "prompt_zh": "中文翻译",
    "genre": "electronic.bass.trap",
    "douyin_tags": ["标签1", "标签2"],
    "dsp_params": {
        "bpm": 140,
        "key": "F Minor",
        "energy_level": "high",
        "frequency_center": "30Hz-80Hz",
        "dynamics_range": "Wide",
        "reverb": "Large Hall",
        "compression": "Aggressive"
    },
    "gem_suggestion": "音频处理建议"
}

Rules:
1. energy_level MUST be one of: low, medium, high, very_high
2. genre MUST use dot notation like: electronic.bass.trap, hip_hop.trap
3. For [Drop] tags: frequency_center = "30Hz-60Hz heavy sub"
4. For [Aggressive 808]: frequency_center = "30Hz-80Hz"
5. Brazilian Funk: BPM 130-150, bouncy 808s
6. Phonk: BPM 130-140, distorted bass, cowbell

Return ONLY the JSON object. No markdown, no explanations."""


SILICONFLOW_SUPPORTED_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
]

# 升级到 72B 模型
DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"


@provider_decorator("siliconflow")
class SiliconFlowProvider(MusicAIProvider):
    """
    SiliconFlow 提供者实现 - 极速炼金模式 (72B)
    
    使用 Qwen2.5-72B-Instruct 模型，具备更强的 JSON 指令遵循能力
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
        rate_limiter: Optional[Any] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        super().__init__(
            api_key=api_key,
            model_config=model_config,
            rate_limiter=rate_limiter
        )
        
        self._api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        self._base_url = "https://api.siliconflow.cn/v1"
        self._client = None
        self._logger = logging.getLogger(f"SiliconFlowProvider.{id(self)}")
        
        if model_config is None:
            self._model_config = ModelConfig(
                model_name=DEFAULT_MODEL,
                max_tokens=4096,
                temperature=0.3,  # 降低温度以获得更确定的输出
                top_p=0.95,
                timeout=60.0,
                max_retries=3,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.JSON_OUTPUT,
                ]
            )
        
        self._circuit_breaker = circuit_breaker or CircuitBreakerRegistry().get_or_create(
            name="siliconflow",
            failure_threshold=10,
            recovery_timeout=60.0,
            logger=self._logger
        )
        
        # 极速模式：0.5秒/次
        self._min_request_interval = 0.5
        self._last_request_time = 0.0
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        return SILICONFLOW_SUPPORTED_MODELS
    
    def initialize(self) -> None:
        if self._is_initialized:
            return
        
        if not self._api_key:
            raise ValueError(
                "API Key 未提供。请设置 SILICONFLOW_API_KEY 环境变量或传入 api_key 参数。"
            )
        
        try:
            from openai import OpenAI
            
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url
            )
            
            self._is_initialized = True
            self._logger.info(
                f"SiliconFlow 提供者初始化成功，模型: {self._model_config.model_name}"
            )
            
        except ImportError as e:
            raise ImportError(
                "未安装 openai 库。"
                "请运行: pip install openai"
            ) from e
        except Exception as e:
            self._logger.error(f"SiliconFlow 初始化失败: {e}")
            raise
    
    def process_batch(
        self,
        contents: List[PromptContent],
        config: Optional[ModelConfig] = None,
        **kwargs
    ) -> BatchProcessingResult:
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
                result = self._call_siliconflow_with_retry(content, config)
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
    
    def _call_siliconflow_with_retry(
        self,
        content: PromptContent,
        config: ModelConfig
    ) -> ProcessingResult:
        """
        调用 SiliconFlow API（带手动重试）
        
        使用 72B 模型和强制 JSON 模式
        """
        max_retries = 3
        base_wait = 0.5
        
        last_error = None
        
        # 检测特殊标签
        prompt_text_lower = content.prompt_text.lower()
        has_drop = "[drop]" in prompt_text_lower
        has_aggressive_808 = "[aggressive 808]" in prompt_text_lower or "aggressive 808" in prompt_text_lower
        is_brazilian_funk = "brazilian" in prompt_text_lower or "funk" in prompt_text_lower
        is_phonk = "phonk" in prompt_text_lower
        
        for attempt in range(max_retries):
            try:
                prompt = self._build_prompt(content)
                
                # 添加特殊标签提示
                special_hints = []
                if has_drop:
                    special_hints.append("[Drop] detected: use frequency_center='30Hz-60Hz heavy sub'")
                if has_aggressive_808:
                    special_hints.append("[Aggressive 808] detected: use frequency_center='30Hz-80Hz'")
                if is_brazilian_funk:
                    special_hints.append("Brazilian Funk: BPM 130-150, bouncy 808s")
                if is_phonk:
                    special_hints.append("Phonk: BPM 130-140, distorted bass, cowbell")
                
                if special_hints:
                    prompt += "\n\n" + "\n".join(special_hints)
                
                # OpenAI 兼容格式调用 - 强制 JSON 模式
                response = self._client.chat.completions.create(
                    model=config.model_name,
                    messages=[
                        {"role": "system", "content": SILICONFLOW_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    top_p=config.top_p,
                    timeout=config.timeout,
                    response_format={"type": "json_object"}  # 强制 JSON 模式
                )
                
                response_text = response.choices[0].message.content
                
                # 容错解析：去除 Markdown 标识符
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                parsed_data = self._parse_response(response_text)
                
                # 后处理：确保特殊标签的频率特征
                if has_aggressive_808 and "dsp_params" in parsed_data:
                    if "frequency_center" not in parsed_data["dsp_params"]:
                        parsed_data["dsp_params"]["frequency_center"] = "30Hz-80Hz heavy sub"
                
                tokens_used = response.usage.total_tokens if response.usage else self._estimate_tokens(prompt, response_text)
                
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
                    wait_time = base_wait * (2 ** attempt)
                    self._logger.warning(
                        f"API 调用失败 (尝试 {attempt + 1}/{max_retries}): {e}. "
                        f"等待 {wait_time} 秒后重试..."
                    )
                    time.sleep(wait_time)
                else:
                    self._logger.error(f"所有重试均失败: {e}")
        
        raise last_error if last_error else Exception("未知错误")
    
    def _apply_rate_limit(self) -> None:
        """应用速率限制 - 极速模式：0.5秒/次"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
        
        if self._rate_limiter:
            self._rate_limiter.acquire()
    
    def health_check(self) -> bool:
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
        return f"""Analyze this music prompt and return JSON:

Title: {content.title}
Prompt: {content.prompt_text}
Tags: {', '.join(content.tags)}
Upvotes: {content.upvotes}

Return ONLY valid JSON."""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析响应 - 增强容错处理
        """
        # 尝试直接解析
        try:
            data = json.loads(response_text)
            return data
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 JSON 块
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data
            except json.JSONDecodeError:
                pass
        
        # 尝试修复常见 JSON 错误
        # 1. 修复缺少逗号的情况
        fixed_text = re.sub(r'(\")(\s*)(\")', r'\1,\2\3', response_text)
        try:
            data = json.loads(fixed_text)
            return data
        except json.JSONDecodeError:
            pass
        
        self._logger.error(f"JSON 解析失败，原始响应: {response_text[:200]}")
        raise ValueError(f"无法解析 JSON 响应")
    
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        char_count = len(prompt) + len(response)
        return char_count // 4
    
    def set_model(self, model_name: str) -> None:
        if model_name not in self.supported_models:
            raise ValueError(
                f"不支持的模型: {model_name}。"
                f"支持的模型: {self.supported_models}"
            )
        
        self._model_config.model_name = model_name
        self._logger.info(f"已切换到模型: {model_name}")


ProviderFactory.register("siliconflow", SiliconFlowProvider)
