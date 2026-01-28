"""
性能监控器
提供实时性能指标收集、监控和告警功能

作者: 开发团队
创建时间: 2026-01-28
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import psutil
from .performance_optimizer import PerformanceMetrics


logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'tags': self.tags,
        }


@dataclass
class PerformanceAlert:
    """性能告警"""
    metric: str
    value: float
    threshold: float
    severity: str  # 'warning', 'critical'
    message: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'metric': self.metric,
            'value': self.value,
            'threshold': self.threshold,
            'severity': self.severity,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
        }


class PerformanceMonitor:
    """性能监控器"""

    def __init__(
        self,
        window_size: int = 100,
        alert_thresholds: Optional[Dict[str, float]] = None,
    ):
        """初始化性能监控器

        Args:
            window_size: 滑动窗口大小
            alert_thresholds: 告警阈值
        """
        self.window_size = window_size
        self.alert_thresholds = alert_thresholds or self._default_thresholds()

        # 指标存储
        self.metrics: Dict[str, deque] = {}
        self.alerts: List[PerformanceAlert] = []
        self._lock = threading.Lock()

        # 回调函数
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []

        # 启动时间
        self.start_time = datetime.now()

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"性能监控器初始化完成，窗口大小={window_size}")

    def _default_thresholds(self) -> Dict[str, float]:
        """默认告警阈值"""
        return {
            'response_time_p95': 2.5,  # P95响应时间（秒）
            'memory_usage': 120,  # 内存使用（MB）
            'cpu_usage': 70,  # CPU使用率（%）
            'error_rate': 5.0,  # 错误率（%）
        }

    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ):
        """记录指标

        Args:
            metric_name: 指标名称
            value: 指标值
            tags: 标签
        """
        with self._lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = deque(maxlen=self.window_size)

            point = MetricPoint(
                timestamp=datetime.now(),
                value=value,
                tags=tags or {},
            )
            self.metrics[metric_name].append(point)

            # 检查告警
            self._check_alert(metric_name, value)

    def record_response_time(self, response_time: float, endpoint: Optional[str] = None):
        """记录响应时间"""
        tags = {'endpoint': endpoint} if endpoint else {}
        self.record_metric('response_time', response_time, tags)

    def record_memory_usage(self):
        """记录当前内存使用情况"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.record_metric('memory_usage', memory_mb)

    def record_cpu_usage(self):
        """记录当前CPU使用率"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.record_metric('cpu_usage', cpu_percent)

    def record_concurrent_requests(self, count: int):
        """记录并发请求数"""
        self.record_metric('concurrent_requests', count)

    def record_success_rate(self, success_count: int, total_count: int):
        """记录成功率"""
        if total_count == 0:
            return
        rate = (success_count / total_count) * 100
        self.record_metric('success_rate', rate)

    def _check_alert(self, metric_name: str, value: float):
        """检查告警条件

        Args:
            metric_name: 指标名称
            value: 指标值
        """
        if metric_name not in self.alert_thresholds:
            return

        threshold = self.alert_thresholds[metric_name]
        severity = None
        message = None

        # 确定告警级别
        if metric_name == 'response_time_p95':
            if value > threshold * 1.2:  # 超过阈值20%
                severity = 'critical'
                message = f"P95响应时间严重超标: {value:.2f}s > {threshold}s"
            elif value > threshold:
                severity = 'warning'
                message = f"P95响应时间超标: {value:.2f}s > {threshold}s"

        elif metric_name == 'memory_usage':
            if value > threshold * 1.25:  # 超过阈值25%
                severity = 'critical'
                message = f"内存使用严重超标: {value:.2f}MB > {threshold}MB"
            elif value > threshold:
                severity = 'warning'
                message = f"内存使用超标: {value:.2f}MB > {threshold}MB"

        elif metric_name == 'cpu_usage':
            if value > threshold * 1.25:
                severity = 'critical'
                message = f"CPU使用率严重超标: {value:.1f}% > {threshold}%"
            elif value > threshold:
                severity = 'warning'
                message = f"CPU使用率超标: {value:.1f}% > {threshold}%"

        elif metric_name == 'error_rate':
            if value > threshold * 1.5:
                severity = 'critical'
                message = f"错误率严重超标: {value:.1f}% > {threshold}%"
            elif value > threshold:
                severity = 'warning'
                message = f"错误率超标: {value:.1f}% > {threshold}%"

        # 创建告警
        if severity and message:
            alert = PerformanceAlert(
                metric=metric_name,
                value=value,
                threshold=threshold,
                severity=severity,
                message=message,
                timestamp=datetime.now(),
            )

            with self._lock:
                self.alerts.append(alert)

                # 触发告警回调
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        self.logger.error(f"告警回调执行失败: {e}")

            self.logger.warning(f"性能告警: {message}")

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """添加告警回调函数

        Args:
            callback: 回调函数
        """
        self.alert_callbacks.append(callback)

    def get_metric_stats(
        self,
        metric_name: str,
        window_minutes: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """获取指标统计信息

        Args:
            metric_name: 指标名称
            window_minutes: 时间窗口（分钟）

        Returns:
            统计信息字典
        """
        with self._lock:
            if metric_name not in self.metrics:
                return None

            points = list(self.metrics[metric_name])

            # 过滤时间窗口
            if window_minutes:
                cutoff = datetime.now() - timedelta(minutes=window_minutes)
                points = [p for p in points if p.timestamp >= cutoff]

            if not points:
                return None

            # 计算统计信息
            values = [p.value for p in points]
            values.sort()

            n = len(values)
            stats = {
                'count': n,
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / n,
                'p50': values[int(n * 0.5)],
                'p95': values[int(n * 0.95)] if n > 0 else 0,
                'p99': values[int(n * 0.99)] if n > 0 else 0,
                'window_minutes': window_minutes,
            }

            return stats

    def get_recent_alerts(
        self,
        count: int = 10,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取最近的告警

        Args:
            count: 获取数量
            severity: 过滤严重级别

        Returns:
            告警列表
        """
        with self._lock:
            alerts = self.alerts

            # 按严重级别过滤
            if severity:
                alerts = [a for a in alerts if a.severity == severity]

            # 获取最近的告警
            recent = sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:count]

            return [alert.to_dict() for alert in recent]

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要

        Returns:
            性能摘要字典
        """
        with self._lock:
            summary = {
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'metrics_count': len(self.metrics),
                'alerts_count': len(self.alerts),
                'metric_stats': {},
            }

            # 获取各指标的统计信息
            for metric_name in self.metrics.keys():
                stats = self.get_metric_stats(metric_name, window_minutes=60)
                if stats:
                    summary['metric_stats'][metric_name] = stats

            return summary

    def export_metrics(self, filepath: str):
        """导出指标到文件

        Args:
            filepath: 文件路径
        """
        import json

        data = {
            'export_time': datetime.now().isoformat(),
            'summary': self.get_performance_summary(),
            'metrics': {
                name: [point.to_dict() for point in points]
                for name, points in self.metrics.items()
            },
            'alerts': [alert.to_dict() for alert in self.alerts],
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"指标已导出到: {filepath}")

    def start_monitoring(self, interval_seconds: int = 60):
        """启动定期监控

        Args:
            interval_seconds: 监控间隔（秒）
        """
        def monitor_loop():
            while True:
                try:
                    self.record_memory_usage()
                    self.record_cpu_usage()
                except Exception as e:
                    self.logger.error(f"监控循环错误: {e}")

                time.sleep(interval_seconds)

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

        self.logger.info(f"定期监控已启动，间隔={interval_seconds}秒")

    def stop(self):
        """停止监控"""
        self.logger.info("性能监控器已停止")


# 全局性能监控器实例
_global_monitor = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def set_global_monitor(monitor: PerformanceMonitor):
    """设置全局性能监控器实例

    Args:
        monitor: 监控器实例
    """
    global _global_monitor
    _global_monitor = monitor
