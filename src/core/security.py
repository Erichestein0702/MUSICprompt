"""
VMDP 安全模块 - 日志脱敏与熔断保护

该模块提供：
1. LogMasker: 自动从日志中屏蔽敏感信息（如 API Key）
2. CircuitBreaker: API 请求熔断保护，防止连续失败导致资源浪费
"""

import logging
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set, List, Pattern


class LogMasker(logging.Filter):
    """
    日志脱敏过滤器
    
    自动从日志记录中屏蔽敏感信息，防止 API Key 等机密数据泄露。
    支持从环境变量自动加载敏感词，并支持自定义正则模式。
    
    Example:
        >>> import logging
        >>> masker = LogMasker.from_env()
        >>> handler = logging.StreamHandler()
        >>> handler.addFilter(masker)
        >>> logging.getLogger().addHandler(handler)
    """
    
    DEFAULT_MASK = "******"
    SENSITIVE_ENV_PATTERNS = [
        r".*_API_KEY.*",
        r".*_SECRET.*",
        r".*_TOKEN.*",
        r".*_PASSWORD.*",
        r".*_CREDENTIAL.*",
    ]
    
    def __init__(
        self,
        sensitive_values: Optional[Set[str]] = None,
        patterns: Optional[List[Pattern]] = None,
        mask: str = DEFAULT_MASK
    ):
        """
        初始化日志脱敏器
        
        Args:
            sensitive_values: 需要屏蔽的敏感值集合
            patterns: 用于匹配敏感信息的正则表达式列表
            mask: 替换敏感信息的掩码字符串
        """
        super().__init__()
        self.sensitive_values: Set[str] = sensitive_values or set()
        self.patterns: List[Pattern] = patterns or []
        self.mask = mask
        self._lock = threading.Lock()
    
    @classmethod
    def from_env(cls, mask: str = DEFAULT_MASK) -> "LogMasker":
        """
        从环境变量自动创建脱敏器
        
        扫描所有环境变量，自动识别并收集敏感值。
        
        Args:
            mask: 替换敏感信息的掩码字符串
            
        Returns:
            配置好的 LogMasker 实例
        """
        sensitive_values = set()
        patterns = []
        
        for env_name, env_value in os.environ.items():
            if not env_value or len(env_value) < 8:
                continue
            
            for pattern in cls.SENSITIVE_ENV_PATTERNS:
                if re.match(pattern, env_name, re.IGNORECASE):
                    sensitive_values.add(env_value)
                    break
        
        api_key_pattern = re.compile(
            r'(?:api[_-]?key|token|secret|password|credential)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            re.IGNORECASE
        )
        patterns.append(api_key_pattern)
        
        bearer_pattern = re.compile(
            r'Bearer\s+[a-zA-Z0-9_\-\.]{20,}',
            re.IGNORECASE
        )
        patterns.append(bearer_pattern)
        
        return cls(
            sensitive_values=sensitive_values,
            patterns=patterns,
            mask=mask
        )
    
    def add_sensitive_value(self, value: str) -> None:
        """
        添加需要屏蔽的敏感值
        
        Args:
            value: 敏感值
        """
        if value and len(value) >= 8:
            with self._lock:
                self.sensitive_values.add(value)
    
    def add_pattern(self, pattern: str) -> None:
        """
        添加敏感信息匹配模式
        
        Args:
            pattern: 正则表达式字符串
        """
        compiled = re.compile(pattern, re.IGNORECASE)
        with self._lock:
            self.patterns.append(compiled)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录，脱敏敏感信息
        
        Args:
            record: 日志记录对象
            
        Returns:
            总是返回 True，允许日志通过，但会修改消息内容
        """
        record.msg = self._mask_message(str(record.msg))
        
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._mask_message(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_message(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        
        return True
    
    def _mask_message(self, message: str) -> str:
        """
        对消息进行脱敏处理
        
        Args:
            message: 原始消息
            
        Returns:
            脱敏后的消息
        """
        masked = message
        
        with self._lock:
            for value in self.sensitive_values:
                if value in masked:
                    masked = masked.replace(value, self.mask)
            
            for pattern in self.patterns:
                masked = pattern.sub(self.mask, masked)
        
        return masked


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    """熔断器统计信息"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    total_requests: int = 0


class CircuitBreaker:
    """
    熔断器 - API 请求保护机制
    
    当 API 请求连续失败达到阈值时，自动触发熔断，终止程序运行，
    防止无效请求浪费 API 额度和系统资源。
    
    Features:
        - 连续失败计数
        - 自动熔断触发
        - 支持重置和恢复
        - 线程安全
        - 可配置阈值和冷却时间
    
    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5)
        >>> with breaker:
        ...     response = api.call()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: str = "default",
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 连续失败次数阈值，达到后触发熔断
            recovery_timeout: 熔断恢复超时时间（秒）
            name: 熔断器名称，用于日志标识
            logger: 日志记录器
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.logger = logger or logging.getLogger(f"CircuitBreaker.{name}")
        
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._lock = threading.RLock()
    
    @property
    def state(self) -> CircuitState:
        """获取当前熔断器状态"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._stats.last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self.logger.info(
                        f"[{self.name}] 熔断器进入半开状态，尝试恢复"
                    )
            return self._state
    
    @property
    def stats(self) -> CircuitStats:
        """获取统计信息"""
        with self._lock:
            return CircuitStats(
                failure_count=self._stats.failure_count,
                success_count=self._stats.success_count,
                last_failure_time=self._stats.last_failure_time,
                last_success_time=self._stats.last_success_time,
                total_requests=self._stats.total_requests
            )
    
    def record_success(self) -> None:
        """
        记录成功请求
        
        成功请求会重置失败计数器，并将熔断器状态恢复为关闭。
        """
        with self._lock:
            self._stats.success_count += 1
            self._stats.total_requests += 1
            self._stats.last_success_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._stats.failure_count = 0
                self.logger.info(
                    f"[{self.name}] 熔断器恢复正常，服务可用"
                )
            elif self._state == CircuitState.CLOSED:
                self._stats.failure_count = 0
    
    def record_failure(self, error: Optional[Exception] = None) -> None:
        """
        记录失败请求
        
        连续失败达到阈值时触发熔断。
        
        Args:
            error: 导致失败的异常对象
            
        Raises:
            SystemExit: 当连续失败达到阈值时，调用 sys.exit(1)
        """
        with self._lock:
            self._stats.failure_count += 1
            self._stats.total_requests += 1
            self._stats.last_failure_time = time.time()
            
            error_msg = str(error) if error else "未知错误"
            
            if self._stats.failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self.logger.critical(
                    f"[{self.name}] 熔断器触发！连续失败 {self._stats.failure_count} 次，"
                    f"已达到阈值 {self.failure_threshold}。最后错误: {error_msg}"
                )
                self.logger.critical(
                    f"[{self.name}] 程序将终止以保护 API 额度。"
                    f"请检查配置或等待 {self.recovery_timeout} 秒后重试。"
                )
                sys.exit(1)
            else:
                self.logger.warning(
                    f"[{self.name}] 请求失败 ({self._stats.failure_count}/"
                    f"{self.failure_threshold}): {error_msg}"
                )
    
    def reset(self) -> None:
        """重置熔断器状态"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._stats = CircuitStats()
            self.logger.info(f"[{self.name}] 熔断器已重置")
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            True 表示服务可用，False 表示熔断器处于开启状态
        """
        return self.state != CircuitState.OPEN
    
    def __enter__(self) -> "CircuitBreaker":
        """上下文管理器入口"""
        if not self.is_available():
            self.logger.error(
                f"[{self.name}] 熔断器处于开启状态，拒绝请求"
            )
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """上下文管理器出口"""
        if exc_type is not None:
            self.record_failure(exc_val)
        else:
            self.record_success()
        return False


class CircuitBreakerRegistry:
    """
    熔断器注册表 - 管理多个熔断器实例
    
    用于为不同的服务或 API 端点创建独立的熔断器。
    
    Example:
        >>> registry = CircuitBreakerRegistry()
        >>> gemini_breaker = registry.get_or_create("gemini", failure_threshold=5)
        >>> reddit_breaker = registry.get_or_create("reddit", failure_threshold=3)
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "CircuitBreakerRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers = {}
                    cls._instance._breakers_lock = threading.Lock()
        return cls._instance
    
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        logger: Optional[logging.Logger] = None
    ) -> CircuitBreaker:
        """
        获取或创建熔断器
        
        Args:
            name: 熔断器名称
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间
            logger: 日志记录器
            
        Returns:
            CircuitBreaker 实例
        """
        with self._breakers_lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    name=name,
                    logger=logger
                )
            return self._breakers[name]
    
    def get_all_stats(self) -> dict:
        """获取所有熔断器的统计信息"""
        with self._breakers_lock:
            return {
                name: breaker.stats
                for name, breaker in self._breakers.items()
            }
    
    def reset_all(self) -> None:
        """重置所有熔断器"""
        with self._breakers_lock:
            for breaker in self._breakers.values():
                breaker.reset()


def setup_secure_logging(
    level: int = logging.INFO,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> LogMasker:
    """
    配置安全的日志系统
    
    自动添加日志脱敏过滤器到根日志记录器。
    
    Args:
        level: 日志级别
        log_format: 日志格式
        
    Returns:
        LogMasker 实例，可用于后续添加敏感值
    """
    masker = LogMasker.from_env()
    
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(log_format))
    handler.addFilter(masker)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    
    return masker
