"""
详细告警使用示例
展示如何在实际场景中使用详细告警功能

作者: 开发团队
创建时间: 2026-01-27
"""

from src.analyzer import ResultAnalyzer, process_alert, ReportGenerator
from src.monitor.monitor_engine import MonitorEngine


def example_with_real_monitor():
    """使用真实监控引擎的示例"""

    print("=" * 80)
    print("详细告警功能使用示例")
    print("=" * 80)
    print()

    # 1. 假设我们有一个接口列表
    interfaces = [
        # 这里应该是从接口扫描模块获取的接口列表
        # 为了演示，我们使用模拟数据
        {
            'name': 'getUserProfile',
            'method': 'GET',
            'url': '/api/v1/users/{id}/profile',
            'service': 'user',
            'file_path': 'interfaces/user/user_profile.json'
        },
        {
            'name': 'createOrder',
            'method': 'POST',
            'url': '/api/v1/orders',
            'service': 'order',
            'file_path': 'interfaces/order/create_order.json'
        },
        {
            'name': 'getPaymentStatus',
            'method': 'GET',
            'url': '/api/v1/payments/{order_id}/status',
            'service': 'payment',
            'file_path': 'interfaces/payment/payment_status.json'
        }
    ]

    # 2. 执行监控（这里只是模拟）
    print("步骤1: 执行接口监控...")
    # engine = MonitorEngine()
    # results = engine.execute(interfaces, token_map)

    # 3. 分析结果
    print("步骤2: 分析监控结果...")

    # 为了演示，我们直接创建模拟结果
    from src.monitor.result import MonitorResult, ErrorType
    from datetime import datetime

    class MockInterface:
        def __init__(self, name, method, url, service, file_path):
            self.name = name
            self.method = method
            self.url = url
            self.service = service
            self.file_path = file_path

    # 创建模拟监控结果
    results = [
        # 成功的接口
        MonitorResult(
            interface=MockInterface(
                'getUserProfile', 'GET', '/api/v1/users/123/profile',
                'user', 'interfaces/user/user_profile.json'
            ),
            status='SUCCESS',
            status_code=200,
            response_time=150.0,
            request_data={'user_id': '123'},
            response_data={'user_id': '123', 'name': 'John Doe', 'email': 'john@example.com'}
        ),

        # 404错误
        MonitorResult(
            interface=MockInterface(
                'getPaymentStatus', 'GET', '/api/v1/payments/456/status',
                'payment', 'interfaces/payment/payment_status.json'
            ),
            status='FAILED',
            status_code=404,
            error_type=ErrorType.HTTP_404,
            error_message='Payment not found',
            request_data={'order_id': '456'},
            response_data={
                'error_code': 404,
                'message': 'Payment not found',
                'success': False
            }
        ),

        # 500错误
        MonitorResult(
            interface=MockInterface(
                'createOrder', 'POST', '/api/v1/orders',
                'order', 'interfaces/order/create_order.json'
            ),
            status='FAILED',
            status_code=500,
            error_type=ErrorType.HTTP_500,
            error_message='Database connection timeout',
            request_data={
                'user_id': '789',
                'items': [{'product_id': 'P001', 'quantity': 1}]
            },
            response_data={
                'error_code': 500,
                'message': 'Database connection timeout',
                'success': False,
                'trace_id': 'trace-abc123'
            }
        ),

        # 非告警错误（不触发）
        MonitorResult(
            interface=MockInterface(
                'getUserProfile', 'GET', '/api/v1/users/999/profile',
                'user', 'interfaces/user/user_profile.json'
            ),
            status='FAILED',
            status_code=503,
            error_type=ErrorType.HTTP_503,
            error_message='Service temporarily unavailable',
            request_data={'user_id': '999'},
            response_data={
                'error_code': 503,
                'message': 'Service temporarily unavailable',
                'success': False
            }
        )
    ]

    # 执行分析
    analyzer = ResultAnalyzer()
    report = analyzer.analyze(results, title="2026-01-27 接口监控报告")

    # 4. 处理告警
    print("步骤3: 处理告警信息...")
    alert_info = process_alert(report)

    # 5. 显示结果
    print("\n" + "=" * 80)
    print("监控分析结果")
    print("=" * 80)
    print(f"总接口数: {report.total_count}")
    print(f"成功数: {report.success_count}")
    print(f"失败数: {report.failure_count}")
    print(f"成功率: {report.success_rate:.2f}%")
    print()

    if alert_info['should_alert']:
        print("=" * 80)
        print("告警信息")
        print("=" * 80)
        print(f"告警级别: {alert_info['priority']}")
        print(f"告警摘要: {alert_info['summary']}")
        print(f"告警接收人: {', '.join(alert_info['recipients'])}")
        print()

        print("=" * 80)
        print("详细告警内容")
        print("=" * 80)
        print(alert_info['detailed_content'])
        print()

        # 6. 推送告警（模拟）
        print("=" * 80)
        print("推送告警")
        print("=" * 80)

        # 生成Markdown报告
        generator = ReportGenerator()
        markdown_report = generator.generate(report)

        print("准备推送到以下接收人:")
        for recipient in alert_info['recipients']:
            print(f"  - {recipient}")

        print()
        print("推送内容:")
        print("  标题: 接口监控告警 - " + alert_info['priority'])
        print("  内容: " + alert_info['summary'])
        print("  详细报告: " + str(len(markdown_report)) + " 字符的Markdown报告")
        print()

        # 这里可以调用实际的推送逻辑
        # for recipient in alert_info['recipients']:
        #     wechat_pusher.send(
        #         to=recipient,
        #         title=f"接口监控告警 - {alert_info['priority']}",
        #         content=alert_info['content'],
        #         markdown=markdown_report
        #     )

    else:
        print("SUCCESS: 无需发送告警")

    print()
    print("=" * 80)
    print("完整Markdown报告")
    print("=" * 80)
    print(f"Markdown报告长度: {len(markdown_report)} 字符")
    print("报告内容已生成，可以推送给相关人员")


def example_business_code_with_details():
    """业务码告警详细示例"""

    print("\n" + "=" * 80)
    print("业务码告警详细示例")
    print("=" * 80)
    print()

    from src.monitor.result import MonitorResult
    from datetime import datetime

    class MockInterface:
        def __init__(self, name, method, url, service, file_path):
            self.name = name
            self.method = method
            self.url = url
            self.service = service
            self.file_path = file_path

    # 创建业务码告警结果
    results = [
        # HTTP 200但业务码404
        MonitorResult(
            interface=MockInterface(
                'checkUserOrder', 'GET', '/api/v1/users/123/orders/456',
                'user', 'interfaces/user/user_order_check.json'
            ),
            status='FAILED',
            status_code=200,  # HTTP状态码正常
            error_type='BUSINESS_ERROR',
            error_message='Order not found',
            request_data={'user_id': '123', 'order_id': '456'},
            response_data={
                'code': 404,  # 业务码404
                'message': 'Order not found',
                'success': False,
                'data': None
            }
        ),

        # HTTP 200但业务码500
        MonitorResult(
            interface=MockInterface(
                'processRefund', 'POST', '/api/v1/refunds',
                'payment', 'interfaces/payment/process_refund.json'
            ),
            status='FAILED',
            status_code=200,  # HTTP状态码正常
            error_type='BUSINESS_ERROR',
            error_message='Refund processing failed',
            request_data={
                'refund_id': 'R001',
                'order_id': 'O123',
                'amount': 99.99
            },
            response_data={
                'error_code': 500,  # 业务码500
                'message': 'Refund processing failed',
                'success': False,
                'trace_id': 'refund-trace-xyz789'
            }
        )
    ]

    analyzer = ResultAnalyzer()
    report = analyzer.analyze(results, title="业务码监控报告")
    alert_info = process_alert(report)

    print("业务码告警结果:")
    print(f"  需要告警: {alert_info['should_alert']}")
    print(f"  告警级别: {alert_info['priority']}")
    print(f"  告警摘要: {alert_info['summary']}")
    print()

    if alert_info['should_alert']:
        print("业务码告警详情:")
        for i, error in enumerate(alert_info['alert_errors'], 1):
            business_code = error.response_data.get('code') or error.response_data.get('error_code')
            print(f"\n  告警 #{i}:")
            print(f"    接口: {error.interface_name}")
            print(f"    HTTP状态码: {error.status_code} (正常)")
            print(f"    业务码: {business_code} (异常)")
            print(f"    文件: {error.interface.file_path if hasattr(error.interface, 'file_path') else 'N/A'}")
            print(f"    请求: {error.request_data}")
            print(f"    响应: {error.response_data}")

        print("\n完整告警内容:")
        print("-" * 80)
        print(alert_info['detailed_content'])


if __name__ == '__main__':
    # 运行示例
    example_with_real_monitor()
    example_business_code_with_details()
