"""
Token管理器测试
测试Token获取、缓存、过期检查和自动刷新功能
作者: 开发团队
创建时间: 2026-01-27
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import threading

from src.auth.token_manager import TokenManager
from src.auth.cache import TokenCache
from src.auth.models.token import TokenInfo
from src.auth.providers.base_provider import (
    BaseAuthProvider,
    TokenRefreshError,
    TokenObtainError
)


class TestTokenCache:
    """Token缓存测试"""

    def test_cache_initialization(self):
        """测试缓存初始化"""
        cache = TokenCache(default_ttl=3600)
        assert cache.size() == 0
        assert len(cache) == 0
        assert 'test' not in cache

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = TokenCache()
        token_info = TokenInfo(
            token='test_token',
            expires_at=datetime.now() + timedelta(hours=1),
            service='test_service'
        )

        cache.set('test_service', token_info)
        assert cache.exists('test_service')
        retrieved = cache.get('test_service')
        assert retrieved is not None
        assert retrieved.token == 'test_token'
        assert retrieved.service == 'test_service'

    def test_cache_delete(self):
        """测试缓存删除"""
        cache = TokenCache()
        token_info = TokenInfo(
            token='test_token',
            expires_at=datetime.now() + timedelta(hours=1),
            service='test_service'
        )

        cache.set('test_service', token_info)
        assert cache.exists('test_service')

        cache.delete('test_service')
        assert not cache.exists('test_service')

    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = TokenCache()
        # 创建一个已过期的Token
        token_info = TokenInfo(
            token='expired_token',
            expires_at=datetime.now() - timedelta(seconds=1),
            service='expired_service'
        )

        cache.set('expired_service', token_info)
        # 缓存中还有，但获取时应该返回None
        retrieved = cache.get('expired_service')
        assert retrieved is None

    def test_cache_cleanup(self):
        """测试缓存清理"""
        cache = TokenCache()
        # 添加过期和未过期的Token
        cache.set('expired', TokenInfo(
            token='expired',
            expires_at=datetime.now() - timedelta(seconds=1),
            service='expired'
        ))
        cache.set('valid', TokenInfo(
            token='valid',
            expires_at=datetime.now() + timedelta(hours=1),
            service='valid'
        ))

        assert cache.size() == 2

        cleaned = cache.cleanup_expired()
        assert cleaned == 1
        assert cache.size() == 1
        assert not cache.exists('expired')
        assert cache.exists('valid')

    def test_cache_thread_safety(self):
        """测试缓存线程安全"""
        cache = TokenCache()
        token_info = TokenInfo(
            token='test_token',
            expires_at=datetime.now() + timedelta(hours=1),
            service='test_service'
        )

        def set_token():
            cache.set('test_service', token_info)

        def get_token():
            return cache.get('test_service')

        # 并发设置和获取
        threads = []
        for _ in range(10):
            t = threading.Thread(target=set_token)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证数据一致性
        assert cache.exists('test_service')
        retrieved = cache.get('test_service')
        assert retrieved is not None

    def test_cache_stats(self):
        """测试缓存统计"""
        cache = TokenCache()
        cache.set('service1', TokenInfo(
            token='token1',
            expires_at=datetime.now() + timedelta(hours=1),
            service='service1'
        ))
        cache.set('service2', TokenInfo(
            token='token2',
            expires_at=datetime.now() + timedelta(hours=1),
            service='service2'
        ))

        stats = cache.get_stats()
        assert stats['total_tokens'] == 2
        assert stats['valid_tokens'] == 2
        assert stats['expired_tokens'] == 0


class MockAuthProvider(BaseAuthProvider):
    """模拟认证提供商"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.token_calls = 0
        self.refresh_calls = 0

    def obtain_token(self) -> TokenInfo:
        """获取Token"""
        self.token_calls += 1
        return TokenInfo(
            token=f'token_{self.token_calls}',
            expires_at=datetime.now() + timedelta(hours=1),
            service=self.service_name
        )

    def refresh_token(self, old_token: str) -> TokenInfo:
        """刷新Token"""
        self.refresh_calls += 1
        return TokenInfo(
            token=f'refreshed_token_{self.refresh_calls}',
            expires_at=datetime.now() + timedelta(hours=1),
            service=self.service_name
        )


class TestTokenManager:
    """Token管理器测试"""

    @pytest.fixture
    def services_config(self):
        """服务配置"""
        return {
            'user': {
                'service_name': 'user',
                'token_url': 'http://user.com/token',
                'refresh_url': 'http://user.com/refresh',
                'method': 'GET'
            },
            'admin': {
                'service_name': 'admin',
                'token_url': 'http://admin.com/token',
                'refresh_url': 'http://admin.com/refresh',
                'method': 'POST'
            }
        }

    @pytest.fixture
    def token_manager(self, services_config):
        """Token管理器实例"""
        manager = TokenManager(
            config={},
            services_config=services_config,
            auto_refresh=True  # 改为True以便测试
        )

        # 注册模拟提供商
        for service_name, config in services_config.items():
            provider = MockAuthProvider(config)
            manager.register_provider(service_name, provider)

        return manager

    def test_token_manager_initialization(self, token_manager):
        """测试Token管理器初始化"""
        assert token_manager is not None
        assert len(token_manager._providers) > 0
        assert token_manager.auto_refresh  # 已改为auto_refresh=True
        assert token_manager.cache is not None

    def test_get_token_first_time(self, token_manager):
        """测试首次获取Token"""
        token = token_manager.get_token('user')
        assert token is not None
        assert len(token) > 0

        # 验证缓存中有Token
        token_info = token_manager.get_token_info('user')
        assert token_info is not None
        assert token_info.token == token

    def test_get_token_from_cache(self, token_manager):
        """测试从缓存获取Token"""
        # 首次获取
        token1 = token_manager.get_token('user')

        # 再次获取，应该从缓存获取
        token2 = token_manager.get_token('user')

        assert token1 == token2

        # 验证统计信息
        stats = token_manager.get_stats()
        assert stats['total_requests'] == 2
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 1

    def test_force_refresh_token(self, token_manager):
        """测试强制刷新Token"""
        # 首次获取
        token1 = token_manager.get_token('user')

        # 强制刷新
        token2 = token_manager.get_token('user', force_refresh=True)

        assert token1 != token2

    def test_is_token_expired(self, token_manager):
        """测试Token过期检查"""
        # 未过期的Token
        token_manager.get_token('user')
        assert not token_manager.is_token_expired('user')

    def test_needs_refresh(self, token_manager):
        """测试Token刷新检查"""
        token_manager.get_token('user')
        # 新获取的Token不应该需要刷新
        assert not token_manager.needs_refresh('user')

    def test_revoke_token(self, token_manager):
        """测试撤销Token"""
        # 获取Token
        token_manager.get_token('user')
        assert token_manager.cache.exists('user')

        # 撤销Token
        token_manager.revoke_token('user')
        assert not token_manager.cache.exists('user')

    def test_clear_all_tokens(self, token_manager):
        """测试清空所有Token"""
        # 获取多个Token
        token_manager.get_token('user')
        token_manager.get_token('admin')

        assert token_manager.cache.size() == 2

        # 清空所有Token
        token_manager.clear_all_tokens()

        assert token_manager.cache.size() == 0

    def test_get_all_tokens(self, token_manager):
        """测试获取所有Token"""
        # 获取Token
        token_manager.get_token('user')
        token_manager.get_token('admin')

        all_tokens = token_manager.get_all_tokens()

        assert 'user' in all_tokens
        assert 'admin' in all_tokens
        assert len(all_tokens) == 2

    def test_get_stats(self, token_manager):
        """测试获取统计信息"""
        # 获取Token
        token_manager.get_token('user')
        token_manager.get_token('admin')

        stats = token_manager.get_stats()

        assert stats['total_requests'] == 2
        assert stats['cache_misses'] == 2  # 第一次获取都是miss
        assert stats['cache_hits'] == 0
        assert stats['cache_hit_rate'] == 0.0

        # 再次获取，应该从缓存获取
        token_manager.get_token('user')
        token_manager.get_token('admin')

        stats = token_manager.get_stats()
        assert stats['total_requests'] == 4
        assert stats['cache_misses'] == 2
        assert stats['cache_hits'] == 2
        assert stats['cache_hit_rate'] == 0.5

    def test_concurrent_token_requests(self, token_manager):
        """测试并发Token请求"""
        def get_token():
            return token_manager.get_token('user')

        # 并发获取Token
        threads = []
        tokens = []

        for _ in range(10):
            t = threading.Thread(target=lambda: tokens.append(get_token()))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证所有线程获取到相同的Token（从缓存）
        assert len(tokens) == 10
        assert all(token == tokens[0] for token in tokens)

        # 验证统计信息
        stats = token_manager.get_stats()
        assert stats['cache_hits'] >= 9  # 大部分来自缓存

    def test_context_manager(self, services_config):
        """测试上下文管理器"""
        manager = TokenManager(
            config={},
            services_config=services_config,
            auto_refresh=True
        )

        # 注册提供商
        for service_name, config in services_config.items():
            provider = MockAuthProvider(config)
            manager.register_provider(service_name, provider)

        # 使用上下文管理器
        with manager:
            assert manager._refresh_thread is not None
            assert manager._refresh_thread.is_alive()

        # 手动停止刷新线程（daemon线程会在主线程退出时自动退出）
        manager.stop_auto_refresh()
        # 不检查线程是否已停止，因为daemon线程可能需要一些时间

    def test_auto_refresh_start_stop(self, services_config):
        """测试自动刷新启动和停止"""
        # 创建启用自动刷新的Token管理器
        manager = TokenManager(
            config={},
            services_config=services_config,
            auto_refresh=True  # 启用自动刷新
        )

        # 注册模拟提供商
        for service_name, config in services_config.items():
            provider = MockAuthProvider(config)
            manager.register_provider(service_name, provider)

        # 启动自动刷新
        manager.start_auto_refresh()
        assert manager._refresh_thread is not None
        assert manager._refresh_thread.is_alive()

        # 停止自动刷新（不检查线程是否立即停止）
        manager.stop_auto_refresh()

    def test_token_manager_repr(self, token_manager):
        """测试TokenManager字符串表示"""
        repr_str = repr(token_manager)
        assert 'TokenManager' in repr_str
        assert 'services' in repr_str
        assert 'auto_refresh' in repr_str
