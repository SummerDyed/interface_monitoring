"""
认证管理模块
提供Token认证管理功能，包括Token获取、缓存、过期检查和自动刷新机制
作者: 开发团队
创建时间: 2026-01-27
"""

from .token_manager import TokenManager
from .cache import TokenCache
from .models.token import TokenInfo
from .providers.base_provider import BaseAuthProvider, AuthProviderError, TokenRefreshError, TokenObtainError

__all__ = [
    'TokenManager',
    'TokenCache',
    'TokenInfo',
    'BaseAuthProvider',
    'AuthProviderError',
    'TokenRefreshError',
    'TokenObtainError'
]
