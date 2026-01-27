"""
认证提供商基类
定义认证提供商的通用接口和基础实现
作者: 开发团队
创建时间: 2026-01-27
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.token import TokenInfo


logger = logging.getLogger(__name__)


class AuthProviderError(Exception):
    """认证提供商异常基类"""
    pass


class TokenRefreshError(AuthProviderError):
    """Token刷新异常"""
    pass


class TokenObtainError(AuthProviderError):
    """Token获取异常"""
    pass


class BaseAuthProvider(ABC):
    """认证提供商基类

    定义了认证提供商需要实现的抽象方法。
    提供通用的HTTP客户端配置和错误处理。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化认证提供商

        Args:
            config: 服务配置信息，包括token_url、refresh_url等
        """
        self.config = config
        self.service_name = config.get('service_name', 'unknown')
        self.token_url = config.get('token_url')
        self.refresh_url = config.get('refresh_url')
        self.method = config.get('method', 'GET').upper()
        self.headers = config.get('headers', {})
        self.cache_duration = config.get('cache_duration', 3600)

        # 配置HTTP会话
        self.session = self._create_session()

        logger.info(
            "认证提供商已初始化: service=%s, token_url=%s, refresh_url=%s, method=%s",
            self.service_name,
            self.token_url,
            self.refresh_url,
            self.method
        )

    def _create_session(self) -> requests.Session:
        """创建HTTP会话

        配置重试策略、超时时间等。

        Returns:
            requests.Session: 配置好的HTTP会话
        """
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置默认超时
        session.timeout = 30

        # 设置默认请求头
        session.headers.update({
            'User-Agent': 'InterfaceMonitoring/1.0',
            'Accept': 'application/json'
        })

        return session

    @abstractmethod
    def obtain_token(self) -> TokenInfo:
        """获取Token

        抽象方法，子类必须实现具体的Token获取逻辑。

        Returns:
            TokenInfo: Token信息

        Raises:
            TokenObtainError: Token获取失败时抛出
        """
        pass

    @abstractmethod
    def refresh_token(self, old_token: str) -> TokenInfo:
        """刷新Token

        抽象方法，子类必须实现具体的Token刷新逻辑。

        Args:
            old_token: 旧的Token值

        Returns:
            TokenInfo: 新的Token信息

        Raises:
            TokenRefreshError: Token刷新失败时抛出
        """
        pass

    def _make_request(
        self,
        url: str,
        method: str = 'GET',
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> requests.Response:
        """发起HTTP请求

        统一的请求方法，包含错误处理和日志记录。

        Args:
            url: 请求URL
            method: 请求方法（GET、POST等）
            data: 请求数据
            headers: 请求头
            timeout: 超时时间（秒）

        Returns:
            requests.Response: 响应对象

        Raises:
            TokenObtainError: 请求失败时抛出
        """
        # 合并请求头
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            logger.debug(
                "发起认证请求: service=%s, method=%s, url=%s",
                self.service_name,
                method,
                url
            )

            if method.upper() == 'GET':
                response = self.session.get(
                    url,
                    headers=request_headers,
                    timeout=timeout
                )
            elif method.upper() == 'POST':
                response = self.session.post(
                    url,
                    json=data,
                    headers=request_headers,
                    timeout=timeout
                )
            else:
                raise TokenObtainError(
                    f"不支持的请求方法: {method}"
                )

            # 记录响应信息
            logger.debug(
                "认证请求响应: service=%s, status=%d, headers=%s",
                self.service_name,
                response.status_code,
                dict(response.headers)
            )

            # 检查响应状态
            if response.status_code != 200:
                error_msg = (
                    f"认证请求失败: service={self.service_name}, "
                    f"status={response.status_code}, "
                    f"response={response.text[:200]}"
                )
                logger.error(error_msg)
                raise TokenObtainError(error_msg)

            return response

        except requests.exceptions.Timeout:
            error_msg = f"认证请求超时: service={self.service_name}, url={url}"
            logger.error(error_msg)
            raise TokenObtainError(error_msg)

        except requests.exceptions.ConnectionError:
            error_msg = f"认证请求连接失败: service={self.service_name}, url={url}"
            logger.error(error_msg)
            raise TokenObtainError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"认证请求异常: service={self.service_name}, error={str(e)}"
            logger.error(error_msg)
            raise TokenObtainError(error_msg)

    def _parse_token_response(self, response: requests.Response) -> Dict[str, Any]:
        """解析Token响应

        子类可以重写此方法以自定义响应解析逻辑。

        Args:
            response: 响应对象

        Returns:
            Dict[str, Any]: 解析后的响应数据

        Raises:
            TokenObtainError: 响应解析失败时抛出
        """
        try:
            return response.json()
        except ValueError as e:
            error_msg = (
                f"Token响应JSON解析失败: service={self.service_name}, "
                f"error={str(e)}"
            )
            logger.error(error_msg)
            raise TokenObtainError(error_msg)

    def _calculate_expiry(self, expires_in: Optional[int] = None) -> datetime:
        """计算Token过期时间

        Args:
            expires_in: Token有效期（秒），如果为None则使用默认缓存时间

        Returns:
            datetime: 过期时间
        """
        if expires_in is None:
            expires_in = self.cache_duration

        expiry = datetime.now() + timedelta(seconds=expires_in)
        logger.debug(
            "Token过期时间计算: service=%s, expires_in=%d, expires_at=%s",
            self.service_name,
            expires_in,
            expiry.isoformat()
        )
        return expiry

    def validate_config(self) -> bool:
        """验证配置

        检查必要的配置项是否齐全。

        Returns:
            bool: 配置是否有效
        """
        if not self.token_url:
            logger.error(
                "认证配置无效: service=%s, 缺少token_url",
                self.service_name
            )
            return False

        logger.debug(
            "认证配置验证通过: service=%s",
            self.service_name
        )
        return True

    def __repr__(self) -> str:
        """认证提供商的字符串表示

        Returns:
            str: 认证提供商信息的字符串表示
        """
        return (
            f"BaseAuthProvider("
            f"service={self.service_name}, "
            f"token_url={self.token_url}, "
            f"refresh_url={self.refresh_url}, "
            f"method={self.method})"
        )
