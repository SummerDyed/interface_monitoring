"""
Token管理器
提供Token获取、缓存、过期检查和自动刷新功能
作者: 开发团队
创建时间: 2026-01-27
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .cache import TokenCache
from .models.token import TokenInfo
from .providers.base_provider import (
    BaseAuthProvider,
    TokenRefreshError,
    TokenObtainError
)


logger = logging.getLogger(__name__)


class TokenManager:
    """Token管理器

    统一管理多个服务的Token认证信息。
    提供Token获取、缓存、过期检查和自动刷新功能。
    支持多服务并发认证和线程安全的缓存访问。
    """

    # 默认配置
    DEFAULT_CONFIG = {
        'refresh_threshold': 300,  # 提前5分钟预警
        'max_workers': 5,  # 最大并发线程数
        'refresh_retry_times': 3,  # 刷新重试次数
        'refresh_retry_delay': 1,  # 重试延迟（秒）
    }

    def __init__(
        self,
        config: Dict,
        services_config: Optional[Dict] = None,
        cache: Optional[TokenCache] = None,
        auto_refresh: bool = True
    ):
        """初始化Token管理器

        Args:
            config: 全局配置
            services_config: 服务配置（services节点）
            cache: Token缓存实例，如果为None则创建新实例
            auto_refresh: 是否启用自动刷新
        """
        self.config = config
        self.services_config = services_config or {}
        self.cache = cache or TokenCache()
        self.auto_refresh = auto_refresh

        # 加载配置
        self.refresh_threshold = config.get(
            'refresh_threshold',
            self.DEFAULT_CONFIG['refresh_threshold']
        )
        self.max_workers = config.get(
            'max_workers',
            self.DEFAULT_CONFIG['max_workers']
        )
        self.refresh_retry_times = config.get(
            'refresh_retry_times',
            self.DEFAULT_CONFIG['refresh_retry_times']
        )
        self.refresh_retry_delay = config.get(
            'refresh_retry_delay',
            self.DEFAULT_CONFIG['refresh_retry_delay']
        )

        # 认证提供商映射
        self._providers: Dict[str, BaseAuthProvider] = {}

        # 自动刷新控制
        self._refresh_thread = None
        self._refresh_lock = threading.RLock()
        self._refresh_interval = 60  # 每分钟检查一次
        self._stop_refresh = False

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'refresh_count': 0,
            'refresh_failures': 0,
            'last_refresh_time': None
        }

        logger.info(
            "TokenManager已初始化: auto_refresh=%s, services=%s",
            auto_refresh,
            list(self.services_config.keys())
        )

    def register_provider(self, service: str, provider: BaseAuthProvider):
        """注册认证提供商

        Args:
            service: 服务名称
            provider: 认证提供商实例
        """
        self._providers[service] = provider
        logger.info("已注册认证提供商: service=%s, provider=%s", service, provider)

    def get_token(self, service: str, force_refresh: bool = False) -> str:
        """获取指定服务的Token

        Args:
            service: 服务名称
            force_refresh: 是否强制刷新Token

        Returns:
            str: Token值

        Raises:
            TokenObtainError: Token获取失败时抛出
        """
        with self._refresh_lock:
            self.stats['total_requests'] += 1

            # 检查缓存
            if not force_refresh:
                cached_token = self.cache.get(service)
                if cached_token:
                    self.stats['cache_hits'] += 1
                    logger.debug(
                        "从缓存获取Token: service=%s, expires_at=%s",
                        service,
                        cached_token.expires_at
                    )
                    return cached_token.token

            self.stats['cache_misses'] += 1

            # 获取或刷新Token
            try:
                if force_refresh:
                    token_info = self._refresh_token_internal(service)
                    logger.info("强制刷新Token成功: service=%s", service)
                else:
                    token_info = self._obtain_token_internal(service)
                    logger.info("首次获取Token成功: service=%s", service)

                # 缓存Token
                self.cache.set(service, token_info)

                return token_info.token

            except Exception as e:
                logger.error(
                    "获取Token失败: service=%s, error=%s",
                    service,
                    str(e)
                )
                raise

    def is_token_expired(self, service: str) -> bool:
        """检查Token是否过期

        Args:
            service: 服务名称

        Returns:
            bool: Token是否过期
        """
        token_info = self.cache.get(service)
        if token_info is None:
            logger.debug("Token不存在: service=%s", service)
            return True

        is_expired = token_info.is_expired()
        logger.debug(
            "Token过期检查: service=%s, is_expired=%s, remaining=%ds",
            service,
            is_expired,
            token_info.time_until_expiry()
        )
        return is_expired

    def needs_refresh(self, service: str) -> bool:
        """检查Token是否需要刷新

        Args:
            service: 服务名称

        Returns:
            bool: Token是否需要刷新
        """
        token_info = self.cache.get(service)
        if token_info is None:
            return True

        needs = token_info.needs_refresh()
        logger.debug(
            "Token刷新检查: service=%s, needs_refresh=%s, remaining=%ds",
            service,
            needs,
            token_info.time_until_expiry()
        )
        return needs

    async def refresh_token(self, service: str) -> bool:
        """刷新指定服务的Token（异步）

        Args:
            service: 服务名称

        Returns:
            bool: 刷新是否成功
        """
        try:
            with self._refresh_lock:
                self._refresh_token_internal(service)
                logger.info("异步刷新Token成功: service=%s", service)
                return True
        except Exception as e:
            logger.error(
                "异步刷新Token失败: service=%s, error=%s",
                service,
                str(e)
            )
            return False

    def _obtain_token_internal(self, service: str) -> TokenInfo:
        """内部Token获取方法

        Args:
            service: 服务名称

        Returns:
            TokenInfo: Token信息
        """
        provider = self._get_provider(service)
        if not provider:
            raise TokenObtainError(f"未找到服务提供商: service={service}")

        if not provider.validate_config():
            raise TokenObtainError(f"认证配置无效: service={service}")

        return provider.obtain_token()

    def _refresh_token_internal(self, service: str, max_retries: int = None) -> TokenInfo:
        """内部Token刷新方法

        Args:
            service: 服务名称
            max_retries: 最大重试次数

        Returns:
            TokenInfo: 新的Token信息
        """
        provider = self._get_provider(service)
        if not provider:
            raise TokenRefreshError(f"未找到服务提供商: service={service}")

        # 获取旧Token
        old_token_info = self.cache.get(service)
        if not old_token_info:
            logger.warning(
                "尝试刷新不存在的Token: service=%s, 将重新获取",
                service
            )
            return self._obtain_token_internal(service)

        old_token = old_token_info.token

        # 计算重试次数
        retries = max_retries or self.refresh_retry_times
        last_error = None

        # 重试刷新
        for attempt in range(retries):
            try:
                logger.debug(
                    "尝试刷新Token: service=%s, attempt=%d/%d",
                    service,
                    attempt + 1,
                    retries
                )

                new_token_info = provider.refresh_token(old_token)

                # 更新统计
                self.stats['refresh_count'] += 1
                self.stats['last_refresh_time'] = datetime.now()

                logger.info(
                    "Token刷新成功: service=%s, expires_at=%s",
                    service,
                    new_token_info.expires_at
                )

                return new_token_info

            except Exception as e:
                last_error = e
                logger.warning(
                    "Token刷新失败（尝试 %d/%d）: service=%s, error=%s",
                    attempt + 1,
                    retries,
                    service,
                    str(e)
                )

                # 最后一次尝试后不再等待
                if attempt < retries - 1:
                    time.sleep(self.refresh_retry_delay * (attempt + 1))

        # 所有重试都失败
        self.stats['refresh_failures'] += 1
        error_msg = (
            f"Token刷新最终失败（已重试{retries}次）: "
            f"service={service}, error={str(last_error)}"
        )
        logger.error(error_msg)
        raise TokenRefreshError(error_msg)

    def _get_provider(self, service: str) -> Optional[BaseAuthProvider]:
        """获取认证提供商

        Args:
            service: 服务名称

        Returns:
            Optional[BaseAuthProvider]: 认证提供商实例
        """
        return self._providers.get(service)

    def start_auto_refresh(self):
        """启动自动刷新线程

        Warning:
            只在主线程调用一次
        """
        if not self.auto_refresh:
            logger.info("自动刷新已禁用")
            return

        if self._refresh_thread and self._refresh_thread.is_alive():
            logger.warning("自动刷新线程已在运行")
            return

        self._stop_refresh = False
        self._refresh_thread = threading.Thread(
            target=self._auto_refresh_worker,
            name="TokenAutoRefresh",
            daemon=True
        )
        self._refresh_thread.start()

        logger.info("自动刷新线程已启动")

    def stop_auto_refresh(self):
        """停止自动刷新线程"""
        self._stop_refresh = True
        if self._refresh_thread and self._refresh_thread.is_alive():
            # 等待线程结束，设置较短的超时时间
            self._refresh_thread.join(timeout=1)
            logger.info("自动刷新线程已停止")

    def _auto_refresh_worker(self):
        """自动刷新工作线程"""
        logger.info("自动刷新工作线程已启动")

        while not self._stop_refresh:
            try:
                # 清理过期Token
                self.cache.cleanup_expired()

                # 检查需要刷新的Token
                services_to_refresh = [
                    service
                    for service in self.cache.get_all()
                    if self.needs_refresh(service)
                ]

                if services_to_refresh:
                    logger.debug(
                        "发现需要刷新的Token: services=%s",
                        services_to_refresh
                    )

                    # 并发刷新
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = {
                            executor.submit(
                                self._refresh_token_internal,
                                service
                            ): service
                            for service in services_to_refresh
                        }

                        for future in as_completed(futures):
                            service = futures[future]
                            try:
                                future.result()
                            except Exception as e:
                                logger.error(
                                    "后台刷新Token失败: service=%s, error=%s",
                                    service,
                                    str(e)
                                )

            except Exception as e:
                logger.error(
                    "自动刷新工作线程异常: error=%s",
                    str(e)
                )

            # 等待下次检查
            time.sleep(self._refresh_interval)

        logger.info("自动刷新工作线程已退出")

    def get_token_info(self, service: str) -> Optional[TokenInfo]:
        """获取Token详细信息

        Args:
            service: 服务名称

        Returns:
            Optional[TokenInfo]: Token详细信息
        """
        return self.cache.get(service)

    def get_all_tokens(self) -> Dict[str, TokenInfo]:
        """获取所有Token信息

        Returns:
            Dict[str, TokenInfo]: 所有Token信息的字典
        """
        return self.cache.get_all()

    def revoke_token(self, service: str):
        """撤销Token（从缓存中删除）

        Args:
            service: 服务名称
        """
        self.cache.delete(service)
        logger.info("Token已撤销: service=%s", service)

    def clear_all_tokens(self):
        """清空所有Token"""
        self.cache.clear()
        logger.warning("所有Token已清空")

    def get_stats(self) -> Dict:
        """获取统计信息

        Returns:
            Dict: 统计信息
        """
        cache_stats = self.cache.get_stats()
        hit_rate = (
            self.stats['cache_hits'] / self.stats['total_requests']
            if self.stats['total_requests'] > 0
            else 0
        )

        return {
            **self.stats,
            'cache_hit_rate': hit_rate,
            'cache_stats': cache_stats,
            'auto_refresh_enabled': self.auto_refresh,
            'auto_refresh_running': (
                self._refresh_thread is not None
                and self._refresh_thread.is_alive()
            )
        }

    def __enter__(self):
        """进入上下文管理器

        Returns:
            TokenManager: TokenManager实例
        """
        self.start_auto_refresh()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        self.stop_auto_refresh()

    def __repr__(self) -> str:
        """TokenManager的字符串表示

        Returns:
            str: TokenManager信息的字符串表示
        """
        return (
            f"TokenManager("
            f"services={list(self.services_config.keys())}, "
            f"cached={len(self.cache)}, "
            f"auto_refresh={self.auto_refresh})"
        )
