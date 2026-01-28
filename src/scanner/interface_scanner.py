"""
接口扫描器
提供接口文档目录扫描和解析功能
作者: 开发团队
创建时间: 2026-01-27
"""

import os
import hashlib
import logging
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .models.interface import Interface
from .parsers.json_parser import JSONParser
from .parsers.yaml_parser import YAMLParser
from .validators.schema_validator import SchemaValidator


class InterfaceScanner:
    """接口扫描器主类"""

    def __init__(self, root_path: str, max_workers: int = 4):
        """
        初始化接口扫描器

        Args:
            root_path: 扫描根目录路径
            max_workers: 最大并发线程数
        """
        self.root_path = Path(root_path).resolve()
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)

        # 初始化组件
        self.json_parser = JSONParser()
        self.yaml_parser = YAMLParser()
        self.validator = SchemaValidator()

        # 缓存
        self._file_hashes: Dict[str, str] = {}
        self._lock = threading.Lock()

        # 支持的文件扩展名
        self.supported_extensions = {'.json', '.yaml', '.yml'}

    def scan(self, force: bool = False) -> List[Interface]:
        """
        扫描目录并返回接口列表

        Args:
            force: 是否强制重新扫描所有文件

        Returns:
            扫描到的接口列表
        """
        self.logger.info("开始扫描目录: %s", self.root_path)

        if not self.root_path.exists():
            raise FileNotFoundError(f"扫描目录不存在: {self.root_path}")

        if not self.root_path.is_dir():
            raise NotADirectoryError(f"路径不是目录: {self.root_path}")

        # 获取所有接口文档文件
        file_paths = self._find_interface_files()

        if not file_paths:
            self.logger.warning("未找到接口文档文件")
            return []

        self.logger.info("找到 %d 个接口文档文件", len(file_paths))

        # 并发解析文件
        all_interfaces = self._parse_files_concurrent(file_paths, force)

        # 验证接口
        validated_interfaces = self._validate_interfaces(all_interfaces)

        self.logger.info("扫描完成，共发现 %d 个接口", len(validated_interfaces))

        return validated_interfaces

    def scan_with_incremental(self) -> Tuple[List[Interface], List[str]]:
        """
        增量扫描，返回新增或修改的接口

        Returns:
            (接口列表, 变更文件列表)
        """
        all_interfaces = self.scan(force=False)
        changed_files = self._get_changed_files()

        return all_interfaces, changed_files

    def _find_interface_files(self) -> List[str]:
        """
        查找所有接口文档文件

        Returns:
            文件路径列表
        """
        file_paths = []

        # 支持的服务类型目录
        service_dirs = ['user', 'nurse', 'admin']

        for service in service_dirs:
            service_path = self.root_path / service
            if not service_path.exists():
                continue

            # 递归查找所有支持的文档文件
            for file_path in service_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    file_paths.append(str(file_path))

        return file_paths

    def _parse_files_concurrent(self, file_paths: List[str], force: bool) -> List[Interface]:
        """
        并发解析文件

        Args:
            file_paths: 文件路径列表
            force: 是否强制重新解析

        Returns:
            解析后的接口列表
        """
        all_interfaces = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self._parse_single_file, file_path, force): file_path
                for file_path in file_paths
            }

            # 收集结果
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    interfaces = future.result()
                    all_interfaces.extend(interfaces)
                except Exception as e:
                    self.logger.error("解析文件失败 %s: %s", file_path, str(e))

        return all_interfaces

    def _parse_single_file(self, file_path: str, force: bool) -> List[Interface]:
        """
        解析单个文件

        Args:
            file_path: 文件路径
            force: 是否强制重新解析

        Returns:
            解析后的接口列表
        """
        # 检查文件是否需要重新解析
        if not force and not self._is_file_changed(file_path):
            return []

        # 确定服务类型
        service = self._extract_service_from_path(file_path)

        try:
            # 根据文件扩展名选择解析器
            if self.json_parser.can_parse(file_path):
                return self.json_parser.parse(file_path, service)
            elif self.yaml_parser.can_parse(file_path):
                return self.yaml_parser.parse(file_path, service)
            else:
                self.logger.warning("不支持的文件格式: %s", file_path)
                return []
        except Exception as e:
            self.logger.error("解析文件失败 %s: %s", file_path, str(e))
            raise

    def _is_file_changed(self, file_path: str) -> bool:
        """
        检查文件是否发生变化

        Args:
            file_path: 文件路径

        Returns:
            是否发生变化
        """
        if not os.path.exists(file_path):
            return False

        current_hash = self.get_file_hash(file_path)

        with self._lock:
            cached_hash = self._file_hashes.get(file_path)
            if cached_hash != current_hash:
                self._file_hashes[file_path] = current_hash
                return True

        return False

    def get_file_hash(self, file_path: str) -> str:
        """
        计算文件MD5哈希值

        Args:
            file_path: 文件路径

        Returns:
            MD5哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_changed_files(self) -> List[str]:
        """
        获取所有变更的文件

        Returns:
            变更文件列表
        """
        changed_files = []
        for file_path in self._file_hashes:
            if self._is_file_changed(file_path):
                changed_files.append(file_path)
        return changed_files

    def _extract_service_from_path(self, file_path: str) -> str:
        """
        从文件路径提取服务类型

        Args:
            file_path: 文件路径

        Returns:
            服务类型
        """
        path = Path(file_path)
        parts = path.parts

        # 查找服务目录 (user, nurse, admin)
        for part in parts:
            if part in ['user', 'nurse', 'admin']:
                return part

        return 'unknown'

    def _validate_interfaces(self, interfaces: List[Interface]) -> List[Interface]:
        """
        验证接口列表

        Args:
            interfaces: 接口列表

        Returns:
            验证后的接口列表
        """
        validated_interfaces = []
        errors = []

        for interface in interfaces:
            is_valid, error_list = self.validator.validate(interface)
            if is_valid:
                validated_interfaces.append(interface)
            else:
                errors.extend(error_list)

        if errors:
            self.logger.warning("发现 %d 个验证错误", len(errors))

        return validated_interfaces

    def get_scan_statistics(self) -> Dict[str, any]:
        """
        获取扫描统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            return {
                'total_files': len(self._file_hashes),
                'scanned_files': len(self._file_hashes),
                'cached_files': len([h for h in self._file_hashes.values() if h]),
                'file_hashes': dict(self._file_hashes)
            }

    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self._file_hashes.clear()
            self.logger.info("已清空扫描缓存")

    def get_interface_by_key(self, interfaces: List[Interface], method: str, url: str) -> Optional[Interface]:
        """
        根据方法和URL查找接口

        Args:
            interfaces: 接口列表
            method: HTTP方法
            url: 接口URL

        Returns:
            匹配的接口或None
        """
        for interface in interfaces:
            if interface.method.upper() == method.upper() and interface.url == url:
                return interface
        return None

    def group_interfaces_by_service(self, interfaces: List[Interface]) -> Dict[str, List[Interface]]:
        """
        按服务类型分组接口

        Args:
            interfaces: 接口列表

        Returns:
            按服务分组的接口字典
        """
        grouped = {
            'user': [],
            'nurse': [],
            'admin': [],
            'unknown': []
        }

        for interface in interfaces:
            service = interface.service.lower()
            if service in grouped:
                grouped[service].append(interface)
            else:
                grouped['unknown'].append(interface)

        return grouped

    def export_interfaces(self, interfaces: List[Interface], output_path: str):
        """
        导出接口列表到JSON文件

        Args:
            interfaces: 接口列表
            output_path: 输出文件路径
        """
        import json

        interfaces_data = [interface.to_dict() for interface in interfaces]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(interfaces_data, f, ensure_ascii=False, indent=2)

        self.logger.info("已导出 %d 个接口到: %s", len(interfaces), output_path)
