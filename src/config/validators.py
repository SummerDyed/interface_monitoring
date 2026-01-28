"""
配置验证函数
验证配置项的类型、约束和完整性
作者: 开发团队
创建时间: 2026-01-26
"""

import logging
from typing import Any, List
from .exceptions import ConfigValidationError


logger = logging.getLogger(__name__)


def validate_type(value: Any, expected_type: type) -> bool:
    """验证值的类型"""
    return isinstance(value, expected_type)


def validate_range(value: int, min_val: int = None, max_val: int = None) -> bool:
    """验证数值范围"""
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True


def validate_choices(value: Any, choices: List[Any]) -> bool:
    """验证值是否在可选列表中"""
    return value in choices


def apply_default(value: Any, default: Any) -> Any:
    """应用默认值"""
    return value if value is not None else default


def deep_merge(defaults: dict, config: dict) -> dict:
    """深度合并配置字典"""
    result = defaults.copy()

    for key, value in config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _validate_field(field: str, value: Any, field_schema: dict, path: str) -> List[str]:
    """验证单个字段"""
    errors = []
    field_path = f"{path}.{field}" if path else field

    # 验证类型
    expected_type = field_schema.get('type')
    if expected_type and not validate_type(value, expected_type):
        errors.append(
            f"类型错误 {field_path}: 期望 {expected_type.__name__}，"
            f"实际 {type(value).__name__}"
        )
        return errors

    # 验证范围（对于数值类型）
    if isinstance(value, (int, float)):
        min_val = field_schema.get('min')
        max_val = field_schema.get('max')
        if min_val is not None or max_val is not None:
            if not validate_range(value, min_val, max_val):
                range_str = _get_range_string(min_val, max_val)
                errors.append(f"数值范围错误 {field_path}: {value} {range_str}")

    # 验证可选值
    choices = field_schema.get('choices')
    if choices and value not in choices:
        errors.append(f"可选值错误 {field_path}: {value} 不在可选列表 {choices} 中")

    # 验证嵌套配置
    if 'nested' in field_schema and isinstance(value, dict):
        nested_errors = validate_nested_config(
            value, field_schema['nested'], field_path
        )
        errors.extend(nested_errors)

    return errors


def _get_range_string(min_val: int = None, max_val: int = None) -> str:
    """生成范围字符串"""
    if min_val is not None and max_val is not None:
        return f"在范围 [{min_val}, {max_val}]"
    if min_val is not None:
        return f">= {min_val}"
    if max_val is not None:
        return f"<= {max_val}"
    return ""


def validate_nested_config(nested_config: dict, schema: dict, path: str = "") -> List[str]:
    """验证嵌套配置"""
    errors = []

    # 检查必需字段
    for field, field_schema in schema.items():
        if field_schema.get('required', False):
            if field not in nested_config:
                full_path = f"{path}.{field}" if path else field
                errors.append(f"必填字段缺失: {full_path}")

    # 验证字段
    for field, value in nested_config.items():
        if field in schema:
            field_schema = schema[field]
            errors.extend(_validate_field(field, value, field_schema, path))

    return errors


def validate_config(config: dict, schema: dict) -> tuple[bool, List[str]]:
    """
    验证整个配置字典

    Returns:
        tuple: (是否验证通过, 错误列表)
    """
    errors = []

    # 验证顶级配置项
    for top_level in schema:
        if top_level not in config:
            errors.append(f"顶级配置项缺失: {top_level}")

    # 验证每个顶级配置项
    for section, section_config in config.items():
        if section in schema:
            section_schema = schema[section]
            if isinstance(section_config, dict):
                section_errors = validate_nested_config(
                    section_config, section_schema, section
                )
                errors.extend(section_errors)
            else:
                errors.append(f"配置项 {section} 应该是字典类型")

    is_valid = len(errors) == 0
    return is_valid, errors


def merge_with_defaults(config: dict, schema: dict) -> dict:
    """
    合并配置与默认值

    Returns:
        dict: 合并后的配置
    """
    defaults = extract_defaults(schema)
    return deep_merge(defaults, config)


def extract_defaults(schema: dict, parent_path: str = "") -> dict:
    """
    从Schema中提取默认值

    Returns:
        dict: 默认值字典
    """
    defaults = {}

    for key, field_schema in schema.items():
        if 'default' in field_schema:
            defaults[key] = field_schema['default']
        elif 'nested' in field_schema:
            path = f"{parent_path}.{key}" if parent_path else key
            defaults[key] = extract_defaults(field_schema['nested'], path)

    return defaults
