"""
企业微信推送器
集成消息格式化和Webhook客户端，提供完整的推送功能

作者: 开发团队
创建时间: 2026-01-27
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from .webhook_client import WebhookClient, RetryConfig
from .message_formatter import MessageFormatter
from .models.wechat_message import WechatMessage, PushResult

logger = logging.getLogger(__name__)


class WechatNotifier:
    """企业微信推送器

    集成消息格式化和Webhook客户端，提供完整的推送功能
    """

    def __init__(
        self,
        webhook_url: str,
        mentioned_list: Optional[List[str]] = None,
        mentioned_mobile_list: Optional[List[str]] = None,
        timeout: int = 10,
        max_retries: int = RetryConfig.MAX_ATTEMPTS,
        max_message_length: int = 4000
    ):
        """初始化企业微信推送器

        Args:
            webhook_url: 企业微信机器人Webhook地址
            mentioned_list: 默认@人员列表（用户ID）
            mentioned_mobile_list: 默认@人员列表（手机号）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            max_message_length: 最大消息长度
        """
        self.webhook_url = webhook_url
        self.default_mentioned_list = mentioned_list or []
        self.default_mentioned_mobile_list = mentioned_mobile_list or []

        # 初始化组件
        self.webhook_client = WebhookClient(
            webhook_url=webhook_url,
            timeout=timeout,
            max_retries=max_retries
        )
        self.message_formatter = MessageFormatter(max_message_length=max_message_length)

        logger.info(
            f"企业微信推送器初始化完成: "
            f"webhook={webhook_url}, "
            f"mentioned_list={len(self.default_mentioned_list)}, "
            f"mentioned_mobile_list={len(self.default_mentioned_mobile_list)}, "
            f"max_message_length={max_message_length}"
        )

    def send_report(
        self,
        report: Any,
        mentioned_list: Optional[List[str]] = None,
        mentioned_mobile_list: Optional[List[str]] = None,
        alert_info: Optional[Dict[str, Any]] = None
    ) -> PushResult:
        """发送监控报告

        Args:
            report: 监控报告对象
            mentioned_list: 临时@人员列表（用户ID）
            mentioned_mobile_list: 临时@人员列表（手机号）
            alert_info: 告警信息（包含告警接收人等）

        Returns:
            PushResult: 推送结果
        """
        try:
            logger.info("开始发送监控报告")

            # 解析告警信息，获取接收人
            final_mentioned_list, final_mentioned_mobile_list = self._resolve_recipients(
                mentioned_list,
                mentioned_mobile_list,
                alert_info
            )

            # 格式化消息
            message = self.message_formatter.format_report(
                report=report,
                mentioned_list=final_mentioned_list,
                mentioned_mobile_list=final_mentioned_mobile_list,
                alert_info=alert_info
            )

            # 检查消息长度，如果超过限制则创建详细日志文件
            content = message.markdown['content']
            if len(content) > self.message_formatter.max_message_length:
                logger.warning(
                    f"消息长度 ({len(content)}) 超过限制 ({self.message_formatter.max_message_length})，将创建详细日志文件"
                )

                # 创建包含详细信息的日志文件
                detailed_content = self._generate_detailed_report(report, alert_info)
                file_path = self.webhook_client.create_detailed_log_file(detailed_content)

                # 创建简化的消息，包含文件说明
                simple_content = self._create_simple_alert_message(report, alert_info, file_path)
                simplified_message = WechatMessage(
                    msgtype="markdown",
                    markdown={"content": simple_content},
                    mentioned_list=final_mentioned_list,
                    mentioned_mobile_list=final_mentioned_mobile_list
                )

                # 发送简化消息
                result = self.webhook_client.send_message(simplified_message)

                # 如果文件创建成功，尝试发送文件
                if file_path and os.path.exists(file_path):
                    logger.info(f"尝试发送详细日志文件: {file_path}")
                    file_result = self.webhook_client.send_file(file_path, os.path.basename(file_path))

                    if file_result.success:
                        logger.info("详细日志文件发送成功")
                    else:
                        logger.warning(f"详细日志文件发送失败: {file_result.error_message}")
            else:
                # 消息长度正常，直接发送
                result = self.webhook_client.send_message(message)

            # 记录结果
            if result.success:
                logger.info(
                    f"监控报告发送成功: message_id={result.message_id}, "
                    f"retry_count={result.retry_count}"
                )
            else:
                logger.error(
                    f"监控报告发送失败: {result.error_message}, "
                    f"retry_count={result.retry_count}"
                )

            return result

        except Exception as e:
            error_msg = f"发送监控报告时发生异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return PushResult.failure_result(error_message=error_msg)

    def _generate_detailed_report(self, report: Any, alert_info: Optional[Dict[str, Any]] = None) -> str:
        """生成详细的监控报告

        Args:
            report: 监控报告对象
            alert_info: 告警信息

        Returns:
            str: 详细报告内容
        """
        try:
            from datetime import datetime

            content_parts = []

            # 添加报告标题
            content_parts.append("=" * 80)
            content_parts.append("接口监控详细报告")
            content_parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            content_parts.append("=" * 80)
            content_parts.append("")

            # 添加基本信息
            content_parts.append("## 基本信息")
            content_parts.append(f"总接口数: {getattr(report, 'total_count', 0)}")
            content_parts.append(f"成功数: {getattr(report, 'success_count', 0)}")
            content_parts.append(f"失败数: {getattr(report, 'failure_count', 0)}")
            content_parts.append(f"成功率: {getattr(report, 'success_rate', 0):.2f}%")
            content_parts.append("")

            # 添加错误详情
            if hasattr(report, 'errors') and report.errors:
                content_parts.append("## 详细错误信息")
                content_parts.append("")

                for i, error in enumerate(report.errors, 1):
                    content_parts.append(f"### 错误 #{i}")
                    content_parts.append(f"接口名称: {getattr(error, 'interface_name', 'Unknown')}")
                    content_parts.append(f"请求方法: {getattr(error, 'interface_method', 'Unknown')}")
                    content_parts.append(f"接口地址: {getattr(error, 'interface_url', 'Unknown')}")
                    content_parts.append(f"服务类型: {getattr(error, 'service', 'Unknown')}")
                    content_parts.append(f"错误类型: {getattr(error, 'error_type', 'Unknown')}")
                    content_parts.append(f"状态码: {getattr(error, 'status_code', 'Unknown')}")
                    content_parts.append(f"错误信息: {getattr(error, 'error_message', 'Unknown')}")
                    content_parts.append(f"发生次数: {getattr(error, 'count', 1)}")
                    content_parts.append("")

                    # 添加请求数据
                    request_data = getattr(error, 'request_data', {})
                    if request_data:
                        content_parts.append("**请求数据:**")
                        import json
                        try:
                            content_parts.append(json.dumps(request_data, indent=2, ensure_ascii=False))
                        except:
                            content_parts.append(str(request_data))
                        content_parts.append("")

                    # 添加响应数据
                    response_data = getattr(error, 'response_data', {})
                    if response_data:
                        content_parts.append("**响应数据:**")
                        import json
                        try:
                            content_parts.append(json.dumps(response_data, indent=2, ensure_ascii=False))
                        except:
                            content_parts.append(str(response_data))
                        content_parts.append("")

                    content_parts.append("-" * 40)
                    content_parts.append("")

            return "\n".join(content_parts)

        except Exception as e:
            logger.error(f"生成详细报告失败: {str(e)}")
            return f"生成详细报告失败: {str(e)}"

    def _create_simple_alert_message(self, report: Any, alert_info: Optional[Dict[str, Any]], file_path: str) -> str:
        """创建简化的告警消息

        Args:
            report: 监控报告对象
            alert_info: 告警信息
            file_path: 详细日志文件路径

        Returns:
            str: 简化消息内容
        """
        try:
            from datetime import datetime
            import os

            filename = os.path.basename(file_path)

            # 创建简化的告警消息
            message_parts = []

            # 告警标题
            if alert_info and alert_info.get('alert_type') == 'error':
                message_parts.append("## 🔔 接口监控告警")
            else:
                message_parts.append("## ✅ 接口监控报告")

            # 基本信息
            message_parts.append(f"**监控时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            message_parts.append(f"**总接口数**: {getattr(report, 'total_count', 0)}")
            message_parts.append(f"**成功数**: {getattr(report, 'success_count', 0)}")
            message_parts.append(f"**失败数**: {getattr(report, 'failure_count', 0)}")
            message_parts.append(f"**成功率**: {getattr(report, 'success_rate', 0):.2f}%")

            # 告警摘要
            if alert_info and alert_info.get('summary'):
                message_parts.append("")
                message_parts.append(f"**告警摘要**: {alert_info['summary']}")

            # 文件说明
            message_parts.append("")
            message_parts.append("## 📄 详细信息")
            message_parts.append(f"由于消息长度限制，详细错误信息已保存到日志文件:")
            message_parts.append(f"文件名: `{filename}`")
            message_parts.append(f"文件路径: `{file_path}`")
            message_parts.append("")
            message_parts.append("---")
            message_parts.append("*详细报告包含完整的请求/响应数据，便于问题诊断*")

            return "\n".join(message_parts)

        except Exception as e:
            logger.error(f"创建简化消息失败: {str(e)}")
            return f"告警消息生成失败: {str(e)}"

    def send_message(
        self,
        content: str,
        mentioned_list: Optional[List[str]] = None,
        mentioned_mobile_list: Optional[List[str]] = None
    ) -> PushResult:
        """发送自定义消息

        Args:
            content: 消息内容（Markdown格式）
            mentioned_list: @人员列表（用户ID）
            mentioned_mobile_list: @人员列表（手机号）

        Returns:
            PushResult: 推送结果
        """
        try:
            logger.info("开始发送自定义消息")

            # 合并@人员列表
            final_mentioned_list = self.default_mentioned_list.copy()
            final_mentioned_mobile_list = self.default_mentioned_mobile_list.copy()

            if mentioned_list:
                final_mentioned_list.extend(mentioned_list)

            if mentioned_mobile_list:
                final_mentioned_mobile_list.extend(mentioned_mobile_list)

            # 创建消息
            message = WechatMessage(
                msgtype="markdown",
                markdown={"content": content},
                mentioned_list=final_mentioned_list,
                mentioned_mobile_list=final_mentioned_mobile_list
            )

            # 发送消息
            result = self.webhook_client.send_message(message)

            # 记录结果
            if result.success:
                logger.info(
                    f"自定义消息发送成功: message_id={result.message_id}, "
                    f"retry_count={result.retry_count}"
                )
            else:
                logger.error(
                    f"自定义消息发送失败: {result.error_message}, "
                    f"retry_count={result.retry_count}"
                )

            return result

        except Exception as e:
            error_msg = f"发送自定义消息时发生异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return PushResult.failure_result(error_message=error_msg)

    def _resolve_recipients(
        self,
        mentioned_list: Optional[List[str]],
        mentioned_mobile_list: Optional[List[str]],
        alert_info: Optional[Dict[str, Any]]
    ) -> tuple[List[str], List[str]]:
        """解析接收人列表

        Args:
            mentioned_list: 临时@人员列表（用户ID）
            mentioned_mobile_list: 临时@人员列表（手机号）
            alert_info: 告警信息

        Returns:
            tuple[List[str], List[str]]: 解析后的@人员列表
        """
        # 从alert_info中提取接收人
        if alert_info and isinstance(alert_info, dict):
            recipients = alert_info.get('recipients', [])

            # 如果有接收人，根据配置解析
            if recipients:
                # 解析邮箱地址，获取用户名部分作为@对象
                # 例如: user-team@company.com -> @user-team
                user_ids = []
                mobile_list = []

                for recipient in recipients:
                    # 如果是邮箱地址，提取用户名部分
                    if '@' in recipient:
                        # 可以根据需要自定义解析逻辑
                        username = recipient.split('@')[0].split('-')[0]
                        user_ids.append(f"@{username}")
                    else:
                        # 直接使用
                        user_ids.append(recipient)

                # 如果有临时参数，合并
                if mentioned_list:
                    user_ids.extend(mentioned_list)

                if mentioned_mobile_list:
                    mobile_list.extend(mentioned_mobile_list)

                return user_ids, mobile_list

        # 如果没有alert_info，使用默认或临时参数
        final_mentioned_list = self.default_mentioned_list.copy()
        final_mentioned_mobile_list = self.default_mentioned_mobile_list.copy()

        if mentioned_list:
            final_mentioned_list.extend(mentioned_list)

        if mentioned_mobile_list:
            final_mentioned_mobile_list.extend(mentioned_mobile_list)

        return final_mentioned_list, final_mentioned_mobile_list

    def test_connection(self) -> bool:
        """测试Webhook连接

        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("测试企业微信Webhook连接")

            # 发送测试消息
            test_content = """## 🔔 连接测试

这是一条测试消息，用于验证企业微信机器人配置是否正确。

**时间**: {timestamp}

如果收到此消息，说明配置正常。

---
*由接口监控系统自动发送*
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            result = self.send_message(test_content)

            return result.success

        except Exception as e:
            logger.error(f"测试连接失败: {str(e)}", exc_info=True)
            return False

    def close(self):
        """关闭推送器，释放资源"""
        if self.webhook_client:
            self.webhook_client.close()
            logger.info("企业微信推送器已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __repr__(self) -> str:
        """对象字符串表示"""
        return (
            f"WechatNotifier(webhook_url='{self.webhook_url}', "
            f"mentioned_list={len(self.default_mentioned_list)}, "
            f"mentioned_mobile_list={len(self.default_mentioned_mobile_list)})"
        )


# 便利函数
def create_notifier_from_config(config: Dict[str, Any]) -> WechatNotifier:
    """从配置字典创建推送器

    Args:
        config: 配置字典，应包含webhook_url等配置

    Returns:
        WechatNotifier: 企业微信推送器实例

    Raises:
        ValueError: 配置不完整时抛出
    """
    if not config.get('webhook_url'):
        raise ValueError("配置中缺少 webhook_url")

    webhook_url = config['webhook_url']
    mentioned_list = config.get('mentioned_list', [])
    mentioned_mobile_list = config.get('mentioned_mobile_list', [])
    timeout = config.get('timeout', 10)
    max_retries = config.get('max_retries', RetryConfig.MAX_ATTEMPTS)
    max_message_length = config.get('max_message_length', 4000)

    logger.info(f"配置读取: max_message_length={max_message_length}, config_keys={list(config.keys())}")

    return WechatNotifier(
        webhook_url=webhook_url,
        mentioned_list=mentioned_list,
        mentioned_mobile_list=mentioned_mobile_list,
        timeout=timeout,
        max_retries=max_retries,
        max_message_length=max_message_length
    )
