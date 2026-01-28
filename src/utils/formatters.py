"""
自定义日志格式化器
提供统一的日志格式和颜色输出支持
作者: 开发团队
创建时间: 2026-01-26
"""

import logging
from datetime import datetime
from typing import Dict, Any


class LogFormatter(logging.Formatter):
    """自定义日志格式化器"""

    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }

    def __init__(self, format_type: str = 'standard', use_colors: bool = False):
        """
        初始化格式化器

        Args:
            format_type: 格式化类型 ('standard', 'detailed', 'simple')
            use_colors: 是否使用颜色输出
        """
        self.format_type = format_type
        self.use_colors = use_colors

        # 定义格式模板
        if format_type == 'detailed':
            fmt = (
                '%(asctime)s '
                '[%(levelname)s] '
                '%(name)s:%(lineno)d '
                '%(funcName)s() '
                '%(message)s'
            )
        elif format_type == 'simple':
            fmt = '%(message)s'
        else:  # standard
            fmt = (
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        super().__init__(fmt, datefmt='%Y-%m-%d %H:%M:%S')

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            格式化后的日志字符串
        """
        # 添加自定义字段
        record.custom_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 格式化基础信息
        formatted = super().format(record)

        # 添加颜色（如果启用）
        if self.use_colors and hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            formatted = f"{color}{formatted}{reset}"

        return formatted

    def format_exception(self, exc_info) -> str:
        """
        格式化异常信息

        Args:
            exc_info: 异常信息

        Returns:
            格式化的异常字符串
        """
        if self.format_type == 'simple':
            return ''
        return super().format_exception(exc_info)


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化JSON日志记录

        Args:
            record: 日志记录对象

        Returns:
            JSON格式的日志字符串
        """
        import json

        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        # 添加自定义字段
        for key, value in record.__dict__.items():
            if key not in log_obj and not key.startswith('_'):
                log_obj[key] = value

        return json.dumps(log_obj, ensure_ascii=False, default=str)
