"""
配置管理器核心实现
提供配置文件的加载、验证、热更新功能
作者: 开发团队
创建时间: 2026-01-26
"""

import logging
import os
import threading
from typing import Any, Callable, Dict, List
import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .schema import CONFIG_SCHEMA
from .validators import validate_config, merge_with_defaults
from .exceptions import ConfigLoadError, ConfigValidationError, ConfigReloadError


logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更事件处理器"""

    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager

    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory and event.src_path == self.config_manager.config_path:
            logger.info("检测到配置文件变更: %s", event.src_path)
            self.config_manager.reload_config()


class ConfigManager:
    """配置管理器"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, config_path: str = "config.yaml"):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config.yaml"):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        if hasattr(self, '_initialized'):
            return

        self.config_path = os.path.abspath(config_path)
        self._config = {}
        self._observers: List[Callable[[dict, dict], None]] = []
        self._observer = None
        self._initialized = True

        # 初始化时加载配置
        self.load_config()

        # 启动文件监控（如果配置启用）
        self._start_file_watcher()

    def _start_file_watcher(self):
        """启动文件监控"""
        try:
            config_dir = os.path.dirname(self.config_path)
            self._observer = Observer()
            event_handler = ConfigFileHandler(self)
            self._observer.schedule(event_handler, config_dir, recursive=False)
            self._observer.start()
            logger.info("配置热更新监控已启动: %s", self.config_path)
        except Exception as e:
            logger.warning("配置热更新监控启动失败: %s", e)

    def load_config(self) -> Dict[str, Any]:
        """加载并验证配置文件

        Returns:
            dict: 配置字典

        Raises:
            ConfigLoadError: 配置文件加载失败
            ConfigValidationError: 配置验证失败
        """
        try:
            if not os.path.exists(self.config_path):
                logger.error("配置文件不存在: %s", self.config_path)
                raise ConfigLoadError("配置文件不存在: %s", self.config_path)

            logger.info("开始加载配置文件: %s", self.config_path)

            with open(self.config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)

            # 验证配置
            is_valid, errors = validate_config(raw_config, CONFIG_SCHEMA)
            if not is_valid:
                error_msg = "配置验证失败:\n" + "\n".join(
                    f"  - {error}" for error in errors
                )
                logger.error(error_msg)
                raise ConfigValidationError(error_msg)

            # 合并默认值
            self._config = merge_with_defaults(raw_config, CONFIG_SCHEMA)

            logger.info("配置加载并验证成功")
            return self._config

        except yaml.YAMLError as e:
            error_msg = "YAML解析错误: %s", e
            logger.error(error_msg)
            raise ConfigLoadError(error_msg) from e
        except ConfigValidationError:
            raise
        except Exception as e:
            error_msg = "配置加载失败: %s", e
            logger.error(error_msg)
            raise ConfigLoadError(error_msg) from e

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键，支持点分隔符（如 'monitor.interval'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        设置配置项

        Args:
            key: 配置键，支持点分隔符
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        # 导航到父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value
        logger.debug("配置项已设置: %s = %s", key, value)

    def reload_config(self):
        """重新加载配置文件"""
        try:
            old_config = self._config.copy()
            self.load_config()

            # 通知观察者
            self._notify_observers(old_config, self._config)

            logger.info("配置热更新完成")
        except Exception as e:
            error_msg = "配置热更新失败: %s", e
            logger.error(error_msg)
            raise ConfigReloadError(error_msg) from e

    def _notify_observers(self, old_config: dict, new_config: dict):
        """通知所有观察者配置已变更"""
        for callback in self._observers:
            try:
                callback(old_config, new_config)
            except Exception as e:
                logger.error("配置变更通知失败: %s", e)

    def subscribe(self, callback: Callable[[dict, dict], None]):
        """
        订阅配置变更事件

        Args:
            callback: 回调函数，接收 (old_config, new_config) 参数
        """
        self._observers.append(callback)
        logger.debug("新增配置变更观察者: %s", callback.__name__)

    def unsubscribe(self, callback: Callable):
        """取消订阅配置变更事件"""
        if callback in self._observers:
            self._observers.remove(callback)
            logger.debug("移除配置变更观察者: %s", callback.__name__)

    def validate(self) -> tuple[bool, List[str]]:
        """
        验证当前配置

        Returns:
            tuple: (是否验证通过, 错误列表)
        """
        return validate_config(self._config, CONFIG_SCHEMA)

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config

    def get_config_snapshot(self) -> Dict[str, Any]:
        """获取配置快照（只读）"""
        return self._config.copy()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()

    def cleanup(self):
        """清理资源"""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
            logger.info("配置监控已停止")

    def __del__(self):
        """析构函数"""
        self.cleanup()
