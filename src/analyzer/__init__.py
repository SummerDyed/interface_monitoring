"""
结果分析模块
提供监控结果的分析、聚合和报告生成功能

作者: 开发团队
创建时间: 2026-01-27
"""

from .result_analyzer import ResultAnalyzer
from .report_generator import ReportGenerator
from .alert_logic import (
    should_send_alert,
    get_alert_priority,
    get_alert_recipients,
    get_alert_summary,
    get_detailed_alert_content,
    get_alert_content,
    filter_alert_errors,
    process_alert,
)
from .models import MonitorReport, ErrorInfo, Stats, ServiceHealth

__all__ = [
    'ResultAnalyzer',
    'ReportGenerator',
    'should_send_alert',
    'get_alert_priority',
    'get_alert_recipients',
    'get_alert_summary',
    'get_detailed_alert_content',
    'get_alert_content',
    'filter_alert_errors',
    'process_alert',
    'MonitorReport',
    'ErrorInfo',
    'Stats',
    'ServiceHealth',
]
