"""
企业微信消息格式化器
将监控报告转换为企业微信Markdown格式消息

作者: 开发团队
创建时间: 2026-01-27
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models.wechat_message import WechatMessage

logger = logging.getLogger(__name__)


class MessageFormatter:
    """企业微信消息格式化器

    负责将监控报告转换为企业微信Markdown格式的消息
    """

    # 企业微信Markdown模板
    WECHAT_TEMPLATE = """## 🔔 接口监控告警

**监控时间**: {timestamp}
**总接口数**: {total_count}
**成功数**: {success_count}
**失败数**: {failure_count}
**成功率**: {success_rate}%

## ⚠️ 异常详情

{error_details}

## 📊 统计信息

{stats_details}

---
*由接口监控系统自动发送*
"""

    # 简化的Markdown模板（用于消息较短时）
    SIMPLE_TEMPLATE = """## 🔔 接口监控告警

**时间**: {timestamp}
**成功率**: {success_rate}%
**异常数**: {failure_count}

{error_summary}
"""

    def __init__(self, max_message_length: int = 4000):
        """初始化消息格式化器

        Args:
            max_message_length: 最大消息长度（企业微信限制）
        """
        self.max_message_length = max_message_length

    def format_report(
        self,
        report: Any,
        mentioned_list: Optional[List[str]] = None,
        mentioned_mobile_list: Optional[List[str]] = None
    ) -> WechatMessage:
        """格式化监控报告为微信消息

        Args:
            report: 监控报告对象
            mentioned_list: @人员列表（用户ID）
            mentioned_mobile_list: @人员列表（手机号）

        Returns:
            WechatMessage: 微信消息对象
        """
        # 生成Markdown内容
        markdown_content = self._generate_markdown_content(report)

        # 创建消息对象
        message = WechatMessage(
            msgtype="markdown",
            markdown={"content": markdown_content}
        )

        # 添加@人员
        if mentioned_list:
            message.mentioned_list.extend(mentioned_list)

        if mentioned_mobile_list:
            message.mentioned_mobile_list.extend(mentioned_mobile_list)

        return message

    def _generate_markdown_content(self, report: Any) -> str:
        """生成Markdown内容

        Args:
            report: 监控报告对象

        Returns:
            str: Markdown格式的字符串
        """
        try:
            # 提取报告信息
            timestamp = self._format_timestamp(report.timestamp if hasattr(report, 'timestamp') else datetime.now())
            total_count = report.total_count if hasattr(report, 'total_count') else 0
            success_count = report.success_count if hasattr(report, 'success_count') else 0
            failure_count = report.failure_count if hasattr(report, 'failure_count') else 0
            success_rate = getattr(report, 'success_rate', 0.0)

            # 生成错误详情
            error_details = self._format_error_details(report)

            # 生成统计信息
            stats_details = self._format_stats(report)

            # 填充模板
            content = self.WECHAT_TEMPLATE.format(
                timestamp=timestamp,
                total_count=total_count,
                success_count=success_count,
                failure_count=failure_count,
                success_rate=f"{success_rate:.2f}",
                error_details=error_details,
                stats_details=stats_details
            )

            # 检查消息长度，如果超过限制则使用简化版本
            if len(content) > self.max_message_length:
                logger.warning(
                    f"消息长度 ({len(content)}) 超过限制 ({self.max_message_length})，使用简化版本"
                )
                content = self._generate_simple_content(
                    timestamp, success_rate, failure_count, report
                )

            return content

        except Exception as e:
            logger.error(f"生成Markdown内容失败: {str(e)}", exc_info=True)
            # 返回简单的错误消息
            return self._generate_error_message(str(e))

    def _format_timestamp(self, timestamp: Any) -> str:
        """格式化时间戳

        Args:
            timestamp: 时间戳

        Returns:
            str: 格式化后的时间字符串
        """
        try:
            # 如果时间为None或空，返回当前时间
            if timestamp is None:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if isinstance(timestamp, datetime):
                return timestamp.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(timestamp, str):
                return timestamp
            else:
                return str(timestamp)
        except Exception as e:
            logger.warning(f"时间格式化失败: {str(e)}")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _format_error_details(self, report: Any) -> str:
        """格式化错误详情

        Args:
            report: 监控报告对象

        Returns:
            str: 错误详情Markdown字符串
        """
        try:
            # 获取错误列表
            errors = []
            if hasattr(report, 'errors') and report.errors:
                errors = report.errors

            if not errors:
                return "✅ 暂无异常"

            # 按错误类型分组
            error_groups = {}
            for error in errors:
                error_type = getattr(error, 'error_type', 'UNKNOWN')
                if error_type not in error_groups:
                    error_groups[error_type] = []
                error_groups[error_type].append(error)

            # 生成错误详情
            details = []
            for error_type, error_list in error_groups.items():
                count = len(error_list)
                details.append(f"### {error_type} ({count}个)")

                # 只显示前5个错误详情，避免消息过长
                for i, error in enumerate(error_list[:5]):
                    interface_name = getattr(error, 'interface_name', 'Unknown')
                    error_message = getattr(error, 'error_message', 'No message')
                    status_code = getattr(error, 'status_code', 'N/A')

                    detail = f"- **{interface_name}**: {error_message} (HTTP {status_code})"
                    details.append(detail)

                # 如果错误数量超过5个，显示省略提示
                if count > 5:
                    details.append(f"- ... 还有 {count - 5} 个类似错误")

                details.append("")  # 空行分隔

            return "\n".join(details).strip()

        except Exception as e:
            logger.error(f"格式化错误详情失败: {str(e)}", exc_info=True)
            return f"❌ 错误详情格式化失败: {str(e)}"

    def _format_stats(self, report: Any) -> str:
        """格式化统计信息

        Args:
            report: 监控报告对象

        Returns:
            str: 统计信息Markdown字符串
        """
        try:
            # 尝试从报告获取统计信息
            stats = getattr(report, 'stats', None)

            if stats:
                # 如果有stats对象，尝试提取信息
                stats_lines = []

                # 尝试获取服务健康度
                if hasattr(stats, 'service_health') and stats.service_health:
                    stats_lines.append("### 服务健康度")
                    for service, health in stats.service_health.items():
                        status_icon = "🟢" if health.get('status') == 'HEALTHY' else \
                                     "🟡" if health.get('status') == 'DEGRADED' else "🔴"
                        success_rate = health.get('success_rate', 0)
                        stats_lines.append(
                            f"- {status_icon} **{service}**: {success_rate:.2f}% "
                            f"({health.get('success_count', 0)}/{health.get('total_count', 0)})"
                        )

                # 尝试获取错误分布
                if hasattr(stats, 'error_distribution') and stats.error_distribution:
                    if stats_lines:
                        stats_lines.append("")
                    stats_lines.append("### 错误分布")
                    for error_type, count in stats.error_distribution.items():
                        stats_lines.append(f"- {error_type}: {count}个")

                if stats_lines:
                    return "\n".join(stats_lines)

            # 如果没有stats对象或stats为空，显示基本信息
            return (
                f"- **平均响应时间**: N/A\n"
                f"- **P95响应时间**: N/A\n"
                f"- **P99响应时间**: N/A"
            )

        except Exception as e:
            logger.error(f"格式化统计信息失败: {str(e)}", exc_info=True)
            return f"❌ 统计信息格式化失败: {str(e)}"

    def _generate_simple_content(
        self,
        timestamp: str,
        success_rate: float,
        failure_count: int,
        report: Any
    ) -> str:
        """生成简化版内容

        Args:
            timestamp: 时间戳
            success_rate: 成功率
            failure_count: 失败数
            report: 报告对象

        Returns:
            str: 简化版Markdown内容
        """
        # 获取主要错误类型
        error_summary = "✅ 暂无异常"
        if failure_count > 0 and hasattr(report, 'errors') and report.errors:
            error_types = {}
            for error in report.errors:
                error_type = getattr(error, 'error_type', 'UNKNOWN')
                error_types[error_type] = error_types.get(error_type, 0) + 1

            summary_parts = []
            for error_type, count in error_types.items():
                summary_parts.append(f"{error_type}: {count}个")

            if summary_parts:
                error_summary = "\n".join([f"- {part}" for part in summary_parts[:3]])
                if len(error_types) > 3:
                    error_summary += f"\n- ... 还有 {len(error_types) - 3} 种错误类型"

        return self.SIMPLE_TEMPLATE.format(
            timestamp=timestamp,
            success_rate=f"{success_rate:.2f}",
            failure_count=failure_count,
            error_summary=error_summary
        )

    def _generate_error_message(self, error_msg: str) -> str:
        """生成错误消息

        Args:
            error_msg: 错误信息

        Returns:
            str: 错误消息Markdown
        """
        return f"""## ❌ 消息生成失败

**错误**: {error_msg}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查监控报告数据格式是否正确。
"""
