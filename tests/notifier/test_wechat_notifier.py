"""
企业微信推送器测试

测试WechatNotifier的完整推送功能

作者: 开发团队
创建时间: 2026-01-27
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.notifier.wechat_notifier import WechatNotifier, create_notifier_from_config
from src.notifier.models.wechat_message import WechatMessage, PushResult


class MockReport:
    """模拟监控报告对象"""
    def __init__(self):
        self.timestamp = datetime(2026, 1, 27, 12, 0, 0)
        self.total_count = 100
        self.success_count = 95
        self.failure_count = 5
        self.success_rate = 95.0
        self.errors = []


class TestWechatNotifier:
    """测试WechatNotifier"""

    def test_init(self):
        """测试初始化"""
        notifier = WechatNotifier(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            mentioned_list=["@user1"],
            mentioned_mobile_list=["13800138000"],
            timeout=15,
            max_retries=5
        )
        assert notifier.webhook_url == "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
        assert notifier.default_mentioned_list == ["@user1"]
        assert notifier.default_mentioned_mobile_list == ["13800138000"]

    def test_init_default(self):
        """测试默认参数初始化"""
        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")
        assert notifier.default_mentioned_list == []
        assert notifier.default_mentioned_mobile_list == []

    @patch('src.notifier.wechat_notifier.WebhookClient')
    @patch('src.notifier.wechat_notifier.MessageFormatter')
    def test_send_report_success(self, mock_formatter, mock_client):
        """测试发送报告成功"""
        # 模拟组件
        mock_client_instance = Mock()
        mock_client_instance.send_message.return_value = PushResult.success_result(
            message_id="msg123"
        )
        mock_client.return_value = mock_client_instance

        mock_formatter_instance = Mock()
        mock_message = WechatMessage(markdown={"content": "测试"})
        mock_formatter_instance.format_report.return_value = mock_message
        mock_formatter.return_value = mock_formatter_instance

        # 创建推送器
        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        # 创建报告
        report = MockReport()

        # 发送报告
        result = notifier.send_report(report)

        # 验证结果
        assert result.success is True
        assert result.message_id == "msg123"
        mock_formatter_instance.format_report.assert_called_once()
        mock_client_instance.send_message.assert_called_once()

    @patch('src.notifier.wechat_notifier.WebhookClient')
    @patch('src.notifier.wechat_notifier.MessageFormatter')
    def test_send_report_with_alert_info(self, mock_formatter, mock_client):
        """测试发送带告警信息的报告"""
        # 模拟组件
        mock_client_instance = Mock()
        mock_client_instance.send_message.return_value = PushResult.success_result(
            message_id="msg123"
        )
        mock_client.return_value = mock_client_instance

        mock_formatter_instance = Mock()
        mock_message = WechatMessage(markdown={"content": "测试"})
        mock_formatter_instance.format_report.return_value = mock_message
        mock_formatter.return_value = mock_formatter_instance

        # 创建推送器
        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        # 创建报告和告警信息
        report = MockReport()
        alert_info = {
            'recipients': ['user-team@company.com', 'dev-team@company.com']
        }

        # 发送报告
        result = notifier.send_report(report, alert_info=alert_info)

        # 验证结果
        assert result.success is True
        # 验证格式化器被调用时传递了正确的参数
        call_args = mock_formatter_instance.format_report.call_args
        assert call_args[1]['mentioned_list'] is not None

    @patch('src.notifier.wechat_notifier.WebhookClient')
    @patch('src.notifier.wechat_notifier.MessageFormatter')
    def test_send_report_failure(self, mock_formatter, mock_client):
        """测试发送报告失败"""
        # 模拟组件
        mock_client_instance = Mock()
        mock_client_instance.send_message.return_value = PushResult.failure_result(
            error_message="API Error"
        )
        mock_client.return_value = mock_client_instance

        mock_formatter_instance = Mock()
        mock_message = WechatMessage(markdown={"content": "测试"})
        mock_formatter_instance.format_report.return_value = mock_message
        mock_formatter.return_value = mock_formatter_instance

        # 创建推送器
        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        # 创建报告
        report = MockReport()

        # 发送报告
        result = notifier.send_report(report)

        # 验证结果
        assert result.success is False
        assert "API Error" in result.error_message

    @patch('src.notifier.wechat_notifier.WebhookClient.send_message')
    def test_send_message_success(self, mock_send):
        """测试发送自定义消息成功"""
        # 模拟发送成功
        mock_send.return_value = PushResult.success_result(message_id="msg456")

        # 创建推送器
        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        # 发送自定义消息
        result = notifier.send_message("测试消息")

        # 验证结果
        assert result.success is True
        assert result.message_id == "msg456"

    @patch('src.notifier.wechat_notifier.WebhookClient.send_message')
    def test_send_message_with_mentions(self, mock_send):
        """测试发送带@人员的消息"""
        # 模拟发送成功
        mock_send.return_value = PushResult.success_result(message_id="msg456")

        # 创建推送器（带默认@人员）
        notifier = WechatNotifier(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            mentioned_list=["@user1"]
        )

        # 发送自定义消息（带额外@人员）
        result = notifier.send_message(
            "测试消息",
            mentioned_list=["@user2"],
            mentioned_mobile_list=["13800138000"]
        )

        # 验证结果
        assert result.success is True
        # 验证调用时合并了@人员列表
        call_args = mock_send.call_args[0][0]
        assert "@user1" in call_args.mentioned_list
        assert "@user2" in call_args.mentioned_list
        assert "13800138000" in call_args.mentioned_mobile_list

    def test_resolve_recipients_from_alert_info(self):
        """测试从告警信息解析接收人"""
        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        alert_info = {
            'recipients': ['user-team@company.com', 'dev-team@company.com']
        }

        # 解析接收人
        mentioned_list, mentioned_mobile_list = notifier._resolve_recipients(
            None, None, alert_info
        )

        # 验证结果（应该从邮箱提取用户名）
        assert len(mentioned_list) > 0
        assert any("@user" in str(mentioned) for mentioned in mentioned_list)

    def test_resolve_recipients_with_temporary_params(self):
        """测试使用临时参数解析接收人"""
        notifier = WechatNotifier(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            mentioned_list=["@default"]
        )

        # 使用临时参数
        mentioned_list, mentioned_mobile_list = notifier._resolve_recipients(
            mentioned_list=["@temp"],
            mentioned_mobile_list=["13900139000"],
            alert_info=None
        )

        # 验证结果（应该合并默认和临时参数）
        assert "@default" in mentioned_list
        assert "@temp" in mentioned_list
        assert "13900139000" in mentioned_mobile_list

    def test_resolve_recipients_no_alert_info(self):
        """测试没有告警信息时解析接收人"""
        notifier = WechatNotifier(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            mentioned_list=["@default"]
        )

        # 解析接收人（无告警信息）
        mentioned_list, mentioned_mobile_list = notifier._resolve_recipients(
            None, None, None
        )

        # 验证结果（应该使用默认参数）
        assert mentioned_list == ["@default"]
        assert mentioned_mobile_list == []

    @patch('src.notifier.wechat_notifier.WebhookClient.send_message')
    def test_test_connection_success(self, mock_send):
        """测试连接成功"""
        # 模拟发送成功
        mock_send.return_value = PushResult.success_result(message_id="msg123")

        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        # 测试连接
        result = notifier.test_connection()

        # 验证结果
        assert result is True
        # 验证发送了测试消息
        assert mock_send.called

    @patch('src.notifier.wechat_notifier.WebhookClient.send_message')
    def test_test_connection_failure(self, mock_send):
        """测试连接失败"""
        # 模拟发送失败
        mock_send.return_value = PushResult.failure_result(error_message="API Error")

        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        # 测试连接
        result = notifier.test_connection()

        # 验证结果
        assert result is False

    def test_close(self):
        """测试关闭推送器"""
        notifier = WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")
        notifier.close()  # 应该不抛异常

    def test_context_manager(self):
        """测试上下文管理器"""
        with WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send") as notifier:
            assert notifier is not None
        # 退出时自动关闭

    def test_repr(self):
        """测试对象字符串表示"""
        notifier = WechatNotifier(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            mentioned_list=["@user1", "@user2"]
        )
        repr_str = repr(notifier)
        assert "WechatNotifier" in repr_str
        assert "webhook_url" in repr_str

    def test_create_from_config(self):
        """测试从配置创建推送器"""
        config = {
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send',
            'mentioned_list': ['@user1'],
            'timeout': 20,
            'max_retries': 5
        }

        notifier = create_notifier_from_config(config)

        assert notifier.webhook_url == config['webhook_url']
        assert notifier.default_mentioned_list == ['@user1']

    def test_create_from_config_missing_webhook_url(self):
        """测试配置缺少webhook_url时抛出异常"""
        config = {
            'mentioned_list': ['@user1']
        }

        with pytest.raises(ValueError, match="缺少 webhook_url"):
            create_notifier_from_config(config)


class TestIntegration:
    """集成测试"""

    @patch('src.notifier.wechat_notifier.WebhookClient')
    @patch('src.notifier.wechat_notifier.MessageFormatter')
    def test_full_workflow(self, mock_formatter, mock_client):
        """测试完整工作流程"""
        # 模拟组件
        mock_client_instance = Mock()
        mock_client_instance.send_message.return_value = PushResult.success_result(
            message_id="msg789"
        )
        mock_client.return_value = mock_client_instance

        mock_formatter_instance = Mock()
        mock_message = WechatMessage(markdown={"content": "测试"})
        mock_formatter_instance.format_report.return_value = mock_message
        mock_formatter.return_value = mock_formatter_instance

        # 使用上下文管理器
        with WechatNotifier("https://qyapi.weixin.qq.com/cgi-bin/webhook/send") as notifier:
            report = MockReport()
            result = notifier.send_report(report)

            assert result.success is True
            assert result.message_id == "msg789"
