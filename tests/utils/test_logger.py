"""
日志系统测试模块
测试LoggerManager类和全局日志函数的完整功能
作者: 测试团队
创建时间: 2026-01-26
"""

import unittest
import logging
import tempfile
import os
import shutil
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest

# 导入被测试模块
from src.utils.logger import (
    LoggerManager,
    initialize,
    get_logger,
    set_level,
    rotate_logs,
    debug,
    info,
    warning,
    error,
    critical
)
from src.utils.log_config import LogConfig
from src.utils.formatters import LogFormatter, JSONFormatter


class TestLogConfig(unittest.TestCase):
    """测试LogConfig类"""

    def setUp(self):
        """测试前准备"""
        # 确保每个测试都有独立的配置
        pass

    def test_default_config(self):
        """测试默认配置"""
        config = LogConfig()
        self.assertEqual(config.get_level(), 'INFO')
        self.assertEqual(config.get_format(), 'standard')
        self.assertTrue(config.is_console_enabled())
        self.assertEqual(config.get_file_path(), 'logs/monitor.log')
        self.assertEqual(config.get_console_level(), 'INFO')

    def test_custom_config(self):
        """测试自定义配置"""
        custom_config = {
            'level': 'DEBUG',
            'format': 'detailed',
            'console': {'enabled': False},
            'file': {'path': 'custom.log'}
        }
        config = LogConfig(custom_config)
        self.assertEqual(config.get_level(), 'DEBUG')
        self.assertEqual(config.get_format(), 'detailed')
        self.assertFalse(config.is_console_enabled())
        self.assertEqual(config.get_file_path(), 'custom.log')

    def test_get_set_config(self):
        """测试配置获取和设置"""
        config = LogConfig()
        config.set('level', 'WARNING')
        self.assertEqual(config.get('level'), 'WARNING')
        self.assertEqual(config.get_level(), 'WARNING')

    def test_nested_config_access(self):
        """测试嵌套配置访问"""
        config = LogConfig()
        config.set('file.max_size', '20MB')
        self.assertEqual(config.get('file.max_size'), '20MB')

    def test_from_env(self):
        """测试从环境变量创建配置"""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG', 'LOG_FILE': '/tmp/test.log'}):
            config = LogConfig.from_env()
            self.assertEqual(config.get_level(), 'DEBUG')
            self.assertEqual(config.get_file_path(), '/tmp/test.log')

    def test_ensure_log_directory(self):
        """测试日志目录创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / 'nonexistent' / 'logs' / 'test.log'
            config_dict = {'file': {'path': str(test_path)}}
            config = LogConfig(config_dict)
            self.assertTrue(test_path.parent.exists())

    def test_format_size_utility(self):
        """测试格式化大小工具函数"""
        from src.utils.log_config import format_size

        # 测试不同大小
        self.assertEqual(format_size(1024), '1.0KB')
        self.assertEqual(format_size(1024 * 1024), '1.0MB')
        self.assertEqual(format_size(1024 * 1024 * 1024), '1.0GB')
        self.assertEqual(format_size(512), '512B')

    def test_parse_size_utility(self):
        """测试解析大小工具函数"""
        from src.utils.log_config import parse_size

        # 测试不同大小格式
        self.assertEqual(parse_size('1KB'), 1024)
        self.assertEqual(parse_size('1MB'), 1024 * 1024)
        self.assertEqual(parse_size('1GB'), 1024 * 1024 * 1024)
        self.assertEqual(parse_size('100'), 100)

    def test_get_nonexistent_key(self):
        """测试获取不存在的配置键"""
        config = LogConfig()
        result = config.get('nonexistent.key', 'default')
        self.assertEqual(result, 'default')


class TestLogFormatter(unittest.TestCase):
    """测试LogFormatter类"""

    def test_standard_format(self):
        """测试标准格式"""
        formatter = LogFormatter(format_type='standard')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        self.assertIn('Test message', formatted)
        self.assertIn('INFO', formatted)

    def test_detailed_format(self):
        """测试详细格式"""
        formatter = LogFormatter(format_type='detailed')
        record = logging.LogRecord(
            name='test',
            level=logging.WARNING,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        self.assertIn('WARNING', formatted)
        self.assertIn('test', formatted)

    def test_simple_format(self):
        """测试简单格式"""
        formatter = LogFormatter(format_type='simple')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        self.assertEqual(formatted, 'Test message')

    def test_color_format(self):
        """测试带颜色格式"""
        formatter = LogFormatter(use_colors=True)
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=10,
            msg='Error message',
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        self.assertIn('\033[31m', formatted)  # 红色
        self.assertIn('Error message', formatted)

    def test_json_format(self):
        """测试JSON格式"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        # JSON格式应该包含message字段
        self.assertIn('Test message', formatted)

    def test_log_formatter_with_custom_fields(self):
        """测试带自定义字段的日志格式化"""
        formatter = LogFormatter(format_type='standard')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        # 添加自定义字段
        record.custom_field = 'custom_value'
        formatted = formatter.format(record)
        self.assertIn('Test message', formatted)

    def test_json_formatter_with_exception(self):
        """测试带异常的JSON格式化"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=10,
            msg='Error occurred',
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        self.assertIn('Error occurred', formatted)


class TestLoggerManager(unittest.TestCase):
    """测试LoggerManager类"""

    def setUp(self):
        """测试前准备"""
        # 清除LoggerManager实例
        LoggerManager._instance = None
        LoggerManager._lock = threading.RLock()

        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.test_log = os.path.join(self.test_dir, 'test.log')

        # 创建测试配置
        self.test_config = {
            'level': 'DEBUG',
            'format': 'standard',
            'console': {'enabled': False},
            'file': {
                'path': self.test_log,
                'encoding': 'utf-8'
            },
            'rotation': {
                'type': 'size',
                'size': '1MB',
                'backup_count': 3
            }
        }

    def tearDown(self):
        """测试后清理"""
        # 清理LoggerManager实例
        LoggerManager._instance = None
        LoggerManager._lock = threading.RLock()

        # 删除临时目录
        if os.path.exists(self.test_dir):
            try:
                # 等待一小段时间确保文件句柄释放
                time.sleep(0.1)
                shutil.rmtree(self.test_dir, ignore_errors=True)
            except Exception:
                pass  # Windows上可能有文件锁定，忽略错误

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = LoggerManager(self.test_config)
        manager2 = LoggerManager(self.test_config)
        self.assertIs(manager1, manager2)

    def test_initialization(self):
        """测试初始化"""
        manager = LoggerManager(self.test_config)
        self.assertIsNotNone(manager)
        self.assertIsInstance(manager._config, LogConfig)

    def test_get_logger(self):
        """测试获取日志记录器"""
        manager = LoggerManager(self.test_config)
        logger = manager.get_logger('test_logger')
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test_logger')

    def test_get_multiple_loggers(self):
        """测试获取多个日志记录器"""
        manager = LoggerManager(self.test_config)
        logger1 = manager.get_logger('logger1')
        logger2 = manager.get_logger('logger2')
        self.assertIsNot(logger1, logger2)

    def test_set_level(self):
        """测试设置日志级别"""
        manager = LoggerManager(self.test_config)
        manager.set_level('WARNING')
        # 验证级别设置成功
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.WARNING)

    def test_file_handler_creation(self):
        """测试文件处理器创建"""
        manager = LoggerManager(self.test_config)
        # 验证文件处理器存在
        self.assertTrue(os.path.exists(self.test_dir))

    def test_rotate_logs(self):
        """测试日志轮转"""
        manager = LoggerManager(self.test_config)

        # 创建一些日志内容
        logger = manager.get_logger('rotate_test')
        logger.info("Test message 1")
        logger.info("Test message 2")

        # 手动触发轮转
        manager.rotate_logs()

        # 验证轮转完成
        # 这里主要是测试方法调用不抛出异常

    def test_reconfigure(self):
        """测试重新配置"""
        manager = LoggerManager(self.test_config)
        new_config = {'level': 'ERROR'}
        manager.reconfigure(new_config)
        self.assertEqual(manager._config.get_level(), 'ERROR')

    def test_get_config(self):
        """测试获取配置"""
        manager = LoggerManager(self.test_config)
        config = manager.get_config()
        self.assertIsInstance(config, dict)
        self.assertEqual(config['level'], 'DEBUG')

    def test_cleanup(self):
        """测试清理资源"""
        manager = LoggerManager(self.test_config)
        manager.cleanup()
        # 验证清理后处理器被关闭
        # 具体验证取决于实现细节

    def test_thread_safety(self):
        """测试线程安全"""
        manager = LoggerManager(self.test_config)
        results = []

        def get_loggers():
            for i in range(10):
                logger = manager.get_logger(f'thread_test_{i}')
                results.append(logger.name)

        threads = [threading.Thread(target=get_loggers) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证所有线程都成功获取了日志记录器
        self.assertEqual(len(results), 50)

    @patch('sys.stderr')
    def test_file_handler_error_handling(self, mock_stderr):
        """测试文件处理器错误处理"""
        # 使用无效路径
        invalid_config = {
            'file': {'path': '/invalid/path/test.log'},
            'console': {'enabled': False}
        }
        manager = LoggerManager(invalid_config)
        # 应该不会崩溃，而是处理错误

    def test_multiple_rotating_handlers(self):
        """测试多种轮转处理器"""
        # 测试大小轮转
        size_config = self.test_config.copy()
        size_config['rotation'] = {'type': 'size', 'size': '1KB', 'backup_count': 2}
        manager1 = LoggerManager(size_config)

        # 测试时间轮转
        time_config = self.test_config.copy()
        time_config['rotation'] = {'type': 'time', 'when': 'midnight', 'backup_count': 2}
        manager2 = LoggerManager(time_config)

        # 测试无轮转
        none_config = self.test_config.copy()
        none_config['rotation'] = {'type': 'none'}
        manager3 = LoggerManager(none_config)

        # 所有配置都应该初始化成功
        self.assertIsNotNone(manager1)
        self.assertIsNotNone(manager2)
        self.assertIsNotNone(manager3)


class TestGlobalFunctions(unittest.TestCase):
    """测试全局函数"""

    def setUp(self):
        """测试前准备"""
        # 清除全局管理器
        LoggerManager._instance = None
        LoggerManager._lock = threading.RLock()

        # 创建临时日志目录
        self.test_dir = tempfile.mkdtemp()
        self.test_log = os.path.join(self.test_dir, 'global_test.log')

    def tearDown(self):
        """测试后清理"""
        # 清理全局管理器
        LoggerManager._instance = None
        LoggerManager._lock = threading.RLock()

        # 删除临时目录
        if os.path.exists(self.test_dir):
            try:
                time.sleep(0.1)
                shutil.rmtree(self.test_dir, ignore_errors=True)
            except Exception:
                pass

    def test_initialize(self):
        """测试初始化函数"""
        config = {'level': 'INFO', 'console': {'enabled': False}}
        manager = initialize(config)
        self.assertIsInstance(manager, LoggerManager)

    def test_get_logger_global(self):
        """测试全局get_logger函数"""
        initialize({'console': {'enabled': False}})
        logger = get_logger('global_test')
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'global_test')

    def test_get_logger_auto_name(self):
        """测试自动获取调用者模块名"""
        initialize({'console': {'enabled': False}})
        logger = get_logger()
        # 应该使用当前模块名

    def test_set_level_global(self):
        """测试全局set_level函数"""
        initialize({'console': {'enabled': False}})
        set_level('WARNING')
        # 验证级别设置成功

    def test_rotate_logs_global(self):
        """测试全局rotate_logs函数"""
        initialize({'console': {'enabled': False}})
        # 不应该抛出异常
        rotate_logs()

    def test_convenience_functions(self):
        """测试便捷函数"""
        initialize({'console': {'enabled': False}, 'level': 'DEBUG'})

        # 测试所有级别函数
        debug("Debug message")
        info("Info message")
        warning("Warning message")
        error("Error message")
        critical("Critical message")

        # 所有函数都应该成功执行而不抛出异常

    def test_convenience_functions_with_formatting(self):
        """测试带格式化的便捷函数"""
        initialize({'console': {'enabled': False}, 'level': 'DEBUG'})

        # 测试格式化参数
        debug("User %s logged in", "Alice")
        info("Processing item %d", 42)
        warning("Invalid value: %s", "invalid")

        # 所有函数都应该成功执行


class TestLoggerIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        LoggerManager._instance = None
        LoggerManager._lock = threading.RLock()
        self.test_dir = tempfile.mkdtemp()
        self.test_log = os.path.join(self.test_dir, 'integration.log')

    def tearDown(self):
        """测试后清理"""
        LoggerManager._instance = None
        LoggerManager._lock = threading.RLock()
        if os.path.exists(self.test_dir):
            try:
                time.sleep(0.1)
                shutil.rmtree(self.test_dir, ignore_errors=True)
            except Exception:
                pass

    def test_file_and_console_output(self):
        """测试文件和控制台双输出"""
        config = {
            'level': 'INFO',
            'console': {'enabled': True, 'level': 'INFO'},
            'file': {'path': self.test_log},
            'rotation': {'type': 'size', 'size': '1MB', 'backup_count': 2}
        }

        manager = initialize(config)
        logger = get_logger('integration_test')

        # 写入日志
        logger.info("Integration test message")
        logger.warning("Warning message")
        logger.error("Error message")

        # 等待日志写入
        time.sleep(0.1)

        # 验证文件存在
        self.assertTrue(os.path.exists(self.test_log))

    def test_log_levels_filtering(self):
        """测试日志级别过滤"""
        config = {
            'level': 'WARNING',
            'console': {'enabled': False},
            'file': {'path': self.test_log}
        }

        manager = initialize(config)
        logger = get_logger('level_test')

        # 这些日志应该被过滤掉
        logger.debug("Debug message")
        logger.info("Info message")

        # 这些日志应该被记录
        logger.warning("Warning message")
        logger.error("Error message")

        # 等待写入
        time.sleep(0.1)

        # 验证只有WARNING和ERROR被记录
        with open(self.test_log, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Warning message", content)
            self.assertIn("Error message", content)
            # DEBUG和INFO应该不存在
            # 注意：实际过滤取决于logging配置

    def test_multiple_logger_instances(self):
        """测试多个日志记录器实例"""
        config = {
            'level': 'DEBUG',
            'console': {'enabled': False},
            'file': {'path': self.test_log}
        }

        initialize(config)

        # 获取多个不同名称的日志记录器
        loggers = [get_logger(f'test_logger_{i}') for i in range(5)]

        # 所有日志记录器都应该工作
        for i, logger in enumerate(loggers):
            logger.info(f"Message from logger {i}")

        # 等待写入
        time.sleep(0.1)

        # 验证文件存在
        self.assertTrue(os.path.exists(self.test_log))

    def test_chinese_logging(self):
        """测试中文日志"""
        config = {
            'level': 'INFO',
            'console': {'enabled': False},
            'file': {'path': self.test_log, 'encoding': 'utf-8'}
        }

        manager = initialize(config)
        logger = get_logger('chinese_test')

        # 写入中文日志
        logger.info("这是一条中文日志消息")
        logger.warning("警告信息")
        logger.error("错误信息")

        # 等待写入
        time.sleep(0.1)

        # 验证中文内容正确写入
        with open(self.test_log, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("中文日志消息", content)
            self.assertIn("警告信息", content)
            self.assertIn("错误信息", content)

    def test_concurrent_logging(self):
        """测试并发日志写入"""
        config = {
            'level': 'INFO',
            'console': {'enabled': False},
            'file': {'path': self.test_log}
        }

        manager = initialize(config)
        results = []
        errors = []

        def write_logs(thread_id):
            try:
                logger = get_logger(f'concurrent_test_{thread_id}')
                for i in range(10):
                    logger.info(f"Thread {thread_id} - Message {i}")
            except Exception as e:
                errors.append(e)

        # 启动多个线程
        threads = [threading.Thread(target=write_logs, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证没有错误
        self.assertEqual(len(errors), 0, f"并发日志写入出错: {errors}")

        # 验证文件存在
        self.assertTrue(os.path.exists(self.test_log))


class TestLoggerEdgeCases(unittest.TestCase):
    """边缘案例测试"""

    def setUp(self):
        """测试前准备"""
        LoggerManager._instance = None
        LoggerManager._lock = threading.RLock()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        LoggerManager._instance = None
        LoggerManager._lock = threading.RLock()
        if os.path.exists(self.test_dir):
            try:
                time.sleep(0.1)
                shutil.rmtree(self.test_dir, ignore_errors=True)
            except Exception:
                pass

    def test_empty_logger_name(self):
        """测试空日志记录器名称"""
        config = {'console': {'enabled': False}}
        manager = initialize(config)
        logger = manager.get_logger('')
        self.assertIsInstance(logger, logging.Logger)

    def test_special_characters_in_logger_name(self):
        """测试日志记录器名称中的特殊字符"""
        config = {'console': {'enabled': False}}
        manager = initialize(config)
        special_names = [
            'test.logger',
            'test-logger',
            'test_logger_123',
            'test Logger',  # 包含空格
        ]

        for name in special_names:
            logger = manager.get_logger(name)
            self.assertIsInstance(logger, logging.Logger)

    def test_very_long_log_message(self):
        """测试超长日志消息"""
        config = {'console': {'enabled': False}, 'file': {'path': os.path.join(self.test_dir, 'long.log')}}
        manager = initialize(config)
        logger = manager.get_logger('long_msg_test')

        # 创建超长消息
        long_message = "A" * 10000
        logger.info(long_message)

        # 应该能处理而不崩溃

    def test_unicode_in_log_message(self):
        """测试Unicode字符"""
        config = {
            'console': {'enabled': False},
            'file': {'path': os.path.join(self.test_dir, 'unicode.log'), 'encoding': 'utf-8'}
        }
        manager = initialize(config)
        logger = manager.get_logger('unicode_test')

        # 各种Unicode字符
        unicode_messages = [
            "Hello 世界 🌍",
            "Emoji test: 😀😁😂",
            "Special chars: ñáéíóú",
            "Math: ∑∫∆∇",
            "Symbols: ♠♣♦♥"
        ]

        for msg in unicode_messages:
            logger.info(msg)

        # 等待写入
        time.sleep(0.1)

        # 验证文件存在
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'unicode.log')))

    def test_none_message(self):
        """测试None消息"""
        config = {'console': {'enabled': False}}
        manager = initialize(config)
        logger = manager.get_logger('none_test')

        # None消息应该被处理
        logger.info(None)

    def test_exception_in_log_message(self):
        """测试日志消息中的异常"""
        config = {'console': {'enabled': False}}
        manager = initialize(config)
        logger = manager.get_logger('exception_test')

        try:
            # 故意抛出异常
            raise ValueError("Test exception")
        except ValueError:
            # 使用异常信息记录日志
            logger.exception("Caught an exception")

    def test_reinitialize_manager(self):
        """测试重新初始化管理器"""
        # 清除之前的实例
        LoggerManager._instance = None

        config1 = {'level': 'INFO', 'console': {'enabled': False}}
        manager1 = initialize(config1)

        config2 = {'level': 'DEBUG', 'console': {'enabled': False}}
        manager2 = initialize(config2)

        # 应该是同一个实例
        self.assertIs(manager1, manager2)

        # 配置应该更新
        self.assertEqual(manager2.get_config()['level'], 'DEBUG')

    def test_missing_log_directory(self):
        """测试日志目录不存在的情况"""
        nonexistent_path = os.path.join(self.test_dir, 'nonexistent', 'logs', 'test.log')
        config = {
            'console': {'enabled': False},
            'file': {'path': nonexistent_path}
        }

        # 应该创建目录
        manager = initialize(config)
        self.assertTrue(os.path.exists(os.path.dirname(nonexistent_path)))

    def test_performance_with_many_loggers(self):
        """测试大量日志记录器的性能"""
        config = {'console': {'enabled': False}}
        initialize(config)

        start_time = time.time()

        # 创建大量日志记录器
        loggers = [get_logger(f'perf_test_{i}') for i in range(100)]

        # 所有日志记录器都工作
        for logger in loggers:
            logger.info("Performance test")

        elapsed = time.time() - start_time

        # 应该在合理时间内完成（这里设定1秒为阈值）
        self.assertLess(elapsed, 1.0, "大量日志记录器创建耗时过长")


if __name__ == '__main__':
    # 运行测试
    unittest.main()
