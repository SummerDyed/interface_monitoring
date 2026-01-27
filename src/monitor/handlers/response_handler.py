"""
响应处理器
负责解析HTTP响应，分类异常类型，提取响应数据

作者: 开发团队
创建时间: 2026-01-27
"""

import logging
from typing import Optional, Tuple, Dict, Any
from ..result import ErrorType, ERROR_TYPES

logger = logging.getLogger(__name__)


class ResponseHandler:
    """响应处理器

    负责解析HTTP响应，分类错误类型，提取响应数据
    """

    def parse_response(
        self,
        response: Any,
        response_time: float,
    ) -> Tuple[str, Optional[int], Optional[str], Optional[str], Dict[str, Any]]:
        """解析HTTP响应

        Args:
            response: HTTP响应对象
            response_time: 响应时间（毫秒）

        Returns:
            tuple: (status, status_code, error_type, error_message, response_data)
        """
        try:
            # 检查是否成功
            if response.status_code < 400:
                status = 'SUCCESS'
                status_code = response.status_code
                error_type = None
                error_message = None
                response_data = self._extract_response_data(response)
                return status, status_code, error_type, error_message, response_data

            # 处理错误状态码
            status_code = response.status_code
            response_data = self._extract_response_data(response)

            if status_code == 404:
                error_type = ErrorType.HTTP_404
                error_message = f"接口不存在 (HTTP {status_code})"
            elif status_code == 500:
                error_type = ErrorType.HTTP_500
                error_message = f"服务器内部错误 (HTTP {status_code})"
            elif status_code == 503:
                error_type = ErrorType.HTTP_503
                error_message = f"服务不可用 (HTTP {status_code})"
            elif 400 <= status_code < 500:
                error_type = ErrorType.VALIDATION_ERROR
                error_message = f"客户端错误 (HTTP {status_code})"
            elif status_code >= 500:
                error_type = ErrorType.HTTP_500
                error_message = f"服务器错误 (HTTP {status_code})"
            else:
                error_type = ErrorType.UNKNOWN_ERROR
                error_message = f"未知错误 (HTTP {status_code})"

            status = 'FAILED'
            return status, status_code, error_type, error_message, response_data

        except Exception as e:
            logger.error(f"解析响应时发生错误: {e}")
            return 'FAILED', None, ErrorType.UNKNOWN_ERROR, str(e), {}

    def handle_timeout(self, response_time: float) -> Tuple[str, Optional[int], Optional[str], Optional[str], Dict[str, Any]]:
        """处理超时错误

        Args:
            response_time: 响应时间（毫秒）

        Returns:
            tuple: 错误信息元组
        """
        return (
            'FAILED',
            None,
            ErrorType.TIMEOUT,
            f"请求超时 (耗时 {response_time:.2f}ms)",
            {}
        )

    def handle_network_error(
        self,
        exception: Exception,
    ) -> Tuple[str, Optional[int], Optional[str], Optional[str], Dict[str, Any]]:
        """处理网络错误

        Args:
            exception: 网络异常

        Returns:
            tuple: 错误信息元组
        """
        error_message = str(exception)
        error_type = ErrorType.NETWORK_ERROR

        # 根据异常类型分类错误
        exception_name = type(exception).__name__

        if 'timeout' in exception_name.lower() or 'timeout' in error_message.lower():
            error_type = ErrorType.TIMEOUT
        elif 'connection' in exception_name.lower() or 'connection' in error_message.lower():
            error_type = ErrorType.CONNECTION_ERROR
        elif 'dns' in exception_name.lower() or 'resolve' in error_message.lower():
            error_type = ErrorType.DNS_ERROR
        elif 'ssl' in exception_name.lower() or 'certificate' in error_message.lower():
            error_type = ErrorType.NETWORK_ERROR

        return (
            'FAILED',
            None,
            error_type,
            error_message,
            {}
        )

    def _extract_response_data(self, response: Any) -> Dict[str, Any]:
        """提取响应数据

        Args:
            response: HTTP响应对象

        Returns:
            dict: 响应数据
        """
        data = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
        }

        # 尝试提取JSON数据
        try:
            if response.text:
                import json
                try:
                    data['json'] = response.json()
                except:
                    data['text'] = response.text
        except Exception as e:
            logger.debug(f"提取响应数据时发生错误: {e}")

        return data

    def get_error_description(self, error_type: str) -> str:
        """获取错误类型描述

        Args:
            error_type: 错误类型

        Returns:
            str: 错误描述
        """
        return ERROR_TYPES.get(error_type, '未知错误')
