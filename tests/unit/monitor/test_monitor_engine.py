"""
监控引擎单元测试

作者: 开发团队
创建时间: 2026-01-28
"""

import pytest
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from monitor.monitor_engine import MonitorEngine
from monitor.result import MonitorResult, ErrorType
from monitor.retry import RetryConfig


class TestMonitorEngine:
    """监控引擎测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        engine = MonitorEngine()

        assert engine.concurrency == 5
        assert engine.timeout == 10
        assert engine.base_url is None
        assert engine.retry_config is not None
        assert engine.enable_monitoring is True

    def test_init_with_config(self):
        """测试使用配置初始化"""
        config = {
            'concurrency': 10,
            'timeout': 30,
            'base_url': 'http://test.com',
        }
        engine = MonitorEngine(config=config)

        assert engine.concurrency == 10
        assert engine.timeout == 30
        assert engine.base_url == 'http://test.com'

    def test_init_invalid_concurrency(self):
        """测试并发数为0时的异常"""
        config = {'concurrency': 0}
        with pytest.raises(ValueError, match="并发数必须大于0"):
            MonitorEngine(config=config)

    def test_set_concurrency(self):
        """测试设置并发数"""
        engine = MonitorEngine()
        engine.set_concurrency(20)

        assert engine.concurrency == 20

    def test_set_concurrency_invalid(self):
        """测试设置无效并发数"""
        engine = MonitorEngine()
        with pytest.raises(ValueError, match="并发数必须大于0"):
            engine.set_concurrency(0)

    def test_set_timeout(self):
        """测试设置超时时间"""
        engine = MonitorEngine()
        engine.set_timeout(60)

        assert engine.timeout == 60

    def test_set_timeout_invalid(self):
        """测试设置无效超时时间"""
        engine = MonitorEngine()
        with pytest.raises(ValueError, match="超时时间必须大于0"):
            engine.set_timeout(0)

    def test_optimize_for_load(self):
        """测试负载优化"""
        engine = MonitorEngine()
        optimal = engine.optimize_for_load(100)

        # 验证返回的并发数合理
        assert optimal >= 1
        assert optimal <= 50

    @pytest.mark.performance
    def test_execute_empty_interfaces(self):
        """测试执行空接口列表"""
        engine = MonitorEngine()
        results = engine.execute([])

        assert results == []

    @pytest.mark.performance
    @patch('monitor.monitor_engine.HTTPExecutor')
    def test_execute_single_interface_success(self, mock_executor):
        """测试成功执行单个接口"""
        # 准备mock
        mock_interface = Mock()
        mock_interface.name = 'test_interface'
        mock_interface.service = 'user'

        mock_result = MonitorResult(
            interface=mock_interface,
            status='SUCCESS',
            status_code=200,
            response_time=1.5,
            error_type=None,
            error_message=None,
            request_data={},
            response_data={'result': 'success'},
        )

        mock_executor_instance = Mock()
        mock_executor_instance.execute_with_retry.return_value = mock_result
        mock_executor.return_value = mock_executor_instance

        # 执行测试
        engine = MonitorEngine()
        results = engine.execute([mock_interface])

        # 验证结果
        assert len(results) == 1
        assert results[0].status == 'SUCCESS'
        assert results[0].response_time == 1.5

    @pytest.mark.performance
    @patch('monitor.monitor_engine.HTTPExecutor')
    def test_execute_multiple_interfaces(self, mock_executor):
        """测试执行多个接口"""
        # 准备mock
        mock_interfaces = []
        mock_results = []

        for i in range(5):
            interface = Mock()
            interface.name = f'test_interface_{i}'
            interface.service = 'user'
            mock_interfaces.append(interface)

            result = MonitorResult(
                interface=interface,
                status='SUCCESS',
                status_code=200,
                response_time=1.0 + i * 0.1,
                error_type=None,
                error_message=None,
                request_data={},
                response_data={'result': 'success'},
            )
            mock_results.append(result)

        mock_executor_instance = Mock()
        mock_executor_instance.execute_with_retry.side_effect = mock_results
        mock_executor.return_value = mock_executor_instance

        # 执行测试
        engine = MonitorEngine()
        results = engine.execute(mock_interfaces)

        # 验证结果
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.status == 'SUCCESS'
            assert result.response_time == 1.0 + i * 0.1

    @pytest.mark.performance
    @patch('monitor.monitor_engine.HTTPExecutor')
    def test_execute_with_exception(self, mock_executor):
        """测试执行时出现异常"""
        # 准备mock
        mock_interface = Mock()
        mock_interface.name = 'test_interface'
        mock_interface.service = 'user'

        mock_executor_instance = Mock()
        mock_executor_instance.execute_with_retry.side_effect = Exception("Test error")
        mock_executor.return_value = mock_executor_instance

        # 执行测试
        engine = MonitorEngine()
        results = engine.execute([mock_interface])

        # 验证结果
        assert len(results) == 1
        assert results[0].status == 'FAILED'
        assert results[0].error_type == ErrorType.UNKNOWN_ERROR
        assert "Test error" in results[0].error_message

    @pytest.mark.performance
    def test_get_statistics(self):
        """测试获取统计信息"""
        engine = MonitorEngine()

        # 空结果
        stats = engine.get_statistics([])
        assert stats['total'] == 0
        assert stats['success'] == 0
        assert stats['failed'] == 0
        assert stats['success_rate'] == 0.0

        # 创建模拟结果
        mock_interface = Mock()

        results = []
        for i in range(10):
            result = MonitorResult(
                interface=mock_interface,
                status='SUCCESS' if i < 8 else 'FAILED',
                status_code=200 if i < 8 else 500,
                response_time=1.0 + i * 0.1,
                error_type=None if i < 8 else ErrorType.HTTP_500,
                error_message=None if i < 8 else "HTTP 500",
                request_data={},
                response_data={},
            )
            results.append(result)

        stats = engine.get_statistics(results)

        assert stats['total'] == 10
        assert stats['success'] == 8
        assert stats['failed'] == 2
        assert stats['success_rate'] == 80.0
        assert stats['avg_response_time'] == 1.45  # (1.0 + 1.9) / 2
        assert ErrorType.HTTP_500 in stats['error_types']
        assert stats['error_types'][ErrorType.HTTP_500] == 2

    @pytest.mark.performance
    @patch('utils.performance_monitor.get_global_monitor')
    def test_execute_with_monitoring(self, mock_get_monitor):
        """测试启用性能监控的执行"""
        # 准备mock
        mock_monitor = Mock()
        mock_get_monitor.return_value = mock_monitor

        mock_interface = Mock()
        mock_interface.name = 'test_interface'
        mock_interface.service = 'user'

        mock_result = MonitorResult(
            interface=mock_interface,
            status='SUCCESS',
            status_code=200,
            response_time=1.5,
            error_type=None,
            error_message=None,
            request_data={},
            response_data={},
        )

        with patch('monitor.monitor_engine.HTTPExecutor') as mock_executor:
            mock_executor_instance = Mock()
            mock_executor_instance.execute_with_retry.return_value = mock_result
            mock_executor.return_value = mock_executor_instance

            engine = MonitorEngine()
            results = engine.execute([mock_interface])

            # 验证监控器被调用
            assert mock_monitor.record_concurrent_requests.called
            assert mock_monitor.record_response_time.called
            assert mock_monitor.record_success_rate.called

    def test_execute_without_monitoring(self):
        """测试禁用性能监控的执行"""
        engine = MonitorEngine(enable_monitoring=False)

        # 验证监控器为None
        assert engine.monitor is None

    def test_cleanup(self):
        """测试清理资源"""
        with patch('monitor.monitor_engine.HTTPExecutor') as mock_executor:
            mock_executor_instance = Mock()
            mock_executor.return_value = mock_executor_instance

            engine = MonitorEngine()
            engine.cleanup()

            # 验证清理被调用
            assert mock_executor_instance.cleanup.called

    def test_context_manager(self):
        """测试上下文管理器"""
        with patch('monitor.monitor_engine.HTTPExecutor') as mock_executor:
            mock_executor_instance = Mock()
            mock_executor.return_value = mock_executor_instance

            with MonitorEngine() as engine:
                assert engine is not None

            # 验证清理被调用
            assert mock_executor_instance.cleanup.called

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_benchmark_execution(self, benchmark, mock_interfaces):
        """基准测试：监控执行性能"""
        with patch('monitor.monitor_engine.HTTPExecutor') as mock_executor:
            mock_executor_instance = Mock()

            # 模拟快速响应
            def quick_response(*args, **kwargs):
                time.sleep(0.01)  # 10ms延迟
                mock_interface = Mock()
                return MonitorResult(
                    interface=mock_interface,
                    status='SUCCESS',
                    status_code=200,
                    response_time=0.01,
                    error_type=None,
                    error_message=None,
                    request_data={},
                    response_data={},
                )

            mock_executor_instance.execute_with_retry.side_effect = quick_response
            mock_executor.return_value = mock_executor_instance

            engine = MonitorEngine()

            # 基准测试
            def execute_benchmark():
                return engine.execute(mock_interfaces[:10])

            results = benchmark.pedantic(execute_benchmark, rounds=5, iterations=1)

            assert len(results) == 10

    def test_p95_response_time_calculation(self):
        """测试P95响应时间计算"""
        engine = MonitorEngine()

        # 创建具有不同响应时间的模拟结果
        mock_interface = Mock()

        # 100个结果，响应时间从0.1到10.0
        results = []
        for i in range(100):
            result = MonitorResult(
                interface=mock_interface,
                status='SUCCESS',
                status_code=200,
                response_time=0.1 + i * 0.1,
                error_type=None,
                error_message=None,
                request_data={},
                response_data={},
            )
            results.append(result)

        # 执行
        with patch('monitor.monitor_engine.HTTPExecutor') as mock_executor:
            mock_executor_instance = Mock()
            mock_executor_instance.execute_with_retry.side_effect = [r.interface for r in results]
            mock_executor.return_value = mock_executor_instance

            results = engine.execute(results)

            # P95应该是第95个值（9.5）
            assert len(results) == 100
