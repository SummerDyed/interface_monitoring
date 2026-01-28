"""
聚合器子包
提供结果聚合功能

作者: 开发团队
创建时间: 2026-01-27
"""

from .error_aggregator import ErrorAggregator
from .stats_aggregator import StatsAggregator

__all__ = [
    'ErrorAggregator',
    'StatsAggregator',
]
