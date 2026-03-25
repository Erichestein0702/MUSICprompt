"""
MUSICprompt Core 模块

提供 MUSICprompt 项目的核心基础设施：
- 安全模块：日志脱敏、熔断保护
- LLM 基础模块：抽象提供者接口
- Gemini 提供者：Google Gemini 实现
"""

from .security import (
    LogMasker,
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
    CircuitStats,
    setup_secure_logging,
)

from .llm_base import (
    MusicAIProvider,
    ProviderFactory,
    ProviderType,
    ModelCapability,
    ModelConfig,
    PromptContent,
    ProcessingResult,
    BatchProcessingResult,
    provider_decorator,
)

from .gemini_provider import (
    GeminiProvider,
    GEMINI_SYSTEM_PROMPT,
    GEMINI_SUPPORTED_MODELS,
    DEFAULT_MODEL as GEMINI_DEFAULT_MODEL,
)

from .siliconflow_provider import (
    SiliconFlowProvider,
    SILICONFLOW_SYSTEM_PROMPT,
    SILICONFLOW_SUPPORTED_MODELS,
    DEFAULT_MODEL as SILICONFLOW_DEFAULT_MODEL,
)

__all__ = [
    # Security
    "LogMasker",
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "CircuitState",
    "CircuitStats",
    "setup_secure_logging",
    
    # LLM Base
    "MusicAIProvider",
    "ProviderFactory",
    "ProviderType",
    "ModelCapability",
    "ModelConfig",
    "PromptContent",
    "ProcessingResult",
    "BatchProcessingResult",
    "provider_decorator",
    
    # Gemini
    "GeminiProvider",
    "GEMINI_SYSTEM_PROMPT",
    "GEMINI_SUPPORTED_MODELS",
    "GEMINI_DEFAULT_MODEL",
    
    # SiliconFlow
    "SiliconFlowProvider",
    "SILICONFLOW_SYSTEM_PROMPT",
    "SILICONFLOW_SUPPORTED_MODELS",
    "SILICONFLOW_DEFAULT_MODEL",
]

__version__ = "1.0.0"
