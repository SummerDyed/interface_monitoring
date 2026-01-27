"""
统计数据模型
定义监控结果的统计信息和服务健康度

作者: 开发团队
创建时间: 2026-01-27
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import statistics


@dataclass
class ServiceHealth:
    """服务健康度信息

    存储单个服务的监控统计和健康度评估
    """

    service_name: str = ""
    """服务名称"""

    total_count: int = 0
    """该服务总接口数"""

    success_count: int = 0
    """该服务成功数"""

    failure_count: int = 0
    """该服务失败数"""

    success_rate: float = 0.0
    """该服务成功率"""

    avg_response_time: float = 0.0
    """平均响应时间（毫秒）"""

    min_response_time: float = 0.0
    """最小响应时间（毫秒）"""

    max_response_time: float = 0.0
    """最大响应时间（毫秒）"""

    p95_response_time: float = 0.0
    """P95响应时间（毫秒）"""

    health_status: str = "UNKNOWN"
    """健康状态：HEALTHY/DEGRADED/CRITICAL/UNKNOWN"""

    def calculate_health_status(self):
        """计算健康状态

        根据成功率判断服务健康状态
        - HEALTHY: 成功率 >= 99%
        - DEGRADED: 成功率 95%-99%
        - CRITICAL: 成功率 < 95%
        """
        if self.total_count == 0:
            self.health_status = "UNKNOWN"
        elif self.success_rate >= 99.0:
            self.health_status = "HEALTHY"
        elif self.success_rate >= 95.0:
            self.health_status = "DEGRADED"
        else:
            self.health_status = "CRITICAL"

    def to_dict(self) -> Dict:
        """转换为字典格式

        Returns:
            dict: 服务健康度的字典表示
        """
        return {
            'service_name': self.service_name,
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'min_response_time': self.min_response_time,
            'max_response_time': self.max_response_time,
            'p95_response_time': self.p95_response_time,
            'health_status': self.health_status,
        }


@dataclass
class Stats:
    """监控统计信息

    存储完整的监控统计分析结果
    """

    total_count: int = 0
    """总接口数"""

    success_count: int = 0
    """成功数"""

    failure_count: int = 0
    """失败数"""

    success_rate: float = 0.0
    """成功率（百分比）"""

    avg_response_time: float = 0.0
    """平均响应时间（毫秒）"""

    min_response_time: float = 0.0
    """最小响应时间（毫秒）"""

    max_response_time: float = 0.0
    """最大响应时间（毫秒）"""

    p95_response_time: float = 0.0
    """P95响应时间（毫秒）"""

    p99_response_time: float = 0.0
    """P99响应时间（毫秒）"""

    error_types: Dict[str, int] = field(default_factory=dict)
    """错误类型分布"""

    services: List[ServiceHealth] = field(default_factory=list)
    """各服务健康度列表"""

    timestamp: datetime = field(default_factory=datetime.now)
    """统计时间"""

    def calculate_response_time_stats(self, response_times: List[float]):
        """计算响应时间统计

        Args:
            response_times: 响应时间列表（毫秒）
        """
        if not response_times:
            self.avg_response_time = 0.0
            self.min_response_time = 0.0
            self.max_response_time = 0.0
            self.p95_response_time = 0.0
            self.p99_response_time = 0.0
            return

        self.avg_response_time = statistics.mean(response_times)
        self.min_response_time = min(response_times)
        self.max_response_time = max(response_times)

        # 计算百分位数
        sorted_times = sorted(response_times)
        n = len(sorted_times)

        self.p95_response_time = sorted_times[int(n * 0.95)] if n > 0 else 0.0
        self.p99_response_time = sorted_times[int(n * 0.99)] if n > 0 else 0.0

    def calculate_success_rate(self):
        """计算成功率"""
        if self.total_count > 0:
            self.success_rate = (self.success_count / self.total_count) * 100
        else:
            self.success_rate = 0.0

    def calculate_service_health(self):
        """计算所有服务的健康状态"""
        for service in self.services:
            service.calculate_health_status()

    def to_dict(self) -> Dict:
        """转换为字典格式

        Returns:
            dict: 统计信息的字典表示
        """
        return {
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'min_response_time': self.min_response_time,
            'max_response_time': self.max_response_time,
            'p95_response_time': self.p95_response_time,
            'p99_response_time': self.p99_response_time,
            'error_types': self.error_types,
            'services': [service.to_dict() for service in self.services],
            'timestamp': self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        """字符串表示

        Returns:
            str: 统计信息的字符串表示
        """
        return (
            f"总接口数: {self.total_count}, 成功率: {self.success_rate:.2f}%, "
            f"平均响应时间: {self.avg_response_time:.2f}ms"
        )
