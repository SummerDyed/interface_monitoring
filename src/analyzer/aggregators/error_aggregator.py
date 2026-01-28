"""
异常聚合器
负责将监控结果中的异常进行分类、聚合和排序

作者: 开发团队
创建时间: 2026-01-27
"""

from collections import defaultdict
import logging
from typing import List, Dict, Any

from monitor.result import MonitorResult, ErrorType
from ..models import ErrorInfo

logger = logging.getLogger(__name__)


class ErrorAggregator:
    """异常聚合器

    负责将异常结果按类型分组、按严重程度排序、提取详细信息
    """

    # 错误严重程度排序（数值越小越严重）
    SEVERITY_ORDER = {
        ErrorType.HTTP_500: 1,
        ErrorType.HTTP_503: 2,
        ErrorType.HTTP_404: 3,
        ErrorType.TIMEOUT: 4,
        ErrorType.NETWORK_ERROR: 5,
        ErrorType.CONNECTION_ERROR: 6,
        ErrorType.DNS_ERROR: 7,
        ErrorType.VALIDATION_ERROR: 8,
        ErrorType.UNKNOWN_ERROR: 9,
    }

    def __init__(self):
        """初始化异常聚合器"""
        self.error_counts = {}

    def aggregate(self, failed_results: List[MonitorResult]) -> List[ErrorInfo]:
        """聚合异常结果

        将失败的监控结果按异常类型分组，去重合并，生成异常详情列表

        Args:
            failed_results: 失败的监控结果列表

        Returns:
            List[ErrorInfo]: 聚合后的异常详情列表（已按严重程度排序）
        """
        if not failed_results:
            logger.info("没有失败的监控结果，返回空异常列表")
            return []

        logger.info(f"开始聚合 {len(failed_results)} 个异常结果")

        # 按异常类型和接口分组
        error_groups = self._group_by_error_type_and_interface(failed_results)

        # 转换为ErrorInfo对象列表
        error_infos = []
        for (error_type, _), results in error_groups.items():
            error_info = self._create_error_info(error_type, results)
            error_infos.append(error_info)

        # 按严重程度排序
        sorted_errors = self._sort_by_severity(error_infos)

        logger.info(f"聚合完成，共 {len(sorted_errors)} 种异常类型")

        return sorted_errors

    def _group_by_error_type_and_interface(
        self, failed_results: List[MonitorResult]
    ) -> Dict[tuple, List[MonitorResult]]:
        """按异常类型和接口分组

        Args:
            failed_results: 失败的监控结果列表

        Returns:
            dict: {(error_type, interface_key): [results]} 的字典
        """
        groups = defaultdict(list)

        for result in failed_results:
            if not result.interface:
                logger.warning(f"监控结果缺少接口信息: {result}")
                continue

            # 创建接口唯一标识（使用name + method + url的组合）
            interface_key = (
                result.interface.name or "",
                result.interface.method or "",
                result.interface.url or "",
            )

            error_type = result.error_type or ErrorType.UNKNOWN_ERROR

            groups[(error_type, interface_key)].append(result)

        return groups

    def _create_error_info(
        self, error_type: str, results: List[MonitorResult]
    ) -> ErrorInfo:
        """创建异常详情

        Args:
            error_type: 异常类型
            results: 同一异常类型和接口的结果列表

        Returns:
            ErrorInfo: 异常详情对象
        """
        # 取第一个结果作为代表（假设同一组的结果信息基本一致）
        representative = results[0]

        # 计算出现次数
        count = len(results)

        # 构建异常详情
        error_info = ErrorInfo(
            interface_name=representative.interface.name or "",
            interface_method=representative.interface.method or "",
            interface_url=representative.interface.url or "",
            service=getattr(representative.interface, 'service', ''),
            error_type=error_type,
            error_message=representative.error_message or "",
            status_code=representative.status_code,
            request_data=representative.request_data,
            response_data=representative.response_data,
            count=count,
            timestamp=representative.timestamp,
        )

        return error_info

    def _sort_by_severity(self, error_infos: List[ErrorInfo]) -> List[ErrorInfo]:
        """按严重程度排序

        Args:
            error_infos: 异常详情列表

        Returns:
            List[ErrorInfo]: 已排序的异常详情列表
        """
        def get_severity(error_type: str) -> int:
            """获取错误类型的严重程度数值"""
            return self.SEVERITY_ORDER.get(error_type, 999)

        # 按严重程度排序（数值越小越靠前）
        sorted_errors = sorted(
            error_infos,
            key=lambda e: (get_severity(e.error_type), e.interface_name)
        )

        return sorted_errors

    def get_error_statistics(self, error_infos: List[ErrorInfo]) -> Dict[str, Any]:
        """获取异常统计信息

        Args:
            error_infos: 异常详情列表

        Returns:
            dict: 异常统计信息
        """
        if not error_infos:
            return {
                'total_errors': 0,
                'error_types': {},
                'most_common_error': None,
                'total_occurrences': 0,
            }

        # 统计各错误类型的出现次数
        error_type_counts = defaultdict(int)
        total_occurrences = 0

        for error_info in error_infos:
            error_type_counts[error_info.error_type] += error_info.count
            total_occurrences += error_info.count

        # 找出最常见的错误类型
        most_common_error = max(
            error_type_counts.items(),
            key=lambda x: x[1]
        ) if error_type_counts else None

        return {
            'total_errors': len(error_infos),
            'error_types': dict(error_type_counts),
            'most_common_error': most_common_error,
            'total_occurrences': total_occurrences,
        }
