"""
接口数据模型
定义接口信息的标准数据结构
作者: 开发团队
创建时间: 2026-01-27
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Interface:
    """接口信息数据模型"""
    name: str = ""                    # 接口名称
    method: str = ""                   # HTTP方法 (GET, POST, PUT, DELETE等)
    url: str = ""                     # 接口URL
    path: str = ""                    # 接口路径
    service: str = ""                 # 服务类型 (user, nurse, admin)
    module: str = ""                   # 模块名称
    headers: Dict[str, Any] = field(default_factory=dict)    # 请求头
    params: Dict[str, Any] = field(default_factory=dict)     # 请求参数
    body: Dict[str, Any] = field(default_factory=dict)       # 请求体
    response: Dict[str, Any] = field(default_factory=dict)    # 响应示例
    file_path: str = ""                # 文档文件路径
    last_modified: float = 0.0        # 文件修改时间戳
    created_at: Optional[datetime] = None  # 创建时间
    updated_at: Optional[datetime] = None  # 更新时间

    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def key(self) -> str:
        """获取接口唯一标识键"""
        return f"{self.method.upper()} {self.url}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'method': self.method,
            'url': self.url,
            'path': self.path,
            'service': self.service,
            'module': self.module,
            'headers': self.headers,
            'params': self.params,
            'body': self.body,
            'response': self.response,
            'file_path': self.file_path,
            'last_modified': self.last_modified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Interface':
        """从字典创建实例"""
        interface = cls(
            name=data.get('name', ''),
            method=data.get('method', ''),
            url=data.get('url', ''),
            path=data.get('path', ''),
            service=data.get('service', ''),
            module=data.get('module', ''),
            headers=data.get('headers', {}),
            params=data.get('params', {}),
            body=data.get('body', {}),
            response=data.get('response', {}),
            file_path=data.get('file_path', ''),
            last_modified=data.get('last_modified', 0.0)
        )

        if data.get('created_at'):
            interface.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            interface.updated_at = datetime.fromisoformat(data['updated_at'])

        return interface

    def __str__(self) -> str:
        return f"{self.service}.{self.module}.{self.name} ({self.method} {self.url})"

    def __repr__(self) -> str:
        return (f"Interface(name='{self.name}', method='{self.method}', "
                f"url='{self.url}', service='{self.service}', "
                f"module='{self.module}')")
