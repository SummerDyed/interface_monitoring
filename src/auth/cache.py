"""
Token缓存管理器
提供线程安全的Token内存缓存管理
作者: 开发团队
创建时间: 2026-01-27
"""

import threading
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

from .models.token import TokenInfo


logger = logging.getLogger(__name__)


class TokenCache:
    """Token缓存管理器

    提供线程安全的Token内存缓存，支持增删改查操作。
    使用RLock确保多线程环境下的数据一致性。
    """

    def __init__(self, default_ttl: int = 3600):
        """初始化Token缓存

        Args:
            default_ttl: 默认缓存时间（秒）
        """
        self._cache: Dict[str, TokenInfo] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
        logger.debug("Token缓存已初始化，默认TTL=%d秒", default_ttl)

    def get(self, service: str) -> Optional[TokenInfo]:
        """获取Token信息

        Args:
            service: 服务名称

        Returns:
            Optional[TokenInfo]: Token信息，如果不存在或已过期则返回None
        """
        with self._lock:
            token_info = self._cache.get(service)

            if token_info is None:
                logger.debug("缓存中未找到Token: service=%s", service)
                return None

            # 检查Token是否已过期
            if token_info.is_expired():
                logger.debug(
                    "Token已过期将从缓存移除: service=%s, expires_at=%s",
                    service,
                    token_info.expires_at
                )
                self._cache.pop(service, None)
                return None

            logger.debug(
                "从缓存获取Token: service=%s, expires_at=%s, remaining=%ds",
                service,
                token_info.expires_at,
                token_info.time_until_expiry()
            )
            return token_info

    def set(self, service: str, token_info: TokenInfo):
        """设置Token信息

        Args:
            service: 服务名称
            token_info: Token信息
        """
        with self._lock:
            self._cache[service] = token_info
            logger.info(
                "Token已缓存: service=%s, expires_at=%s, remaining=%ds",
                service,
                token_info.expires_at,
                token_info.time_until_expiry()
            )

    def delete(self, service: str):
        """删除Token信息

        Args:
            service: 服务名称
        """
        with self._lock:
            if service in self._cache:
                del self._cache[service]
                logger.debug("已从缓存删除Token: service=%s", service)
            else:
                logger.debug("尝试删除不存在的Token: service=%s", service)

    def clear(self):
        """清空所有缓存

        Warning:
            这是一个危险操作，将删除所有缓存的Token
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.warning("已清空Token缓存，删除了%d个Token", count)

    def exists(self, service: str) -> bool:
        """检查Token是否存在且有效

        Args:
            service: 服务名称

        Returns:
            bool: Token是否存在且有效
        """
        return self.get(service) is not None

    def get_all(self) -> Dict[str, TokenInfo]:
        """获取所有缓存的Token信息

        Returns:
            Dict[str, TokenInfo]: 所有Token信息的字典
        """
        with self._lock:
            # 返回副本，避免外部修改内部缓存
            return self._cache.copy()

    def get_expired_tokens(self) -> Dict[str, TokenInfo]:
        """获取所有已过期的Token

        Returns:
            Dict[str, TokenInfo]: 已过期的Token信息字典
        """
        with self._lock:
            expired = {}
            now = datetime.now()
            for service, token_info in list(self._cache.items()):
                if token_info.expires_at <= now:
                    expired[service] = token_info
            return expired

    def cleanup_expired(self) -> int:
        """清理所有已过期的Token

        Returns:
            int: 清理的Token数量
        """
        with self._lock:
            expired_services = [
                service
                for service, token_info in self._cache.items()
                if token_info.is_expired()
            ]

            for service in expired_services:
                del self._cache[service]

            if expired_services:
                logger.info(
                    "已清理%d个过期Token: services=%s",
                    len(expired_services),
                    expired_services
                )

            return len(expired_services)

    def get_stats(self) -> dict:
        """获取缓存统计信息

        Returns:
            dict: 缓存统计信息
        """
        with self._lock:
            total = len(self._cache)
            expired = len(self.get_expired_tokens())
            valid = total - expired

            # 计算平均剩余时间
            total_remaining = sum(
                token.time_until_expiry()
                for token in self._cache.values()
                if not token.is_expired()
            )
            avg_remaining = total_remaining / valid if valid > 0 else 0

            return {
                'total_tokens': total,
                'valid_tokens': valid,
                'expired_tokens': expired,
                'cache_hit_rate': None,  # 需要外部统计
                'average_remaining_time': avg_remaining
            }

    def size(self) -> int:
        """获取缓存大小

        Returns:
            int: 缓存中的Token数量
        """
        with self._lock:
            return len(self._cache)

    def __len__(self) -> int:
        """获取缓存大小（支持len()函数）

        Returns:
            int: 缓存中的Token数量
        """
        return self.size()

    def __contains__(self, service: str) -> bool:
        """检查Token是否存在（支持in操作符）

        Args:
            service: 服务名称

        Returns:
            bool: Token是否存在且有效
        """
        return self.exists(service)

    def __repr__(self) -> str:
        """缓存的字符串表示

        Returns:
            str: 缓存信息的字符串表示
        """
        stats = self.get_stats()
        return (
            f"TokenCache("
            f"total={stats['total_tokens']}, "
            f"valid={stats['valid_tokens']}, "
            f"expired={stats['expired_tokens']})"
        )
