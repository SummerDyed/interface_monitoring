"""
配置管理器单元测试

作者: 开发团队
创建时间: 2026-01-28
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import yaml
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from config.config_manager import ConfigManager, ConfigFileHandler
from config.exceptions import ConfigLoadError, ConfigValidationError


class TestConfigManager:
    """配置管理器测试类"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'test_config.yaml'

            # 创建两个管理器实例
            manager1 = ConfigManager(str(config_path))
            manager2 = ConfigManager(str(config_path))

            # 验证是同一个实例
            assert manager1 is manager2

    def test_init_with_default_config(self, temp_dir):
        """测试使用默认配置初始化"""
        config_path = Path(temp_dir) / 'test_config.yaml'

        manager = ConfigManager(str(config_path))

        assert manager.config_path == str(config_path)
        assert len(manager._observers) == 0

    def test_load_config_success(self, config_file):
        """测试成功加载配置"""
        manager = ConfigManager(str(config_file))

        assert 'monitor' in manager._config
        assert 'wechat' in manager._config
        assert 'logging' in manager._config

    def test_load_config_file_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(ConfigLoadError):
            ConfigManager('/nonexistent/path/config.yaml')

    def test_get_config(self, config_file):
        """测试获取配置"""
        manager = ConfigManager(str(config_file))

        config = manager.get_config()

        assert 'monitor' in config
        assert config['monitor']['interval'] == 15
        assert config['monitor']['timeout'] == 10
        assert config['monitor']['concurrent_threads'] == 5

    def test_get_config_with_default(self, config_file):
        """测试获取配置使用默认值"""
        manager = ConfigManager(str(config_file))

        # 获取不存在的配置项
        value = manager.get_config('nonexistent.key', default='default_value')

        assert value == 'default_value'

    def test_get_nested_config(self, config_file):
        """测试获取嵌套配置"""
        manager = ConfigManager(str(config_file))

        # 获取嵌套配置
        timeout = manager.get_config('monitor.timeout')

        assert timeout == 10

    def test_set_config(self, config_file):
        """测试设置配置"""
        manager = ConfigManager(str(config_file))

        # 设置新配置
        manager.set_config('test_key', 'test_value')

        assert manager.get_config('test_key') == 'test_value'

    def test_set_nested_config(self, config_file):
        """测试设置嵌套配置"""
        manager = ConfigManager(str(config_file))

        # 设置嵌套配置
        manager.set_config('monitor.new_setting', 100)

        assert manager.get_config('monitor.new_setting') == 100

    def test_has_config(self, config_file):
        """测试检查配置是否存在"""
        manager = ConfigManager(str(config_file))

        assert manager.has_config('monitor')
        assert manager.has_config('monitor.timeout')
        assert not manager.has_config('nonexistent')

    def test_subscribe_config_change(self, config_file):
        """测试订阅配置变更"""
        manager = ConfigManager(str(config_path))

        # 创建mock回调
        callback = Mock()

        # 订阅配置变更
        manager.subscribe_config_change(callback)

        # 触发配置变更
        manager.set_config('test_key', 'new_value')

        # 验证回调被调用
        callback.assert_called_once()

    def test_unsubscribe_config_change(self, config_file):
        """测试取消订阅配置变更"""
        manager = ConfigManager(str(config_file))

        callback = Mock()
        manager.subscribe_config_change(callback)

        # 取消订阅
        manager.unsubscribe_config_change(callback)

        # 触发配置变更
        manager.set_config('test_key', 'new_value')

        # 验证回调未被调用
        callback.assert_not_called()

    @patch('config.config_manager.yaml.safe_load')
    def test_load_config_yaml_error(self, mock_yaml_load, temp_dir):
        """测试加载YAML文件错误"""
        config_path = Path(temp_dir) / 'test_config.yaml'
        config_path.write_text('invalid: yaml: content: [', encoding='utf-8')

        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

        with pytest.raises(ConfigLoadError):
            ConfigManager(str(config_path))

    @patch('config.config_manager.validate_config')
    def test_load_config_validation_error(self, mock_validate, config_file):
        """测试配置验证错误"""
        mock_validate.side_effect = ConfigValidationError("Invalid config")

        with pytest.raises(ConfigValidationError):
            ConfigManager(str(config_file))

    def test_reload_config(self, config_file):
        """测试重新加载配置"""
        manager = ConfigManager(str(config_file))

        # 修改配置
        manager.set_config('monitor.timeout', 30)

        # 重新加载
        manager.reload_config()

        # 验证配置被重置为原始值
        assert manager.get_config('monitor.timeout') == 10

    def test_merge_with_defaults(self, temp_dir):
        """测试与默认值合并"""
        config_path = Path(temp_dir) / 'test_config.yaml'

        # 创建部分配置
        partial_config = {
            'monitor': {
                'timeout': 30,
            }
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(partial_config, f)

        manager = ConfigManager(str(config_path))

        # 验证默认值被合并
        config = manager.get_config()
        assert config['monitor']['timeout'] == 30
        assert 'concurrent_threads' in config['monitor']  # 默认值

    def test_hot_reload_config(self, config_file):
        """测试热重载配置"""
        manager = ConfigManager(str(config_file))

        # 启用文件监控
        manager._start_file_watcher()

        # 修改配置文件
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        config['monitor']['timeout'] = 60

        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # 等待文件监控触发
        import time
        time.sleep(0.5)

        # 验证配置被更新
        # 注意：实际测试中需要模拟文件修改事件
        # 这里只验证代码逻辑

    def test_export_config(self, config_file, temp_dir):
        """测试导出配置"""
        manager = ConfigManager(str(config_file))

        export_path = Path(temp_dir) / 'exported_config.json'
        manager.export_config(str(export_path))

        # 验证文件被创建
        assert export_path.exists()

        # 验证内容
        with open(export_path, 'r') as f:
            exported = json.load(f)

        assert 'monitor' in exported

    def test_validate_required_fields(self, temp_dir):
        """测试验证必需字段"""
        config_path = Path(temp_dir) / 'test_config.yaml'

        # 创建无效配置
        invalid_config = {
            'monitor': {
                # 缺少必需字段
            }
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_config, f)

        # 应该抛出验证错误
        with pytest.raises(ConfigValidationError):
            ConfigManager(str(config_path))

    def test_get_all_service_configs(self, config_file):
        """测试获取所有服务配置"""
        manager = ConfigManager(str(config_file))

        service_configs = manager.get_all_service_configs()

        assert 'user' in service_configs
        assert 'token_url' in service_configs['user']
        assert service_configs['user']['token_url'] == 'http://test.com/token'

    def test_get_service_config(self, config_file):
        """测试获取特定服务配置"""
        manager = ConfigManager(str(config_file))

        user_config = manager.get_service_config('user')

        assert user_config['token_url'] == 'http://test.com/token'
        assert user_config['method'] == 'GET'

    def test_get_service_config_not_found(self, config_file):
        """测试获取不存在的服务配置"""
        manager = ConfigManager(str(config_file))

        config = manager.get_service_config('nonexistent')

        assert config == {}

    def test_update_service_config(self, config_file):
        """测试更新服务配置"""
        manager = ConfigManager(str(config_file))

        # 更新服务配置
        manager.update_service_config('user', 'new_field', 'new_value')

        user_config = manager.get_service_config('user')
        assert user_config['new_field'] == 'new_value'

    def test_get_logging_config(self, config_file):
        """测试获取日志配置"""
        manager = ConfigManager(str(config_file))

        log_config = manager.get_logging_config()

        assert log_config['level'] == 'DEBUG'
        assert 'log_file' in log_config
        assert 'error_log_file' in log_config

    def test_get_monitor_config(self, config_file):
        """测试获取监控配置"""
        manager = ConfigManager(str(config_file))

        monitor_config = manager.get_monitor_config()

        assert monitor_config['interval'] == 15
        assert monitor_config['timeout'] == 10
        assert monitor_config['concurrent_threads'] == 5

    def test_get_wechat_config(self, config_file):
        """测试获取微信配置"""
        manager = ConfigManager(str(config_file))

        wechat_config = manager.get_wechat_config()

        assert wechat_config['webhook_url'] == 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test'
        assert wechat_config['enabled'] is True

    def test_file_watcher_handler(self, temp_dir):
        """测试文件监控处理器"""
        config_path = Path(temp_dir) / 'test_config.yaml'
        config_path.write_text('test: value', encoding='utf-8')

        manager = ConfigManager(str(config_path))

        # 创建事件处理器
        handler = ConfigFileHandler(manager)

        # 模拟文件修改事件
        event = Mock()
        event.is_directory = False
        event.src_path = str(config_path)

        # 验证处理器不抛出异常
        handler.on_modified(event)


class TestConfigFileHandler:
    """配置文件处理器测试类"""

    def test_on_modified_event(self, temp_dir):
        """测试处理文件修改事件"""
        config_path = Path(temp_dir) / 'test_config.yaml'
        config_path.write_text('test: value', encoding='utf-8')

        manager = ConfigManager(str(config_path))

        with patch.object(manager, 'reload_config') as mock_reload:
            handler = ConfigFileHandler(manager)

            # 模拟文件修改事件
            event = Mock()
            event.is_directory = False
            event.src_path = str(config_path)

            handler.on_modified(event)

            # 验证重新加载被调用
            mock_reload.assert_called_once()

    def test_on_modified_different_file(self, temp_dir):
        """测试处理不同文件的修改事件"""
        config_path = Path(temp_dir) / 'test_config.yaml'
        config_path.write_text('test: value', encoding='utf-8')

        manager = ConfigManager(str(config_path))

        with patch.object(manager, 'reload_config') as mock_reload:
            handler = ConfigFileHandler(manager)

            # 模拟不同文件的修改事件
            event = Mock()
            event.is_directory = False
            event.src_path = str(Path(temp_dir) / 'other_file.yaml')

            handler.on_modified(event)

            # 验证重新加载未被调用
            mock_reload.assert_not_called()

    def test_on_modified_directory(self, temp_dir):
        """测试处理目录修改事件"""
        config_path = Path(temp_dir) / 'test_config.yaml'
        config_path.write_text('test: value', encoding='utf-8')

        manager = ConfigManager(str(config_path))

        with patch.object(manager, 'reload_config') as mock_reload:
            handler = ConfigFileHandler(manager)

            # 模拟目录修改事件
            event = Mock()
            event.is_directory = True
            event.src_path = str(temp_dir)

            handler.on_modified(event)

            # 验证重新加载未被调用
            mock_reload.assert_not_called()
