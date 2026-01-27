"""
结果分析器
提供监控结果的分析、分类和聚合功能

作者: 开发团队
创建时间: 2026-01-27
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from src.monitor.result import MonitorResult
from .aggregators import ErrorAggregator, StatsAggregator
from .models import MonitorReport, Stats, ErrorInfo
from .alert_logic import (
    should_send_alert,
    get_alert_priority,
    get_alert_recipients,
    get_alert_summary,
    filter_alert_errors,
    process_alert,
)

logger = logging.getLogger(__name__)


class ResultAnalyzer:
    """结果分析器

    负责分析监控结果，进行分类、聚合和统计，生成完整的分析报告
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化结果分析器

        Args:
            config: 配置字典，可包含：
                - max_batch_size: 批处理大小（默认1000）
                - enable_streaming: 是否启用流式处理（默认False）
        """
        self.config = config or {}
        self.max_batch_size = self.config.get('max_batch_size', 1000)
        self.enable_streaming = self.config.get('enable_streaming', False)

        # 创建聚合器
        self.error_aggregator = ErrorAggregator()
        self.stats_aggregator = StatsAggregator()

        logger.info(
            f"结果分析器初始化完成: "
            f"批处理大小={self.max_batch_size}, "
            f"流式处理={'启用' if self.enable_streaming else '禁用'}"
        )

    def analyze(
        self,
        results: List[MonitorResult],
        title: Optional[str] = None,
    ) -> MonitorReport:
        """分析监控结果并生成报告

        Args:
            results: 监控结果列表
            title: 报告标题（可选）

        Returns:
            MonitorReport: 完整的监控分析报告
        """
        if not results:
            logger.warning("监控结果为空，创建空报告")
            return self._create_empty_report(title)

        logger.info(f"开始分析 {len(results)} 个监控结果")

        # 分类结果
        success_results, failed_results = self.categorize_results(results)

        # 聚合异常
        errors = self.aggregate_errors(failed_results)

        # 生成统计
        stats = self.generate_stats(results)

        # 构建报告
        report = self._build_report(results, errors, stats, title)

        # 判断是否需要告警（仅404和500错误）
        alert_info = process_alert(report)

        # 添加告警信息到报告
        report.alert_info = alert_info

        logger.info(
            f"分析完成: 总数={len(results)}, "
            f"成功={len(success_results)}, "
            f"失败={len(failed_results)}, "
            f"异常类型={len(errors)}, "
            f"需要告警={alert_info.get('should_alert', False)}, "
            f"告警摘要={alert_info.get('summary', '无')}"
        )

        return report

    def categorize_results(
        self, results: List[MonitorResult]
    ) -> Tuple[List[MonitorResult], List[MonitorResult]]:
        """分类监控结果

        将结果分为成功和失败两类

        Args:
            results: 监控结果列表

        Returns:
            Tuple[List, List]: (成功结果列表, 失败结果列表)
        """
        if not results:
            return [], []

        success_results = []
        failed_results = []

        for result in results:
            if result.is_success():
                success_results.append(result)
            else:
                failed_results.append(result)

        logger.debug(
            f"结果分类完成: 成功={len(success_results)}, 失败={len(failed_results)}"
        )

        return success_results, failed_results

    def aggregate_errors(self, failed_results: List[MonitorResult]) -> List[ErrorInfo]:
        """聚合异常结果

        Args:
            failed_results: 失败的监控结果列表

        Returns:
            List[ErrorInfo]: 聚合后的异常详情列表
        """
        if not failed_results:
            logger.debug("没有失败的监控结果，无需聚合异常")
            return []

        # 使用ErrorAggregator聚合异常
        errors = self.error_aggregator.aggregate(failed_results)

        logger.debug(f"异常聚合完成，共 {len(errors)} 种异常类型")

        return errors

    def generate_stats(self, results: List[MonitorResult]) -> Stats:
        """生成统计信息

        Args:
            results: 监控结果列表

        Returns:
            Stats: 统计信息对象
        """
        if not results:
            logger.debug("没有监控结果，返回默认统计")
            return self.stats_aggregator._create_empty_stats()

        # 使用StatsAggregator生成统计
        stats = self.stats_aggregator.aggregate(results)

        logger.debug(
            f"统计生成完成: 总数={stats.total_count}, 成功率={stats.success_rate:.2f}%"
        )

        return stats

    def _build_report(
        self,
        results: List[MonitorResult],
        errors: List[ErrorInfo],
        stats: Stats,
        title: Optional[str],
    ) -> MonitorReport:
        """构建监控报告

        Args:
            results: 原始监控结果列表
            errors: 异常详情列表
            stats: 统计信息对象
            title: 报告标题

        Returns:
            MonitorReport: 监控报告对象
        """
        # 计算基础统计
        total_count = len(results)
        success_count = sum(1 for r in results if r.is_success())
        failure_count = total_count - success_count
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0.0

        # 构建报告
        report = MonitorReport(
            title=title or "接口监控报告",
            timestamp=datetime.now(),
            total_count=total_count,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            errors=errors,
            stats=stats,
        )

        return report

    def _create_empty_report(self, title: Optional[str] = None) -> MonitorReport:
        """创建空报告

        Args:
            title: 报告标题

        Returns:
            MonitorReport: 空的监控报告对象
        """
        return MonitorReport(
            title=title or "接口监控报告",
            timestamp=datetime.now(),
            total_count=0,
            success_count=0,
            failure_count=0,
            success_rate=0.0,
            errors=[],
            stats=self.stats_aggregator._create_empty_stats(),
        )

    def analyze_streaming(
        self,
        result_generator,
        batch_size: Optional[int] = None,
        title: Optional[str] = None,
    ) -> MonitorReport:
        """流式分析监控结果

        适用于大量数据的场景，避免内存溢出

        Args:
            result_generator: 监控结果生成器
            batch_size: 批处理大小
            title: 报告标题

        Returns:
            MonitorReport: 监控分析报告
        """
        batch_size = batch_size or self.max_batch_size

        if not self.enable_streaming:
            logger.warning("流式处理未启用，将结果收集到内存后分析")
            # 将生成器转换为列表（可能耗用大量内存）
            results = list(result_generator)
            return self.analyze(results, title)

        logger.info(f"开始流式分析，批处理大小={batch_size}")

        all_results = []
        batch_count = 0

        try:
            # 逐批处理结果
            batch = []
            for result in result_generator:
                batch.append(result)

                # 当批次满时进行处理
                if len(batch) >= batch_size:
                    batch_count += 1
                    logger.debug(f"处理第 {batch_count} 批，共 {len(batch)} 个结果")

                    # 分析当前批次
                    report = self.analyze(batch, title)
                    all_results.extend(batch)

                    # 重置批次
                    batch = []

            # 处理剩余结果
            if batch:
                batch_count += 1
                logger.debug(f"处理最后一批，共 {len(batch)} 个结果")
                all_results.extend(batch)

            logger.info(f"流式分析完成，共处理 {len(all_results)} 个结果")

            # 重新分析全部结果（为了保证统计准确性）
            return self.analyze(all_results, title)

        except Exception as e:
            logger.error(f"流式分析过程中发生错误: {e}", exc_info=True)
            # 如果流式分析失败，回退到普通分析
            logger.info("回退到普通分析模式")
            results = list(result_generator)
            return self.analyze(results, title)

    def get_error_summary(self, errors: List[ErrorInfo]) -> Dict[str, Any]:
        """获取异常摘要

        Args:
            errors: 异常详情列表

        Returns:
            dict: 异常摘要信息
        """
        if not errors:
            return {
                'total_error_types': 0,
                'total_occurrences': 0,
                'most_severe_error': None,
                'error_distribution': {},
            }

        # 获取异常统计
        error_stats = self.error_aggregator.get_error_statistics(errors)

        # 找出最严重的错误（按严重程度排序的第一个）
        most_severe_error = None
        if errors:
            most_severe_error = {
                'error_type': errors[0].error_type,
                'interface': errors[0].interface_name,
                'count': errors[0].count,
            }

        return {
            'total_error_types': error_stats['total_errors'],
            'total_occurrences': error_stats['total_occurrences'],
            'most_severe_error': most_severe_error,
            'error_distribution': error_stats['error_types'],
        }
