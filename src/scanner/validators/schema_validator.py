"""
Schema验证器
验证接口文档格式的完整性和正确性
作者: 开发团队
创建时间: 2026-01-27
"""

from typing import Dict, Any, List, Tuple
from ..models.interface import Interface


class SchemaValidator:
    """接口文档Schema验证器"""

    # 必需字段
    REQUIRED_FIELDS = ['method', 'url']

    # 支持的HTTP方法
    VALID_HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

    # 字段类型定义
    FIELD_TYPES = {
        'method': str,
        'url': str,
        'path': str,
        'headers': dict,
        'params': dict,
        'body': dict,
        'response': dict
    }

    def validate(self, interface: Interface) -> Tuple[bool, List[str]]:
        """
        验证接口对象的Schema

        Args:
            interface: 待验证的接口对象

        Returns:
            (是否验证通过, 错误信息列表)
        """
        errors = []

        # 验证必需字段
        if not interface.method or not interface.method.strip():
            errors.append("缺少必需字段: method")

        if not interface.url or not interface.url.strip():
            errors.append("缺少必需字段: url")

        # 验证字段类型
        errors.extend(self._validate_field_types(interface))

        # 验证HTTP方法
        errors.extend(self._validate_http_method(interface.method))

        # 验证URL格式
        errors.extend(self._validate_url(interface.url))

        # 验证服务类型
        errors.extend(self._validate_service(interface.service))

        return len(errors) == 0, errors

    def validate_dict(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证字典格式的接口数据

        Args:
            data: 待验证的字典数据

        Returns:
            (是否验证通过, 错误信息列表)
        """
        errors = []

        # 验证必需字段
        for field in self.REQUIRED_FIELDS:
            if field not in data or not data.get(field):
                errors.append(f"缺少必需字段: {field}")

        # 验证字段类型
        errors.extend(self._validate_dict_field_types(data))

        # 验证HTTP方法
        if 'method' in data:
            errors.extend(self._validate_http_method(data['method']))

        # 验证URL格式
        if 'url' in data:
            errors.extend(self._validate_url(data['url']))

        # 验证服务类型
        if 'service' in data:
            errors.extend(self._validate_service(data['service']))

        return len(errors) == 0, errors

    def _validate_field_types(self, interface: Interface) -> List[str]:
        """
        验证字段类型

        Args:
            interface: 接口对象

        Returns:
            错误信息列表
        """
        errors = []

        for field, expected_type in self.FIELD_TYPES.items():
            value = getattr(interface, field, None)
            if value is not None and not isinstance(value, expected_type):
                errors.append(
                    f"字段 {field} 类型错误，期望 {expected_type.__name__}，实际 {type(value).__name__}"
                )

        return errors

    def _validate_dict_field_types(self, data: Dict[str, Any]) -> List[str]:
        """
        验证字典字段类型

        Args:
            data: 字典数据

        Returns:
            错误信息列表
        """
        errors = []

        for field, expected_type in self.FIELD_TYPES.items():
            if field in data:
                value = data[field]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"字段 {field} 类型错误，期望 {expected_type.__name__}，实际 {type(value).__name__}"
                    )

        return errors

    def _validate_http_method(self, method: str) -> List[str]:
        """
        验证HTTP方法

        Args:
            method: HTTP方法

        Returns:
            错误信息列表
        """
        errors = []

        if not method:
            errors.append("HTTP方法不能为空")
            return errors

        method = method.upper().strip()
        if method not in self.VALID_HTTP_METHODS:
            errors.append(
                f"不支持的HTTP方法: {method}，支持的方法: {', '.join(self.VALID_HTTP_METHODS)}"
            )

        return errors

    def _validate_url(self, url: str) -> List[str]:
        """
        验证URL格式

        Args:
            url: URL字符串

        Returns:
            错误信息列表
        """
        errors = []

        if not url:
            errors.append("URL不能为空")
            return errors

        url = url.strip()

        # 基本URL格式检查
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
            errors.append(
                f"URL格式错误: {url}，应以 http://, https:// 或 / 开头"
            )

        return errors

    def _validate_service(self, service: str) -> List[str]:
        """
        验证服务类型

        Args:
            service: 服务类型

        Returns:
            错误信息列表
        """
        errors = []

        if not service:
            errors.append("服务类型不能为空")
            return errors

        valid_services = ['user', 'nurse', 'admin']
        if service not in valid_services:
            errors.append(
                f"不支持的服务类型: {service}，支持的服务: {', '.join(valid_services)}"
            )

        return errors

    def validate_batch(self, interfaces: List[Interface]) -> Tuple[int, int, List[str]]:
        """
        批量验证接口

        Args:
            interfaces: 接口列表

        Returns:
            (总数量, 通过数量, 错误信息列表)
        """
        total_count = len(interfaces)
        passed_count = 0
        all_errors = []

        for i, interface in enumerate(interfaces):
            is_valid, errors = self.validate(interface)
            if is_valid:
                passed_count += 1
            else:
                for error in errors:
                    all_errors.append(f"接口 {i}: {error}")

        return total_count, passed_count, all_errors

    def get_schema_template(self) -> Dict[str, Any]:
        """
        获取接口文档Schema模板

        Returns:
            Schema模板字典
        """
        return {
            'method': 'POST',  # HTTP方法
            'url': 'http://example.com/api/v1/path',  # 完整URL
            'path': '/api/v1/path',  # 路径
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {token}'
            },  # 请求头
            'params': {
                'page': 1,
                'size': 20
            },  # 查询参数
            'body': {
                'field1': 'value1',
                'field2': 'value2'
            },  # 请求体
            'response': {
                'code': 0,
                'message': 'success',
                'data': {}
            }  # 响应示例
        }

    def check_completeness(self, interface: Interface) -> Dict[str, bool]:
        """
        检查接口信息的完整性

        Args:
            interface: 接口对象

        Returns:
            各字段完整性检查结果
        """
        return {
            'has_method': bool(interface.method),
            'has_url': bool(interface.url),
            'has_headers': bool(interface.headers),
            'has_params': bool(interface.params),
            'has_body': bool(interface.body),
            'has_response': bool(interface.response),
            'has_service': bool(interface.service),
            'has_module': bool(interface.module)
        }
