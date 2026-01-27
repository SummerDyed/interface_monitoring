"""
企业微信消息模型测试

测试WechatMessage和PushResult数据模型的功能

作者: 开发团队
创建时间: 2026-01-27
"""

import pytest
from datetime import datetime
from src.notifier.models.wechat_message import WechatMessage, PushResult


class TestWechatMessage:
    """测试WechatMessage数据模型"""

    def test_init_default(self):
        """测试初始化默认值"""
        message = WechatMessage()
        assert message.msgtype == "markdown"
        assert message.markdown == {}
        assert message.mentioned_list == []
        assert message.mentioned_mobile_list == []

    def test_init_with_data(self):
        """测试使用数据初始化"""
        markdown_content = {"content": "测试消息"}
        message = WechatMessage(
            msgtype="markdown",
            markdown=markdown_content,
            mentioned_list=["@user1"],
            mentioned_mobile_list=["13800138000"]
        )
        assert message.msgtype == "markdown"
        assert message.markdown == markdown_content
        assert message.mentioned_list == ["@user1"]
        assert message.mentioned_mobile_list == ["13800138000"]

    def test_to_dict(self):
        """测试转换为字典"""
        message = WechatMessage(
            markdown={"content": "测试"},
            mentioned_list=["@user1"]
        )
        result = message.to_dict()
        assert result["msgtype"] == "markdown"
        assert result["markdown"] == {"content": "测试"}
        assert result["mentioned_list"] == ["@user1"]

    def test_to_dict_without_mentions(self):
        """测试无@人员时转换为字典"""
        message = WechatMessage(markdown={"content": "测试"})
        result = message.to_dict()
        assert "mentioned_list" not in result
        assert "mentioned_mobile_list" not in result

    def test_to_json(self):
        """测试转换为JSON"""
        message = WechatMessage(markdown={"content": "测试消息"})
        json_str = message.to_json()
        assert '"msgtype":"markdown"' in json_str
        assert '"content":"测试消息"' in json_str

    def test_from_dict(self):
        """测试从字典创建对象"""
        data = {
            "msgtype": "markdown",
            "markdown": {"content": "测试"},
            "mentioned_list": ["@user1"]
        }
        message = WechatMessage.from_dict(data)
        assert message.msgtype == "markdown"
        assert message.markdown == {"content": "测试"}
        assert message.mentioned_list == ["@user1"]

    def test_add_mention_user_id(self):
        """测试添加用户ID @人员"""
        message = WechatMessage()
        message.add_mention(user_id="@user1")
        assert "@user1" in message.mentioned_list

    def test_add_mention_mobile(self):
        """测试添加手机号 @人员"""
        message = WechatMessage()
        message.add_mention(mobile="13800138000")
        assert "13800138000" in message.mentioned_mobile_list

    def test_add_mention_both(self):
        """测试同时添加用户ID和手机号"""
        message = WechatMessage()
        message.add_mention(user_id="@user1", mobile="13800138000")
        assert "@user1" in message.mentioned_list
        assert "13800138000" in message.mentioned_mobile_list

    def test_add_mentions(self):
        """测试批量添加@人员"""
        message = WechatMessage()
        message.add_mentions(
            user_ids=["@user1", "@user2"],
            mobiles=["13800138000", "13800138001"]
        )
        assert "@user1" in message.mentioned_list
        assert "@user2" in message.mentioned_list
        assert "13800138000" in message.mentioned_mobile_list
        assert "13800138001" in message.mentioned_mobile_list


class TestPushResult:
    """测试PushResult数据模型"""

    def test_success_result(self):
        """测试创建成功结果"""
        result = PushResult.success_result(
            message_id="msg123",
            response_data={"errcode": 0}
        )
        assert result.success is True
        assert result.message_id == "msg123"
        assert result.response_data == {"errcode": 0}
        assert result.retry_count == 0

    def test_success_result_with_retry(self):
        """测试创建带重试次数的成功结果"""
        result = PushResult.success_result(
            message_id="msg123",
            retry_count=2
        )
        assert result.success is True
        assert result.retry_count == 2

    def test_failure_result(self):
        """测试创建失败结果"""
        result = PushResult.failure_result(
            error_message="测试错误",
            response_data={"errcode": 40001}
        )
        assert result.success is False
        assert result.error_message == "测试错误"
        assert result.response_data == {"errcode": 40001}
        assert result.retry_count == 0

    def test_failure_result_with_retry(self):
        """测试创建带重试次数的失败结果"""
        result = PushResult.failure_result(
            error_message="测试错误",
            retry_count=3
        )
        assert result.success is False
        assert result.retry_count == 3

    def test_timestamp_default(self):
        """测试默认时间戳"""
        before = datetime.now()
        result = PushResult(success=True)
        after = datetime.now()
        assert before <= result.timestamp <= after

    def test_to_dict(self):
        """测试转换为字典"""
        result = PushResult(
            success=True,
            message_id="msg123",
            error_message="错误",
            retry_count=1,
            timestamp=datetime(2026, 1, 27, 12, 0, 0)
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["message_id"] == "msg123"
        assert data["error_message"] == "错误"
        assert data["retry_count"] == 1
        assert data["timestamp"] == "2026-01-27T12:00:00"
