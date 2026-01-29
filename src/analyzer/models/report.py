"""
监控报告数据模型
定义分析结果的报告结构和异常详情

作者: 开发团队
创建时间: 2026-01-27
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class ErrorInfo:
    """异常详情信息

    存储单个异常的详细信息，包括接口、错误类型、请求响应数据等
    """

    interface_name: str = ""
    """接口名称"""

    interface_method: str = ""
    """接口方法"""

    interface_url: str = ""
    """接口URL"""

    service: str = ""
    """服务名称"""

    error_type: str = ""
    """错误类型：HTTP_500/HTTP_404/HTTP_503/TIMEOUT/NETWORK_ERROR等"""

    error_message: str = ""
    """错误信息"""

    status_code: Optional[int] = None
    """HTTP状态码"""

    request_data: Dict[str, Any] = field(default_factory=dict)
    """请求数据"""

    response_data: Dict[str, Any] = field(default_factory=dict)
    """响应数据"""

    count: int = 1
    """出现次数"""

    timestamp: datetime = field(default_factory=datetime.now)
    """首次异常时间"""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            dict: 异常详情的字典表示
        """
        return {
            'interface_name': self.interface_name,
            'interface_method': self.interface_method,
            'interface_url': self.interface_url,
            'service': self.service,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'status_code': self.status_code,
            'request_data': self.request_data,
            'response_data': self.response_data,
            'count': self.count,
            'timestamp': self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """转换为JSON字符串

        Returns:
            str: JSON格式的异常详情
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def __str__(self) -> str:
        """字符串表示

        Returns:
            str: 异常详情的字符串表示
        """
        return f"{self.interface_name} [{self.error_type}]: {self.error_message} (出现{self.count}次)"


@dataclass
class MonitorReport:
    """监控报告主体

    存储完整的监控分析报告，包括统计信息、异常详情和Markdown内容
    """

    title: str = "接口监控报告"
    """报告标题"""

    timestamp: datetime = field(default_factory=datetime.now)
    """报告生成时间"""

    total_count: int = 0
    """总接口数"""

    success_count: int = 0
    """成功数"""

    failure_count: int = 0
    """失败数"""

    success_rate: float = 0.0
    """成功率（百分比）"""

    errors: List[ErrorInfo] = field(default_factory=list)
    """异常列表"""

    stats: Optional['Stats'] = None
    """统计信息"""

    timeout_interfaces: List[str] = field(default_factory=list)
    """超时接口列表（响应时间超过3秒）"""

    content: str = ""
    """Markdown格式的报告内容"""

    alert_info: Optional[Dict[str, Any]] = None
    """告警信息（是否需要告警、优先级、接收人等）"""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            dict: 报告的字典表示
        """
        return {
            'title': self.title,
            'timestamp': self.timestamp.isoformat(),
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_rate,
            'errors': [error.to_dict() for error in self.errors],
            'stats': self.stats.to_dict() if self.stats else None,
            'timeout_interfaces': self.timeout_interfaces,
            'content': self.content,
            'alert_info': self.alert_info,
        }

    def to_json(self) -> str:
        """转换为JSON字符串

        Returns:
            str: JSON格式的报告
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def __str__(self) -> str:
        """字符串表示

        Returns:
            str: 报告的字符串表示
        """
        return (
            f"{self.title}\n"
            f"时间: {self.timestamp.isoformat()}\n"
            f"总数: {self.total_count}, 成功: {self.success_count}, 失败: {self.failure_count}\n"
            f"成功率: {self.success_rate:.2f}%"
        )
