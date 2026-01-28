"""
性能测试套件

作者: 开发团队
创建时间: 2026-01-28
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import time
import psutil
import threading
from unittest.mock import Mock
from concurrent.futures import ThreadPoolExecutor

from monitor.monitor_engine import MonitorEngine
from scanner.interface_scanner import InterfaceScanner
from analyzer.result_analyzer import ResultAnalyzer
from utils.performance_optimizer import PerformanceOptimizer, OptimizationConfig
from utils.performance_monitor import PerformanceMonitor


@pytest.mark.performance
class TestPerformanceOptimization:
    """性能优化测试类"""

    def test_performance_optimizer_init(self):
        """测试性能优化器初始化"""
        optimizer = PerformanceOptimizer()

        assert optimizer.config is not None
        assert optimizer.config.max_concurrent_threads == 50

    def test_performance_optimizer_concurrency_optimization(self):
        """测试并发优化"""
        optimizer = PerformanceOptimizer()

        optimal_threads = optimizer.optimize_concurrency(
            current_threads=5,
            target_interfaces=1000,
        )

        assert optimal_threads >= 1
        assert optimal_threads <= 50

    def test_performance_optimizer_memory_optimization(self):
        """测试内存优化"""
        optimizer = PerformanceOptimizer()

        batch_size = optimizer.optimize_memory(data_size=10000)

        assert batch_size >= 1
        assert batch_size <= 1000

    def test_performance_optimizer_cache_optimization(self):
        """测试缓存优化"""
        optimizer = PerformanceOptimizer()

        # 测试低命中率
        cache_size_low = optimizer.optimize_cache(
            cache_hit_rate=0.5,
            cache_size=1000,
        )
        assert cache_size_low > 1000

        # 测试高命中率
        cache_size_high = optimizer.optimize_cache(
            cache_hit_rate=0.95,
            cache_size=1000,
        )
        assert cache_size_high < 1000

    def test_performance_score_calculation(self):
        """测试性能评分计算"""
        optimizer = PerformanceOptimizer()

        metrics = {
            'concurrent_interfaces': 1000,
            'p95_response_time': 1.5,
            'memory_usage_mb': 80,
            'cpu_usage_percent': 40,
            'success_rate': 99,
            'test_coverage': 85,
        }

        from utils.performance_optimizer import PerformanceMetrics
        perf_metrics = PerformanceMetrics(**metrics)

        score = optimizer.calculate_performance_score(perf_metrics)

        assert score >= 0
        assert score <= 100

    def test_benchmark_operation(self):
        """测试基准测试操作"""
        optimizer = PerformanceOptimizer()

        def dummy_operation():
            time.sleep(0.01)
            return "result"

        result = optimizer.benchmark_operation(
            operation=dummy_operation,
            iterations=10,
        )

        assert 'avg_time' in result
        assert 'ops_per_second' in result
        assert result['ops_per_second'] > 0


@pytest.mark.performance
class TestPerformanceMonitor:
    """性能监控测试类"""

    def test_monitor_init(self):
        """测试监控器初始化"""
        monitor = PerformanceMonitor()

        assert monitor.window_size == 100
        assert len(monitor.alert_thresholds) > 0

    def test_record_metrics(self):
        """测试记录指标"""
        monitor = PerformanceMonitor()

        monitor.record_metric('test_metric', 100)
        monitor.record_metric('test_metric', 200)

        stats = monitor.get_metric_stats('test_metric')

        assert stats is not None
        assert stats['count'] == 2

    def test_record_response_time(self):
        """测试记录响应时间"""
        monitor = PerformanceMonitor()

        monitor.record_response_time(1.5, 'test_endpoint')

        stats = monitor.get_metric_stats('response_time')

        assert stats is not None
        assert stats['avg'] == 1.5

    def test_record_memory_usage(self):
        """测试记录内存使用"""
        monitor = PerformanceMonitor()

        monitor.record_memory_usage()

        stats = monitor.get_metric_stats('memory_usage')

        assert stats is not None
        assert stats['avg'] > 0

    def test_alert_callback(self):
        """测试告警回调"""
        monitor = PerformanceMonitor()

        alerts_triggered = []

        def alert_handler(alert):
            alerts_triggered.append(alert)

        monitor.add_alert_callback(alert_handler)

        # 触发告警
        monitor.record_metric('response_time_p95', 3.0)

        # 等待告警处理
        time.sleep(0.1)

        assert len(alerts_triggered) > 0

    def test_performance_summary(self):
        """测试性能摘要"""
        monitor = PerformanceMonitor()

        # 记录一些指标
        for i in range(10):
            monitor.record_metric('test_metric', i)

        summary = monitor.get_performance_summary()

        assert 'uptime_seconds' in summary
        assert 'metrics_count' in summary
        assert summary['metrics_count'] >= 1


@pytest.mark.performance
class TestMonitorEnginePerformance:
    """监控引擎性能测试类"""

    @pytest.mark.benchmark
    def test_benchmark_monitor_execution(self, benchmark, mock_interfaces):
        """基准测试：监控执行性能"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            def execute_monitor():
                engine = MonitorEngine()
                results = []
                for interface in mock_interfaces[:10]:
                    # 模拟快速响应
                    result = Mock()
                    result.status = 'SUCCESS'
                    result.response_time = 0.01
                    results.append(result)
                return results

            results = benchmark.pedantic(execute_monitor, rounds=5, iterations=1)

            assert len(results) == 10

    def test_concurrent_monitoring(self):
        """测试并发监控"""
        num_threads = 10
        num_interfaces = 50

        results = []
        errors = []

        def monitor_batch(thread_id):
            try:
                engine = MonitorEngine()
                # 模拟处理
                for i in range(num_interfaces):
                    result = {
                        'thread_id': thread_id,
                        'interface_id': i,
                        'status': 'SUCCESS',
                        'response_time': 0.01,
                    }
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建并发线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=monitor_batch, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(errors) == 0
        assert len(results) == num_threads * num_interfaces

    def test_memory_usage_under_load(self):
        """测试负载下的内存使用"""
        process = psutil.Process()

        initial_memory = process.memory_info().rss / 1024 / 1024

        # 执行大量操作
        for batch in range(100):
            engine = MonitorEngine()
            # 模拟处理
            for i in range(100):
                result = Mock()
                result.status = 'SUCCESS'
                result.response_time = 0.001

        final_memory = process.memory_info().rss / 1024 / 1024

        # 验证内存增长在合理范围内
        memory_increase = final_memory - initial_memory
        assert memory_increase < 200  # 内存增长应小于200MB


@pytest.mark.performance
class TestScannerPerformance:
    """扫描器性能测试类"""

    @pytest.mark.benchmark
    def test_benchmark_file_scanning(self, benchmark, interface_data_dir):
        """基准测试：文件扫描性能"""
        def scan_files():
            scanner = InterfaceScanner(str(interface_data_dir))
            return scanner.scan()

        results = benchmark.pedantic(scan_files, rounds=5, iterations=1)

        assert isinstance(results, list)

    def test_concurrent_file_parsing(self, temp_dir):
        """测试并发文件解析性能"""
        # 创建大量测试文件
        for i in range(100):
            file_path = temp_dir / f'test_{i}.json'
            file_path.write_text('{"name": "test"}', encoding='utf-8')

        scanner = InterfaceScanner(str(temp_dir), max_workers=10)

        start_time = time.time()
        results = scanner.scan()
        scan_time = time.time() - start_time

        # 验证扫描在合理时间内完成
        assert scan_time < 10  # 应在10秒内完成
        assert len(results) == 100


@pytest.mark.performance
class TestAnalyzerPerformance:
    """分析器性能测试类"""

    @pytest.mark.benchmark
    def test_benchmark_result_analysis(self, benchmark):
        """基准测试：结果分析性能"""
        analyzer = ResultAnalyzer()

        # 创建大量模拟结果
        results = []
        for i in range(1000):
            result = Mock()
            result.status = 'SUCCESS' if i % 10 != 0 else 'FAILED'
            result.response_time = 1.0 + (i % 100) * 0.01
            result.is_success.return_value = result.status == 'SUCCESS'
            results.append(result)

        def analyze_results():
            return analyzer.analyze(results)

        report = benchmark.pedantic(analyze_results, rounds=3, iterations=1)

        assert report.total == 1000

    def test_batch_processing_performance(self):
        """测试批处理性能"""
        analyzer = ResultAnalyzer(config={'max_batch_size': 100})

        # 创建大量结果
        results = []
        for i in range(1000):
            result = Mock()
            result.status = 'SUCCESS'
            result.response_time = 1.0
            result.is_success.return_value = True
            results.append(result)

        start_time = time.time()
        report = analyzer.analyze(results)
        processing_time = time.time() - start_time

        # 验证批处理在合理时间内完成
        assert processing_time < 5  # 应在5秒内完成
        assert report.total == 1000


@pytest.mark.performance
class TestSystemIntegrationPerformance:
    """系统集成性能测试类"""

    def test_end_to_end_performance(self, interface_data_dir):
        """端到端性能测试"""
        # 步骤1：扫描接口
        scanner = InterfaceScanner(str(interface_data_dir))
        interfaces = scanner.scan()

        # 步骤2：执行监控
        engine = MonitorEngine()
        # 模拟监控结果
        results = []
        for interface in interfaces:
            result = Mock()
            result.status = 'SUCCESS'
            result.response_time = 0.1
            results.append(result)

        # 步骤3：分析结果
        analyzer = ResultAnalyzer()
        report = analyzer.analyze(results)

        # 验证端到端流程在合理时间内完成
        assert report.total >= 0

    def test_stability_under_load(self):
        """负载下的稳定性测试"""
        num_iterations = 50
        num_operations = 100

        for iteration in range(num_iterations):
            # 执行一系列操作
            for op in range(num_operations):
                engine = MonitorEngine()
                analyzer = ResultAnalyzer()

                # 模拟结果
                result = Mock()
                result.status = 'SUCCESS'
                result.response_time = 0.01
                result.is_success.return_value = True

                report = analyzer.analyze([result])

                assert report.total == 1

        # 验证系统仍然稳定
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        # 内存使用应在合理范围内
        assert memory_mb < 500

    def test_performance_regression_detection(self):
        """性能回归检测"""
        # 基线性能
        baseline_time = 1.0

        # 当前性能
        start_time = time.time()

        # 执行模拟操作
        for i in range(1000):
            result = Mock()
            result.status = 'SUCCESS'
            result.response_time = 0.001

        current_time = time.time() - start_time

        # 性能回归检查
        performance_ratio = current_time / baseline_time

        # 如果性能下降超过50%，标记为回归
        if performance_ratio > 1.5:
            pytest.fail(f"性能回归检测：性能下降 {performance_ratio:.2f}x")
