"""
报告生成器
负责生成Markdown格式的监控报告

作者: 开发团队
创建时间: 2026-01-27
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .models import MonitorReport, ErrorInfo, Stats

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器

    负责将监控分析结果转换为Markdown格式的报告
    """

    # Markdown模板
    REPORT_TEMPLATE = """# {title}

## 概览

**监控时间**: {timestamp}
**总接口数**: {total_count}
**成功数**: {success_count}
**失败数**: {failure_count}
**成功率**: {success_rate:.2f}%

## 异常详情

{error_sections}

## 统计信息

### 总体统计

- **平均响应时间**: {avg_response_time:.2f}ms
- **P95响应时间**: {p95_response_time:.2f}ms
- **P99响应时间**: {p99_response_time:.2f}ms
- **最小响应时间**: {min_response_time:.2f}ms
- **最大响应时间**: {max_response_time:.2f}ms

### 错误类型分布

{error_types_section}

### 服务健康度

{service_health_section}

## 报告说明

本报告由接口监控系统自动生成。
监控时间: {timestamp}
"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化报告生成器

        Args:
            config: 配置字典，可包含：
                - template: 自定义模板（可选）
                - include_timestamp: 是否包含时间戳（默认True）
                - max_error_details: 最大异常详情数量（默认50）
        """
        self.config = config or {}
        self.template = self.config.get('template', self.REPORT_TEMPLATE)
        self.include_timestamp = self.config.get('include_timestamp', True)
        self.max_error_details = self.config.get('max_error_details', 50)

        logger.info(
            f"报告生成器初始化完成: "
            f"包含时间戳={'是' if self.include_timestamp else '否'}, "
            f"最大异常详情数={self.max_error_details}"
        )

    def generate(self, report: MonitorReport) -> str:
        """生成Markdown格式报告

        Args:
            report: 监控报告对象

        Returns:
            str: Markdown格式的报告内容
        """
        logger.info(f"开始生成报告: {report.title}")

        # 构建模板变量
        template_vars = self._build_template_variables(report)

        # 渲染模板
        content = self.template.format(**template_vars)

        logger.info(f"报告生成完成，字符数={len(content)}")

        return content

    def _build_template_variables(self, report: MonitorReport) -> Dict[str, Any]:
        """构建模板变量

        Args:
            report: 监控报告对象

        Returns:
            dict: 模板变量字典
        """
        # 基础变量
        template_vars = {
            'title': report.title,
            'timestamp': self._format_timestamp(report.timestamp),
            'total_count': report.total_count,
            'success_count': report.success_count,
            'failure_count': report.failure_count,
            'success_rate': report.success_rate,
        }

        # 统计信息变量
        if report.stats:
            template_vars.update({
                'avg_response_time': report.stats.avg_response_time,
                'p95_response_time': report.stats.p95_response_time,
                'p99_response_time': report.stats.p99_response_time,
                'min_response_time': report.stats.min_response_time,
                'max_response_time': report.stats.max_response_time,
            })
        else:
            # 默认值
            template_vars.update({
                'avg_response_time': 0.0,
                'p95_response_time': 0.0,
                'p99_response_time': 0.0,
                'min_response_time': 0.0,
                'max_response_time': 0.0,
            })

        # 异常详情
        error_sections = self._build_error_sections(report.errors)
        template_vars['error_sections'] = error_sections

        # 错误类型分布
        error_types_section = self._build_error_types_section(report.stats)
        template_vars['error_types_section'] = error_types_section

        # 服务健康度
        service_health_section = self._build_service_health_section(report.stats)
        template_vars['service_health_section'] = service_health_section

        return template_vars

    def _build_error_sections(self, errors: List[ErrorInfo]) -> str:
        """构建异常详情章节

        Args:
            errors: 异常详情列表

        Returns:
            str: Markdown格式的异常详情章节
        """
        if not errors:
            return "✅ 恭喜！未发现异常。"

        # 按错误类型分组
        error_groups = {}
        for error in errors:
            error_type = error.error_type
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(error)

        # 构建章节
        sections = []
        for error_type, type_errors in error_groups.items():
            # 统计该错误类型的总数
            total_count = sum(e.count for e in type_errors)

            section = f"### {error_type} ({total_count}次)\n\n"

            # 添加每个异常的详情（限制数量）
            max_details = min(self.max_error_details, len(type_errors))
            for i, error in enumerate(type_errors[:max_details]):
                section += self._format_error_detail(error)
                if i < max_details - 1:
                    section += "\n"

            # 如果超过限制，添加提示
            if len(type_errors) > max_details:
                section += f"\n_（仅显示前{max_details}个异常，共{len(type_errors)}个）_"

            sections.append(section)

        return "\n\n".join(sections)

    def _format_error_detail(self, error: ErrorInfo) -> str:
        """格式化单个异常详情

        Args:
            error: 异常详情对象

        Returns:
            str: Markdown格式的异常详情
        """
        detail = f"**{error.interface_name}** "
        detail += f"`{error.interface_method}` "
        detail += f"{error.interface_url}\n\n"

        detail += f"- **错误信息**: {error.error_message}\n"

        if error.status_code is not None:
            detail += f"- **状态码**: {error.status_code}\n"

        detail += f"- **出现次数**: {error.count}\n"

        detail += f"- **服务**: {error.service}\n"

        # 添加请求数据（如果存在且不为空）
        if error.request_data and len(error.request_data) > 0:
            detail += f"- **请求数据**: {self._format_dict(error.request_data)}\n"

        # 添加响应数据（如果存在且不为空）
        if error.response_data and len(error.response_data) > 0:
            detail += f"- **响应数据**: {self._format_dict(error.response_data)}\n"

        return detail

    def _build_error_types_section(self, stats: Optional[Stats]) -> str:
        """构建错误类型分布章节

        Args:
            stats: 统计信息对象

        Returns:
            str: Markdown格式的错误类型分布
        """
        if not stats or not stats.error_types:
            return "无错误类型数据。"

        section = ""
        for error_type, count in stats.error_types.items():
            percentage = (count / stats.total_count * 100) if stats.total_count > 0 else 0
            section += f"- **{error_type}**: {count}次 ({percentage:.2f}%)\n"

        return section

    def _build_service_health_section(self, stats: Optional[Stats]) -> str:
        """构建服务健康度章节

        Args:
            stats: 统计信息对象

        Returns:
            str: Markdown格式的服务健康度
        """
        if not stats or not stats.services:
            return "无服务数据。"

        # 按健康状态分组
        healthy_services = []
        degraded_services = []
        critical_services = []
        unknown_services = []

        for service in stats.services:
            if service.health_status == 'HEALTHY':
                healthy_services.append(service)
            elif service.health_status == 'DEGRADED':
                degraded_services.append(service)
            elif service.health_status == 'CRITICAL':
                critical_services.append(service)
            else:
                unknown_services.append(service)

        sections = []

        # 健康服务
        if healthy_services:
            section = "#### ✅ 健康服务 (" + str(len(healthy_services)) + ")\n\n"
            for service in healthy_services:
                section += f"- **{service.service_name}**: 成功率 {service.success_rate:.2f}%\n"
            sections.append(section)

        # 降级服务
        if degraded_services:
            section = "#### ⚠️ 降级服务 (" + str(len(degraded_services)) + ")\n\n"
            for service in degraded_services:
                section += f"- **{service.service_name}**: 成功率 {service.success_rate:.2f}%\n"
            sections.append(section)

        # 严重服务
        if critical_services:
            section = "#### 🚨 严重服务 (" + str(len(critical_services)) + ")\n\n"
            for service in critical_services:
                section += f"- **{service.service_name}**: 成功率 {service.success_rate:.2f}%\n"
            sections.append(section)

        # 未知服务
        if unknown_services:
            section = "#### ❓ 未知服务 (" + str(len(unknown_services)) + ")\n\n"
            for service in unknown_services:
                section += f"- **{service.service_name}**: 无监控数据\n"
            sections.append(section)

        return "\n".join(sections) if sections else "无服务数据。"

    def _format_timestamp(self, timestamp: datetime) -> str:
        """格式化时间戳

        Args:
            timestamp: 时间戳

        Returns:
            str: 格式化后的时间字符串
        """
        if not self.include_timestamp:
            return ""

        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """格式化字典数据

        Args:
            data: 字典数据

        Returns:
            str: 格式化的字符串
        """
        if not data:
            return ""

        # 如果数据太大，截断
        max_length = 200
        str_data = str(data)

        if len(str_data) > max_length:
            return str_data[:max_length] + "...（已截断）"

        return str_data

    def save_to_file(self, report: MonitorReport, file_path: str) -> bool:
        """保存报告到文件

        Args:
            report: 监控报告对象
            file_path: 文件路径

        Returns:
            bool: 保存是否成功
        """
        try:
            content = self.generate(report)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"报告已保存到文件: {file_path}")

            return True

        except Exception as e:
            logger.error(f"保存报告到文件失败: {file_path}, 错误: {e}", exc_info=True)
            return False
