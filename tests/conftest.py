"""
pytest配置文件
提供全局测试配置、fixtures和工具函数

作者: 开发团队
创建时间: 2026-01-28
"""

import pytest
import tempfile
import os
import json
from typing import Dict, List, Any
from pathlib import Path


@pytest.fixture
def temp_dir():
    """创建临时目录fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def config_file(temp_dir):
    """创建测试配置文件fixture"""
    config = {
        'monitor': {
            'interval': 15,
            'timeout': 10,
            'concurrent_threads': 5,
            'retry_times': 3,
            'interface_pool_path': './Interface-pool',
        },
        'wechat': {
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test',
            'enabled': True,
            'at_users': ['user1'],
            'message_format': 'simple',
        },
        'logging': {
            'level': 'DEBUG',
            'log_file': './logs/test.log',
            'error_log_file': './logs/test_error.log',
        },
        'services': {
            'user': {
                'token_url': 'http://test.com/token',
                'refresh_url': 'http://test.com/refresh',
                'method': 'GET',
                'headers': {'Accept': '*/*'},
                'cache_duration': 3600,
                'interface_path': './Interface-pool/user',
            }
        }
    }

    config_path = Path(temp_dir) / 'test_config.yaml'
    import yaml
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    yield config_path

    # 清理
    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def mock_interfaces():
    """创建模拟接口列表fixture"""
    class MockInterface:
        def __init__(self, name, service, method='GET', path='/test'):
            self.name = name
            self.service = service
            self.method = method
            self.path = path

    return [
        MockInterface('user_login', 'user', 'POST', '/api/v1/user/login'),
        MockInterface('user_info', 'user', 'GET', '/api/v1/user/info'),
        MockInterface('nurse_list', 'nurse', 'GET', '/api/v1/nurse/list'),
        MockInterface('admin_dashboard', 'admin', 'GET', '/api/v1/admin/dashboard'),
    ]


@pytest.fixture
def mock_token_map():
    """创建模拟Token映射fixture"""
    return {
        'user': 'user_token_123',
        'nurse': 'nurse_token_456',
        'admin': 'admin_token_789',
    }


@pytest.fixture
def sample_response_data():
    """创建示例响应数据fixture"""
    return {
        'success': True,
        'code': 200,
        'message': 'success',
        'data': {
            'user_id': 123,
            'username': 'test_user',
            'status': 'active',
        }
    }


@pytest.fixture
def benchmark_config():
    """性能测试配置fixture"""
    return {
        'iterations': 10,
        'rounds': 3,
        'warmup': True,
        'min_time': 0.1,
        'max_time': 10.0,
    }


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集钩子"""
    for item in items:
        # 自动添加markers基于路径
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        if "slow" in str(item.fspath):
            item.add_marker(pytest.mark.slow)


@pytest.fixture
def performance_monitor():
    """性能监控器fixture"""
    from utils.performance_monitor import PerformanceMonitor
    monitor = PerformanceMonitor(window_size=100)
    yield monitor
    monitor.stop()


@pytest.fixture
def performance_optimizer():
    """性能优化器fixture"""
    from utils.performance_optimizer import PerformanceOptimizer, OptimizationConfig
    config = OptimizationConfig(
        max_concurrent_threads=50,
        thread_pool_size=20,
        batch_size=100,
    )
    optimizer = PerformanceOptimizer(config)
    yield optimizer


@pytest.fixture
def interface_data_dir(temp_dir):
    """创建接口数据目录fixture"""
    data_dir = Path(temp_dir) / 'interface_data'
    data_dir.mkdir(exist_ok=True)

    # 创建user服务目录
    user_dir = data_dir / 'user'
    user_dir.mkdir(exist_ok=True)

    # 创建nurse服务目录
    nurse_dir = data_dir / 'nurse'
    nurse_dir.mkdir(exist_ok=True)

    # 创建admin服务目录
    admin_dir = data_dir / 'admin'
    admin_dir.mkdir(exist_ok=True)

    # 创建示例接口文档
    sample_interfaces = {
        'user': {
            'name': 'user_login',
            'service': 'user',
            'method': 'POST',
            'path': '/api/v1/user/login',
            'headers': {'Content-Type': 'application/json'},
            'body': {'username': 'test', 'password': 'test123'},
            'expected_status': 200,
        },
        'nurse': {
            'name': 'nurse_list',
            'service': 'nurse',
            'method': 'GET',
            'path': '/api/v1/nurse/list',
            'headers': {},
            'expected_status': 200,
        },
        'admin': {
            'name': 'admin_dashboard',
            'service': 'admin',
            'method': 'GET',
            'path': '/api/v1/admin/dashboard',
            'headers': {},
            'expected_status': 200,
        },
    }

    # 保存为JSON文件
    for service, interface in sample_interfaces.items():
        interface_file = data_dir / service / f"{interface['name']}.json"
        with open(interface_file, 'w', encoding='utf-8') as f:
            json.dump(interface, f, indent=2, ensure_ascii=False)

    yield data_dir

    # 清理
    import shutil
    if data_dir.exists():
        shutil.rmtree(data_dir)
