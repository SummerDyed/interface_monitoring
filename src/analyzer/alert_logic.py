"""
告警逻辑
定义告警推送规则和条件

作者: 开发团队
创建时间: 2026-01-27
"""

from typing import List, Dict, Any, Optional
import logging

from .models import MonitorReport, ErrorInfo

logger = logging.getLogger(__name__)


class AlertRule:
    """告警规则"""

    # 只关注404和500错误
    CRITICAL_ERROR_TYPES = {
        'HTTP_404',  # 页面不存在
        'HTTP_500',  # 服务器内部错误
    }

    # HTTP状态码阈值
    HTTP_404_CODE = 404
    HTTP_500_CODE = 500


def should_send_alert(report: MonitorReport) -> bool:
    """判断是否需要发送告警

    只推送404和500错误作为告警

    Args:
        report: 监控报告

    Returns:
        bool: 是否需要发送告警
    """

    # 检查是否有404或500错误
    for error in report.errors:
        # 检查HTTP错误类型
        if error.error_type in AlertRule.CRITICAL_ERROR_TYPES:
            logger.info(
                f"发现{error.error_type}错误，触发告警: {error.interface_name}"
            )
            return True

        # 检查HTTP状态码
        if error.status_code == AlertRule.HTTP_404_CODE:
            logger.info(
                f"发现404状态码，触发告警: {error.interface_name}"
            )
            return True

        if error.status_code == AlertRule.HTTP_500_CODE:
            logger.info(
                f"发现500状态码，触发告警: {error.interface_name}"
            )
            return True

        # 检查业务码（从响应数据中提取）
        if _check_business_error_code(error):
            logger.info(
                f"发现业务错误码404/500，触发告警: {error.interface_name}"
            )
            return True

    return False


def _check_business_error_code(error: ErrorInfo) -> bool:
    """检查业务错误码是否为404或500

    Args:
        error: 异常详情

    Returns:
        bool: 是否为业务404/500错误
    """
    # 检查响应数据中的业务码
    if error.response_data:
        # 常见的业务码字段名
        business_code_fields = [
            'error_code', 'code', 'status_code', 'errorCode',
            'business_code', 'result_code', 'ret_code'
        ]

        for field in business_code_fields:
            if field in error.response_data:
                value = error.response_data[field]
                # 转换为字符串比较，支持数字和字符串
                if str(value) in ['404', '500', 404, 500]:
                    return True

    return False


def get_alert_priority(report: MonitorReport) -> str:
    """获取告警优先级

    Args:
        report: 监控报告

    Returns:
        str: 告警优先级
    """
    if not report.errors:
        return 'LOW'

    # 检查是否有500错误（最高优先级）
    has_500 = any(
        e.error_type == 'HTTP_500' or
        e.status_code == 500 or
        _extract_business_code(e) == '500'
        for e in report.errors
    )

    if has_500:
        return 'CRITICAL'  # 500错误，最高优先级

    # 检查是否有404错误
    has_404 = any(
        e.error_type == 'HTTP_404' or
        e.status_code == 404 or
        _extract_business_code(e) == '404'
        for e in report.errors
    )

    if has_404:
        return 'HIGH'  # 404错误，高优先级

    return 'LOW'


def _extract_business_code(error: ErrorInfo) -> Optional[str]:
    """提取业务错误码

    Args:
        error: 异常详情

    Returns:
        Optional[str]: 业务错误码
    """
    if not error.response_data:
        return None

    business_code_fields = [
        'error_code', 'code', 'status_code', 'errorCode',
        'business_code', 'result_code', 'ret_code'
    ]

    for field in business_code_fields:
        if field in error.response_data:
            return str(error.response_data[field])

    return None


def get_alert_recipients(report: MonitorReport) -> List[str]:
    """获取告警接收人列表

    Args:
        report: 监控报告

    Returns:
        List[str]: 告警接收人列表
    """
    recipients = set()  # 使用set去重

    # 收集所有涉及的服务
    error_services = set()
    for error in report.errors:
        if error.service:
            error_services.add(error.service)

    # 根据服务类型确定接收人
    service_recipients = {
        'user': 'user-team@company.com',
        'admin': 'admin-team@company.com',
        'nurse': 'nurse-team@company.com',
        'order': 'order-team@company.com',
        'payment': 'payment-team@company.com',
    }

    for service in error_services:
        if service in service_recipients:
            recipients.add(service_recipients[service])

    # 如果有500错误，额外通知运维和开发团队
    has_500_error = any(
        e.error_type == 'HTTP_500' or
        e.status_code == 500
        for e in report.errors
    )

    if has_500_error:
        recipients.add('dev-team@company.com')  # 开发团队
        recipients.add('ops-team@company.com')  # 运维团队

    return list(recipients)


def get_alert_summary(report: MonitorReport) -> str:
    """获取告警摘要

    Args:
        report: 监控报告

    Returns:
        str: 告警摘要
    """
    if not report.errors:
        return "无告警"

    # 统计404和500错误数量
    error_404_count = sum(
        1 for e in report.errors
        if e.error_type == 'HTTP_404' or e.status_code == 404
    )

    error_500_count = sum(
        1 for e in report.errors
        if e.error_type == 'HTTP_500' or e.status_code == 500
    )

    summary_parts = []

    if error_500_count > 0:
        summary_parts.append(f"{error_500_count}个500错误")

    if error_404_count > 0:
        summary_parts.append(f"{error_404_count}个404错误")

    return "，".join(summary_parts) if summary_parts else "未知错误"


def get_detailed_alert_content(alert_errors: List[ErrorInfo]) -> str:
    """获取详细的告警内容

    包含异常状态、接口信息、请求响应详情、文件路径等

    Args:
        alert_errors: 需要告警的错误列表

    Returns:
        str: 详细的告警内容
    """
    if not alert_errors:
        return "无告警错误"

    content_parts = []

    for i, error in enumerate(alert_errors, 1):
        # 构建单个错误的详细内容
        error_detail = f"""
=== 告警 #{i} ===

异常状态: {error.error_type} (HTTP {error.status_code or 'N/A'})
接口名称: {error.interface_name}
接口方法: {error.interface_method}
接口路径: {error.interface_url}
服务名称: {error.service}
错误信息: {error.error_message}
发生次数: {error.count}次
发生时间: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S') if error.timestamp else 'N/A'}

--- 请求详情 ---
"""

        # 添加请求数据
        if error.request_data:
            error_detail += f"请求参数:\n{_format_dict_data(error.request_data)}\n"
        else:
            error_detail += "请求参数: 无\n"

        # 添加响应数据
        if error.response_data:
            error_detail += f"""
--- 响应详情 ---
响应内容:
{_format_dict_data(error.response_data)}
"""
        else:
            error_detail += "--- 响应详情 ---\n响应内容: 无\n"

        # 添加文件路径信息（接口定义文件）
        file_path = _get_interface_file_path(error)
        if file_path:
            error_detail += f"""
--- 接口定义文件 ---
{file_path}
"""

        content_parts.append(error_detail)

    return "\n".join(content_parts)


def _format_dict_data(data: Dict[str, Any]) -> str:
    """格式化字典数据为可读字符串

    Args:
        data: 要格式化的数据

    Returns:
        str: 格式化后的字符串
    """
    if not data:
        return "无"

    # 如果是简单的键值对，直接显示
    if isinstance(data, dict):
        formatted_parts = []
        for key, value in data.items():
            # 限制每个值的显示长度
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "...(已截断)"
            formatted_parts.append(f"  {key}: {value}")
        return "\n".join(formatted_parts)
    else:
        return str(data)


def _get_interface_file_path(error: ErrorInfo) -> str:
    """获取接口定义文件路径

    根据接口信息推断可能的文件路径

    Args:
        error: 错误信息

    Returns:
        str: 接口定义文件路径
    """
    # 根据服务名称和接口路径推断文件路径
    service = error.service.lower()
    url_path = error.interface_url.strip('/')

    # 常见的接口文件路径模式
    possible_paths = [
        f"interfaces/{service}/{url_path}.json",
        f"docs/{service}/apis/{url_path}.yaml",
        f"api_specs/{service}/{url_path}.json",
        f"configs/{service}/interfaces/{url_path}.json",
    ]

    # 返回第一个可能的路径
    return possible_paths[0] if possible_paths else f"interfaces/{service}/"


def get_alert_content(alert_errors: List[ErrorInfo]) -> str:
    """获取告警内容（简化版）

    用于企业微信等平台推送的简洁告警内容

    Args:
        alert_errors: 需要告警的错误列表

    Returns:
        str: 告警内容
    """
    if not alert_errors:
        return "无告警错误"

    content = f"发现 {len(alert_errors)} 个告警错误:\n\n"

    for i, error in enumerate(alert_errors, 1):
        file_path = _get_interface_file_path(error)
        content += f"""告警 #{i}:
- 接口: {error.interface_name} ({error.interface_method} {error.interface_url})
- 异常: {error.error_type} (HTTP {error.status_code or 'N/A'})
- 错误: {error.error_message}
- 服务: {error.service}
- 文件: {file_path}
- 时间: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S') if error.timestamp else 'N/A'}

"""

    return content


def filter_alert_errors(report: MonitorReport) -> List[ErrorInfo]:
    """过滤出需要告警的错误（仅404和500）

    Args:
        report: 监控报告

    Returns:
        List[ErrorInfo]: 需要告警的错误列表
    """
    alert_errors = []

    for error in report.errors:
        # 检查HTTP错误类型
        if error.error_type in AlertRule.CRITICAL_ERROR_TYPES:
            alert_errors.append(error)
            continue

        # 检查HTTP状态码
        if error.status_code in [404, 500]:
            alert_errors.append(error)
            continue

        # 检查业务码
        if _check_business_error_code(error):
            alert_errors.append(error)
            continue

    return alert_errors


# 使用示例
def process_alert(report: MonitorReport) -> Dict[str, Any]:
    """处理告警推送

    Args:
        report: 监控报告

    Returns:
        Dict[str, Any]: 告警信息
    """
    # 判断是否需要告警
    if not should_send_alert(report):
        logger.info("无需发送告警")
        return {
            'should_alert': False,
            'reason': '无404/500错误'
        }

    # 获取告警信息
    priority = get_alert_priority(report)
    recipients = get_alert_recipients(report)
    summary = get_alert_summary(report)
    alert_errors = filter_alert_errors(report)

    # 获取详细告警内容
    detailed_content = get_detailed_alert_content(alert_errors)
    simple_content = get_alert_content(alert_errors)

    # 构建告警信息
    alert_info = {
        'should_alert': True,
        'priority': priority,
        'recipients': recipients,
        'summary': summary,
        'error_count': len(alert_errors),
        'total_errors': len(report.errors),
        'alert_errors': alert_errors,  # 仅包含404/500错误
        'detailed_content': detailed_content,  # 详细告警内容
        'content': simple_content,  # 简化告警内容
        'report': report,
    }

    logger.info(
        f"准备发送告警: 优先级={priority}, "
        f"接收人={len(recipients)}个, "
        f"告警错误={len(alert_errors)}个"
    )

    return alert_info
