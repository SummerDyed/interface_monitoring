"""
接口扫描器测试
测试接口扫描模块的核心功能
作者: 开发团队
创建时间: 2026-01-27
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.scanner import InterfaceScanner
from src.scanner.models.interface import Interface
from src.scanner.parsers.json_parser import JSONParser
from src.scanner.parsers.yaml_parser import YAMLParser
from src.scanner.validators.schema_validator import SchemaValidator


class TestInterfaceScanner:
    """接口扫描器测试"""

    def setup_method(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.scanner = InterfaceScanner(self.test_dir, max_workers=2)

    def teardown_method(self):
        """测试后清理"""
        # 清理测试目录
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        scanner = InterfaceScanner("/tmp/test", max_workers=4)
        assert scanner.root_path == Path("/tmp/test").resolve()
        assert scanner.max_workers == 4
        assert scanner.json_parser is not None
        assert scanner.yaml_parser is not None
        assert scanner.validator is not None

    def test_find_interface_files(self):
        """测试查找接口文件"""
        # 创建测试文件
        service_dirs = ['user', 'nurse', 'admin']
        for service in service_dirs:
            service_path = Path(self.test_dir) / service
            service_path.mkdir(exist_ok=True)

            # 创建JSON文件
            json_file = service_path / "test.json"
            json_file.write_text('{"POST /test": {"url": "http://test.com"}}')

            # 创建YAML文件
            yaml_file = service_path / "test.yaml"
            yaml_file.write_text('POST /test:\n  url: http://test.com')

        # 查找文件
        file_paths = self.scanner._find_interface_files()

        assert len(file_paths) == 6  # 3个服务 × 2种格式

    def test_parse_single_json_file(self):
        """测试解析单个JSON文件"""
        # 创建测试JSON文件
        test_file = Path(self.test_dir) / "test.json"
        test_data = {
            "POST /api/v1/test": {
                "url": "http://120.79.173.8:8201/api/v1/test",
                "method": "POST",
                "body": {
                    "field1": "value1"
                }
            }
        }
        test_file.write_text(json.dumps(test_data, ensure_ascii=False))

        # 解析文件
        interfaces = self.scanner._parse_single_file(str(test_file), force=True)

        assert len(interfaces) == 1
        assert interfaces[0].method == "POST"
        assert interfaces[0].url == "http://120.79.173.8:8201/api/v1/test"
        assert interfaces[0].service == "unknown"

    def test_file_hash(self):
        """测试文件哈希计算"""
        test_file = Path(self.test_dir) / "test.json"
        test_file.write_text('{"test": "data"}')

        hash1 = self.scanner.get_file_hash(str(test_file))
        hash2 = self.scanner.get_file_hash(str(test_file))

        assert hash1 == hash2

        # 修改文件后哈希应改变
        test_file.write_text('{"test": "data2"}')
        hash3 = self.scanner.get_file_hash(str(test_file))

        assert hash1 != hash3

    def test_is_file_changed(self):
        """测试文件变更检测"""
        test_file = Path(self.test_dir) / "test.json"
        test_file.write_text('{"test": "data"}')

        # 第一次检查应返回True
        assert self.scanner._is_file_changed(str(test_file)) is True

        # 第二次检查应返回False（未变更）
        assert self.scanner._is_file_changed(str(test_file)) is False

    def test_extract_service_from_path(self):
        """测试从路径提取服务类型"""
        user_path = "/tmp/Interface-pool/user/test/file.json"
        nurse_path = "/tmp/Interface-pool/nurse/test/file.json"
        admin_path = "/tmp/Interface-pool/admin/test/file.json"

        assert self.scanner._extract_service_from_path(user_path) == "user"
        assert self.scanner._extract_service_from_path(nurse_path) == "nurse"
        assert self.scanner._extract_service_from_path(admin_path) == "admin"

    @patch('src.scanner.interface_scanner.logging')
    def test_scan_with_empty_directory(self, mock_logging):
        """测试扫描空目录"""
        interfaces = self.scanner.scan()

        assert len(interfaces) == 0

    def test_scan_with_invalid_directory(self):
        """测试扫描不存在的目录"""
        scanner = InterfaceScanner("/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            scanner.scan()


class TestJSONParser:
    """JSON解析器测试"""

    def setup_method(self):
        """测试前准备"""
        self.parser = JSONParser()
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_can_parse_json(self):
        """测试JSON文件识别"""
        assert self.parser.can_parse("test.json") is True
        assert self.parser.can_parse("test.JSON") is True
        assert self.parser.can_parse("test.yaml") is False

    def test_parse_valid_json(self):
        """测试解析有效JSON"""
        test_file = Path(self.test_dir) / "test.json"
        test_data = {
            "POST /api/v1/orders/create": {
                "url": "http://120.79.173.8:8201/maiban-user/api/v1/user/orders/create",
                "method": "POST",
                "body": {
                    "serviceItemId": 1001
                }
            }
        }
        test_file.write_text(json.dumps(test_data, ensure_ascii=False))

        interfaces = self.parser.parse(str(test_file), "user", "订单")

        assert len(interfaces) == 1
        assert interfaces[0].name == "Create"
        assert interfaces[0].method == "POST"
        assert interfaces[0].url == "http://120.79.173.8:8201/maiban-user/api/v1/user/orders/create"
        assert interfaces[0].service == "user"
        assert interfaces[0].module == "订单"

    def test_parse_invalid_json(self):
        """测试解析无效JSON"""
        test_file = Path(self.test_dir) / "test.json"
        test_file.write_text('{"invalid": json}')  # 无效JSON

        with pytest.raises(json.JSONDecodeError):
            self.parser.parse(str(test_file))

    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse("/nonexistent/file.json")


class TestYAMLParser:
    """YAML解析器测试"""

    def setup_method(self):
        """测试前准备"""
        self.parser = YAMLParser()
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_can_parse_yaml(self):
        """测试YAML文件识别"""
        assert self.parser.can_parse("test.yaml") is True
        assert self.parser.can_parse("test.yml") is True
        assert self.parser.can_parse("test.json") is False

    def test_parse_valid_yaml(self):
        """测试解析有效YAML"""
        test_file = Path(self.test_dir) / "test.yaml"
        test_data = """POST /api/v1/test:
  url: http://test.com/api/v1/test
  method: POST
  body:
    field1: value1
"""
        test_file.write_text(test_data)

        interfaces = self.parser.parse(str(test_file), "user", "test")

        assert len(interfaces) == 1
        assert interfaces[0].name == "Test"
        assert interfaces[0].method == "POST"
        assert interfaces[0].url == "http://test.com/api/v1/test"


class TestSchemaValidator:
    """Schema验证器测试"""

    def setup_method(self):
        """测试前准备"""
        self.validator = SchemaValidator()

    def test_validate_valid_interface(self):
        """测试验证有效接口"""
        interface = Interface(
            name="Test Interface",
            method="POST",
            url="http://test.com/api/v1/test",
            service="user",
            module="test"
        )

        is_valid, errors = self.validator.validate(interface)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_interface_missing_method(self):
        """测试验证缺少方法的接口"""
        interface = Interface(
            name="Test Interface",
            method="",
            url="http://test.com/api/v1/test",
            service="user"
        )

        is_valid, errors = self.validator.validate(interface)

        assert is_valid is False
        assert "method" in str(errors)

    def test_validate_interface_invalid_method(self):
        """测试验证无效HTTP方法的接口"""
        interface = Interface(
            name="Test Interface",
            method="INVALID",
            url="http://test.com/api/v1/test",
            service="user"
        )

        is_valid, errors = self.validator.validate(interface)

        assert is_valid is False
        assert "不支持的HTTP方法" in str(errors)

    def test_validate_interface_invalid_service(self):
        """测试验证无效服务类型的接口"""
        interface = Interface(
            name="Test Interface",
            method="POST",
            url="http://test.com/api/v1/test",
            service="invalid"
        )

        is_valid, errors = self.validator.validate(interface)

        assert is_valid is False
        assert "不支持的服务类型" in str(errors)

    def test_get_schema_template(self):
        """测试获取Schema模板"""
        template = self.validator.get_schema_template()

        assert "method" in template
        assert "url" in template
        assert "headers" in template
        assert template["method"] == "POST"

    def test_check_completeness(self):
        """测试检查接口完整性"""
        interface = Interface(
            name="Test",
            method="POST",
            url="http://test.com"
        )

        completeness = self.validator.check_completeness(interface)

        assert completeness["has_method"] is True
        assert completeness["has_url"] is True
        assert completeness["has_headers"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
