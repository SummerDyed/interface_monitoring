"""
Token与接口集成测试
测试TokenManager与Interface-pool中接口的集成
验证Token是否可以有效携带到接口请求中
作者: 开发团队
创建时间: 2026-01-27
"""

import pytest
from unittest.mock import Mock, patch
import json
import os
from pathlib import Path

from src.auth.token_manager import TokenManager
from src.auth.providers.base_provider import BaseAuthProvider
from src.auth.models.token import TokenInfo
from src.scanner.models.interface import Interface
from datetime import datetime, timedelta


class MockAuthProvider(BaseAuthProvider):
    """模拟认证提供商"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.token_calls = 0

    def obtain_token(self) -> TokenInfo:
        """获取Token"""
        self.token_calls += 1
        return TokenInfo(
            token=f'mock_token_for_{self.service_name}_{self.token_calls}',
            expires_at=datetime.now() + timedelta(hours=1),
            service=self.service_name
        )

    def refresh_token(self, old_token: str) -> TokenInfo:
        """刷新Token"""
        return TokenInfo(
            token=f'refreshed_token_for_{self.service_name}',
            expires_at=datetime.now() + timedelta(hours=1),
            service=self.service_name
        )


class TestTokenInterfaceIntegration:
    """Token与接口集成测试"""

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
            'nurse': {
                'service_name': 'nurse',
                'token_url': 'http://nurse.com/token',
                'refresh_url': 'http://nurse.com/refresh',
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
            auto_refresh=False
        )

        # 注册模拟提供商
        for service_name, config in services_config.items():
            provider = MockAuthProvider(config)
            manager.register_provider(service_name, provider)

        return manager

    def test_token_injection_into_interface(self, token_manager):
        """测试Token注入到Interface对象"""
        # 创建一个Interface对象（模拟从Interface-pool加载的接口）
        interface = Interface(
            name="获取订单详情",
            method="GET",
            url="http://120.79.173.8:8201/maiban-user/api/v1/user/orders/{orderId}/detail",
            path="/api/v1/user/orders/{orderId}/detail",
            service="user",
            module="订单",
            params={"orderId": 12345}
        )

        # 获取Token
        token = token_manager.get_token('user')

        # 将Token注入到Interface的headers中
        if 'Authorization' not in interface.headers:
            interface.headers['Authorization'] = f'Bearer {token}'

        # 验证Token已正确注入
        assert 'Authorization' in interface.headers
        assert interface.headers['Authorization'] == f'Bearer {token}'
        print(f"[PASS] Token已成功注入Interface: Authorization: {interface.headers['Authorization']}")

    def test_interface_with_existing_headers(self, token_manager):
        """测试带有现有headers的Interface"""
        # 创建一个已有headers的Interface
        interface = Interface(
            name="查询资源分类列表",
            method="GET",
            url="http://120.79.173.8:8201/maiban-admin/admin/api/v1/resource-categories",
            path="/admin/api/v1/resource-categories",
            service="admin",
            module="查询资源分类列表",
            headers={
                "Content-Type": "application/json",
                "X-Custom-Header": "custom-value"
            }
        )

        # 获取Token
        token = token_manager.get_token('admin')

        # 保留现有headers，添加Authorization
        interface.headers['Authorization'] = f'Bearer {token}'

        # 验证headers完整性和Token注入
        assert 'Content-Type' in interface.headers
        assert 'X-Custom-Header' in interface.headers
        assert 'Authorization' in interface.headers
        assert interface.headers['Authorization'] == f'Bearer {token}'
        assert interface.headers['Content-Type'] == 'application/json'
        assert interface.headers['X-Custom-Header'] == 'custom-value'
        print(f"[PASS] 保留现有headers并添加Token: {interface.headers}")

    def test_multiple_services_token_management(self, token_manager):
        """测试多个服务的Token管理"""
        # 创建多个不同服务的接口
        user_interface = Interface(
            name="创建订单",
            method="POST",
            url="http://120.79.173.8:8201/maiban-user/api/v1/user/orders",
            path="/api/v1/user/orders",
            service="user",
            module="订单"
        )

        nurse_interface = Interface(
            name="获取隐私政策",
            method="GET",
            url="http://120.79.173.8:8201/maiban-nurse/api/v1/privacy-policy",
            path="/api/v1/privacy-policy",
            service="nurse",
            module="获取隐私政策"
        )

        admin_interface = Interface(
            name="创建资源分类",
            method="POST",
            url="http://120.79.173.8:8201/maiban-admin/admin/api/v1/resource-categories",
            path="/admin/api/v1/resource-categories",
            service="admin",
            module="查询资源分类列表"
        )

        interfaces = [user_interface, nurse_interface, admin_interface]

        # 为每个接口获取并注入对应的Token
        for interface in interfaces:
            token = token_manager.get_token(interface.service)
            interface.headers['Authorization'] = f'Bearer {token}'

        # 验证每个接口都有正确的Token
        assert user_interface.headers['Authorization'] == f'Bearer {token_manager.get_token("user")}'
        assert nurse_interface.headers['Authorization'] == f'Bearer {token_manager.get_token("nurse")}'
        assert admin_interface.headers['Authorization'] == f'Bearer {token_manager.get_token("admin")}'

        # 验证不同服务的Token不同
        assert user_interface.headers['Authorization'] != nurse_interface.headers['Authorization']
        assert nurse_interface.headers['Authorization'] != admin_interface.headers['Authorization']
        assert user_interface.headers['Authorization'] != admin_interface.headers['Authorization']

        print(f"[PASS] 多服务Token管理正确:")
        print(f"   User Token: {user_interface.headers['Authorization'][:30]}...")
        print(f"   Nurse Token: {nurse_interface.headers['Authorization'][:30]}...")
        print(f"   Admin Token: {admin_interface.headers['Authorization'][:30]}...")

    def test_interface_pool_compatibility(self, token_manager):
        """测试与Interface-pool的兼容性"""
        # 模拟从Interface-pool加载的实际接口文件
        interface_pool_files = [
            {
                'name': '查询资源分类列表',
                'service': 'admin',
                'method': 'GET',
                'url': 'http://120.79.173.8:8201/maiban-admin/admin/api/v1/resource-categories',
                'path': '/admin/api/v1/resource-categories',
                'parameters': {}
            },
            {
                'name': '获取订单详情',
                'service': 'user',
                'method': 'GET',
                'url': 'http://120.79.173.8:8201/maiban-user/api/v1/user/orders/{orderId}/detail',
                'path': '/api/v1/user/orders/{orderId}/detail',
                'parameters': {'orderId': 12345}
            },
            {
                'name': '获取当前隐私政策',
                'service': 'nurse',
                'method': 'GET',
                'url': 'http://120.79.173.8:8201/maiban-nurse/api/v1/privacy-policy',
                'path': '/api/v1/privacy-policy',
                'parameters': {}
            }
        ]

        # 转换并添加Token
        interfaces_with_tokens = []
        for file_data in interface_pool_files:
            # 创建Interface对象
            interface = Interface(
                name=file_data['name'],
                method=file_data['method'],
                url=file_data['url'],
                path=file_data['path'],
                service=file_data['service'],
                module=file_data['name'],
                params=file_data.get('parameters', {})
            )

            # 获取Token并注入
            token = token_manager.get_token(interface.service)
            interface.headers['Authorization'] = f'Bearer {token}'

            interfaces_with_tokens.append(interface)

        # 验证所有接口都正确添加了Token
        assert len(interfaces_with_tokens) == 3
        for interface in interfaces_with_tokens:
            assert 'Authorization' in interface.headers
            assert interface.headers['Authorization'].startswith('Bearer ')
            print(f"[PASS] {interface.service}接口 '{interface.name}' Token: {interface.headers['Authorization'][:40]}...")

    def test_token_refresh_and_interface_reuse(self, token_manager):
        """测试Token刷新后接口重用的Token"""
        # 创建接口
        interface = Interface(
            name="获取订单详情",
            method="GET",
            url="http://120.79.173.8:8201/maiban-user/api/v1/user/orders/{orderId}/detail",
            path="/api/v1/user/orders/{orderId}/detail",
            service="user",
            module="订单"
        )

        # 首次获取Token
        token1 = token_manager.get_token('user')
        interface.headers['Authorization'] = f'Bearer {token1}'
        first_token = interface.headers['Authorization']

        # 强制刷新Token
        token2 = token_manager.get_token('user', force_refresh=True)

        # 更新接口的Token
        interface.headers['Authorization'] = f'Bearer {token2}'

        # 验证Token已更新
        assert first_token != interface.headers['Authorization']
        assert interface.headers['Authorization'] == f'Bearer {token2}'
        print(f"[PASS] Token刷新后接口Token已更新: {interface.headers['Authorization'][:40]}...")

    def test_cache_hit_rate_with_interfaces(self, token_manager):
        """测试使用接口时的缓存命中率"""
        # 创建多个接口
        interfaces = []
        for i in range(5):
            interface = Interface(
                name=f"测试接口{i}",
                method="GET",
                url=f"http://example.com/api/test{i}",
                path=f"/api/test{i}",
                service="user",
                module="测试"
            )
            interfaces.append(interface)

        # 第一次获取：所有Token都需要从提供商获取
        for interface in interfaces:
            token = token_manager.get_token('user')
            interface.headers['Authorization'] = f'Bearer {token}'

        # 检查初始统计
        stats = token_manager.get_stats()
        initial_requests = stats['total_requests']
        initial_misses = stats['cache_misses']

        # 再次获取相同服务的Token：应该从缓存获取
        for interface in interfaces:
            token = token_manager.get_token('user')
            interface.headers['Authorization'] = f'Bearer {token}'

        # 检查更新后的统计
        stats = token_manager.get_stats()
        final_requests = stats['total_requests']
        final_misses = stats['cache_misses']
        hits = stats['cache_hits']

        # 验证缓存命中率
        assert final_requests > initial_requests
        assert final_misses == initial_misses  # 缓存miss没有增加
        assert hits >= 5  # 至少有5次缓存命中
        assert stats['cache_hit_rate'] > 0  # 缓存命中率大于0

        print(f"[PASS] 缓存命中率统计: 总请求={final_requests}, 命中={hits}, 未命中={final_misses}, 命中率={stats['cache_hit_rate']:.2%}")


if __name__ == '__main__':
    # 运行示例测试
    print("=" * 60)
    print("Token与Interface-pool集成测试")
    print("=" * 60)
    pytest.main([__file__, '-v', '-s'])
