"""
JSON格式解析器
解析JSON格式的接口文档文件
作者: 开发团队
创建时间: 2026-01-27
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path

from ..models.interface import Interface


class JSONParser:
    """JSON格式接口文档解析器"""

    def __init__(self):
        """初始化JSON解析器"""
        self.supported_extensions = ['.json']

    def can_parse(self, file_path: str) -> bool:
        """检查是否能够解析该文件"""
        return Path(file_path).suffix.lower() in self.supported_extensions

    def parse(self, file_path: str, service: str = "", module: str = "") -> List[Interface]:
        """
        解析JSON文件并返回接口列表

        Args:
            file_path: JSON文件路径
            service: 服务类型 (user, nurse, admin)
            module: 模块名称

        Returns:
            解析后的接口列表

        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON格式错误
            ValueError: 数据格式错误
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"JSON格式错误 in {file_path}: {str(e)}",
                e.doc,
                e.pos
            )
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(
                f"文件编码错误 in {file_path}: {str(e)}",
                e.encoding,
                e.start,
                e.end,
                e.reason
            )

        return self._parse_data(data, file_path, service, module)

    def _parse_data(self, data: Dict[str, Any], file_path: str,
                   service: str, module: str) -> List[Interface]:
        """
        解析数据并生成接口列表

        Args:
            data: 解析后的JSON数据
            file_path: 文件路径
            service: 服务类型
            module: 模块名称

        Returns:
            接口列表
        """
        interfaces = []

        if not isinstance(data, dict):
            raise ValueError(f"JSON根对象必须是字典，in {file_path}")

        # 获取文件修改时间
        last_modified = os.path.getmtime(file_path)

        # 遍历数据，每个键值对代表一个接口
        for key, value in data.items():
            interface = self._parse_interface(key, value, file_path, service, module, last_modified)
            if interface:
                interfaces.append(interface)

        if not interfaces:
            raise ValueError(f"未找到有效的接口定义 in {file_path}")

        return interfaces

    def _parse_interface(self, key: str, value: Any, file_path: str,
                        service: str, module: str, last_modified: float) -> Interface:
        """
        解析单个接口

        Args:
            key: 接口键 (格式: "{METHOD} {PATH}")
            value: 接口数据
            file_path: 文件路径
            service: 服务类型
            module: 模块名称
            last_modified: 文件修改时间

        Returns:
            解析后的接口对象
        """
        if not isinstance(value, dict):
            raise ValueError(f"接口数据必须是字典: {key}")

        # 解析方法、URL和路径
        method, path = self._parse_key(key)
        url = value.get('url', '')
        name = self._extract_name_from_path(path)

        # 如果模块未指定，从文件路径推断
        if not module:
            module = self._extract_module_from_path(file_path)

        # 创建接口对象
        interface = Interface(
            name=name,
            method=method,
            url=url,
            path=path,
            service=service,
            module=module,
            headers=value.get('headers', {}),
            params=value.get('params', {}),
            body=value.get('body', {}),
            response=value.get('response', {}),
            file_path=file_path,
            last_modified=last_modified
        )

        return interface

    def _parse_key(self, key: str) -> tuple:
        """
        解析接口键，提取方法和路径

        Args:
            key: 接口键，格式如 "POST /api/v1/user/orders/create"

        Returns:
            (method, path) 元组
        """
        parts = key.strip().split(' ', 1)
        if len(parts) != 2:
            raise ValueError(f"无效的接口键格式: {key}，应为: METHOD PATH")

        method = parts[0].upper().strip()
        path = parts[1].strip()

        # 验证HTTP方法
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        if method not in valid_methods:
            raise ValueError(f"不支持的HTTP方法: {method}")

        return method, path

    def _extract_name_from_path(self, path: str) -> str:
        """
        从路径中提取接口名称

        Args:
            path: 接口路径

        Returns:
            接口名称
        """
        # 获取路径最后一段作为名称
        parts = path.strip('/').split('/')
        if parts:
            name = parts[-1]
            # 将下划线转换为空格，首字母大写
            return name.replace('_', ' ').title()
        return path

    def _extract_module_from_path(self, file_path: str) -> str:
        """
        从文件路径中提取模块名称

        Args:
            file_path: 文件路径

        Returns:
            模块名称
        """
        # 从文件路径提取目录名
        path_obj = Path(file_path)
        parent_dir = path_obj.parent.name
        return parent_dir

    def parse_batch(self, file_paths: List[str], service: str = "") -> List[Interface]:
        """
        批量解析多个JSON文件

        Args:
            file_paths: 文件路径列表
            service: 服务类型

        Returns:
            所有解析后的接口列表
        """
        all_interfaces = []

        for file_path in file_paths:
            try:
                if not self.can_parse(file_path):
                    continue

                module = self._extract_module_from_path(file_path)
                interfaces = self.parse(file_path, service, module)
                all_interfaces.extend(interfaces)
            except Exception as e:
                # 记录错误但继续处理其他文件
                print(f"解析文件失败 {file_path}: {str(e)}")
                continue

        return all_interfaces
