"""
接口扫描器单元测试

作者: 开发团队
创建时间: 2026-01-28
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json
import yaml

from scanner.interface_scanner import InterfaceScanner
from scanner.models.interface import Interface


class TestInterfaceScanner:
    """接口扫描器测试类"""

    def test_init_default(self, interface_data_dir):
        """测试默认初始化"""
        scanner = InterfaceScanner(str(interface_data_dir))

        assert scanner.root_path == Path(interface_data_dir).resolve()
        assert scanner.max_workers == 4
        assert scanner.json_parser is not None
        assert scanner.yaml_parser is not None
        assert scanner.validator is not None

    def test_init_custom_workers(self, interface_data_dir):
        """测试自定义worker数量初始化"""
        scanner = InterfaceScanner(str(interface_data_dir), max_workers=8)

        assert scanner.max_workers == 8

    def test_scan_nonexistent_directory(self):
        """测试扫描不存在的目录"""
        scanner = InterfaceScanner('/nonexistent/path')

        with pytest.raises(FileNotFoundError):
            scanner.scan()

    def test_scan_not_directory(self, temp_file):
        """测试扫描非目录路径"""
        scanner = InterfaceScanner(str(temp_file))

        with pytest.raises(NotADirectoryError):
            scanner.scan()

    @patch('scanner.interface_scanner.JSONParser')
    @patch('scanner.interface_scanner.YAMLParser')
    def test_scan_success(self, mock_yaml_parser, mock_json_parser, interface_data_dir):
        """测试成功扫描"""
        # 准备mock
        mock_interface = Mock(spec=Interface)
        mock_interface.name = 'test_interface'

        mock_json_instance = Mock()
        mock_json_instance.can_parse.return_value = True
        mock_json_instance.parse.return_value = [mock_interface]
        mock_json_parser.return_value = mock_json_instance

        scanner = InterfaceScanner(str(interface_data_dir))
        results = scanner.scan()

        assert len(results) == 1
        assert results[0] == mock_interface

    def test_scan_empty_directory(self, temp_dir):
        """测试扫描空目录"""
        scanner = InterfaceScanner(str(temp_dir))
        results = scanner.scan()

        assert results == []

    def test_find_interface_files(self, interface_data_dir):
        """测试查找接口文档文件"""
        scanner = InterfaceScanner(str(interface_data_dir))

        files = scanner._find_interface_files()

        assert len(files) >= 3  # user, nurse, admin各一个文件
        assert any('user' in f for f in files)
        assert any('nurse' in f for f in files)
        assert any('admin' in f for f in files)

    def test_find_interface_files_no_service_dirs(self, temp_dir):
        """测试查找时没有服务目录"""
        scanner = InterfaceScanner(str(temp_dir))

        files = scanner._find_interface_files()

        assert files == []

    @patch('scanner.interface_scanner.ThreadPoolExecutor')
    def test_parse_files_concurrent(self, mock_executor_class, interface_data_dir):
        """测试并发解析文件"""
        # 准备mock
        mock_future = Mock()
        mock_interface = Mock(spec=Interface)
        mock_interface.name = 'test_interface'
        mock_future.result.return_value = [mock_interface]

        mock_executor = Mock()
        mock_executor.submit.return_value = mock_future
        mock_executor_class.return_value.__enter__ = Mock(return_value=mock_executor)
        mock_executor_class.return_value.__exit__ = Mock(return_value=None)
        mock_executor_class.return_value.__enter__ = Mock(return_value=mock_executor)

        scanner = InterfaceScanner(str(interface_data_dir))
        results = scanner._parse_files_concurrent(['test_file.json'], force=True)

        assert len(results) == 1
        assert results[0] == mock_interface

    def test_parse_single_file_json(self, interface_data_dir):
        """测试解析单个JSON文件"""
        scanner = InterfaceScanner(str(interface_data_dir))

        # 创建测试JSON文件
        test_file = interface_data_dir / 'user' / 'test.json'
        test_data = {
            'name': 'test_interface',
            'service': 'user',
            'method': 'GET',
            'path': '/api/test',
        }
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        results = scanner._parse_single_file(str(test_file), force=True)

        assert len(results) >= 1

    def test_parse_single_file_yaml(self, temp_dir):
        """测试解析单个YAML文件"""
        # 创建YAML文件
        test_file = Path(temp_dir) / 'test.yaml'
        test_data = {
            'name': 'test_interface',
            'service': 'user',
            'method': 'POST',
            'path': '/api/test',
        }
        with open(test_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_data, f)

        scanner = InterfaceScanner(str(temp_dir))
        results = scanner._parse_single_file(str(test_file), force=True)

        assert len(results) >= 1

    def test_parse_single_file_unsupported(self, temp_dir):
        """测试解析不支持的文件格式"""
        test_file = Path(temp_dir) / 'test.txt'
        test_file.write_text('test content', encoding='utf-8')

        scanner = InterfaceScanner(str(temp_dir))
        results = scanner._parse_single_file(str(test_file), force=True)

        assert results == []

    def test_parse_single_file_parse_error(self, temp_dir):
        """测试解析文件时出现错误"""
        test_file = Path(temp_dir) / 'test.json'
        test_file.write_text('invalid json', encoding='utf-8')

        scanner = InterfaceScanner(str(temp_dir))

        with pytest.raises(json.JSONDecodeError):
            scanner._parse_single_file(str(test_file), force=True)

    def test_is_file_changed_new_file(self, interface_data_dir):
        """测试新文件的变更检测"""
        scanner = InterfaceScanner(str(interface_data_dir))

        test_file = interface_data_dir / 'user' / 'new_file.json'
        test_file.write_text('{}', encoding='utf-8')

        changed = scanner._is_file_changed(str(test_file))

        assert changed is True

    def test_is_file_changed_not_changed(self, interface_data_dir):
        """测试文件未变更"""
        scanner = InterfaceScanner(str(interface_data_dir))

        # 获取一个现有文件
        files = scanner._find_interface_files()
        if files:
            test_file = files[0]
            changed = scanner._is_file_changed(test_file)

            assert changed is False

    def test_extract_service_from_path(self, interface_data_dir):
        """测试从路径提取服务名"""
        scanner = InterfaceScanner(str(interface_data_dir))

        test_path = str(interface_data_dir / 'user' / 'test.json')
        service = scanner._extract_service_from_path(test_path)

        assert service == 'user'

    def test_get_file_hash(self, interface_data_dir):
        """测试获取文件哈希"""
        scanner = InterfaceScanner(str(interface_data_dir))

        files = scanner._find_interface_files()
        if files:
            test_file = files[0]
            hash1 = scanner.get_file_hash(test_file)
            hash2 = scanner.get_file_hash(test_file)

            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256哈希长度

    @patch('scanner.interface_scanner.JSONParser')
    @patch('scanner.interface_scanner.YAMLParser')
    def test_scan_with_incremental(self, mock_yaml_parser, mock_json_parser, interface_data_dir):
        """测试增量扫描"""
        # 准备mock
        mock_interface = Mock(spec=Interface)
        mock_interface.name = 'test_interface'

        mock_json_instance = Mock()
        mock_json_instance.can_parse.return_value = True
        mock_json_instance.parse.return_value = [mock_interface]
        mock_json_parser.return_value = mock_json_instance

        scanner = InterfaceScanner(str(interface_data_dir))

        with patch.object(scanner, '_get_changed_files', return_value=['changed_file.json']):
            interfaces, changed_files = scanner.scan_with_incremental()

            assert len(interfaces) == 1
            assert 'changed_file.json' in changed_files

    @patch('scanner.interface_scanner.JSONParser')
    def test_validate_interfaces(self, mock_json_parser, interface_data_dir):
        """测试验证接口"""
        # 准备mock
        mock_interface = Mock(spec=Interface)
        mock_interface.name = 'test_interface'
        mock_interface.is_valid.return_value = True

        mock_json_instance = Mock()
        mock_json_instance.can_parse.return_value = True
        mock_json_instance.parse.return_value = [mock_interface]
        mock_json_parser.return_value = mock_json_instance

        scanner = InterfaceScanner(str(interface_data_dir))

        # 添加mock接口到列表
        interfaces = [mock_interface]
        validated = scanner._validate_interfaces(interfaces)

        assert len(validated) == 1

    @patch('scanner.interface_scanner.JSONParser')
    def test_validate_interfaces_invalid(self, mock_json_parser, interface_data_dir):
        """测试验证无效接口"""
        # 准备mock
        mock_interface = Mock(spec=Interface)
        mock_interface.name = 'invalid_interface'
        mock_interface.is_valid.return_value = False

        mock_json_instance = Mock()
        mock_json_instance.can_parse.return_value = True
        mock_json_instance.parse.return_value = [mock_interface]
        mock_json_parser.return_value = mock_json_instance

        scanner = InterfaceScanner(str(interface_data_dir))

        # 添加mock接口到列表
        interfaces = [mock_interface]
        validated = scanner._validate_interfaces(interfaces)

        assert len(validated) == 0

    def test_supported_extensions(self, interface_data_dir):
        """测试支持的文件扩展名"""
        scanner = InterfaceScanner(str(interface_data_dir))

        assert '.json' in scanner.supported_extensions
        assert '.yaml' in scanner.supported_extensions
        assert '.yml' in scanner.supported_extensions

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_benchmark_scan(self, benchmark, interface_data_dir):
        """基准测试：扫描性能"""
        scanner = InterfaceScanner(str(interface_data_dir))

        # 基准测试
        def scan_benchmark():
            return scanner.scan()

        results = benchmark.pedantic(scan_benchmark, rounds=5, iterations=1)

        assert isinstance(results, list)

    @pytest.mark.performance
    def test_memory_usage_during_scan(self, interface_data_dir):
        """测试扫描过程中的内存使用"""
        scanner = InterfaceScanner(str(interface_data_dir))

        # 执行多次扫描
        for _ in range(10):
            scanner.scan()

        # 验证内存使用在合理范围内
        # 这里只是示例，实际项目中需要更精确的内存监控
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        assert memory_mb < 500  # 内存使用应小于500MB

    def test_concurrent_file_parsing(self, temp_dir):
        """测试并发文件解析"""
        # 创建多个测试文件
        for i in range(10):
            test_file = Path(temp_dir) / f'test_{i}.json'
            test_data = {
                'name': f'test_interface_{i}',
                'service': 'user',
                'method': 'GET',
                'path': f'/api/test_{i}',
            }
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)

        scanner = InterfaceScanner(str(temp_dir), max_workers=5)

        # 扫描并解析
        results = scanner.scan()

        assert len(results) == 10

    def test_file_lock_handling(self, interface_data_dir):
        """测试文件锁处理"""
        scanner = InterfaceScanner(str(interface_data_dir))

        # 获取文件列表
        files = scanner._find_interface_files()

        # 多次计算哈希
        for _ in range(3):
            for file_path in files:
                scanner.get_file_hash(file_path)

        # 验证没有异常抛出
        assert True

    def test_incremental_scan_performance(self, interface_data_dir):
        """测试增量扫描性能"""
        scanner = InterfaceScanner(str(interface_data_dir))

        # 第一次完整扫描
        start_time = time.time()
        results1 = scanner.scan()
        first_scan_time = time.time() - start_time

        # 增量扫描（无变更）
        start_time = time.time()
        interfaces, changed_files = scanner.scan_with_incremental()
        incremental_scan_time = time.time() - start_time

        # 增量扫描应该更快
        assert incremental_scan_time < first_scan_time
        assert len(interfaces) == len(results1)
        assert len(changed_files) == 0
