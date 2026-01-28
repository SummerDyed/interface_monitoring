"""
重试机制模块
实现指数退避重试策略和重试装饰器

作者: 开发团队
创建时间: 2026-01-27
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Set, Type
from .result import ErrorType, RETRYABLE_ERRORS

logger = logging.getLogger(__name__)


class RetryConfig:
    """重试配置类

    配置重试策略的参数，包括最大重试次数、退避策略等
    """

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_strategy: Optional[list] = None,
        retryable_errors: Optional[Set[str]] = None,
    ):
        """初始化重试配置

        Args:
            max_attempts: 最大重试次数（默认3次）
            backoff_strategy: 退避策略列表，默认[1, 2, 4]秒
            retryable_errors: 可重试的错误类型集合，默认包含TIMEOUT、NETWORK_ERROR等
        """
        self.max_attempts = max_attempts
        self.backoff_strategy = backoff_strategy if backoff_strategy is not None else [1, 2, 4]
        self.retryable_errors = retryable_errors if retryable_errors is not None else RETRYABLE_ERRORS.copy()

    def is_retryable(self, error_type: Optional[str]) -> bool:
        """判断错误是否可重试

        Args:
            error_type: 错误类型

        Returns:
            bool: True if the error is retryable, False otherwise
        """
        if not error_type:
            return False
        return error_type in self.retryable_errors

    def get_backoff_delay(self, attempt: int) -> float:
        """获取退避延迟时间

        Args:
            attempt: 当前重试次数（从0开始）

        Returns:
            float: 延迟时间（秒）
        """
        if attempt < 0:
            return 0

        if attempt < len(self.backoff_strategy):
            return self.backoff_strategy[attempt]
        else:
            # 如果超过预定义策略，使用最后一个值
            return self.backoff_strategy[-1]

    def __repr__(self) -> str:
        return (
            f"RetryConfig(max_attempts={self.max_attempts}, "
            f"backoff_strategy={self.backoff_strategy}, "
            f"retryable_errors={self.retryable_errors})"
        )


def retry_on_failure(
    config: Optional[RetryConfig] = None,
    exceptions: tuple = (Exception,),
):
    """重试装饰器

    当函数执行失败时，根据配置进行重试

    Args:
        config: 重试配置，默认使用RetryConfig()
        exceptions: 需要重试的异常类型，默认捕获所有Exception

    Example:
        @retry_on_failure(RetryConfig(max_attempts=3))
        def monitor_interface(interface):
            # 执行监控逻辑
            pass
    """
    config = config or RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            last_error_type = None

            for attempt in range(config.max_attempts):
                try:
                    result = func(*args, **kwargs)

                    # 检查结果是否有错误
                    if hasattr(result, 'error_type'):
                        if result.error_type:
                            error_type = result.error_type
                            if config.is_retryable(error_type) and attempt < config.max_attempts - 1:
                                # 记录重试信息
                                delay = config.get_backoff_delay(attempt)
                                logger.warning(
                                    f"Function {func.__name__} failed with retryable error {error_type}, "
                                    f"retrying in {delay}s (attempt {attempt + 1}/{config.max_attempts})"
                                )
                                time.sleep(delay)
                                last_error_type = error_type
                                continue

                    # 成功或不可重试的错误，返回结果
                    return result

                except exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = config.get_backoff_delay(attempt)
                        logger.warning(
                            f"Function {func.__name__} raised exception: {e}, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{config.max_attempts})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )

            # 所有重试都失败了
            if last_exception:
                raise last_exception
            else:
                # 返回最后一次的结果
                return None

        return wrapper
    return decorator


class RetryableError(Exception):
    """可重试的异常类"""

    def __init__(self, message: str, error_type: str):
        super().__init__(message)
        self.error_type = error_type
