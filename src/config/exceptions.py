"""
配置管理异常定义
作者: 开发团队
创建时间: 2026-01-26
"""


class ConfigError(Exception):
    """配置管理基础异常类"""


class ConfigLoadError(ConfigError):
    """配置文件加载异常"""


class ConfigValidationError(ConfigError):
    """配置验证异常"""


class ConfigReloadError(ConfigError):
    """配置热更新异常"""
