"""
统计聚合器
负责计算各种统计指标和服务健康度

作者: 开发团队
创建时间: 2026-01-27
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import logging

from ..models import Stats, ServiceHealth
from monitor.result import MonitorResult

logger = logging.getLogger(__name__)


class StatsAggregator:
    """统计聚合器

    负责计算监控结果的统计信息，包括总体统计、服务健康度和响应时间分析
    """

    def __init__(self):
        """初始化统计聚合器"""
        pass

    def aggregate(self, results: List[MonitorResult]) -> Stats:
        """聚合监控结果并生成统计信息

        Args:
            results: 监控结果列表（包含成功和失败）

        Returns:
            Stats: 统计信息对象
        """
        if not results:
            logger.warning("监控结果为空，返回默认统计")
            return self._create_empty_stats()

        logger.info(f"开始统计 {len(results)} 个监控结果")

        # 计算总体统计
        stats = self._calculate_overall_stats(results)

        # 计算响应时间统计
        response_times = self._extract_response_times(results)
        stats.calculate_response_time_stats(response_times)

        # 计算各服务健康度
        stats.services = self._calculate_service_health(results)
        stats.calculate_service_health()

        logger.info(
            f"统计完成: 总数={stats.total_count}, 成功率={stats.success_rate:.2f}%"
        )

        return stats

    def _calculate_overall_stats(self, results: List[MonitorResult]) -> Stats:
        """计算总体统计

        Args:
            results: 监控结果列表

        Returns:
            Stats: 包含总体统计的Stats对象
        """
        total_count = len(results)
        success_count = sum(1 for r in results if r.is_success())
        failure_count = total_count - success_count

        # 计算错误类型分布
        error_types = defaultdict(int)
        for result in results:
            if result.error_type:
                error_types[result.error_type] += 1

        stats = Stats(
            total_count=total_count,
            success_count=success_count,
            failure_count=failure_count,
            error_types=dict(error_types),
            timestamp=datetime.now(),
        )

        # 计算成功率
        stats.calculate_success_rate()

        return stats

    def _extract_response_times(self, results: List[MonitorResult]) -> List[float]:
        """提取响应时间

        Args:
            results: 监控结果列表

        Returns:
            List[float]: 响应时间列表（毫秒）
        """
        response_times = []
        for result in results:
            if result.response_time > 0:
                response_times.append(result.response_time)

        return response_times

    def _calculate_service_health(
        self, results: List[MonitorResult]
    ) -> List[ServiceHealth]:
        """计算各服务健康度

        Args:
            results: 监控结果列表

        Returns:
            List[ServiceHealth]: 各服务的健康度列表
        """
        # 按服务分组
        service_groups = defaultdict(list)

        for result in results:
            if not result.interface:
                continue

            service_name = getattr(result.interface, 'service', 'unknown')
            service_groups[service_name].append(result)

        # 计算每个服务的健康度
        service_health_list = []
        for service_name, service_results in service_groups.items():
            health = self._calculate_single_service_health(service_name, service_results)
            service_health_list.append(health)

        return service_health_list

    def _calculate_single_service_health(
        self, service_name: str, results: List[MonitorResult]
    ) -> ServiceHealth:
        """计算单个服务的健康度

        Args:
            service_name: 服务名称
            results: 该服务的监控结果列表

        Returns:
            ServiceHealth: 服务健康度对象
        """
        total_count = len(results)
        success_count = sum(1 for r in results if r.is_success())
        failure_count = total_count - success_count

        # 计算成功率
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0.0

        # 计算响应时间统计
        response_times = [r.response_time for r in results if r.response_time > 0]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )
        min_response_time = min(response_times) if response_times else 0.0
        max_response_time = max(response_times) if response_times else 0.0

        # 计算P95响应时间
        p95_response_time = 0.0
        if response_times:
            sorted_times = sorted(response_times)
            n = len(sorted_times)
            p95_response_time = sorted_times[int(n * 0.95)]

        health = ServiceHealth(
            service_name=service_name,
            total_count=total_count,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
        )

        # 计算健康状态
        health.calculate_health_status()

        return health

    def _create_empty_stats(self) -> Stats:
        """创建空统计对象

        Returns:
            Stats: 空的Stats对象
        """
        return Stats(
            total_count=0,
            success_count=0,
            failure_count=0,
            success_rate=0.0,
            timestamp=datetime.now(),
        )

    def get_performance_metrics(self, stats: Stats) -> Dict[str, Any]:
        """获取性能指标

        Args:
            stats: 统计信息对象

        Returns:
            dict: 性能指标字典
        """
        return {
            'total_interfaces': stats.total_count,
            'success_rate': f"{stats.success_rate:.2f}%",
            'avg_response_time': f"{stats.avg_response_time:.2f}ms",
            'p95_response_time': f"{stats.p95_response_time:.2f}ms",
            'p99_response_time': f"{stats.p99_response_time:.2f}ms",
            'healthy_services': sum(1 for s in stats.services if s.health_status == 'HEALTHY'),
            'degraded_services': sum(1 for s in stats.services if s.health_status == 'DEGRADED'),
            'critical_services': sum(1 for s in stats.services if s.health_status == 'CRITICAL'),
        }
