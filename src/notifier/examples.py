"""
企业微信推送模块使用示例

展示如何在实际场景中使用企业微信推送功能

作者: 开发团队
创建时间: 2026-01-27
"""

from .notifier import WechatNotifier, create_notifier_from_config
from .analyzer import MonitorReport
from datetime import datetime


def example_basic_usage():
    """基础使用示例"""

    print("=" * 80)
    print("基础使用示例")
    print("=" * 80)
    print()

    # 1. 创建推送器
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key"
    notifier = WechatNotifier(
        webhook_url=webhook_url,
        mentioned_list=["@user1"],  # 默认@人员
        mentioned_mobile_list=["13800138000"]
    )

    # 2. 发送自定义消息
    message = """
## 🔔 测试消息

这是一条测试消息。

**时间**: {timestamp}

如果收到此消息，说明配置正常。

---
*由接口监控系统自动发送*
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print("发送自定义消息...")
    result = notifier.send_message(message)

    if result.success:
        print(f"✓ 消息发送成功: message_id={result.message_id}")
    else:
        print(f"✗ 消息发送失败: {result.error_message}")

    # 3. 清理资源
    notifier.close()
    print()


def example_with_monitor_report():
    """使用监控报告推送示例"""

    print("=" * 80)
    print("监控报告推送示例")
    print("=" * 80)
    print()

    # 1. 创建推送器
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key"
    notifier = WechatNotifier(
        webhook_url=webhook_url,
        mentioned_list=["@ops-team"]
    )

    # 2. 假设我们有一个监控报告
    # 这里使用模拟数据，实际使用时应该从监控模块获取
    from analyzer.models.report import MonitorReport
    from analyzer.models.stats import Stats

    # 创建监控报告
    report = MonitorReport(
        title="接口监控报告",
        timestamp=datetime.now(),
        total_count=100,
        success_count=95,
        failure_count=5,
        success_rate=95.0,
        errors=[],
        stats=Stats()
    )

    # 3. 添加错误信息（模拟）
    from analyzer.models.report import ErrorInfo

    error = ErrorInfo(
        interface_name="getUserProfile",
        interface_method="GET",
        interface_url="/api/v1/users/profile",
        service="user",
        error_type="HTTP_500",
        error_message="Database connection timeout",
        status_code=500,
        request_data={"user_id": "123"},
        response_data={"error": "Connection timeout"},
        count=1,
        timestamp=datetime.now()
    )
    report.errors.append(error)

    # 4. 发送报告
    print("发送监控报告...")
    alert_info = {
        'recipients': ['user-team@company.com', 'dev-team@company.com'],
        'priority': 'HIGH',
        'summary': '5个接口异常'
    }

    result = notifier.send_report(
        report=report,
        alert_info=alert_info
    )

    if result.success:
        print(f"✓ 报告发送成功: message_id={result.message_id}")
    else:
        print(f"✗ 报告发送失败: {result.error_message}")

    # 5. 清理资源
    notifier.close()
    print()


def example_with_config():
    """从配置文件创建推送器示例"""

    print("=" * 80)
    print("从配置文件创建推送器示例")
    print("=" * 80)
    print()

    # 1. 配置字典
    config = {
        'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key',
        'mentioned_list': ['@admin'],
        'mentioned_mobile_list': ['13900139000'],
        'timeout': 15,
        'max_retries': 3,
        'max_message_length': 4000
    }

    # 2. 从配置创建推送器
    notifier = create_notifier_from_config(config)

    print(f"✓ 推送器创建成功")
    print(f"  - Webhook URL: {notifier.webhook_url}")
    print(f"  - 默认@人员: {notifier.default_mentioned_list}")
    print(f"  - 超时时间: {notifier.webhook_client.timeout}秒")
    print(f"  - 最大重试: {notifier.webhook_client.max_retries}次")
    print()

    # 3. 发送测试消息
    message = "这是一条测试消息，验证配置是否正确。"
    result = notifier.send_message(message)

    if result.success:
        print(f"✓ 消息发送成功")
    else:
        print(f"✗ 消息发送失败: {result.error_message}")

    # 4. 清理资源
    notifier.close()
    print()


def example_context_manager():
    """使用上下文管理器示例"""

    print("=" * 80)
    print("使用上下文管理器示例")
    print("=" * 80)
    print()

    # 使用with语句自动管理资源
    with WechatNotifier(
        webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key",
        mentioned_list=["@test"]
    ) as notifier:
        # 在with块内使用推送器
        message = "这是一条使用上下文管理器的测试消息。"
        result = notifier.send_message(message)

        if result.success:
            print(f"✓ 消息发送成功，自动管理资源")
        else:
            print(f"✗ 消息发送失败")

    # with块结束后自动调用close()
    print("✓ 资源已自动释放")
    print()


def example_error_handling():
    """错误处理示例"""

    print("=" * 80)
    print("错误处理示例")
    print("=" * 80)
    print()

    # 创建推送器
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=invalid-key"
    notifier = WechatNotifier(
        webhook_url=webhook_url,
        timeout=5,  # 短超时
        max_retries=2  # 少重试次数
    )

    # 发送消息（会失败）
    message = "这条消息会因为无效的webhook key而发送失败。"
    result = notifier.send_message(message)

    if result.success:
        print(f"✓ 消息发送成功")
    else:
        print(f"✗ 消息发送失败")
        print(f"  - 错误信息: {result.error_message}")
        print(f"  - 重试次数: {result.retry_count}")
        print(f"  - 时间: {result.timestamp}")

    # 清理资源
    notifier.close()
    print()


def example_connection_test():
    """连接测试示例"""

    print("=" * 80)
    print("连接测试示例")
    print("=" * 80)
    print()

    # 创建推送器
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key"
    notifier = WechatNotifier(webhook_url=webhook_url)

    # 测试连接
    print("测试企业微信机器人连接...")
    is_connected = notifier.test_connection()

    if is_connected:
        print("✓ 连接成功，配置正确")
    else:
        print("✗ 连接失败，请检查:")
        print("  - Webhook URL是否正确")
        print("  - 网络是否连通")
        print("  - 企业微信机器人是否被禁用")

    # 清理资源
    notifier.close()
    print()


def example_advanced_usage():
    """高级使用示例"""

    print("=" * 80)
    print("高级使用示例")
    print("=" * 80)
    print()

    # 创建推送器
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key"
    notifier = WechatNotifier(webhook_url=webhook_url)

    # 1. 发送带多个@人员的消息
    print("1. 发送带多个@人员的消息")
    message = "这是一条紧急告警，需要所有人关注！"
    result = notifier.send_message(
        content=message,
        mentioned_list=["@user1", "@user2"],
        mentioned_mobile_list=["13800138000", "13900139000"]
    )
    print(f"  结果: {'✓ 成功' if result.success else '✗ 失败'}")
    print()

    # 2. 发送长消息（会自动截断或分页）
    print("2. 发送长消息")
    long_message = "\n".join([f"第{i}行: 这是一条很长的消息内容" for i in range(100)])
    result = notifier.send_message(long_message)
    print(f"  结果: {'✓ 成功' if result.success else '✗ 失败'}")
    print()

    # 3. 使用WebhookClient直接发送（绕过格式化器）
    print("3. 直接使用WebhookClient")
    from notifier.models.wechat_message import WechatMessage

    custom_message = WechatMessage(
        markdown={"content": "自定义格式的消息"},
        mentioned_list=["@custom"]
    )
    result = notifier.webhook_client.send_message(custom_message)
    print(f"  结果: {'✓ 成功' if result.success else '✗ 失败'}")
    print()

    # 清理资源
    notifier.close()
    print()


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("企业微信推送模块使用示例")
    print("=" * 80)
    print()
    print("注意：以下示例需要有效的企业微信Webhook URL才能发送成功")
    print("请将示例中的webhook_url替换为你的实际Webhook地址")
    print()

    # 运行示例
    try:
        example_basic_usage()
        print()

        example_with_monitor_report()
        print()

        example_with_config()
        print()

        example_context_manager()
        print()

        example_error_handling()
        print()

        example_connection_test()
        print()

        example_advanced_usage()

    except Exception as e:
        print(f"\n✗ 运行示例时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
