"""
推送模块单元测试

作者: 开发团队
创建时间: 2026-01-28
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from unittest.mock import Mock, patch, MagicMock
import json
import yaml

from notifier.wechat_notifier import WechatNotifier
from notifier.webhook_client import WebhookClient
from notifier.message_formatter import MessageFormatter
from notifier.models.wechat_message import WeChatMessage


class TestWechatNotifier:
    """微信通知器测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        notifier = WechatNotifier()

        assert notifier.webhook_url is None
        assert notifier.enabled is False
        assert notifier.message_formatter is not None
        assert notifier.webhook_client is not None

    def test_init_with_config(self):
        """测试使用配置初始化"""
        config = {
            'webhook_url': 'https://test.com/webhook',
            'enabled': True,
            'at_users': ['user1', 'user2'],
            'message_format': 'detail',
        }

        notifier = WechatNotifier(config=config)

        assert notifier.webhook_url == 'https://test.com/webhook'
        assert notifier.enabled is True
        assert notifier.at_users == ['user1', 'user2']
        assert notifier.message_format == 'detail'

    @patch('notifier.wechat_notifier.WebhookClient')
    def test_send_success(self, mock_webhook_client):
        """测试成功发送消息"""
        # 准备mock
        mock_client_instance = Mock()
        mock_client_instance.send.return_value = True
        mock_webhook_client.return_value = mock_client_instance

        notifier = WechatNotifier(config={'webhook_url': 'https://test.com/webhook'})
        notifier.enabled = True

        # 创建模拟消息
        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = notifier.send(message)

        assert result is True
        mock_client_instance.send.assert_called_once_with(message)

    @patch('notifier.wechat_notifier.WebhookClient')
    def test_send_disabled(self, mock_webhook_client):
        """测试禁用时发送消息"""
        notifier = WechatNotifier()
        notifier.enabled = False

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = notifier.send(message)

        assert result is False
        # 不应该调用webhook
        mock_webhook_client.return_value.send.assert_not_called()

    @patch('notifier.wechat_notifier.WebhookClient')
    def test_send_no_webhook_url(self, mock_webhook_client):
        """测试没有webhook URL时发送"""
        notifier = WechatNotifier()
        notifier.enabled = True

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = notifier.send(message)

        assert result is False

    @patch('notifier.wechat_notifier.WebhookClient')
    def test_send_failure(self, mock_webhook_client):
        """测试发送失败"""
        # 准备mock
        mock_client_instance = Mock()
        mock_client_instance.send.return_value = False
        mock_webhook_client.return_value = mock_client_instance

        notifier = WechatNotifier(config={'webhook_url': 'https://test.com/webhook'})
        notifier.enabled = True

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = notifier.send(message)

        assert result is False

    @patch('notifier.wechat_notifier.WebhookClient')
    def test_send_with_exception(self, mock_webhook_client):
        """测试发送时出现异常"""
        # 准备mock
        mock_client_instance = Mock()
        mock_client_instance.send.side_effect = Exception("Network error")
        mock_webhook_client.return_value = mock_client_instance

        notifier = WechatNotifier(config={'webhook_url': 'https://test.com/webhook'})
        notifier.enabled = True

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = notifier.send(message)

        assert result is False

    def test_format_message_simple(self):
        """测试格式化简单消息"""
        notifier = WechatNotifier()
        notifier.message_format = 'simple'

        report_data = {
            'total': 100,
            'success': 90,
            'failed': 10,
            'success_rate': 90.0,
        }

        message = notifier.format_message(report_data)

        assert message is not None
        assert 'text' in message
        assert 'content' in message['text']

    def test_format_message_detail(self):
        """测试格式化详细消息"""
        notifier = WechatNotifier()
        notifier.message_format = 'detail'

        report_data = {
            'total': 100,
            'success': 90,
            'failed': 10,
            'success_rate': 90.0,
            'details': [],
        }

        message = notifier.format_message(report_data)

        assert message is not None
        assert 'text' in message

    @patch('notifier.wechat_notifier.WebhookClient')
    def test_notify_success(self, mock_webhook_client):
        """测试通知成功"""
        # 准备mock
        mock_client_instance = Mock()
        mock_client_instance.send.return_value = True
        mock_webhook_client.return_value = mock_client_instance

        notifier = WechatNotifier(config={'webhook_url': 'https://test.com/webhook'})
        notifier.enabled = True

        report_data = {
            'total': 100,
            'success': 90,
            'failed': 10,
        }

        result = notifier.notify(report_data)

        assert result is True
        mock_client_instance.send.assert_called_once()

    @patch('notifier.wechat_notifier.WebhookClient')
    def test_notify_failure(self, mock_webhook_client):
        """测试通知失败"""
        # 准备mock
        mock_client_instance = Mock()
        mock_client_instance.send.return_value = False
        mock_webhook_client.return_value = mock_client_instance

        notifier = WechatNotifier(config={'webhook_url': 'https://test.com/webhook'})
        notifier.enabled = True

        report_data = {
            'total': 100,
            'success': 90,
            'failed': 10,
        }

        result = notifier.notify(report_data)

        assert result is False

    def test_get_status(self):
        """测试获取状态"""
        notifier = WechatNotifier(
            config={
                'webhook_url': 'https://test.com/webhook',
                'enabled': True,
            }
        )

        status = notifier.get_status()

        assert status['webhook_url'] == 'https://test.com/webhook'
        assert status['enabled'] is True
        assert 'message_formatter' in status
        assert 'webhook_client' in status


class TestWebhookClient:
    """Webhook客户端测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        client = WebhookClient()

        assert client.webhook_url is None
        assert client.timeout == 10
        assert client.max_retries == 3

    def test_init_with_config(self):
        """测试使用配置初始化"""
        config = {
            'webhook_url': 'https://test.com/webhook',
            'timeout': 30,
            'max_retries': 5,
        }

        client = WebhookClient(config=config)

        assert client.webhook_url == 'https://test.com/webhook'
        assert client.timeout == 30
        assert client.max_retries == 5

    @patch('notifier.webhook_client.requests.post')
    def test_send_success(self, mock_post):
        """测试成功发送"""
        # 准备mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_response

        client = WebhookClient(config={'webhook_url': 'https://test.com/webhook'})

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = client.send(message)

        assert result is True
        mock_post.assert_called_once()

    @patch('notifier.webhook_client.requests.post')
    def test_send_failure(self, mock_post):
        """测试发送失败"""
        # 准备mock
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'errcode': 400, 'errmsg': 'bad request'}
        mock_post.return_value = mock_response

        client = WebhookClient(config={'webhook_url': 'https://test.com/webhook'})

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = client.send(message)

        assert result is False

    @patch('notifier.webhook_client.requests.post')
    def test_send_network_error(self, mock_post):
        """测试网络错误"""
        # 准备mock
        mock_post.side_effect = Exception("Network error")

        client = WebhookClient(config={'webhook_url': 'https://test.com/webhook'})

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = client.send(message)

        assert result is False

    @patch('notifier.webhook_client.requests.post')
    def test_send_timeout(self, mock_post):
        """测试超时"""
        # 准备mock
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout("Request timeout")

        client = WebhookClient(config={'webhook_url': 'https://test.com/webhook'})

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = client.send(message)

        assert result is False

    def test_is_retryable_error(self):
        """测试是否可重试的错误"""
        client = WebhookClient()

        # 可重试的错误
        assert client.is_retryable_error(500) is True
        assert client.is_retryable_error(502) is True
        assert client.is_retryable_error(503) is True
        assert client.is_retryable_error(504) is True

        # 不可重试的错误
        assert client.is_retryable_error(400) is False
        assert client.is_retryable_error(401) is False
        assert client.is_retryable_error(403) is False
        assert client.is_retryable_error(404) is False

    def test_build_payload(self):
        """测试构建负载"""
        client = WebhookClient()

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        payload = client._build_payload(message)

        assert 'msgtype' in payload
        assert payload['msgtype'] == 'text'
        assert 'text' in payload

    @patch('notifier.webhook_client.requests.post')
    def test_send_with_retry(self, mock_post):
        """测试带重试的发送"""
        # 准备mock - 第一次失败，第二次成功
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'errcode': 0, 'errmsg': 'ok'}

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        client = WebhookClient(config={
            'webhook_url': 'https://test.com/webhook',
            'max_retries': 3,
        })

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = client.send(message)

        assert result is True
        assert mock_post.call_count == 2

    @patch('notifier.webhook_client.requests.post')
    def test_send_max_retries_exceeded(self, mock_post):
        """测试超过最大重试次数"""
        # 准备mock - 一直失败
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        client = WebhookClient(config={
            'webhook_url': 'https://test.com/webhook',
            'max_retries': 3,
        })

        message = WeChatMessage(
            msgtype='text',
            text={'content': 'Test message'},
        )

        result = client.send(message)

        assert result is False
        # 初始请求 + 3次重试 = 4次
        assert mock_post.call_count == 4

    def test_cleanup(self):
        """测试清理资源"""
        client = WebhookClient()

        # 验证没有异常抛出
        client.cleanup()

    def test_get_stats(self):
        """测试获取统计信息"""
        client = WebhookClient()

        stats = client.get_stats()

        assert 'webhook_url' in stats
        assert 'timeout' in stats
        assert 'max_retries' in stats


class TestMessageFormatter:
    """消息格式化器测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        formatter = MessageFormatter()

        assert formatter.template is not None

    def test_format_simple_message(self):
        """测试格式化简单消息"""
        formatter = MessageFormatter()

        report_data = {
            'total': 100,
            'success': 90,
            'failed': 10,
            'success_rate': 90.0,
        }

        message = formatter.format_simple(report_data)

        assert 'content' in message
        assert 'Test message' not in message['content']  # 实际内容

    def test_format_detail_message(self):
        """测试格式化详细消息"""
        formatter = MessageFormatter()

        report_data = {
            'total': 100,
            'success': 90,
            'failed': 10,
            'success_rate': 90.0,
            'details': [
                {
                    'service': 'user',
                    'success': 50,
                    'failed': 5,
                },
                {
                    'service': 'nurse',
                    'success': 40,
                    'failed': 5,
                },
            ],
        }

        message = formatter.format_detail(report_data)

        assert 'content' in message
        assert len(message['content']) > len(message.get('content', ''))

    def test_format_message_with_markdown(self):
        """测试格式化带Markdown的消息"""
        formatter = MessageFormatter()

        report_data = {
            'total': 100,
            'success': 90,
            'failed': 10,
        }

        message = formatter.format_markdown(report_data)

        assert 'msgtype' in message
        assert message['msgtype'] == 'markdown'

    def test_add_mentions(self):
        """测试添加@用户"""
        formatter = MessageFormatter()

        message = {'content': 'Test message'}
        mentions = ['user1', 'user2']

        result = formatter.add_mentions(message, mentions)

        assert 'content' in result

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_benchmark_format(self, benchmark):
        """基准测试：格式化性能"""
        formatter = MessageFormatter()

        report_data = {
            'total': 100,
            'success': 90,
            'failed': 10,
            'success_rate': 90.0,
            'details': [
                {'service': 'user', 'success': 50, 'failed': 5},
                {'service': 'nurse', 'success': 40, 'failed': 5},
            ],
        }

        # 基准测试
        def format_benchmark():
            return formatter.format_detail(report_data)

        result = benchmark.pedantic(format_benchmark, rounds=100, iterations=1)

        assert 'content' in result

    def test_format_empty_report(self):
        """测试格式化空报告"""
        formatter = MessageFormatter()

        report_data = {}

        message = formatter.format_simple(report_data)

        assert 'content' in message

    def test_format_report_with_errors(self):
        """测试格式化有错误的报告"""
        formatter = MessageFormatter()

        report_data = {
            'total': 100,
            'success': 50,
            'failed': 50,
            'success_rate': 50.0,
            'errors': [
                {'type': 'timeout', 'count': 20},
                {'type': '500', 'count': 30},
            ],
        }

        message = formatter.format_detail(report_data)

        assert 'content' in message
        # 应该包含错误信息
        content = message['content']
        assert 'timeout' in content.lower() or '500' in content.lower()
