"""
性能优化器
提供系统级性能优化功能，包括并发调优、内存优化、I/O优化等

作者: 开发团队
创建时间: 2026-01-28
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from memory_profiler import profile
import psutil


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    concurrent_interfaces: int
    p95_response_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    test_coverage: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'concurrent_interfaces': self.concurrent_interfaces,
            'p95_response_time': self.p95_response_time,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'success_rate': self.success_rate,
            'test_coverage': self.test_coverage,
        }


@dataclass
class OptimizationConfig:
    """优化配置"""
    max_concurrent_threads: int = 50
    thread_pool_size: int = 20
    batch_size: int = 100
    connection_pool_size: int = 10
    cache_size: int = 1000
    enable_connection_reuse: bool = True
    enable_batch_processing: bool = True
    memory_threshold_mb: int = 100


class PerformanceOptimizer:
    """性能优化器主类"""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """初始化性能优化器

        Args:
            config: 优化配置
        """
        self.config = config or OptimizationConfig()
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        self.logger.info(
            f"性能优化器初始化完成: "
            f"最大并发={self.config.max_concurrent_threads}, "
            f"批大小={self.config.batch_size}"
        )

    @profile
    def optimize_concurrency(
        self,
        current_threads: int,
        target_interfaces: int,
    ) -> int:
        """优化并发参数

        Args:
            current_threads: 当前线程数
            target_interfaces: 目标接口数

        Returns:
            优化后的线程数
        """
        self.logger.info(f"优化并发参数: 当前={current_threads}, 目标={target_interfaces}")

        # 计算最优线程数
        # 公式: min(目标接口数/10, CPU核心数*2, 最大并发)
        import os
        cpu_count = os.cpu_count() or 4
        optimal_threads = min(
            target_interfaces // 10,  # 每10个接口1个线程
            cpu_count * 2,  # CPU核心数*2
            self.config.max_concurrent_threads,  # 最大并发限制
        )

        # 确保至少1个线程
        optimal_threads = max(1, optimal_threads)

        self.logger.info(f"计算得到最优线程数: {optimal_threads}")
        return optimal_threads

    @profile
    def optimize_memory(self, data_size: int) -> int:
        """优化内存使用

        Args:
            data_size: 数据大小

        Returns:
            建议的批处理大小
        """
        self.logger.info(f"优化内存使用: 数据大小={data_size}")

        # 获取当前内存使用情况
        process = psutil.Process()
        current_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 计算建议的批大小
        if current_memory > self.config.memory_threshold_mb:
            # 内存使用过高，减少批大小
            batch_size = min(self.config.batch_size // 2, 10)
        else:
            # 内存使用正常，保持或增加批大小
            batch_size = min(self.config.batch_size, data_size)

        self.logger.info(f"内存优化建议: 当前={current_memory:.2f}MB, 建议批大小={batch_size}")
        return batch_size

    def optimize_io(
        self,
        connection_pool_size: Optional[int] = None,
        enable_reuse: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """优化I/O操作

        Args:
            connection_pool_size: 连接池大小
            enable_reuse: 是否启用连接复用

        Returns:
            优化建议字典
        """
        pool_size = connection_pool_size or self.config.connection_pool_size
        reuse = enable_reuse if enable_reuse is not None else self.config.enable_connection_reuse

        recommendations = {
            'connection_pool_size': pool_size,
            'enable_connection_reuse': reuse,
            'enable_keep_alive': True,
            'enable_http2': True,
            'connection_timeout': 5,
            'read_timeout': 10,
        }

        self.logger.info(f"I/O优化建议: {recommendations}")
        return recommendations

    def optimize_cache(
        self,
        cache_hit_rate: float,
        cache_size: Optional[int] = None,
    ) -> int:
        """优化缓存策略

        Args:
            cache_hit_rate: 缓存命中率
            cache_size: 当前缓存大小

        Returns:
            建议的缓存大小
        """
        current_size = cache_size or self.config.cache_size

        # 根据命中率调整缓存大小
        if cache_hit_rate < 0.7:  # 命中率低于70%
            # 命中率低，增加缓存大小
            recommended_size = min(current_size * 2, 10000)
        elif cache_hit_rate > 0.9:  # 命中率高于90%
            # 命中率高，可以适当减少缓存大小
            recommended_size = max(current_size // 2, 100)
        else:
            # 命中率正常，保持当前大小
            recommended_size = current_size

        self.logger.info(
            f"缓存优化建议: 当前命中率={cache_hit_rate:.2%}, "
            f"当前大小={current_size}, 建议大小={recommended_size}"
        )
        return recommended_size

    def calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """计算性能评分

        Args:
            metrics: 性能指标

        Returns:
            性能评分 (0-100)
        """
        score = 0.0

        # 并发能力评分 (0-20)
        if metrics.concurrent_interfaces >= 1000:
            score += 20
        elif metrics.concurrent_interfaces >= 500:
            score += 15
        elif metrics.concurrent_interfaces >= 100:
            score += 10
        else:
            score += 5

        # 响应时间评分 (0-20)
        if metrics.p95_response_time <= 1.0:
            score += 20
        elif metrics.p95_response_time <= 2.0:
            score += 15
        elif metrics.p95_response_time <= 5.0:
            score += 10
        else:
            score += 5

        # 内存使用评分 (0-20)
        if metrics.memory_usage_mb <= 50:
            score += 20
        elif metrics.memory_usage_mb <= 100:
            score += 15
        elif metrics.memory_usage_mb <= 200:
            score += 10
        else:
            score += 5

        # CPU使用评分 (0-20)
        if metrics.cpu_usage_percent <= 30:
            score += 20
        elif metrics.cpu_usage_percent <= 50:
            score += 15
        elif metrics.cpu_usage_percent <= 70:
            score += 10
        else:
            score += 5

        # 成功率评分 (0-20)
        if metrics.success_rate >= 99:
            score += 20
        elif metrics.success_rate >= 95:
            score += 15
        elif metrics.success_rate >= 90:
            score += 10
        else:
            score += 5

        return min(score, 100.0)

    def get_optimization_recommendations(
        self,
        current_metrics: PerformanceMetrics,
    ) -> Dict[str, Any]:
        """获取优化建议

        Args:
            current_metrics: 当前性能指标

        Returns:
            优化建议字典
        """
        recommendations = {
            'concurrency': self.optimize_concurrency(
                current_threads=5,  # 默认当前值
                target_interfaces=current_metrics.concurrent_interfaces,
            ),
            'memory': self.optimize_memory(data_size=1000),
            'io': self.optimize_io(),
            'cache': self.optimize_cache(cache_hit_rate=0.8),
            'performance_score': self.calculate_performance_score(current_metrics),
        }

        self.logger.info(f"生成优化建议: {recommendations}")
        return recommendations

    def benchmark_operation(
        self,
        operation: Callable,
        *args,
        iterations: int = 100,
        **kwargs,
    ) -> Dict[str, Any]:
        """基准测试操作

        Args:
            operation: 要测试的操作
            iterations: 迭代次数
            *args: 操作参数
            **kwargs: 操作关键字参数

        Returns:
            基准测试结果
        """
        import time

        self.logger.info(f"开始基准测试: 操作={operation.__name__}, 迭代={iterations}")

        times = []
        for i in range(iterations):
            start = time.time()
            try:
                result = operation(*args, **kwargs)
                elapsed = time.time() - start
                times.append(elapsed)
            except Exception as e:
                self.logger.error(f"基准测试迭代 {i} 失败: {e}")
                times.append(float('inf'))

        # 过滤无效时间
        valid_times = [t for t in times if t != float('inf')]

        if not valid_times:
            return {'error': '所有迭代都失败了'}

        # 计算统计信息
        times.sort()
        n = len(valid_times)
        avg_time = sum(valid_times) / n
        min_time = min(valid_times)
        max_time = max(valid_times)
        p95_index = int(n * 0.95)
        p95_time = valid_times[p95_index] if p95_index < n else valid_times[-1]

        result = {
            'iterations': n,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'p95_time': p95_time,
            'ops_per_second': 1.0 / avg_time if avg_time > 0 else 0,
        }

        self.logger.info(f"基准测试完成: {result}")
        return result


# 性能目标常量
PERFORMANCE_TARGETS = {
    'concurrent_interfaces': 1000,      # 并发接口数
    'completion_time': 300,            # 完成时间（秒）
    'p95_response_time': 2.0,         # P95响应时间（秒）
    'memory_usage': 100,               # 内存使用（MB）
    'cpu_usage': 50,                   # CPU使用率（%）
    'success_rate': 95,                # 成功率（%）
    'test_coverage': 80                # 测试覆盖率（%）
}
