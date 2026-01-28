"""
认证模块单元测试

作者: 开发团队
创建时间: 2026-01-28
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from unittest.mock import Mock, patch, MagicMock
import time

from auth.token_manager import TokenManager
from auth.cache import TokenCache
from auth.models.token import TokenInfo


class TestTokenCache:
    """Token缓存测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        cache = TokenCache()

        assert cache._cache == {}
        assert cache._max_size == 1000

    def test_init_custom_max_size(self):
        """测试自定义最大大小初始化"""
        cache = TokenCache(max_size=500)

        assert cache._max_size == 500

    def test_get_token_exists(self):
        """测试获取存在的token"""
        cache = TokenCache()
        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )
        cache._cache['test_service'] = token

        result = cache.get_token('test_service')

        assert result == token

    def test_get_token_not_exists(self):
        """测试获取不存在的token"""
        cache = TokenCache()

        result = cache.get_token('nonexistent')

        assert result is None

    def test_get_token_expired(self):
        """测试获取过期的token"""
        cache = TokenCache()
        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() - 100,  # 已过期
        )
        cache._cache['test_service'] = token

        result = cache.get_token('test_service')

        assert result is None

    def test_set_token(self):
        """测试设置token"""
        cache = TokenCache()
        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )

        cache.set_token('test_service', token)

        assert 'test_service' in cache._cache
        assert cache._cache['test_service'] == token

    def test_remove_token(self):
        """测试移除token"""
        cache = TokenCache()
        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )
        cache._cache['test_service'] = token

        cache.remove_token('test_service')

        assert 'test_service' not in cache._cache

    def test_clear_cache(self):
        """测试清空缓存"""
        cache = TokenCache()
        cache._cache['service1'] = Mock()
        cache._cache['service2'] = Mock()

        cache.clear()

        assert len(cache._cache) == 0

    def test_get_stats(self):
        """测试获取统计信息"""
        cache = TokenCache()
        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )
        cache._cache['test_service'] = token

        stats = cache.get_stats()

        assert stats['total_tokens'] == 1
        assert stats['max_size'] == 1000
        assert stats['usage_percent'] == 0.1  # 1/1000 * 100

    def test_evict_expired(self):
        """测试驱逐过期token"""
        cache = TokenCache()
        # 添加过期token
        expired_token = TokenInfo(
            access_token='expired_token',
            refresh_token='refresh',
            expires_at=time.time() - 100,
        )
        cache._cache['expired'] = expired_token

        # 添加有效token
        valid_token = TokenInfo(
            access_token='valid_token',
            refresh_token='refresh',
            expires_at=time.time() + 3600,
        )
        cache._cache['valid'] = valid_token

        evicted = cache.evict_expired()

        assert evicted == 1
        assert 'expired' not in cache._cache
        assert 'valid' in cache._cache


class TestTokenManager:
    """Token管理器测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        manager = TokenManager()

        assert manager._providers == {}
        assert manager._cache is not None
        assert manager._default_provider is None

    def test_register_provider(self):
        """测试注册provider"""
        manager = TokenManager()

        mock_provider = Mock()
        manager.register_provider('test_service', mock_provider)

        assert 'test_service' in manager._providers
        assert manager._providers['test_service'] == mock_provider

    def test_register_provider_exists(self):
        """测试注册已存在的provider"""
        manager = TokenManager()

        mock_provider1 = Mock()
        mock_provider2 = Mock()
        manager.register_provider('test_service', mock_provider1)
        manager.register_provider('test_service', mock_provider2)

        # 覆盖
        assert manager._providers['test_service'] == mock_provider2

    @patch('auth.token_manager.HTTPExecutor')
    def test_get_token_success(self, mock_executor):
        """测试成功获取token"""
        manager = TokenManager()

        mock_provider = Mock()
        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )
        mock_provider.get_token.return_value = token
        manager.register_provider('test_service', mock_provider)

        result = manager.get_token('test_service')

        assert result == token
        mock_provider.get_token.assert_called_once()

    @patch('auth.token_manager.HTTPExecutor')
    def test_get_token_from_cache(self, mock_executor):
        """测试从缓存获取token"""
        manager = TokenManager()

        # 直接设置缓存
        token = TokenInfo(
            access_token='cached_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )
        manager._cache.set_token('test_service', token)

        mock_provider = Mock()
        manager.register_provider('test_service', mock_provider)

        result = manager.get_token('test_service')

        assert result == token
        # 不会调用provider
        mock_provider.get_token.assert_not_called()

    @patch('auth.token_manager.HTTPExecutor')
    def test_get_token_expired_refresh(self, mock_executor):
        """测试token过期后刷新"""
        manager = TokenManager()

        # 设置过期token
        expired_token = TokenInfo(
            access_token='expired_token',
            refresh_token='refresh_token',
            expires_at=time.time() - 100,
        )
        manager._cache.set_token('test_service', expired_token)

        # 设置新token
        new_token = TokenInfo(
            access_token='new_token',
            refresh_token='new_refresh',
            expires_at=time.time() + 3600,
        )
        mock_provider = Mock()
        mock_provider.get_token.return_value = new_token
        mock_provider.refresh_token.return_value = new_token
        manager.register_provider('test_service', mock_provider)

        result = manager.get_token('test_service')

        assert result == new_token
        # 会调用刷新
        mock_provider.refresh_token.assert_called_once()

    @patch('auth.token_manager.HTTPExecutor')
    def test_get_token_no_provider(self, mock_executor):
        """测试获取不存在的service的token"""
        manager = TokenManager()

        with pytest.raises(ValueError, match="No provider registered for service"):
            manager.get_token('nonexistent_service')

    @patch('auth.token_manager.HTTPExecutor')
    def test_get_token_provider_error(self, mock_executor):
        """测试provider错误"""
        manager = TokenManager()

        mock_provider = Mock()
        mock_provider.get_token.side_effect = Exception("Network error")
        manager.register_provider('test_service', mock_provider)

        with pytest.raises(Exception, match="Network error"):
            manager.get_token('test_service')

    @patch('auth.token_manager.HTTPExecutor')
    def test_invalidate_token(self, mock_executor):
        """测试使token无效"""
        manager = TokenManager()

        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )
        manager._cache.set_token('test_service', token)

        manager.invalidate_token('test_service')

        # 验证token被移除
        assert manager._cache.get_token('test_service') is None

    @patch('auth.token_manager.HTTPExecutor')
    def test_invalidate_all_tokens(self, mock_executor):
        """测试使所有token无效"""
        manager = TokenManager()

        token1 = TokenInfo(
            access_token='token1',
            refresh_token='refresh1',
            expires_at=time.time() + 3600,
        )
        token2 = TokenInfo(
            access_token='token2',
            refresh_token='refresh2',
            expires_at=time.time() + 3600,
        )

        manager._cache.set_token('service1', token1)
        manager._cache.set_token('service2', token2)

        manager.invalidate_all_tokens()

        # 验证所有token被移除
        assert manager._cache.get_token('service1') is None
        assert manager._cache.get_token('service2') is None

    @patch('auth.token_manager.HTTPExecutor')
    def test_get_token_map(self, mock_executor):
        """测试获取token映射"""
        manager = TokenManager()

        token1 = TokenInfo(
            access_token='token1',
            refresh_token='refresh1',
            expires_at=time.time() + 3600,
        )
        token2 = TokenInfo(
            access_token='token2',
            refresh_token='refresh2',
            expires_at=time.time() + 3600,
        )

        manager._cache.set_token('service1', token1)
        manager._cache.set_token('service2', token2)

        token_map = manager.get_token_map()

        assert token_map == {
            'service1': 'token1',
            'service2': 'token2',
        }

    def test_get_cache_stats(self):
        """测试获取缓存统计信息"""
        manager = TokenManager()

        stats = manager.get_cache_stats()

        assert 'total_tokens' in stats
        assert 'max_size' in stats
        assert 'usage_percent' in stats

    @patch('auth.token_manager.HTTPExecutor')
    def test_refresh_token_success(self, mock_executor):
        """测试成功刷新token"""
        manager = TokenManager()

        mock_provider = Mock()
        new_token = TokenInfo(
            access_token='new_token',
            refresh_token='new_refresh',
            expires_at=time.time() + 3600,
        )
        mock_provider.refresh_token.return_value = new_token
        manager.register_provider('test_service', mock_provider)

        result = manager.refresh_token('test_service', 'old_refresh_token')

        assert result == new_token
        mock_provider.refresh_token.assert_called_once()

    @patch('auth.token_manager.HTTPExecutor')
    def test_refresh_token_no_provider(self, mock_executor):
        """测试刷新不存在的service的token"""
        manager = TokenManager()

        with pytest.raises(ValueError, match="No provider registered for service"):
            manager.refresh_token('nonexistent', 'refresh_token')

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_benchmark_get_token(self, benchmark):
        """基准测试：获取token性能"""
        manager = TokenManager()

        mock_provider = Mock()
        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )
        mock_provider.get_token.return_value = token
        manager.register_provider('test_service', mock_provider)

        # 基准测试
        def get_token_benchmark():
            return manager.get_token('test_service')

        result = benchmark.pedantic(get_token_benchmark, rounds=100, iterations=1)

        assert result == token

    @pytest.mark.performance
    def test_concurrent_token_requests(self):
        """测试并发token请求"""
        import threading

        manager = TokenManager()

        mock_provider = Mock()
        token = TokenInfo(
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=time.time() + 3600,
        )
        mock_provider.get_token.return_value = token
        manager.register_provider('test_service', mock_provider)

        results = []
        errors = []

        def get_token():
            try:
                result = manager.get_token('test_service')
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建10个并发请求
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_token)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(errors) == 0
        assert len(results) == 10
        assert all(r == token for r in results)

    def test_cache_eviction_on_limit(self):
        """测试达到限制时缓存驱逐"""
        cache = TokenCache(max_size=2)

        token1 = TokenInfo(
            access_token='token1',
            refresh_token='refresh1',
            expires_at=time.time() + 3600,
        )
        token2 = TokenInfo(
            access_token='token2',
            refresh_token='refresh2',
            expires_at=time.time() + 3600,
        )
        token3 = TokenInfo(
            access_token='token3',
            refresh_token='refresh3',
            expires_at=time.time() + 3600,
        )

        cache.set_token('service1', token1)
        cache.set_token('service2', token2)
        cache.set_token('service3', token3)

        # 验证最早的可能被驱逐（实际实现可能不同）
        stats = cache.get_stats()
        assert stats['total_tokens'] <= 2
