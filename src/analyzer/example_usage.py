"""
告警逻辑使用示例
展示如何在实际场景中使用告警判断功能

作者: 开发团队
创建时间: 2026-01-27
"""

from . import ResultAnalyzer, ReportGenerator, process_alert
from monitor.result import MonitorResult, ErrorType


def example_usage():
    """使用示例"""

    # 创建模拟接口
    class MockInterface:
        def __init__(self, name, method, url, service):
            self.name = name
            self.method = method
            self.url = url
            self.service = service

    # 创建监控结果
    results = [
        # 成功的接口
        MonitorResult(
            interface=MockInterface('getUser', 'GET', '/api/user', 'user'),
            status='SUCCESS',
            status_code=200,
            response_time=100.0
        ),
        MonitorResult(
            interface=MockInterface('login', 'POST', '/api/login', 'auth'),
            status='SUCCESS',
            status_code=200,
            response_time=200.0
        ),

        # 404错误（需要告警）
        MonitorResult(
            interface=MockInterface('getMissingData', 'GET', '/api/missing', 'user'),
            status='FAILED',
            status_code=404,
            error_type=ErrorType.HTTP_404,
            error_message='Resource not found'
        ),

        # 500错误（需要告警）
        MonitorResult(
            interface=MockInterface('createOrder', 'POST', '/api/order', 'order'),
            status='FAILED',
            status_code=500,
            error_type=ErrorType.HTTP_500,
            error_message='Database connection failed'
        ),

        # 503错误（不需要告警）
        MonitorResult(
            interface=MockInterface('getStats', 'GET', '/api/stats', 'admin'),
            status='FAILED',
            status_code=503,
            error_type=ErrorType.HTTP_503,
            error_message='Service temporarily unavailable'
        ),

        # 超时错误（不需要告警）
        MonitorResult(
            interface=MockInterface('getReport', 'GET', '/api/report', 'admin'),
            status='FAILED',
            status_code=None,
            error_type=ErrorType.TIMEOUT,
            error_message='Request timeout'
        ),
    ]

    # 执行分析
    analyzer = ResultAnalyzer()
    report = analyzer.analyze(results, title="每日接口监控报告")

    # 生成报告内容
    generator = ReportGenerator()
    markdown_content = generator.generate(report)

    # 处理告警
    alert_info = process_alert(report)

    # 打印结果
    print("=" * 60)
    print("监控分析报告")
    print("=" * 60)
    print(f"总接口数: {report.total_count}")
    print(f"成功数: {report.success_count}")
    print(f"失败数: {report.failure_count}")
    print(f"成功率: {report.success_rate:.2f}%")
    print()

    print("=" * 60)
    print("告警信息")
    print("=" * 60)

    if alert_info['should_alert']:
        print(f"WARNING: 需要发送告警")
        print(f"优先级: {alert_info['priority']}")
        print(f"告警摘要: {alert_info['summary']}")
        print(f"接收人: {', '.join(alert_info['recipients'])}")
        print()

        print("=== 简化告警内容 ===")
        print(alert_info['content'])
        print()

        print("=== 详细告警内容（前1000字符） ===")
        print(alert_info['detailed_content'][:1000])
        print("...(已截断)")
        print()

        # 这里可以调用推送模块
        # send_to_wechat(alert_info, markdown_content)

    else:
        print("SUCCESS: 无需发送告警")
        print(f"原因: {alert_info.get('reason', '未知')}")

    print()
    print("=" * 60)
    print("Markdown报告预览（前500字符）")
    print("=" * 60)
    print(markdown_content[:500] + "...")


def example_business_code_alert():
    """业务码告警示例"""

    class MockInterface:
        def __init__(self, name, method, url, service):
            self.name = name
            self.method = method
            self.url = url
            self.service = service

    # 创建带有业务码的响应
    results = [
        MonitorResult(
            interface=MockInterface('checkUser', 'GET', '/api/user/check', 'user'),
            status='FAILED',
            status_code=200,  # HTTP状态码是200
            error_type='BUSINESS_ERROR',
            error_message='User not found',
            response_data={
                'code': 404,  # 业务码是404
                'message': 'User not found',
                'success': False
            }
        ),
        MonitorResult(
            interface=MockInterface('processPayment', 'POST', '/api/payment', 'payment'),
            status='FAILED',
            status_code=200,  # HTTP状态码是200
            error_type='BUSINESS_ERROR',
            error_message='Payment failed',
            response_data={
                'error_code': 500,  # 业务码是500
                'message': 'Insufficient balance',
                'success': False
            }
        )
    ]

    analyzer = ResultAnalyzer()
    report = analyzer.analyze(results, title="业务码监控报告")

    alert_info = process_alert(report)

    print("=" * 60)
    print("业务码告警测试")
    print("=" * 60)
    print(f"需要告警: {alert_info['should_alert']}")
    print(f"告警摘要: {alert_info['summary']}")

    if alert_info['should_alert']:
        print("\n=== 业务码告警详情 ===")
        for error in alert_info['alert_errors']:
            business_code = error.response_data.get('code') or error.response_data.get('error_code')
            print(f"  - {error.interface_name}: 业务码 {business_code}")
            print(f"    HTTP状态码: {error.status_code}")
            print(f"    文件路径: interfaces/{error.service}/{error.interface_url.strip('/')}.json")
        print()
        print("=== 详细告警内容 ===")
        print(alert_info['detailed_content'])


if __name__ == '__main__':
    print("示例1: HTTP状态码告警")
    example_usage()

    print("\n" + "=" * 80 + "\n")

    print("示例2: 业务码告警")
    example_business_code_alert()
