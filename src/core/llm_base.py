"""
VMDP LLM 基础模块 - 抽象提供者接口

该模块定义了音乐 AI 提供者的抽象基类，支持无缝切换不同的 LLM 后端
（如 Gemini、OpenAI、Groq、DeepSeek 等），无需修改业务代码。

设计模式：策略模式 + 工厂模式
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
    runtime_checkable
)
import time


class ProviderType(Enum):
    """LLM 提供者类型"""
    GEMINI = "gemini"
    OPENAI = "openai"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class ModelCapability(Enum):
    """模型能力标识"""
    TEXT_GENERATION = "text_generation"
    JSON_OUTPUT = "json_output"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    LONG_CONTEXT = "long_context"


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.95
    timeout: float = 60.0
    max_retries: int = 3
    capabilities: List[ModelCapability] = field(default_factory=list)
    
    def has_capability(self, capability: ModelCapability) -> bool:
        """检查模型是否支持指定能力"""
        return capability in self.capabilities


@dataclass
class PromptContent:
    """Prompt 内容结构"""
    title: str
    prompt_text: str
    tags: List[str]
    upvotes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """处理结果结构"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    tokens_used: int = 0
    model: str = ""
    provider: ProviderType = ProviderType.CUSTOM
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "model": self.model,
            "provider": self.provider.value
        }


@dataclass
class BatchProcessingResult:
    """批量处理结果"""
    results: List[ProcessingResult]
    total_success: int = 0
    total_failure: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    
    def __post_init__(self):
        self.total_success = sum(1 for r in self.results if r.success)
        self.total_failure = sum(1 for r in self.results if not r.success)
        self.total_latency_ms = sum(r.latency_ms for r in self.results)
        self.total_tokens = sum(r.tokens_used for r in self.results)
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = len(self.results)
        return self.total_success / total if total > 0 else 0.0


T = TypeVar('T')


@runtime_checkable
class RateLimiterProtocol(Protocol):
    """速率限制器协议"""
    def wait_if_needed(self) -> None: ...
    def acquire(self) -> bool: ...
    def release(self) -> None: ...


class MusicAIProvider(ABC):
    """
    音乐 AI 提供者抽象基类
    
    定义了所有 LLM 提供者必须实现的接口，确保业务代码可以无缝切换
    不同的后端服务（Gemini、OpenAI、Groq、DeepSeek 等）。
    
    设计原则：
        - 依赖倒置：业务层依赖抽象，不依赖具体实现
        - 开闭原则：对扩展开放，对修改关闭
        - 单一职责：每个方法只做一件事
    
    Example:
        >>> class GeminiProvider(MusicAIProvider):
        ...     def process_batch(self, contents, config):
        ...         # 实现具体逻辑
        ...         pass
        >>> 
        >>> provider = GeminiProvider(api_key="...")
        >>> result = provider.process_batch(contents, config)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
        rate_limiter: Optional[RateLimiterProtocol] = None
    ):
        """
        初始化提供者
        
        Args:
            api_key: API 密钥
            model_config: 模型配置
            rate_limiter: 速率限制器
        """
        self._api_key = api_key
        self._model_config = model_config or ModelConfig(model_name="default")
        self._rate_limiter = rate_limiter
        self._is_initialized = False
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """返回提供者类型"""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """返回支持的模型列表"""
        pass
    
    @property
    def model_config(self) -> ModelConfig:
        """获取当前模型配置"""
        return self._model_config
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._is_initialized
    
    @abstractmethod
    def initialize(self) -> None:
        """
        初始化提供者
        
        执行必要的设置，如配置客户端、验证凭证等。
        子类必须实现此方法。
        
        Raises:
            ValueError: API Key 无效
            ConnectionError: 无法连接到服务
        """
        pass
    
    @abstractmethod
    def process_batch(
        self,
        contents: List[PromptContent],
        config: Optional[ModelConfig] = None,
        **kwargs
    ) -> BatchProcessingResult:
        """
        批量处理 Prompt 内容
        
        这是核心方法，接收一批 Prompt 内容，返回处理结果。
        子类必须实现具体的处理逻辑。
        
        Args:
            contents: 待处理的 Prompt 内容列表
            config: 可选的模型配置，覆盖默认配置
            **kwargs: 额外的提供者特定参数
            
        Returns:
            BatchProcessingResult: 批量处理结果
            
        Raises:
            RuntimeError: 提供者未初始化
            ValueError: 输入内容无效
        """
        pass
    
    @abstractmethod
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
            **kwargs: 额外的参数
            
        Returns:
            ProcessingResult: 处理结果
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        健康检查
        
        检查服务是否可用，API Key 是否有效。
        
        Returns:
            bool: 服务是否健康
        """
        pass
    
    def _apply_rate_limit(self) -> None:
        """应用速率限制"""
        if self._rate_limiter:
            self._rate_limiter.wait_if_needed()
    
    def _validate_content(self, content: PromptContent) -> bool:
        """
        验证内容有效性
        
        Args:
            content: 待验证的内容
            
        Returns:
            bool: 内容是否有效
        """
        if not content.title or not content.title.strip():
            return False
        if not content.prompt_text or not content.prompt_text.strip():
            return False
        return True
    
    def _validate_batch(self, contents: List[PromptContent]) -> List[PromptContent]:
        """
        验证批量内容，过滤无效项
        
        Args:
            contents: 待验证的内容列表
            
        Returns:
            List[PromptContent]: 有效的内容列表
        """
        return [c for c in contents if self._validate_content(c)]
    
    def update_config(self, config: ModelConfig) -> None:
        """
        更新模型配置
        
        Args:
            config: 新的模型配置
        """
        self._model_config = config
    
    def set_rate_limiter(self, limiter: RateLimiterProtocol) -> None:
        """
        设置速率限制器
        
        Args:
            limiter: 速率限制器实例
        """
        self._rate_limiter = limiter
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"provider={self.provider_type.value}, "
            f"model={self._model_config.model_name})"
        )


class ProviderFactory:
    """
    提供者工厂
    
    用于创建和管理不同的 LLM 提供者实例。
    支持注册自定义提供者。
    
    Example:
        >>> factory = ProviderFactory()
        >>> factory.register("gemini", GeminiProvider)
        >>> provider = factory.create("gemini", api_key="...")
    """
    
    _providers: Dict[str, type] = {}
    _instances: Dict[str, MusicAIProvider] = {}
    _lock = None
    
    @classmethod
    def _get_lock(cls):
        """获取线程锁"""
        if cls._lock is None:
            import threading
            cls._lock = threading.Lock()
        return cls._lock
    
    @classmethod
    def register(cls, name: str, provider_class: type) -> None:
        """
        注册提供者类
        
        Args:
            name: 提供者名称
            provider_class: 提供者类（必须继承自 MusicAIProvider）
            
        Raises:
            TypeError: 提供者类无效
        """
        if not issubclass(provider_class, MusicAIProvider):
            raise TypeError(
                f"提供者类必须继承自 MusicAIProvider，当前: {provider_class}"
            )
        with cls._get_lock():
            cls._providers[name.lower()] = provider_class
    
    @classmethod
    def create(
        cls,
        name: str,
        api_key: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
        rate_limiter: Optional[RateLimiterProtocol] = None,
        singleton: bool = False,
        **kwargs
    ) -> MusicAIProvider:
        """
        创建提供者实例
        
        Args:
            name: 提供者名称
            api_key: API 密钥
            model_config: 模型配置
            rate_limiter: 速率限制器
            singleton: 是否使用单例模式
            **kwargs: 额外的初始化参数
            
        Returns:
            MusicAIProvider: 提供者实例
            
        Raises:
            KeyError: 提供者未注册
        """
        name_lower = name.lower()
        
        if singleton and name_lower in cls._instances:
            return cls._instances[name_lower]
        
        if name_lower not in cls._providers:
            raise KeyError(
                f"提供者 '{name}' 未注册。"
                f"可用提供者: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[name_lower]
        instance = provider_class(
            api_key=api_key,
            model_config=model_config,
            rate_limiter=rate_limiter,
            **kwargs
        )
        
        if singleton:
            with cls._get_lock():
                if name_lower not in cls._instances:
                    cls._instances[name_lower] = instance
                return cls._instances[name_lower]
        
        return instance
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """获取所有已注册的提供者名称"""
        return list(cls._providers.keys())
    
    @classmethod
    def clear_instances(cls) -> None:
        """清除所有单例实例"""
        with cls._get_lock():
            cls._instances.clear()


def provider_decorator(name: str):
    """
    提供者注册装饰器
    
    用于简化提供者类的注册。
    
    Example:
        >>> @provider_decorator("my_provider")
        ... class MyProvider(MusicAIProvider):
        ...     pass
    """
    def decorator(cls):
        ProviderFactory.register(name, cls)
        return cls
    return decorator
