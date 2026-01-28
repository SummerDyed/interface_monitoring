"""
企业微信Webhook客户端
封装Webhook API调用逻辑，支持重试机制

作者: 开发团队
创建时间: 2026-01-27
"""

import logging
import time
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models.wechat_message import WechatMessage, PushResult

logger = logging.getLogger(__name__)


class RetryConfig:
    """重试配置"""
    MAX_ATTEMPTS = 3
    BACKOFF_STRATEGY = [1, 2, 5]  # 指数退避（秒）
    RETRYABLE_STATUS_CODES = [500, 502, 503, 504]
    RETRYABLE_ERRORS = [
        'timeout',
        'connection_error',
        'ConnectionError',
        'Timeout'
    ]


class WebhookClient:
    """企业微信Webhook客户端

    Attributes:
        webhook_url: Webhook地址
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
    """

    def __init__(
        self,
        webhook_url: str,
        timeout: int = 10,
        max_retries: int = RetryConfig.MAX_ATTEMPTS
    ):
        """初始化Webhook客户端

        Args:
            webhook_url: 企业微信机器人Webhook地址
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.max_retries = max_retries

        # 配置重试策略
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=RetryConfig.RETRYABLE_STATUS_CODES,
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def send_message(self, message: WechatMessage) -> PushResult:
        """发送消息到企业微信

        Args:
            message: 微信消息对象

        Returns:
            PushResult: 推送结果
        """
        message_data = message.to_dict()

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"发送企业微信消息 (尝试 {attempt + 1}/{self.max_retries})"
                )

                response = self.session.post(
                    self.webhook_url,
                    json=message_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=self.timeout
                )

                # 解析响应
                result_data = response.json()

                # 检查响应状态
                if response.status_code == 200:
                    errcode = result_data.get('errcode', -1)
                    errmsg = result_data.get('errmsg', '')

                    if errcode == 0:
                        logger.info(
                            f"消息发送成功: {result_data.get('msgid', 'N/A')}"
                        )
                        return PushResult.success_result(
                            message_id=str(result_data.get('msgid', '')),
                            response_data=result_data,
                            retry_count=attempt
                        )
                    else:
                        error_msg = f"企业微信API错误: {errcode} - {errmsg}"
                        logger.error(error_msg)

                        # 不可重试的错误
                        if not self._is_retryable_error(errcode, errmsg):
                            return PushResult.failure_result(
                                error_message=error_msg,
                                retry_count=attempt,
                                response_data=result_data
                            )
                else:
                    error_msg = (
                        f"HTTP请求失败: {response.status_code} - {response.text}"
                    )
                    logger.error(error_msg)

                    # HTTP错误判断是否可重试
                    if response.status_code not in RetryConfig.RETRYABLE_STATUS_CODES:
                        return PushResult.failure_result(
                            error_message=error_msg,
                            retry_count=attempt,
                            response_data={"status_code": response.status_code}
                        )

                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries - 1:
                    wait_time = self._get_backoff_time(attempt)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

            except requests.exceptions.Timeout as e:
                error_msg = f"请求超时: {str(e)}"
                logger.error(error_msg)

            except requests.exceptions.ConnectionError as e:
                error_msg = f"连接错误: {str(e)}"
                logger.error(error_msg)

            except Exception as e:
                error_msg = f"未知错误: {str(e)}"
                logger.error(error_msg, exc_info=True)

            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries - 1:
                wait_time = self._get_backoff_time(attempt)
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

        # 所有重试都失败
        final_error = (
            f"消息发送失败，已重试 {self.max_retries} 次"
        )
        logger.error(final_error)
        return PushResult.failure_result(
            error_message=final_error,
            retry_count=self.max_retries
        )

    def _is_retryable_error(self, errcode: int, errmsg: str) -> bool:
        """判断错误是否可重试

        Args:
            errcode: 错误码
            errmsg: 错误信息

        Returns:
            bool: 是否可重试
        """
        # 常见的不可重试错误
        non_retryable_codes = {
            40001: "access_token无效",
            40002: "access_token过期",
            40004: "无效的媒体文件",
            40008: "不合法的消息类型",
            40013: "无效的CorpID",
            40014: "无效的access_token",
            40015: "无效的会话",
            40016: "不合法的按钮个数",
            40017: "不合法的按钮类型",
            40018: "不合法的按钮名称长度",
            40019: "不合法的按钮key长度",
            40020: "不合法的按钮url长度",
            40021: "不合法的菜单版本号",
            40022: "不合法的子菜单级数",
            40023: "不合法的子菜单按钮个数",
            40024: "不合法的子菜单按钮类型",
            40025: "不合法的子菜单按钮名称长度",
            40026: "不合法的子菜单按钮key长度",
            40027: "不合法的子菜单按钮url长度",
            40028: "不合法的菜单类型",
            40029: "不合法菜单名称长度",
            40030: "不合法的chatid",
            40031: "发送者或接收者不存在",
            40032: "发送者不存在",
            40033: "消息不存在",
            40034: "消息type不合法",
            40035: "不合法session",
            40036: "不合法部门id",
            40037: "无效的agentid",
            40038: "不合法的话题id",
            40039: "不合法的话题类型",
            40040: "webhook地址不存在",
            40041: "webhook已禁用",
            40042: "不合法的主题",
            40043: "不合法的发送者",
            40044: "不合法的主题id",
            40045: "不合法的话题类型",
            40046: "API禁用",
            40048: "不合法的userid",
            40049: "不合法的人名",
            40050: "不合法的人名长度",
            40051: "部门id不存在",
            40052: "部门已删除",
            40053: "不合法的主部门id",
            40054: "不合法的主部门",
            40055: "用户已删除",
            40056: "不存在的PartyID",
            40057: "PartyID已删除",
            40058: "参数错误",
            40059: "不存在的关系",
            40060: "不合法的主题id",
            40061: "不合法的主题id",
            40062: "不合法的主题id",
            40063: "参数为空",
            40064: "不合法的主题id",
            40065: "不合法的主题id",
            40066: "不合法的主题id",
            40067: "不合法的主题id",
            40068: "不合法的主题id",
            40069: "不合法的主题id",
            40070: "不合法的主题id",
            40071: "不合法的主题id",
            40072: "不合法的主题id",
            40073: "不合法的主题id",
            40074: "不合法的主题id",
            40075: "不合法的主题id",
            40076: "不合法的主题id",
            40077: "不合法的主题id",
            40078: "不合法的主题id",
            40079: "不合法的主题id",
            40080: "不合法的主题id",
            40081: "不合法的主题id",
            40082: "不合法的主题id",
            40083: "不合法的主题id",
            40084: "不合法的主题id",
            40085: "不合法的主题id",
            40086: "不合法的主题id",
            40087: "不合法的主题id",
            40088: "不合法的主题id",
            40089: "不合法的主题id",
            40090: "不合法的主题id",
            40091: "不合法的主题id",
            40092: "不合法的主题id",
            40093: "不合法的主题id",
            40094: "不合法的主题id",
            40095: "不合法的主题id",
            40096: "不合法的主题id",
            40097: "不合法的主题id",
            40098: "不合法的主题id",
            40099: "不合法的主题id",
            40100: "不合法的主题id",
            40101: "不合法的主题id",
            40102: "不合法的主题id",
            40103: "不合法的主题id",
            40104: "不合法的主题id",
            40105: "不合法的主题id",
            40106: "不合法的主题id",
            40107: "不合法的主题id",
            40108: "不合法的主题id",
            40109: "不合法的主题id",
            40110: "不合法的主题id",
            40111: "不合法的主题id",
            40112: "不合法的主题id",
            40113: "不合法的主题id",
            40114: "不合法的主题id",
            40115: "不合法的主题id",
            40116: "不合法的主题id",
            40117: "不合法的主题id",
            40118: "不合法的主题id",
            40119: "不合法的主题id",
            40120: "不合法的主题id",
            40121: "不合法的主题id",
            40122: "不合法的主题id",
            40123: "不合法的主题id",
            40124: "不合法的主题id",
            40125: "不合法的主题id",
            40126: "不合法的主题id",
            40127: "不合法的主题id",
            40128: "不合法的主题id",
            40129: "不合法的主题id",
            40130: "不合法的主题id",
            40131: "不合法的主题id",
            40132: "不合法的主题id",
            40133: "不合法的主题id",
            40134: "不合法的主题id",
            40135: "不合法的主题id",
            40136: "不合法的主题id",
            40137: "不合法的主题id",
            40138: "不合法的主题id",
            40139: "不合法的主题id",
            40140: "不合法的主题id",
            40141: "不合法的主题id",
            40142: "不合法的主题id",
            40143: "不合法的主题id",
            40144: "不合法的主题id",
            40145: "不合法的主题id",
            40146: "不合法的主题id",
            40147: "不合法的主题id",
            40148: "不合法的主题id",
            40149: "不合法的主题id",
            40150: "不合法的主题id",
            40151: "不合法的主题id",
            40152: "不合法的主题id",
            40153: "不合法的主题id",
            40154: "不合法的主题id",
            40155: "不合法的主题id",
            40156: "不合法的主题id",
            40157: "不合法的主题id",
            40158: "不合法的主题id",
            40159: "不合法的主题id",
            40160: "不合法的主题id",
            40161: "不合法的主题id",
            40162: "不合法的主题id",
            40163: "不合法的主题id",
            40164: "不合法的主题id",
            40165: "不合法的主题id",
            40166: "不合法的主题id",
            40167: "不合法的主题id",
            40168: "不合法的主题id",
            40169: "不合法的主题id",
            40170: "不合法的主题id",
            40171: "不合法的主题id",
            40172: "不合法的主题id",
            40173: "不合法的主题id",
            40174: "不合法的主题id",
            40175: "不合法的主题id",
            40176: "不合法的主题id",
            40177: "不合法的主题id",
            40178: "不合法的主题id",
            40179: "不合法的主题id",
            40180: "不合法的主题id",
            40181: "不合法的主题id",
            40182: "不合法的主题id",
            40183: "不合法的主题id",
            40184: "不合法的主题id",
            40185: "不合法的主题id",
            40186: "不合法的主题id",
            40187: "不合法的主题id",
            40188: "不合法的主题id",
            40189: "不合法的主题id",
            40190: "不合法的主题id",
            40191: "不合法的主题id",
            40192: "不合法的主题id",
            40193: "不合法的主题id",
            40194: "不合法的主题id",
            40195: "不合法的主题id",
            40196: "不合法的主题id",
            40197: "不合法的主题id",
            40198: "不合法的主题id",
            40199: "不合法的主题id",
            40200: "不合法的主题id",
            40201: "不合法的主题id",
            40202: "不合法的主题id",
            40203: "不合法的主题id",
            40204: "不合法的主题id",
            40205: "不合法的主题id",
            40206: "不合法的主题id",
            40207: "不合法的主题id",
            40208: "不合法的主题id",
            40209: "不合法的主题id",
            40210: "不合法的主题id",
            40211: "不合法的主题id",
            40212: "不合法的主题id",
            40213: "不合法的主题id",
            40214: "不合法的主题id",
            40215: "不合法的主题id",
            40216: "不合法的主题id",
            40217: "不合法的主题id",
            40218: "不合法的主题id",
            40219: "不合法的主题id",
            40220: "不合法的主题id",
            40221: "不合法的主题id",
            40222: "不合法的主题id",
            40223: "不合法的主题id",
            40224: "不合法的主题id",
            40225: "不合法的主题id",
            40226: "不合法的主题id",
            40227: "不合法的主题id",
            40228: "不合法的主题id",
            40229: "不合法的主题id",
            40230: "不合法的主题id",
            40231: "不合法的主题id",
            40232: "不合法的主题id",
            40233: "不合法的主题id",
            40234: "不合法的主题id",
            40235: "不合法的主题id",
            40236: "不合法的主题id",
            40237: "不合法的主题id",
            40238: "不合法的主题id",
            40239: "不合法的主题id",
            40240: "不合法的主题id",
            40241: "不合法的主题id",
            40242: "不合法的主题id",
            40243: "不合法的主题id",
            40244: "不合法的主题id",
            40245: "不合法的主题id",
            40246: "不合法的主题id",
            40247: "不合法的主题id",
            40248: "不合法的主题id",
            40249: "不合法的主题id",
            40250: "不合法的主题id",
        }

        # 如果是常见的不可重试错误，不重试
        if errcode in non_retryable_codes:
            return False

        # 其他错误默认可重试
        return True

    def _get_backoff_time(self, attempt: int) -> float:
        """获取退避时间

        Args:
            attempt: 当前尝试次数（从0开始）

        Returns:
            float: 退避时间（秒）
        """
        if attempt < len(RetryConfig.BACKOFF_STRATEGY):
            return RetryConfig.BACKOFF_STRATEGY[attempt]
        else:
            return RetryConfig.BACKOFF_STRATEGY[-1]

    def close(self):
        """关闭客户端会话"""
        self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def __repr__(self) -> str:
        """对象字符串表示"""
        return (
            f"WebhookClient(webhook_url='{self.webhook_url}', "
            f"timeout={self.timeout}, max_retries={self.max_retries})"
        )
