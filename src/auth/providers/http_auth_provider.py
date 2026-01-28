"""
HTTP认证提供商
提供基于HTTP请求的Token获取和刷新功能

作者: 开发团队
创建时间: 2026-01-27
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .base_provider import (
    BaseAuthProvider,
    TokenObtainError,
    TokenRefreshError
)
from ..models.token import TokenInfo

logger = logging.getLogger(__name__)


class HTTPAuthProvider(BaseAuthProvider):
    """HTTP认证提供商

    支持基于HTTP请求的Token认证，包括GET和POST方法。
    可以处理简单的Token响应或标准格式响应。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化HTTP认证提供商

        Args:
            config: 服务配置信息，包括：
                - service_name: 服务名称
                - token_url: Token获取接口URL
                - refresh_url: Token刷新接口URL
                - method: 请求方法（GET/POST）
                - headers: 请求头
                - auth_data: 认证数据（POST时使用）
                - response_field: Token字段名（默认data）
        """
        super().__init__(config)

        # 扩展配置
        self.auth_data = config.get('auth_data', {})
        self.response_field = config.get('response_field', 'data')
        self.token_field = config.get('token_field', 'accessToken')

        # 验证配置
        if not self.validate_config():
            raise TokenObtainError(f"认证配置无效: service={self.service_name}")

    def validate_config(self) -> bool:
        """验证配置

        Returns:
            bool: 配置是否有效
        """
        # 基础验证
        if not super().validate_config():
            return False

        # 方法验证
        if self.method not in ['GET', 'POST']:
            logger.error(
                "不支持的认证方法: service=%s, method=%s",
                self.service_name,
                self.method
            )
            return False

        # POST方法需要认证数据
        if self.method == 'POST' and not self.auth_data:
            logger.warning(
                "POST方法未配置认证数据: service=%s",
                self.service_name
            )

        logger.debug(
            "HTTP认证配置验证通过: service=%s, method=%s",
            self.service_name,
            self.method
        )
        return True

    def obtain_token(self) -> TokenInfo:
        """获取Token

        Returns:
            TokenInfo: Token信息

        Raises:
            TokenObtainError: Token获取失败时抛出
        """
        try:
            logger.info(
                "开始获取Token: service=%s, method=%s",
                self.service_name,
                self.method
            )

            # 发起请求
            if self.method == 'GET':
                response = self._make_request(
                    url=self.token_url,
                    method='GET',
                    timeout=30
                )
            elif self.method == 'POST':
                response = self._make_request(
                    url=self.token_url,
                    method='POST',
                    data=self.auth_data,
                    timeout=30
                )
            else:
                raise TokenObtainError(
                    f"不支持的请求方法: {self.method}"
                )

            # 解析响应
            response_data = self._parse_token_response(response)

            # 提取Token
            token_value = self._extract_token(response_data)

            # 计算过期时间（默认1小时）
            expires_in = self.cache_duration
            expires_at = self._calculate_expiry(expires_in)

            # 创建TokenInfo
            token_info = TokenInfo(
                token=token_value,
                expires_at=expires_at,
                service=self.service_name
            )

            logger.info(
                "Token获取成功: service=%s, expires_at=%s",
                self.service_name,
                expires_at.isoformat()
            )

            return token_info

        except Exception as e:
            error_msg = f"Token获取失败: service={self.service_name}, error={str(e)}"
            logger.error(error_msg)
            raise TokenObtainError(error_msg) from e

    def refresh_token(self, old_token: str) -> TokenInfo:
        """刷新Token

        Args:
            old_token: 旧的Token值

        Returns:
            TokenInfo: 新的Token信息

        Raises:
            TokenRefreshError: Token刷新失败时抛出
        """
        try:
            # 如果没有刷新URL，使用获取接口
            refresh_url = self.refresh_url or self.token_url

            logger.info(
                "开始刷新Token: service=%s, method=%s",
                self.service_name,
                self.method
            )

            # 准备刷新数据
            refresh_data = self.auth_data.copy()
            if old_token:
                refresh_data['refresh_token'] = old_token

            # 发起请求
            if self.method == 'GET':
                response = self._make_request(
                    url=refresh_url,
                    method='GET',
                    timeout=30
                )
            elif self.method == 'POST':
                response = self._make_request(
                    url=refresh_url,
                    method='POST',
                    data=refresh_data,
                    timeout=30
                )
            else:
                raise TokenRefreshError(
                    f"不支持的请求方法: {self.method}"
                )

            # 解析响应
            response_data = self._parse_token_response(response)

            # 提取Token
            token_value = self._extract_token(response_data)

            # 计算过期时间
            expires_at = self._calculate_expiry(self.cache_duration)

            # 创建TokenInfo
            token_info = TokenInfo(
                token=token_value,
                expires_at=expires_at,
                service=self.service_name
            )

            logger.info(
                "Token刷新成功: service=%s, expires_at=%s",
                self.service_name,
                expires_at.isoformat()
            )

            return token_info

        except Exception as e:
            error_msg = f"Token刷新失败: service={self.service_name}, error={str(e)}"
            logger.error(error_msg)
            raise TokenRefreshError(error_msg) from e

    def _extract_token(self, response_data: Dict[str, Any]) -> str:
        """从响应数据中提取Token

        Args:
            response_data: 响应数据

        Returns:
            str: Token值

        Raises:
            TokenObtainError: Token提取失败时抛出
        """
        try:
            # 尝试从响应字段提取
            if self.response_field in response_data:
                data = response_data[self.response_field]

                # 如果data是字典，尝试获取token字段
                if isinstance(data, dict) and self.token_field in data:
                    token = data[self.token_field]
                # 如果data直接是字符串
                elif isinstance(data, str):
                    token = data
                else:
                    # 尝试整个响应作为Token
                    token = str(data)
            else:
                # 尝试从响应根级别获取
                if self.token_field in response_data:
                    token = response_data[self.token_field]
                else:
                    # 尝试其他常见字段名
                    for field in ['token', 'access_token', 'accessToken']:
                        if field in response_data:
                            token = response_data[field]
                            break
                    else:
                        raise TokenObtainError(
                            f"响应中未找到Token字段: service={self.service_name}, "
                            f"response={response_data}"
                        )

            if not token:
                raise TokenObtainError(
                    f"Token值为空: service={self.service_name}"
                )

            logger.debug(
                "Token提取成功: service=%s, field=%s",
                self.service_name,
                self.token_field
            )

            return token

        except (KeyError, TypeError) as e:
            error_msg = (
                f"Token提取失败: service={self.service_name}, "
                f"error={str(e)}, response={response_data}"
            )
            logger.error(error_msg)
            raise TokenObtainError(error_msg)

    def __repr__(self) -> str:
        """认证提供商的字符串表示

        Returns:
            str: 认证提供商信息的字符串表示
        """
        return (
            f"HTTPAuthProvider("
            f"service={self.service_name}, "
            f"token_url={self.token_url}, "
            f"method={self.method}, "
            f"response_field={self.response_field}"
            f")"
        )
