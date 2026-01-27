"""
监控执行引擎主模块
提供并发监控执行能力，支持线程池调度和结果收集

作者: 开发团队
创建时间: 2026-01-27
"""

import logging
import time
from typing import List, Any, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from .executor import HTTPExecutor
from .retry import RetryConfig
from .result import MonitorResult, ErrorType

logger = logging.getLogger(__name__)


class MonitorEngine:
    """监控执行引擎

    负责并发执行多个接口的监控任务，支持线程池调度
    """

    def __init__(
        self,
        config: Optional[Dict] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        """初始化监控引擎

        Args:
            config: 配置字典，包含：
                - concurrency: 并发数（默认5）
                - timeout: 请求超时时间（默认10秒）
                - base_url: 基础URL
            retry_config: 重试配置
        """
        self.config = config or {}
        self.retry_config = retry_config or RetryConfig()

        # 从配置中读取参数
        self.concurrency = self.config.get('concurrency', 5)
        self.timeout = self.config.get('timeout', 10)
        self.base_url = self.config.get('base_url')

        # 验证并发数
        if self.concurrency <= 0:
            raise ValueError("并发数必须大于0")

        # 创建HTTP执行器
        self.executor = HTTPExecutor(
            config={
                'base_url': self.base_url,
                'timeout': self.timeout,
            },
            retry_config=self.retry_config,
        )

        logger.info(
            f"监控引擎初始化完成: 并发数={self.concurrency}, "
            f"超时时间={self.timeout}s, 基础URL={self.base_url or 'None'}"
        )

    def execute(
        self,
        interfaces: List[Any],
        token_map: Optional[Dict[str, str]] = None,
    ) -> List[MonitorResult]:
        """并发执行监控任务

        Args:
            interfaces: 接口列表
            token_map: 服务名到Token的映射

        Returns:
            List[MonitorResult]: 监控结果列表
        """
        if not interfaces:
            logger.warning("接口列表为空，返回空结果")
            return []

        logger.info(f"开始执行监控: {len(interfaces)}个接口，{self.concurrency}线程并发")

        start_time = time.time()
        results = []
        futures = []

        # 使用ThreadPoolExecutor进行并发执行
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # 提交所有任务
            for interface in interfaces:
                service = interface.service
                token = token_map.get(service) if token_map else None

                future = executor.submit(
                    self._execute_single,
                    interface,
                    token,
                )
                futures.append((future, interface))

            # 收集结果
            for future, interface in futures:
                try:
                    result = future.result()
                    results.append(result)
                    logger.debug(f"接口监控完成: {interface.name} - {result.status}")
                except Exception as e:
                    logger.error(f"接口监控异常: {interface.name} - {e}")
                    # 创建错误结果
                    error_result = MonitorResult(
                        interface=interface,
                        status='FAILED',
                        status_code=None,
                        response_time=0.0,
                        error_type=ErrorType.UNKNOWN_ERROR,
                        error_message=f"监控执行异常: {e}",
                        request_data={},
                        response_data={},
                    )
                    results.append(error_result)

        # 统计信息
        elapsed_time = time.time() - start_time
        success_count = sum(1 for r in results if r.is_success())
        failed_count = len(results) - success_count

        logger.info(
            f"监控执行完成: 总数={len(results)}, "
            f"成功={success_count}, 失败={failed_count}, "
            f"耗时={elapsed_time:.2f}s"
        )

        return results

    def execute_single(
        self,
        interface: Any,
        token: Optional[str] = None,
    ) -> MonitorResult:
        """执行单个接口监控（别名方法）

        Args:
            interface: 接口对象
            token: 认证Token

        Returns:
            MonitorResult: 监控结果
        """
        return self._execute_single(interface, token)

    def _execute_single(
        self,
        interface: Any,
        token: Optional[str] = None,
    ) -> MonitorResult:
        """执行单个接口监控

        Args:
            interface: 接口对象
            token: 认证Token

        Returns:
            MonitorResult: 监控结果
        """
        try:
            result = self.executor.execute_with_retry(interface, token)
            return result
        except Exception as e:
            logger.error(f"执行接口监控失败: {interface.name} - {e}")
            return MonitorResult(
                interface=interface,
                status='FAILED',
                status_code=None,
                response_time=0.0,
                error_type=ErrorType.UNKNOWN_ERROR,
                error_message=str(e),
                request_data={},
                response_data={},
            )

    def set_concurrency(self, count: int):
        """设置并发数

        Args:
            count: 并发数
        """
        if count <= 0:
            raise ValueError("并发数必须大于0")

        self.concurrency = count
        logger.info(f"并发数已更新: {count}")

    def set_timeout(self, seconds: int):
        """设置超时时间

        Args:
            seconds: 超时时间（秒）
        """
        if seconds <= 0:
            raise ValueError("超时时间必须大于0")

        self.timeout = seconds
        self.executor.http_handler.timeout = seconds
        logger.info(f"超时时间已更新: {seconds}s")

    def get_statistics(self, results: List[MonitorResult]) -> Dict[str, Any]:
        """获取监控结果统计

        Args:
            results: 监控结果列表

        Returns:
            dict: 统计信息
        """
        if not results:
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'error_types': {},
            }

        total = len(results)
        success_count = sum(1 for r in results if r.is_success())
        failed_count = total - success_count

        # 计算平均响应时间
        response_times = [r.response_time for r in results if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        # 统计错误类型
        error_types = {}
        for result in results:
            if result.error_type:
                error_types[result.error_type] = error_types.get(result.error_type, 0) + 1

        return {
            'total': total,
            'success': success_count,
            'failed': failed_count,
            'success_rate': (success_count / total) * 100 if total > 0 else 0.0,
            'avg_response_time': avg_response_time,
            'error_types': error_types,
        }

    def cleanup(self):
        """清理资源"""
        self.executor.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
