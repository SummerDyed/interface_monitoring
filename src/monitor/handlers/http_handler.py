"""
HTTP请求处理器
负责构造和发送HTTP请求，处理认证和请求参数

作者: 开发团队
创建时间: 2026-01-27
"""

import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin
from ..result import ErrorType

logger = logging.getLogger(__name__)


class HTTPHandler:
    """HTTP请求处理器

    负责构造HTTP请求，添加认证信息，处理请求参数
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        """初始化HTTP处理器

        Args:
            base_url: 基础URL，用于拼接相对URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = None

    def prepare_request(
        self,
        interface: Any,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """准备HTTP请求参数

        Args:
            interface: 接口对象，包含method、url、headers等
            token: 认证Token

        Returns:
            dict: 包含请求参数的字典
        """
        # 构建完整的URL
        url = self._build_url(interface.url)

        # 准备请求头
        headers = self._prepare_headers(interface.headers, token)

        # 准备请求数据
        request_data = self._prepare_request_data(interface)

        return {
            'method': interface.method.upper(),
            'url': url,
            'headers': headers,
            'params': interface.params,
            'json': interface.body if interface.body else None,
            'timeout': self.timeout,
        }

    def _build_url(self, url: str) -> str:
        """构建完整的URL

        Args:
            url: 接口URL（可能是相对路径）

        Returns:
            str: 完整的URL
        """
        if self.base_url and not url.startswith(('http://', 'https://')):
            return urljoin(self.base_url.rstrip('/') + '/', url.lstrip('/'))
        return url

    def _prepare_headers(
        self,
        headers: Dict[str, Any],
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """准备请求头

        Args:
            headers: 基础请求头
            token: 认证Token

        Returns:
            dict: 完整的请求头
        """
        result = headers.copy() if headers else {}

        # 添加默认Content-Type
        if 'Content-Type' not in result and 'content-type' not in result:
            result['Content-Type'] = 'application/json'

        # 添加认证Token
        if token:
            # 尝试常见的认证头
            auth_headers = ['Authorization', 'authorization', 'Auth-Token']
            for auth_header in auth_headers:
                if auth_header not in result:
                    result[auth_header] = f"Bearer {token}"
                    break

        # 添加User-Agent
        if 'User-Agent' not in result and 'user-agent' not in result:
            result['User-Agent'] = 'Interface-Monitor/1.0'

        return result

    def _prepare_request_data(self, interface: Any) -> Dict[str, Any]:
        """准备请求数据

        Args:
            interface: 接口对象

        Returns:
            dict: 请求数据
        """
        data = {}

        # 添加查询参数
        if interface.params:
            data['params'] = interface.params

        # 添加请求体
        if interface.body:
            data['json'] = interface.body

        return data

    def cleanup(self):
        """清理资源"""
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
