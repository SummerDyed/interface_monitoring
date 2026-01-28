"""
企业微信Webhook客户端测试

测试WebhookClient的API调用和重试机制

作者: 开发团队
创建时间: 2026-01-27
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from src.notifier.webhook_client import WebhookClient, RetryConfig
from src.notifier.models.wechat_message import WechatMessage, PushResult


class TestWebhookClient:
    """测试WebhookClient"""

    def test_init(self):
        """测试初始化"""
        client = WebhookClient(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            timeout=15,
            max_retries=5
        )
        assert client.webhook_url == "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
        assert client.timeout == 15
        assert client.max_retries == 5

    def test_init_default(self):
        """测试默认参数初始化"""
        client = WebhookClient("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")
        assert client.timeout == 10
        assert client.max_retries == RetryConfig.MAX_ATTEMPTS

    @patch('requests.Session.post')
    def test_send_message_success(self, mock_post):
        """测试发送消息成功"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errcode": 0,
            "errmsg": "ok",
            "msgid": "123456"
        }
        mock_post.return_value = mock_response

        # 创建客户端和消息
        client = WebhookClient("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")
        message = WechatMessage(markdown={"content": "测试"})

        # 发送消息
        result = client.send_message(message)

        # 验证结果
        assert result.success is True
        assert result.message_id == "123456"
        assert result.retry_count == 0
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_send_message_api_error(self, mock_post):
        """测试API错误"""
        # 模拟API错误响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errcode": 40001,
            "errmsg": "access_token invalid"
        }
        mock_post.return_value = mock_response

        # 创建客户端和消息
        client = WebhookClient("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")
        message = WechatMessage(markdown={"content": "测试"})

        # 发送消息
        result = client.send_message(message)

        # 验证结果
        assert result.success is False
        assert "access_token无效" in result.error_message or "access_token invalid" in result.error_message
        assert result.retry_count == 0  # 不可重试的错误

    @patch('requests.Session.post')
    def test_send_message_http_error(self, mock_post):
        """测试HTTP错误"""
        # 模拟HTTP 500错误
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        # 创建客户端和消息
        client = WebhookClient(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            max_retries=2
        )
        message = WechatMessage(markdown={"content": "测试"})

        # 发送消息
        result = client.send_message(message)

        # 验证结果
        assert result.success is False
        assert result.retry_count == 2  # 重试2次后失败

    @patch('requests.Session.post')
    def test_send_message_timeout(self, mock_post):
        """测试超时错误"""
        # 模拟超时异常
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        # 创建客户端和消息
        client = WebhookClient(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            max_retries=2
        )
        message = WechatMessage(markdown={"content": "测试"})

        # 发送消息
        result = client.send_message(message)

        # 验证结果
        assert result.success is False
        assert "消息发送失败" in result.error_message
        assert "已重试 2 次" in result.error_message
        assert result.retry_count == 2

    @patch('requests.Session.post')
    def test_send_message_connection_error(self, mock_post):
        """测试连接错误"""
        # 模拟连接错误
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # 创建客户端和消息
        client = WebhookClient(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            max_retries=2
        )
        message = WechatMessage(markdown={"content": "测试"})

        # 发送消息
        result = client.send_message(message)

        # 验证结果
        assert result.success is False
        assert "消息发送失败" in result.error_message
        assert "已重试 2 次" in result.error_message
        assert result.retry_count == 2

    @patch('requests.Session.post')
    def test_send_message_retry_success(self, mock_post):
        """测试重试后成功"""
        # 模拟前两次失败，第三次成功
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503
        mock_response_fail.json.return_value = {}

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "errcode": 0,
            "errmsg": "ok",
            "msgid": "123456"
        }

        mock_post.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]

        # 创建客户端和消息
        client = WebhookClient(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            max_retries=3
        )
        message = WechatMessage(markdown={"content": "测试"})

        # 发送消息
        result = client.send_message(message)

        # 验证结果
        assert result.success is True
        assert result.retry_count == 2  # 重试2次后成功
        assert mock_post.call_count == 3

    def test_is_retryable_error(self):
        """测试错误是否可重试"""
        client = WebhookClient("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        # 不可重试的错误
        assert client._is_retryable_error(40001, "access_token invalid") is False
        assert client._is_retryable_error(40002, "access_token expired") is False

        # 可重试的错误
        assert client._is_retryable_error(500, "Internal Server Error") is True
        assert client._is_retryable_error(503, "Service Unavailable") is True

    def test_get_backoff_time(self):
        """测试退避时间计算"""
        client = WebhookClient("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")

        assert client._get_backoff_time(0) == 1
        assert client._get_backoff_time(1) == 2
        assert client._get_backoff_time(2) == 5
        assert client._get_backoff_time(10) == 5  # 超过配置次数时使用最大值

    def test_close(self):
        """测试关闭客户端"""
        client = WebhookClient("https://qyapi.weixin.qq.com/cgi-bin/webhook/send")
        assert client.session is not None
        client.close()
        # 验证会话是否关闭
        # 注意：requests.Session没有is_closed属性，这里主要验证不抛异常

    def test_context_manager(self):
        """测试上下文管理器"""
        with WebhookClient("https://qyapi.weixin.qq.com/cgi-bin/webhook/send") as client:
            assert client is not None
        # 退出时自动关闭

    def test_repr(self):
        """测试对象字符串表示"""
        client = WebhookClient(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
            max_retries=5
        )
        repr_str = repr(client)
        assert "WebhookClient" in repr_str
        assert "webhook_url" in repr_str
