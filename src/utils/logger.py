"""
统一的日志管理系统
提供多级别日志输出、文件和控制台双输出、日志轮转和格式化输出
作者: 开发团队
创建时间: 2026-01-26
"""

import logging
import threading
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, Optional, Any
import sys

from .log_config import LogConfig, parse_size
from .formatters import LogFormatter, JSONFormatter


class LoggerManager:
    """日志管理器，统一管理所有日志实例"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化日志管理器"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._config = LogConfig(config) if config else LogConfig()
        self._lock = threading.RLock()

        # 初始化日志系统
        self._setup_logging()

    def _setup_logging(self):
        """设置日志系统"""
        # 清除现有处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 设置根日志级别
        root_logger.setLevel(getattr(logging, self._config.get_level()))

        # 添加文件处理器
        if self._add_file_handler():
            logging.info("文件日志处理器添加成功")

        # 添加控制台处理器
        if self._config.is_console_enabled():
            self._add_console_handler()

    def _add_file_handler(self) -> bool:
        """
        添加文件处理器

        Returns:
            是否添加成功
        """
        try:
            log_path = Path(self._config.get_file_path())
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # 获取轮转配置
            rotation_config = self._config.get_rotation_config()
            rotation_type = rotation_config.get('type', 'both')
            backup_count = rotation_config.get('backup_count', 7)

            # 创建文件处理器
            if rotation_type in ['size', 'both']:
                max_size = parse_size(rotation_config.get('size', '10MB'))
                handler = RotatingFileHandler(
                    log_path,
                    maxBytes=max_size,
                    backupCount=backup_count,
                    encoding=self._config.get('file.encoding', 'utf-8')
                )
            elif rotation_type == 'time':
                when = rotation_config.get('when', 'midnight')
                handler = TimedRotatingFileHandler(
                    log_path,
                    when=when,
                    backupCount=backup_count,
                    encoding=self._config.get('file.encoding', 'utf-8')
                )
            else:
                # 不轮转
                handler = logging.FileHandler(
                    log_path,
                    encoding=self._config.get('file.encoding', 'utf-8')
                )

            # 设置格式化器
            formatter = self._create_formatter()
            handler.setFormatter(formatter)

            # 设置日志级别
            handler.setLevel(getattr(logging, self._config.get_level()))

            # 添加到根日志器
            logging.getLogger().addHandler(handler)

            # 保存处理器引用
            self._handlers['file'] = handler

            return True

        except Exception as e:
            print(f"添加文件处理器失败: {e}", file=sys.stderr)
            return False

    def _add_console_handler(self):
        """添加控制台处理器"""
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self._config.get_console_level()))

            # 控制台使用带颜色的格式化器
            formatter = self._create_formatter(use_colors=True)
            console_handler.setFormatter(formatter)

            logging.getLogger().addHandler(console_handler)
            self._handlers['console'] = console_handler

        except Exception as e:
            print(f"添加控制台处理器失败: {e}", file=sys.stderr)

    def _create_formatter(self, use_colors: bool = False) -> LogFormatter:
        """
        创建格式化器

        Args:
            use_colors: 是否使用颜色

        Returns:
            格式化器实例
        """
        format_type = self._config.get_format()

        if format_type == 'json':
            return JSONFormatter()
        else:
            return LogFormatter(format_type=format_type, use_colors=use_colors)

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器

        Args:
            name: 日志记录器名称

        Returns:
            日志记录器实例
        """
        with self._lock:
            if name not in self._loggers:
                logger = logging.getLogger(name)
                self._loggers[name] = logger
            return self._loggers[name]

    def set_level(self, level: str):
        """
        设置日志级别

        Args:
            level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        log_level = getattr(logging, level.upper())
        logging.getLogger().setLevel(log_level)

        # 更新所有处理器的级别
        for handler in self._handlers.values():
            handler.setLevel(log_level)

    def add_handler(self, handler: logging.Handler):
        """
        添加日志处理器

        Args:
            handler: 日志处理器
        """
        logging.getLogger().addHandler(handler)

    def rotate_logs(self):
        """手动触发日志轮转"""
        file_handler = self._handlers.get('file')
        if file_handler:
            try:
                if hasattr(file_handler, 'doRollover'):
                    file_handler.doRollover()
                    logging.info("日志轮转完成")
            except Exception as e:
                logging.error(f"日志轮转失败: {e}")

    def reconfigure(self, config: Dict[str, Any]):
        """
        重新配置日志系统

        Args:
            config: 新配置字典
        """
        self._config = LogConfig(config)
        self._setup_logging()

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置

        Returns:
            配置字典
        """
        return self._config.config.copy()

    def cleanup(self):
        """清理资源"""
        with self._lock:
            # 关闭所有处理器
            for handler in self._handlers.values():
                handler.close()

            # 清除日志器
            self._loggers.clear()
            self._handlers.clear()


# 全局日志管理器实例
_logger_manager = None


def initialize(config: Optional[Dict[str, Any]] = None) -> LoggerManager:
    """
    初始化日志系统

    Args:
        config: 配置字典，如果为None则使用默认配置

    Returns:
        日志管理器实例
    """
    global _logger_manager

    if _logger_manager is None:
        _logger_manager = LoggerManager(config)
    elif config:
        # 如果已有实例且提供了新配置，则重新配置
        _logger_manager.reconfigure(config)

    return _logger_manager


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称，默认为调用模块名

    Returns:
        日志记录器实例
    """
    global _logger_manager

    if _logger_manager is None:
        # 如果尚未初始化，使用默认配置初始化
        _logger_manager = LoggerManager()

    if name is None:
        # 获取调用模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'root')

    return _logger_manager.get_logger(name)


def set_level(level: str):
    """
    设置日志级别

    Args:
        level: 日志级别
    """
    global _logger_manager
    if _logger_manager:
        _logger_manager.set_level(level)


def rotate_logs():
    """手动触发日志轮转"""
    global _logger_manager
    if _logger_manager:
        _logger_manager.rotate_logs()


# 便捷函数
def debug(message: str, *args, **kwargs):
    """记录DEBUG级别日志"""
    logger = get_logger()
    logger.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """记录INFO级别日志"""
    logger = get_logger()
    logger.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """记录WARNING级别日志"""
    logger = get_logger()
    logger.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """记录ERROR级别日志"""
    logger = get_logger()
    logger.error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """记录CRITICAL级别日志"""
    logger = get_logger()
    logger.critical(message, *args, **kwargs)
