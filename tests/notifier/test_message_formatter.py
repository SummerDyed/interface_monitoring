"""
企业微信消息格式化器测试

测试MessageFormatter的格式化功能

作者: 开发团队
创建时间: 2026-01-27
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from src.notifier.message_formatter import MessageFormatter
from src.notifier.models.wechat_message import WechatMessage


class MockReport:
    """模拟监控报告对象"""
    def __init__(self):
        self.timestamp = datetime(2026, 1, 27, 12, 0, 0)
        self.total_count = 100
        self.success_count = 95
        self.failure_count = 5
        self.success_rate = 95.0
        self.errors = []


class MockError:
    """模拟错误对象"""
    def __init__(self, error_type, interface_name, error_message, status_code):
        self.error_type = error_type
        self.interface_name = interface_name
        self.error_message = error_message
        self.status_code = status_code


class TestMessageFormatter:
    """测试MessageFormatter"""

    def test_init(self):
        """测试初始化"""
        formatter = MessageFormatter(max_message_length=5000)
        assert formatter.max_message_length == 5000

    def test_init_default(self):
        """测试默认参数初始化"""
        formatter = MessageFormatter()
        assert formatter.max_message_length == 4000

    def test_format_report_no_errors(self):
        """测试格式化无错误的报告"""
        formatter = MessageFormatter()
        report = MockReport()
        report.errors = []

        message = formatter.format_report(report)

        assert message.msgtype == "markdown"
        assert "✅ 暂无异常" in message.markdown["content"]
        assert "100" in message.markdown["content"]
        assert "95.00%" in message.markdown["content"]

    def test_format_report_with_errors(self):
        """测试格式化有错误的报告"""
        formatter = MessageFormatter()
        report = MockReport()
        report.errors = [
            MockError("HTTP_500", "getUser", "Server Error", 500),
            MockError("HTTP_404", "getProfile", "Not Found", 404),
        ]

        message = formatter.format_report(report)

        assert message.msgtype == "markdown"
        content = message.markdown["content"]
        assert "HTTP_500" in content
        assert "HTTP_404" in content
        assert "getUser" in content
        assert "getProfile" in content

    def test_format_report_with_mentions(self):
        """测试格式化带@人员的报告"""
        formatter = MessageFormatter()
        report = MockReport()

        message = formatter.format_report(
            report,
            mentioned_list=["@user1"],
            mentioned_mobile_list=["13800138000"]
        )

        assert "@user1" in message.mentioned_list
        assert "13800138000" in message.mentioned_mobile_list

    def test_format_timestamp_datetime(self):
        """测试格式化datetime时间戳"""
        formatter = MessageFormatter()
        dt = datetime(2026, 1, 27, 12, 0, 0)
        result = formatter._format_timestamp(dt)
        assert result == "2026-01-27 12:00:00"

    def test_format_timestamp_string(self):
        """测试格式化字符串时间戳"""
        formatter = MessageFormatter()
        result = formatter._format_timestamp("2026-01-27 12:00:00")
        assert result == "2026-01-27 12:00:00"

    def test_format_timestamp_invalid(self):
        """测试格式化无效时间戳"""
        formatter = MessageFormatter()
        result = formatter._format_timestamp(None)
        # 应该返回当前时间
        assert "20" in result  # 年份

    def test_format_error_details_no_errors(self):
        """测试格式化无错误详情"""
        formatter = MessageFormatter()
        report = MockReport()
        report.errors = []

        result = formatter._format_error_details(report)
        assert "✅ 暂无异常" in result

    def test_format_error_details_with_errors(self):
        """测试格式化有错误详情"""
        formatter = MessageFormatter()
        report = MockReport()
        report.errors = [
            MockError("HTTP_500", "getUser", "Server Error", 500),
            MockError("HTTP_500", "createOrder", "DB Error", 500),
        ]

        result = formatter._format_error_details(report)

        assert "HTTP_500 (2个)" in result
        assert "getUser" in result
        assert "createOrder" in result
        assert "Server Error" in result
        assert "DB Error" in result

    def test_format_error_details_too_many_errors(self):
        """测试错误数量超过限制时的处理"""
        formatter = MessageFormatter()
        report = MockReport()
        # 创建6个错误（超过默认显示的5个）
        report.errors = [
            MockError("HTTP_500", f"Interface{i}", f"Error{i}", 500)
            for i in range(6)
        ]

        result = formatter._format_error_details(report)

        # 应该显示省略提示
        assert "... 还有 1 个类似错误" in result

    def test_format_stats_no_stats(self):
        """测试格式化无统计信息"""
        formatter = MessageFormatter()
        report = MockReport()
        # report没有stats属性

        result = formatter._format_stats(report)

        assert "平均响应时间" in result
        assert "N/A" in result

    def test_format_stats_with_service_health(self):
        """测试格式化服务健康度统计"""
        formatter = MessageFormatter()
        report = MockReport()

        # 模拟stats对象
        stats = Mock()
        stats.service_health = {
            "user": {"status": "HEALTHY", "success_rate": 99.0, "success_count": 100, "total_count": 101},
            "order": {"status": "DEGRADED", "success_rate": 95.0, "success_count": 95, "total_count": 100}
        }
        stats.error_distribution = {"HTTP_500": 3, "HTTP_404": 2}
        report.stats = stats

        result = formatter._format_stats(report)

        assert "服务健康度" in result
        assert "🟢" in result
        assert "🟡" in result
        assert "user" in result
        assert "order" in result
        assert "错误分布" in result
        assert "HTTP_500" in result
        assert "HTTP_404" in result

    def test_generate_simple_content(self):
        """测试生成简化内容"""
        formatter = MessageFormatter()
        timestamp = "2026-01-27 12:00:00"
        success_rate = 95.0
        failure_count = 5

        report = MockReport()
        report.errors = [
            MockError("HTTP_500", "getUser", "Server Error", 500),
            MockError("HTTP_404", "getProfile", "Not Found", 404),
        ]

        result = formatter._generate_simple_content(
            timestamp, success_rate, failure_count, report
        )

        assert "🔔" in result
        assert "2026-01-27 12:00:00" in result
        assert "95.00%" in result
        assert "HTTP_500" in result
        assert "HTTP_404" in result

    def test_generate_error_message(self):
        """测试生成错误消息"""
        formatter = MessageFormatter()
        result = formatter._generate_error_message("测试错误")

        assert "❌" in result
        assert "测试错误" in result
        assert "消息生成失败" in result

    def test_message_length_limit(self):
        """测试消息长度限制"""
        formatter = MessageFormatter(max_message_length=100)  # 很小的限制
        report = MockReport()
        report.errors = [
            MockError("HTTP_500", f"Interface{i}", f"Error{i}", 500)
            for i in range(20)  # 创建很多错误
        ]

        message = formatter.format_report(report)

        # 应该使用简化版本
        content = message.markdown["content"]
        assert len(content) <= formatter.max_message_length + 100  # 允许一定误差
