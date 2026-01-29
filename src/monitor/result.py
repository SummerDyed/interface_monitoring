"""
监控结果数据模型
定义监控执行的结果结构和相关信息

作者: 开发团队
创建时间: 2026-01-27
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class MonitorResult:
    """监控结果数据模型

    存储接口监控的详细结果，包括状态、响应时间、错误信息等
    """

    interface: Any = None
    """接口信息（Interface对象）"""

    status: str = ""
    """监控状态：SUCCESS/FAILED"""

    status_code: Optional[int] = None
    """HTTP状态码"""

    response_time: float = 0.0
    """响应时间（毫秒）"""

    error_type: Optional[str] = None
    """错误类型：HTTP_500/HTTP_404/HTTP_503/TIMEOUT/NETWORK_ERROR等"""

    error_message: Optional[str] = None
    """错误信息"""

    request_data: Dict[str, Any] = field(default_factory=dict)
    """请求数据"""

    response_data: Dict[str, Any] = field(default_factory=dict)
    """响应数据"""

    timestamp: datetime = field(default_factory=datetime.now)
    """监控时间"""

    retry_count: int = 0
    """重试次数"""

    def __post_init__(self):
        """初始化后处理"""
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp) if isinstance(self.timestamp, str) else datetime.now()

    def is_success(self) -> bool:
        """判断监控是否成功

        Returns:
            bool: True if status is SUCCESS, False otherwise
        """
        return self.status.upper() == 'SUCCESS'

    def is_failed(self) -> bool:
        """判断监控是否失败

        Returns:
            bool: True if status is FAILED, False otherwise
        """
        return self.status.upper() == 'FAILED'

    def get_error_summary(self) -> str:
        """获取错误摘要

        Returns:
            str: 错误摘要信息
        """
        if self.is_success():
            return "OK"

        parts = []
        if self.error_type:
            parts.append(f"[{self.error_type}]")
        if self.error_message:
            parts.append(self.error_message)
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")

        return " ".join(parts) if parts else "Unknown error"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            dict: 监控结果的字典表示
        """
        return {
            'interface_name': self.interface.name if self.interface else '',
            'interface_method': self.interface.method if self.interface else '',
            'interface_url': self.interface.url if self.interface else '',
            'status': self.status,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'error_summary': self.get_error_summary(),
            'request_data': self.request_data,
            'response_data': self.response_data,
            'timestamp': self.timestamp.isoformat(),
            'retry_count': self.retry_count,
        }

    def to_json(self) -> str:
        """转换为JSON字符串

        Returns:
            str: JSON格式的监控结果
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def __str__(self) -> str:
        """字符串表示

        Returns:
            str: 监控结果的字符串表示
        """
        interface_name = self.interface.name if self.interface else 'Unknown'
        status = self.status
        response_time = f"{self.response_time:.2f}ms"

        if self.is_success():
            return f"✅ {interface_name}: {status} ({response_time})"
        else:
            error_summary = self.get_error_summary()
            return f"❌ {interface_name}: {status} - {error_summary}"

    def __repr__(self) -> str:
        """详细字符串表示

        Returns:
            str: 监控结果的详细字符串表示
        """
        return (
            f"MonitorResult(interface='{self.interface.name if self.interface else 'None'}', "
            f"status='{self.status}', "
            f"status_code={self.status_code}, "
            f"response_time={self.response_time:.2f}ms, "
            f"error_type='{self.error_type}', "
            f"timestamp={self.timestamp.isoformat()})"
        )


# 异常类型常量
class ErrorType:
    """异常类型枚举"""

    HTTP_500 = 'HTTP_500'
    """服务器内部错误"""

    HTTP_404 = 'HTTP_404'
    """接口不存在"""

    HTTP_401 = 'HTTP_401'
    """认证失败"""

    HTTP_403 = 'HTTP_403'
    """禁止访问"""

    HTTP_503 = 'HTTP_503'
    """服务不可用"""

    TIMEOUT = 'TIMEOUT'
    """请求超时"""

    NETWORK_ERROR = 'NETWORK_ERROR'
    """网络错误"""

    CONNECTION_ERROR = 'CONNECTION_ERROR'
    """连接错误"""

    DNS_ERROR = 'DNS_ERROR'
    """DNS解析错误"""

    VALIDATION_ERROR = 'VALIDATION_ERROR'
    """验证错误"""

    UNKNOWN_ERROR = 'UNKNOWN_ERROR'
    """未知错误"""


# 异常类型映射
ERROR_TYPES = {
    ErrorType.HTTP_500: '服务器内部错误',
    ErrorType.HTTP_404: '接口不存在',
    ErrorType.HTTP_503: '服务不可用',
    ErrorType.TIMEOUT: '请求超时',
    ErrorType.NETWORK_ERROR: '网络错误',
    ErrorType.CONNECTION_ERROR: '连接错误',
    ErrorType.DNS_ERROR: 'DNS解析错误',
    ErrorType.VALIDATION_ERROR: '验证错误',
    ErrorType.UNKNOWN_ERROR: '未知错误',
}

# 可重试的错误类型
RETRYABLE_ERRORS = {
    ErrorType.TIMEOUT,
    ErrorType.NETWORK_ERROR,
    ErrorType.CONNECTION_ERROR,
    ErrorType.DNS_ERROR,
}

# 不可重试的错误类型
NON_RETRYABLE_ERRORS = {
    ErrorType.HTTP_500,
    ErrorType.HTTP_404,
    ErrorType.HTTP_503,
    ErrorType.VALIDATION_ERROR,
}
