"""
配置Schema定义
定义所有配置项的类型、约束和默认值
作者: 开发团队
创建时间: 2026-01-26
"""

# 配置Schema定义
CONFIG_SCHEMA = {
    'monitor': {
        'interval': {
            'type': int,
            'min': 1,
            'max': 1440,
            'default': 15,
            'description': '监控间隔时间（分钟）'
        },
        'timeout': {
            'type': int,
            'min': 1,
            'max': 60,
            'default': 10,
            'description': '请求超时时间（秒）'
        },
        'concurrent_threads': {
            'type': int,
            'min': 1,
            'max': 50,
            'default': 5,
            'description': '并发线程数'
        },
        'retry_times': {
            'type': int,
            'min': 0,
            'max': 10,
            'default': 3,
            'description': '重试次数'
        },
        'retry_backoff': {
            'type': list,
            'default': [1, 2, 4],
            'description': '指数退避策略（秒）'
        },
        'interface_pool_path': {
            'type': str,
            'required': True,
            'default': './Interface-pool',
            'description': '接口文档目录路径'
        }
    },
    'wechat': {
        'webhook_url': {
            'type': str,
            'required': True,
            'description': 'Webhook地址'
        },
        'enabled': {
            'type': bool,
            'default': True,
            'description': '是否启用通知'
        },
        'at_users': {
            'type': list,
            'default': [],
            'description': '@人员列表（企业微信ID）'
        },
        'message_format': {
            'type': str,
            'choices': ['simple', 'detail'],
            'default': 'simple',
            'description': '通知内容格式'
        }
    },
    'logging': {
        'level': {
            'type': str,
            'choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            'default': 'INFO',
            'description': '日志级别'
        },
        'format': {
            'type': str,
            'default': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'description': '日志格式'
        },
        'log_file': {
            'type': str,
            'default': './logs/monitor.log',
            'description': '日志文件路径'
        },
        'error_log_file': {
            'type': str,
            'default': './logs/error.log',
            'description': '错误日志文件路径'
        },
        'rotation': {
            'type': dict,
            'nested': {
                'max_size': {
                    'type': int,
                    'min': 1,
                    'default': 10,
                    'description': '单个日志文件最大大小（MB）'
                },
                'backup_count': {
                    'type': int,
                    'min': 1,
                    'default': 5,
                    'description': '保留的日志文件数量'
                }
            }
        }
    },
    'services': {
        'user': {
            'type': dict,
            'nested': {
                'token_url': {
                    'type': str,
                    'required': True,
                    'description': 'Token获取接口URL'
                },
                'refresh_url': {
                    'type': str,
                    'required': True,
                    'description': 'Token刷新接口URL'
                },
                'method': {
                    'type': str,
                    'default': 'GET',
                    'description': '请求方法'
                },
                'headers': {
                    'type': dict,
                    'default': {},
                    'description': '请求头配置'
                },
                'cache_duration': {
                    'type': int,
                    'min': 1,
                    'default': 3600,
                    'description': 'Token缓存时间（秒）'
                },
                'interface_path': {
                    'type': str,
                    'required': True,
                    'description': '接口文档路径'
                }
            }
        },
        'nurse': {
            'type': dict,
            'nested': {
                'token_url': {
                    'type': str,
                    'required': True,
                    'description': 'Token获取接口URL'
                },
                'refresh_url': {
                    'type': str,
                    'required': True,
                    'description': 'Token刷新接口URL'
                },
                'method': {
                    'type': str,
                    'default': 'GET',
                    'description': '请求方法'
                },
                'headers': {
                    'type': dict,
                    'default': {},
                    'description': '请求头配置'
                },
                'cache_duration': {
                    'type': int,
                    'min': 1,
                    'default': 3600,
                    'description': 'Token缓存时间（秒）'
                },
                'interface_path': {
                    'type': str,
                    'required': True,
                    'description': '接口文档路径'
                }
            }
        },
        'admin': {
            'type': dict,
            'nested': {
                'token_url': {
                    'type': str,
                    'required': True,
                    'description': 'Token获取接口URL'
                },
                'refresh_url': {
                    'type': str,
                    'required': True,
                    'description': 'Token刷新接口URL'
                },
                'method': {
                    'type': str,
                    'default': 'POST',
                    'description': '请求方法'
                },
                'headers': {
                    'type': dict,
                    'default': {},
                    'description': '请求头配置'
                },
                'username': {
                    'type': str,
                    'description': '用户名'
                },
                'password': {
                    'type': str,
                    'description': '密码'
                },
                'cache_duration': {
                    'type': int,
                    'min': 1,
                    'default': 3600,
                    'description': 'Token缓存时间（秒）'
                },
                'interface_path': {
                    'type': str,
                    'required': True,
                    'description': '接口文档路径'
                }
            }
        }
    }
}
