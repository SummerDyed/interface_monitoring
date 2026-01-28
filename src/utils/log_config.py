"""
日志配置管理
提供日志系统的配置参数和默认值管理
作者: 开发团队
创建时间: 2026-01-26
"""

import os
import copy
from typing import Dict, Any, Optional
from pathlib import Path


class LogConfig:
    """日志配置管理器"""

    # 默认配置
    DEFAULT_CONFIG = {
        'level': 'INFO',
        'format': 'standard',
        'use_colors': False,
        'file': {
            'path': 'logs/monitor.log',
            'max_size': '10MB',
            'backup_count': 7,
            'when': 'midnight',
            'encoding': 'utf-8'
        },
        'console': {
            'enabled': True,
            'level': 'INFO'
        },
        'rotation': {
            'type': 'both',  # 'size', 'time', 'both'
            'size': '10MB',
            'when': 'midnight',
            'backup_count': 7
        },
        'performance': {
            'async_write': False,
            'buffer_size': 1024,
            'flush_interval': 5  # 秒
        }
    }

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        初始化配置

        Args:
            config_dict: 配置字典，如果为None则使用默认配置
        """
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        if config_dict:
            self._merge_config(config_dict)

        # 确保logs目录存在
        self._ensure_log_directory()

    def _merge_config(self, user_config: Dict[str, Any]):
        """
        合并用户配置

        Args:
            user_config: 用户配置字典
        """
        def merge_dict(base: dict, update: dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(self.config, user_config)

    def _ensure_log_directory(self):
        """确保日志目录存在"""
        log_path = Path(self.config['file']['path'])
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔符
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键，支持点分隔符
            value: 配置值
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_level(self) -> str:
        """获取日志级别"""
        return self.config['level']

    def get_format(self) -> str:
        """获取日志格式"""
        return self.config['format']

    def is_console_enabled(self) -> bool:
        """检查是否启用控制台输出"""
        return self.config['console']['enabled']

    def get_console_level(self) -> str:
        """获取控制台日志级别"""
        return self.config['console']['level']

    def get_file_path(self) -> str:
        """获取日志文件路径"""
        return self.config['file']['path']

    def get_rotation_config(self) -> Dict[str, Any]:
        """获取轮转配置"""
        return self.config['rotation']

    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self.config['performance']

    @staticmethod
    def from_env() -> 'LogConfig':
        """
        从环境变量创建配置

        Returns:
            LogConfig实例

        环境变量:
            LOG_LEVEL: 日志级别
            LOG_FILE: 日志文件路径
            LOG_CONSOLE: 是否启用控制台输出 (true/false)
        """
        config = {}

        log_level = os.getenv('LOG_LEVEL')
        if log_level:
            config['level'] = log_level

        log_file = os.getenv('LOG_FILE')
        if log_file:
            config.setdefault('file', {})['path'] = log_file

        log_console = os.getenv('LOG_CONSOLE')
        if log_console:
            config.setdefault('console', {})['enabled'] = log_console.lower() == 'true'

        return LogConfig(config)

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> 'LogConfig':
        """
        从字典创建配置

        Args:
            config_dict: 配置字典

        Returns:
            LogConfig实例
        """
        return LogConfig(config_dict)


def parse_size(size_str: str) -> int:
    """
    解析大小字符串为字节数

    Args:
        size_str: 大小字符串，如 '10MB', '1GB'

    Returns:
        字节数

    Raises:
        ValueError: 无法解析大小格式
    """
    size_str = size_str.upper().strip()

    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


def format_size(size_bytes: int) -> str:
    """
    格式化字节数为可读字符串

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"
