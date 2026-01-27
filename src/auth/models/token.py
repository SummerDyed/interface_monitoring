"""
Token数据模型
定义Token信息的数据结构和相关操作
作者: 开发团队
创建时间: 2026-01-27
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
import logging


logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Token信息数据模型

    存储Token的详细信息，包括Token值、过期时间、创建时间等。
    提供过期检查和剩余时间计算等方法。
    """

    token: str
    """Token值"""

    expires_at: datetime
    """Token过期时间"""

    service: str
    """服务名称"""

    created_at: datetime = field(default_factory=datetime.now)
    """Token创建时间"""

    refresh_threshold: int = 300
    """刷新阈值（秒），默认提前5分钟预警"""

    metadata: dict = field(default_factory=dict)
    """Token元数据，如用户信息、权限等"""

    def is_expired(self, buffer_seconds: int = 0) -> bool:
        """检查Token是否已过期

        Args:
            buffer_seconds: 缓冲时间（秒），额外的时间缓冲

        Returns:
            bool: Token是否已过期
        """
        now = datetime.now()
        expiry_time = self.expires_at - timedelta(seconds=buffer_seconds)
        is_expired = now >= expiry_time

        if is_expired:
            logger.debug(
                "Token已过期: service=%s, expires_at=%s, now=%s",
                self.service,
                self.expires_at,
                now
            )

        return is_expired

    def needs_refresh(self) -> bool:
        """检查Token是否需要刷新

        根据refresh_threshold判断Token是否接近过期，需要提前刷新。

        Returns:
            bool: Token是否需要刷新
        """
        return self.time_until_expiry() <= self.refresh_threshold

    def time_until_expiry(self) -> int:
        """计算到过期的剩余时间

        Returns:
            int: 剩余时间（秒），负数表示已过期
        """
        now = datetime.now()
        delta = self.expires_at - now
        return int(delta.total_seconds())

    def get_age(self) -> int:
        """获取Token已存在的时间

        Returns:
            int: 已存在时间（秒）
        """
        now = datetime.now()
        delta = now - self.created_at
        return int(delta.total_seconds())

    def extend_expiry(self, additional_seconds: int):
        """延长Token过期时间

        Args:
            additional_seconds: 要延长的秒数
        """
        self.expires_at = self.expires_at + timedelta(seconds=additional_seconds)
        logger.debug(
            "Token过期时间已延长: service=%s, additional_seconds=%d, new_expires_at=%s",
            self.service,
            additional_seconds,
            self.expires_at
        )

    def to_dict(self) -> dict:
        """转换为字典格式

        Returns:
            dict: Token信息的字典表示
        """
        return {
            'token': self.token,
            'expires_at': self.expires_at.isoformat(),
            'service': self.service,
            'created_at': self.created_at.isoformat(),
            'refresh_threshold': self.refresh_threshold,
            'metadata': self.metadata,
            'time_until_expiry': self.time_until_expiry(),
            'age': self.get_age(),
            'needs_refresh': self.needs_refresh()
        }

    def __str__(self) -> str:
        """字符串表示

        Returns:
            str: Token信息的字符串表示
        """
        return (
            f"TokenInfo(service={self.service}, "
            f"expires_at={self.expires_at.isoformat()}, "
            f"time_until_expiry={self.time_until_expiry()}s)"
        )

    def __repr__(self) -> str:
        """详细字符串表示

        Returns:
            str: Token信息的详细字符串表示
        """
        return (
            f"TokenInfo(token='{self.token[:10]}...', "
            f"service='{self.service}', "
            f"expires_at={self.expires_at.isoformat()}, "
            f"created_at={self.created_at.isoformat()}, "
            f"refresh_threshold={self.refresh_threshold}, "
            f"metadata={self.metadata})"
        )
