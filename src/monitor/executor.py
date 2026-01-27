"""
HTTP执行器
负责执行单个HTTP请求，处理响应和异常

作者: 开发团队
创建时间: 2026-01-27
"""

import time
import logging
from typing import Optional, Any
from concurrent.futures import ThreadPoolExecutor
import requests
from .handlers.http_handler import HTTPHandler
from .handlers.response_handler import ResponseHandler
from .retry import RetryConfig, retry_on_failure
from .result import MonitorResult, ErrorType

logger = logging.getLogger(__name__)


class HTTPExecutor:
    """HTTP请求执行器

    负责执行单个接口的HTTP请求，处理响应和异常
    """

    def __init__(
        self,
        config: Optional[dict] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        """初始化HTTP执行器

        Args:
            config: 配置字典，包含base_url、timeout等
            retry_config: 重试配置
        """
        self.config = config or {}
        self.retry_config = retry_config or RetryConfig()
        self.http_handler = HTTPHandler(
            base_url=self.config.get('base_url'),
            timeout=self.config.get('timeout', 10),
        )
        self.response_handler = ResponseHandler()

    @retry_on_failure()
    def execute(
        self,
        interface: Any,
        token: Optional[str] = None,
    ) -> MonitorResult:
        """执行单个接口的监控

        Args:
            interface: 接口对象
            token: 认证Token

        Returns:
            MonitorResult: 监控结果
        """
        start_time = time.time()

        try:
            # 准备请求参数
            request_params = self.http_handler.prepare_request(interface, token)

            # 发送HTTP请求
            logger.debug(f"发送请求: {interface.method} {request_params['url']}")
            response = requests.request(**request_params)

            # 计算响应时间
            response_time = (time.time() - start_time) * 1000

            # 解析响应
            (
                status,
                status_code,
                error_type,
                error_message,
                response_data,
            ) = self.response_handler.parse_response(response, response_time)

            # 构建监控结果
            result = MonitorResult(
                interface=interface,
                status=status,
                status_code=status_code,
                response_time=response_time,
                error_type=error_type,
                error_message=error_message,
                request_data=request_params,
                response_data=response_data,
            )

            return result

        except requests.exceptions.Timeout:
            # 处理超时
            response_time = (time.time() - start_time) * 1000
            (
                status,
                status_code,
                error_type,
                error_message,
                response_data,
            ) = self.response_handler.handle_timeout(response_time)

            result = MonitorResult(
                interface=interface,
                status=status,
                status_code=status_code,
                response_time=response_time,
                error_type=error_type,
                error_message=error_message,
                request_data=request_params if 'request_params' in locals() else {},
                response_data=response_data,
            )
            return result

        except requests.exceptions.RequestException as e:
            # 处理网络错误
            response_time = (time.time() - start_time) * 1000
            (
                status,
                status_code,
                error_type,
                error_message,
                response_data,
            ) = self.response_handler.handle_network_error(e)

            result = MonitorResult(
                interface=interface,
                status=status,
                status_code=status_code,
                response_time=response_time,
                error_type=error_type,
                error_message=error_message,
                request_data=request_params if 'request_params' in locals() else {},
                response_data=response_data,
            )
            return result

        except Exception as e:
            # 处理未知错误
            response_time = (time.time() - start_time) * 1000
            logger.error(f"执行接口监控时发生未知错误: {e}", exc_info=True)

            result = MonitorResult(
                interface=interface,
                status='FAILED',
                status_code=None,
                response_time=response_time,
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=str(e),
                request_data=request_params if 'request_params' in locals() else {},
                response_data={},
            )
            return result

    def execute_with_retry(
        self,
        interface: Any,
        token: Optional[str] = None,
        max_attempts: Optional[int] = None,
    ) -> MonitorResult:
        """执行监控并处理重试

        Args:
            interface: 接口对象
            token: 认证Token
            max_attempts: 最大重试次数

        Returns:
            MonitorResult: 监控结果
        """
        retry_config = RetryConfig(
            max_attempts=max_attempts or self.retry_config.max_attempts,
            backoff_strategy=self.retry_config.backoff_strategy,
            retryable_errors=self.retry_config.retryable_errors,
        )

        result = self.execute(interface, token)

        # 记录重试次数
        result.retry_count = 0

        return result

    def cleanup(self):
        """清理资源"""
        self.http_handler.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
