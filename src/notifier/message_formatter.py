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
**运行时间**: {duration}
**超时接口**: {timeout_interfaces}

## ⚠️ 异常详情

{error_details}

---
*由接口监控系统自动发送*
"""

    # 正常情况模板（无错误时使用）
    NORMAL_TEMPLATE = """## ✅ 接口监控正常

**监控时间**: {timestamp}
**接口总数**: {total_count}
**运行时间**: {duration}
**超时接口**: {timeout_interfaces}

---
*由接口监控系统自动发送*
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
        mentioned_mobile_list: Optional[List[str]] = None,
        alert_info: Optional[Dict[str, Any]] = None
    ) -> WechatMessage:
        """格式化监控报告为微信消息

        Args:
            report: 监控报告对象
            mentioned_list: @人员列表（用户ID）
            mentioned_mobile_list: @人员列表（手机号）
            alert_info: 告警信息（包含告警类型等）

        Returns:
            WechatMessage: 微信消息对象
        """
        # 生成Markdown内容
        markdown_content = self._generate_markdown_content(report, alert_info)

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

    def _generate_markdown_content(self, report: Any, alert_info: Optional[Dict[str, Any]] = None) -> str:
        """生成Markdown内容

        Args:
            report: 监控报告对象
            alert_info: 告警信息

        Returns:
            str: Markdown格式的字符串
        """
        try:
            # 如果有alert_info且类型为normal，使用正常模板
            if alert_info and alert_info.get('alert_type') == 'normal':
                return self._generate_normal_content(report, alert_info)

            # 否则使用默认模板
            # 提取报告信息
            timestamp = self._format_timestamp(report.timestamp if hasattr(report, 'timestamp') else datetime.now())
            total_count = report.total_count if hasattr(report, 'total_count') else 0
            failure_count = report.failure_count if hasattr(report, 'failure_count') else 0

            # 如果有alert_info且包含statistics，优先使用其中的数据
            if alert_info and 'statistics' in alert_info:
                statistics = alert_info['statistics']
                duration = statistics.get('duration', '未知')
                timeout_interfaces = alert_info.get('timeout_interfaces', [])
            else:
                # 否则计算运行时间和超时接口
                duration = '未知'
                timeout_interfaces = getattr(report, 'timeout_interfaces', [])

            # 构建超时接口信息
            if timeout_interfaces:
                timeout_info = "\n".join([f"- {url}" for url in timeout_interfaces])
            else:
                timeout_info = "无"

            # 生成错误详情
            error_details = self._format_error_details(report)

            # 填充模板
            content = self.WECHAT_TEMPLATE.format(
                timestamp=timestamp,
                total_count=total_count,
                duration=duration,
                timeout_interfaces=timeout_info,
                error_details=error_details
            )

            # 检查消息长度，如果超过限制则截断
            if len(content) > self.max_message_length:
                logger.warning(
                    f"消息长度 ({len(content)}) 超过限制 ({self.max_message_length})，将截断内容"
                )
                content = content[:self.max_message_length - 50] + "\n\n...内容已截断"

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

            # 按HTTP状态码分组，但只保留404和500错误
            status_groups = {}
            for error in errors:
                status_code = getattr(error, 'status_code', None)
                if status_code in [404, 500]:  # 只处理404和500错误
                    status_key = f"HTTP_{status_code}"
                    if status_key not in status_groups:
                        status_groups[status_key] = []
                    status_groups[status_key].append(error)

            # 生成错误详情
            details = []
            for status_key in sorted(status_groups.keys()):
                error_list = status_groups[status_key]
                count = len(error_list)
                status_code = status_key.replace('HTTP_', '')
                details.append(f"### {status_key} ({count}个)")

                # 显示所有错误详情，压缩格式
                for error in error_list:
                    interface_name = getattr(error, 'interface_name', 'Unknown')
                    method = getattr(error, 'interface_method', 'GET')
                    url = getattr(error, 'interface_url', '')

                    # 压缩显示：一行显示
                    details.append(f"- {method} {interface_name} | {url}")

                details.append("")

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
            # 获取平均响应时间
            avg_response_time = 0.0
            if hasattr(report, 'stats') and report.stats:
                if hasattr(report.stats, 'avg_response_time'):
                    avg_response_time = report.stats.avg_response_time
                else:
                    # 从原始响应时间计算
                    response_times = []
                    for result in getattr(report, 'results', []):
                        if hasattr(result, 'response_time'):
                            response_times.append(result.response_time)
                    if response_times:
                        avg_response_time = sum(response_times) / len(response_times)
            else:
                # 如果没有stats对象，从错误结果中计算平均响应时间
                response_times = []
                if hasattr(report, 'errors'):
                    for error in report.errors:
                        if hasattr(error, 'response_time') and error.response_time:
                            response_times.append(error.response_time)
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)

            # 返回平均响应时间
            return f"- **平均响应时间**: {avg_response_time:.2f}ms"

        except Exception as e:
            logger.error(f"格式化统计信息失败: {str(e)}", exc_info=True)
            return f"❌ 统计信息格式化失败: {str(e)}"

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

    def _generate_normal_content(self, report: Any, alert_info: Dict[str, Any]) -> str:
        """生成正常情况内容（无错误时）

        Args:
            report: 监控报告对象
            alert_info: 告警信息

        Returns:
            str: 正常情况Markdown内容
        """
        try:
            # 获取当前时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 从 alert_info 中提取数据
            statistics = alert_info.get('statistics', {})
            total_count = statistics.get('total', 0)
            duration = statistics.get('duration', '0秒')
            timeout_interfaces = alert_info.get('timeout_interfaces', [])

            # 构建超时接口信息
            if timeout_interfaces:
                timeout_info = "\n".join([f"- {url}" for url in timeout_interfaces])
            else:
                timeout_info = "无"

            # 填充正常模板
            content = self.NORMAL_TEMPLATE.format(
                timestamp=timestamp,
                total_count=total_count,
                duration=duration,
                timeout_interfaces=timeout_info
            )

            return content

        except Exception as e:
            logger.error(f"生成正常内容失败: {str(e)}", exc_info=True)
            # 返回简单的错误消息
            return self._generate_error_message(str(e))

    def _calculate_duration_and_slowest(self, report: Any) -> tuple:
        """计算运行时间和最慢接口

        Args:
            report: 监控报告对象

        Returns:
            tuple: (运行时间字符串, 最慢接口信息字符串)
        """
        try:
            # 获取所有结果
            results = getattr(report, 'results', [])

            # 计算运行时间（简化处理，默认为空或从报告时间推断）
            duration = "未知"

            # 查找最慢的接口（只统计成功的接口）
            max_response_time = 0
            slowest_interface_info = "无"

            for result in results:
                # 只统计成功的接口
                if hasattr(result, 'is_success') and result.is_success():
                    if hasattr(result, 'response_time') and result.response_time > max_response_time:
                        max_response_time = result.response_time

                    # 获取接口信息
                    interface_name = getattr(result, 'interface_name', '未知接口')
                    interface_method = getattr(result, 'interface_method', 'GET')
                    interface_url = getattr(result, 'interface_url', '')

                    # 处理错误信息中的 "[Request interrupted by user]"
                    error_message = getattr(result, 'error_message', '')
                    if '[Request interrupted by user]' in error_message:
                        error_message = error_message.replace('[Request interrupted by user]', '').strip()

                    # 构建最慢接口信息
                    if interface_url:
                        slowest_interface_info = f"{interface_name} ({interface_method} {interface_url}) - {max_response_time:.2f}秒"
                    else:
                        slowest_interface_info = f"{interface_name} - {max_response_time:.2f}秒"

            return duration, slowest_interface_info

        except Exception as e:
            logger.error(f"计算运行时间和最慢接口失败: {str(e)}", exc_info=True)
            return "未知", "无"
