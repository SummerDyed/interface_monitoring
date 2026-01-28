"""
企业微信消息模型
定义推送消息的数据结构和结果模型

作者: 开发团队
创建时间: 2026-01-27
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


@dataclass
class WechatMessage:
    """企业微信消息模型

    Attributes:
        msgtype: 消息类型，默认markdown
        markdown: Markdown格式的消息内容
        mentioned_list: @人员列表（用户ID）
        mentioned_mobile_list: @人员列表（手机号）
    """
    msgtype: str = "markdown"
    markdown: Dict[str, Any] = field(default_factory=dict)
    mentioned_list: List[str] = field(default_factory=list)
    mentioned_mobile_list: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            Dict[str, Any]: 消息字典
        """
        result = {
            "msgtype": self.msgtype,
            self.msgtype: self.markdown
        }

        if self.mentioned_list:
            result["mentioned_list"] = self.mentioned_list

        if self.mentioned_mobile_list:
            result["mentioned_mobile_list"] = self.mentioned_mobile_list

        return result

    def to_json(self) -> str:
        """转换为JSON字符串

        Returns:
            str: JSON字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(',', ':'))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WechatMessage':
        """从字典创建消息对象

        Args:
            data: 消息字典数据

        Returns:
            WechatMessage: 消息对象
        """
        return cls(
            msgtype=data.get("msgtype", "markdown"),
            markdown=data.get("markdown", {}),
            mentioned_list=data.get("mentioned_list", []),
            mentioned_mobile_list=data.get("mentioned_mobile_list", [])
        )

    def add_mention(self, user_id: Optional[str] = None, mobile: Optional[str] = None):
        """添加@人员

        Args:
            user_id: 用户ID
            mobile: 手机号
        """
        if user_id:
            self.mentioned_list.append(user_id)

        if mobile:
            self.mentioned_mobile_list.append(mobile)

    def add_mentions(self, user_ids: Optional[List[str]] = None,
                     mobiles: Optional[List[str]] = None):
        """批量添加@人员

        Args:
            user_ids: 用户ID列表
            mobiles: 手机号列表
        """
        if user_ids:
            self.mentioned_list.extend(user_ids)

        if mobiles:
            self.mentioned_mobile_list.extend(mobiles)


@dataclass
class PushResult:
    """推送结果模型

    Attributes:
        success: 推送是否成功
        message_id: 消息ID（成功后返回）
        error_message: 错误信息（失败时）
        retry_count: 重试次数
        timestamp: 推送时间
        response_data: 响应数据
    """
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    response_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            Dict[str, Any]: 结果字典
        """
        return {
            "success": self.success,
            "message_id": self.message_id,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat(),
            "response_data": self.response_data
        }

    @classmethod
    def success_result(cls, message_id: str, response_data: Optional[Dict[str, Any]] = None,
                     retry_count: int = 0) -> 'PushResult':
        """创建成功结果

        Args:
            message_id: 消息ID
            response_data: 响应数据
            retry_count: 重试次数

        Returns:
            PushResult: 成功结果
        """
        return cls(
            success=True,
            message_id=message_id,
            response_data=response_data,
            retry_count=retry_count
        )

    @classmethod
    def failure_result(cls, error_message: str, retry_count: int = 0,
                      response_data: Optional[Dict[str, Any]] = None) -> 'PushResult':
        """创建失败结果

        Args:
            error_message: 错误信息
            retry_count: 重试次数
            response_data: 响应数据

        Returns:
            PushResult: 失败结果
        """
        return cls(
            success=False,
            error_message=error_message,
            retry_count=retry_count,
            response_data=response_data
        )
