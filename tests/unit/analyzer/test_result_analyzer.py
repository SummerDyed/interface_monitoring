"""
结果分析器单元测试

作者: 开发团队
创建时间: 2026-01-28
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List

from analyzer.result_analyzer import ResultAnalyzer
from analyzer.models.report import MonitorReport
from analyzer.models.stats import Stats, ServiceHealth
from monitor.result import MonitorResult, ErrorType


class TestResultAnalyzer:
    """结果分析器测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        analyzer = ResultAnalyzer()

        assert analyzer.config == {}
        assert analyzer.max_batch_size == 1000
        assert analyzer.enable_streaming is False
        assert analyzer.error_aggregator is not None
        assert analyzer.stats_aggregator is not None

    def test_init_with_config(self):
        """测试使用配置初始化"""
        config = {
            'max_batch_size': 500,
            'enable_streaming': True,
        }
        analyzer = ResultAnalyzer(config=config)

        assert analyzer.max_batch_size == 500
        assert analyzer.enable_streaming is True

    def test_create_empty_report(self):
        """测试创建空报告"""
        analyzer = ResultAnalyzer()

        report = analyzer._create_empty_report("Test Report")

        assert report.title == "Test Report"
        assert report.total == 0
        assert report.success == 0
        assert report.failed == 0

    def test_analyze_empty_results(self):
        """测试分析空结果"""
        analyzer = ResultAnalyzer()

        report = analyzer.analyze([])

        assert report.total == 0
        assert report.success == 0
        assert report.failed == 0

    @pytest.mark.performance
    def test_analyze_success_results(self):
        """测试分析成功结果"""
        analyzer = ResultAnalyzer()

        # 创建模拟成功结果
        results = []
        for i in range(10):
            result = MonitorResult(
                interface=Mock(name=f'interface_{i}', service='user'),
                status='SUCCESS',
                status_code=200,
                response_time=1.0 + i * 0.1,
                error_type=None,
                error_message=None,
                request_data={},
                response_data={},
            )
            results.append(result)

        report = analyzer.analyze(results)

        assert report.total == 10
        assert report.success == 10
        assert report.failed == 0
        assert report.success_rate == 100.0

    @pytest.mark.performance
    def test_analyze_mixed_results(self):
        """测试分析混合结果"""
        analyzer = ResultAnalyzer()

        # 创建混合结果
        results = []
        for i in range(10):
            if i < 7:
                # 成功
                result = MonitorResult(
                    interface=Mock(name=f'interface_{i}', service='user'),
                    status='SUCCESS',
                    status_code=200,
                    response_time=1.0,
                    error_type=None,
                    error_message=None,
                    request_data={},
                    response_data={},
                )
            elif i < 9:
                # 失败 - 404错误
                result = MonitorResult(
                    interface=Mock(name=f'interface_{i}', service='user'),
                    status='FAILED',
                    status_code=404,
                    response_time=0.5,
                    error_type=ErrorType.HTTP_ERROR,
                    error_message='Not Found',
                    request_data={},
                    response_data={},
                )
            else:
                # 失败 - 500错误
                result = MonitorResult(
                    interface=Mock(name=f'interface_{i}', service='user'),
                    status='FAILED',
                    status_code=500,
                    response_time=2.0,
                    error_type=ErrorType.HTTP_ERROR,
                    error_message='Internal Server Error',
                    request_data={},
                    response_data={},
                )
            results.append(result)

        report = analyzer.analyze(results)

        assert report.total == 10
        assert report.success == 7
        assert report.failed == 3
        assert report.success_rate == 70.0

    def test_categorize_results(self):
        """测试分类结果"""
        analyzer = ResultAnalyzer()

        # 创建模拟结果
        success_result = MonitorResult(
            interface=Mock(name='success', service='user'),
            status='SUCCESS',
            status_code=200,
            response_time=1.0,
            error_type=None,
            error_message=None,
            request_data={},
            response_data={},
        )

        failed_result = MonitorResult(
            interface=Mock(name='failed', service='user'),
            status='FAILED',
            status_code=404,
            response_time=0.5,
            error_type=ErrorType.HTTP_ERROR,
            error_message='Not Found',
            request_data={},
            response_data={},
        )

        results = [success_result, failed_result]

        success, failed = analyzer.categorize_results(results)

        assert len(success) == 1
        assert len(failed) == 1
        assert success[0].status == 'SUCCESS'
        assert failed[0].status == 'FAILED'

    def test_categorize_results_empty(self):
        """测试分类空结果"""
        analyzer = ResultAnalyzer()

        success, failed = analyzer.categorize_results([])

        assert success == []
        assert failed == []

    @patch('analyzer.result_analyzer.ErrorAggregator')
    def test_aggregate_errors(self, mock_error_aggregator):
        """测试聚合错误"""
        # 准备mock
        mock_aggregator_instance = Mock()
        mock_aggregator_instance.aggregate.return_value = []
        mock_error_aggregator.return_value = mock_aggregator_instance

        analyzer = ResultAnalyzer()

        # 创建失败结果
        failed_result = MonitorResult(
            interface=Mock(name='failed', service='user'),
            status='FAILED',
            status_code=404,
            response_time=0.5,
            error_type=ErrorType.HTTP_ERROR,
            error_message='Not Found',
            request_data={},
            response_data={},
        )

        errors = analyzer.aggregate_errors([failed_result])

        assert isinstance(errors, list)

    @patch('analyzer.result_analyzer.StatsAggregator')
    def test_generate_stats(self, mock_stats_aggregator):
        """测试生成统计信息"""
        # 准备mock
        mock_aggregator_instance = Mock()
        mock_aggregator_instance.aggregate.return_value = Mock()
        mock_stats_aggregator.return_value = mock_aggregator_instance

        analyzer = ResultAnalyzer()

        # 创建模拟结果
        result = MonitorResult(
            interface=Mock(name='test', service='user'),
            status='SUCCESS',
            status_code=200,
            response_time=1.0,
            error_type=None,
            error_message=None,
            request_data={},
            response_data={},
        )

        stats = analyzer.generate_stats([result])

        assert stats is not None

    def test_calculate_percentiles(self):
        """测试计算百分位数"""
        analyzer = ResultAnalyzer()

        # 创建具有不同响应时间的结果
        values = [1.0, 2.0, 3.0, 4.0, 5.0]

        p50 = analyzer._calculate_percentile(values, 50)
        p95 = analyzer._calculate_percentile(values, 95)
        p99 = analyzer._calculate_percentile(values, 99)

        assert p50 == 3.0
        assert p95 == 4.8
        assert p99 == 4.96

    def test_calculate_percentiles_empty(self):
        """测试计算空值百分位数"""
        analyzer = ResultAnalyzer()

        p50 = analyzer._calculate_percentile([], 50)

        assert p50 == 0.0

    def test_calculate_percentiles_single_value(self):
        """测试计算单个值的百分位数"""
        analyzer = ResultAnalyzer()

        p50 = analyzer._calculate_percentile([5.0], 50)

        assert p50 == 5.0

    def test_group_results_by_service(self):
        """测试按服务分组结果"""
        analyzer = ResultAnalyzer()

        # 创建不同服务的模拟结果
        results = [
            MonitorResult(
                interface=Mock(name='user1', service='user'),
                status='SUCCESS',
                status_code=200,
                response_time=1.0,
                error_type=None,
                error_message=None,
                request_data={},
                response_data={},
            ),
            MonitorResult(
                interface=Mock(name='nurse1', service='nurse'),
                status='SUCCESS',
                status_code=200,
                response_time=1.5,
                error_type=None,
                error_message=None,
                request_data={},
                response_data={},
            ),
            MonitorResult(
                interface=Mock(name='user2', service='user'),
                status='FAILED',
                status_code=500,
                response_time=2.0,
                error_type=ErrorType.HTTP_ERROR,
                error_message='Error',
                request_data={},
                response_data={},
            ),
        ]

        grouped = analyzer._group_results_by_service(results)

        assert 'user' in grouped
        assert 'nurse' in grouped
        assert len(grouped['user']) == 2
        assert len(grouped['nurse']) == 1

    def test_group_results_by_service_empty(self):
        """测试按服务分组空结果"""
        analyzer = ResultAnalyzer()

        grouped = analyzer._group_results_by_service([])

        assert grouped == {}

    @patch('analyzer.result_analyzer.process_alert')
    def test_process_alert(self, mock_process_alert):
        """测试处理告警"""
        # 准备mock
        mock_process_alert.return_value = {
            'should_alert': True,
            'priority': 'high',
            'summary': 'Test alert',
        }

        analyzer = ResultAnalyzer()

        # 创建模拟报告
        report = Mock()
        report.total = 10
        report.failed = 3

        alert_info = analyzer.process_alert(report)

        assert alert_info['should_alert'] is True

    def test_build_report(self):
        """测试构建报告"""
        analyzer = ResultAnalyzer()

        # 创建模拟数据
        results = []
        errors = []
        stats = Mock()
        stats.total = 10
        stats.success = 8

        report = analyzer._build_report(results, errors, stats, "Test Report")

        assert report.title == "Test Report"
        assert report.total == 10
        assert report.success == 8

    def test_build_report_with_default_title(self):
        """测试构建报告使用默认标题"""
        analyzer = ResultAnalyzer()

        results = []
        errors = []
        stats = Mock()
        stats.total = 0

        report = analyzer._build_report(results, errors, stats, None)

        assert "监控报告" in report.title

    def test_get_performance_metrics(self):
        """测试获取性能指标"""
        analyzer = ResultAnalyzer()

        # 创建具有不同响应时间的模拟结果
        results = []
        for i in range(100):
            result = MonitorResult(
                interface=Mock(name=f'interface_{i}', service='user'),
                status='SUCCESS',
                status_code=200,
                response_time=1.0 + i * 0.01,
                error_type=None,
                error_message=None,
                request_data={},
                response_data={},
            )
            results.append(result)

        metrics = analyzer.get_performance_metrics(results)

        assert 'avg_response_time' in metrics
        assert 'p95_response_time' in metrics
        assert 'p99_response_time' in metrics
        assert 'min_response_time' in metrics
        assert 'max_response_time' in metrics

    def test_get_performance_metrics_empty(self):
        """测试获取空结果的性能指标"""
        analyzer = ResultAnalyzer()

        metrics = analyzer.get_performance_metrics([])

        assert metrics['avg_response_time'] == 0.0
        assert metrics['p95_response_time'] == 0.0

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_benchmark_analyze(self, benchmark, mock_interfaces):
        """基准测试：分析性能"""
        analyzer = ResultAnalyzer()

        # 创建大量模拟结果
        results = []
        for i in range(1000):
            result = MonitorResult(
                interface=Mock(name=f'interface_{i}', service='user'),
                status='SUCCESS' if i % 10 != 0 else 'FAILED',
                status_code=200 if i % 10 != 0 else 500,
                response_time=1.0 + (i % 100) * 0.01,
                error_type=None if i % 10 != 0 else ErrorType.HTTP_ERROR,
                error_message=None if i % 10 != 0 else 'Error',
                request_data={},
                response_data={},
            )
            results.append(result)

        # 基准测试
        def analyze_benchmark():
            return analyzer.analyze(results)

        report = benchmark.pedantic(analyze_benchmark, rounds=3, iterations=1)

        assert report.total == 1000

    def test_batch_processing(self):
        """测试批处理"""
        config = {'max_batch_size': 100}
        analyzer = ResultAnalyzer(config=config)

        # 创建大量结果
        results = []
        for i in range(250):
            result = MonitorResult(
                interface=Mock(name=f'interface_{i}', service='user'),
                status='SUCCESS',
                status_code=200,
                response_time=1.0,
                error_type=None,
                error_message=None,
                request_data={},
                response_data={},
            )
            results.append(result)

        # 批处理分析
        report = analyzer.analyze(results)

        assert report.total == 250
        assert report.success == 250

    def test_streaming_processing(self):
        """测试流式处理"""
        config = {'enable_streaming': True, 'max_batch_size': 50}
        analyzer = ResultAnalyzer(config=config)

        # 创建大量结果
        results = []
        for i in range(150):
            result = MonitorResult(
                interface=Mock(name=f'interface_{i}', service='user'),
                status='SUCCESS',
                status_code=200,
                response_time=1.0,
                error_type=None,
                error_message=None,
                request_data={},
                response_data={},
            )
            results.append(result)

        # 流式分析
        report = analyzer.analyze(results)

        assert report.total == 150
        assert report.success == 150
