"""
数据模型子包
提供报告和统计数据的模型定义

作者: 开发团队
创建时间: 2026-01-27
"""

from .report import MonitorReport, ErrorInfo
from .stats import Stats, ServiceHealth

__all__ = [
    'MonitorReport',
    'ErrorInfo',
    'Stats',
    'ServiceHealth',
]
