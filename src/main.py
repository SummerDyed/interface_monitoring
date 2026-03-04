#!/usr/bin/env python3
"""
接口监控脚本主程序
作者: 开发团队
创建时间: 2026-01-26
最后更新: 2026-01-27
"""

import signal
import sys
import os
import traceback
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from config import ConfigManager
from utils import initialize, get_logger

# Import all core modules
from scanner import InterfaceScanner
from auth import TokenManager
from monitor import MonitorEngine
from analyzer import ResultAnalyzer
from notifier import WechatNotifier

# 进程锁文件路径
PID_FILE = Path("monitor.pid")


def check_process_lock() -> bool:
    """检查进程锁，防止重复启动

    Returns:
        bool: True表示可以启动，False表示已有进程在运行
    """
    try:
        if PID_FILE.exists():
            with open(PID_FILE, 'r') as f:
                old_pid = f.read().strip()
            # 检查进程是否还在运行
            try:
                import psutil
                if psutil.pid_exists(int(old_pid)):
                    if _logger:
                        _logger.error(f"监控程序已在运行 (PID: {old_pid})，请先停止该进程")
                    else:
                        print(f"错误: 监控程序已在运行 (PID: {old_pid})")
                    return False
                else:
                    # 进程不存在，删除锁文件
                    PID_FILE.unlink()
                    if _logger:
                        _logger.info(f"清理过期进程锁文件: {old_pid}")
                    else:
                        print(f"清理过期进程锁文件: {old_pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, ImportError):
                # psutil未安装或进程检查失败，删除锁文件
                PID_FILE.unlink()
                if _logger:
                    _logger.info("清理无效进程锁文件")
                else:
                    print("清理无效进程锁文件")
        return True
    except Exception as e:
        if _logger:
            _logger.warning(f"检查进程锁时发生异常: {e}")
        else:
            print(f"警告: 检查进程锁时发生异常: {e}")
        return True  # 发生异常时允许启动


def acquire_process_lock() -> bool:
    """获取进程锁

    Returns:
        bool: True表示获取成功，False表示失败
    """
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        if _logger:
            _logger.error(f"创建进程锁文件失败: {e}")
        else:
            print(f"错误: 创建进程锁文件失败: {e}")
        return False


def release_process_lock():
    """释放进程锁"""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
            if _logger:
                _logger.info("已清理进程锁文件")
            else:
                print("已清理进程锁文件")
    except Exception as e:
        if _logger:
            _logger.warning(f"清理进程锁文件失败: {e}")
        else:
            print(f"警告: 清理进程锁文件失败: {e}")


def signal_handler(signum, frame):
    """信号处理器，用于优雅关闭"""
    global _should_stop
    _logger.info(f"接收到信号 {signum}，准备优雅关闭...")
    _should_stop = True

# Global variables for graceful shutdown
_config_manager: Optional[ConfigManager] = None
_scanner: Optional[InterfaceScanner] = None
_token_manager: Optional[TokenManager] = None
_monitor_engine: Optional[MonitorEngine] = None
_analyzer: Optional[ResultAnalyzer] = None
_notifier: Optional[WechatNotifier] = None
_should_stop = False
_logger = None


def initialize_modules(config: Dict[str, Any]) -> bool:
    """初始化所有核心模块

    Args:
        config: 配置字典

    Returns:
        bool: 初始化是否成功
    """
    global _scanner, _token_manager, _monitor_engine, _analyzer, _notifier, _logger

    try:
        _logger.info("开始初始化核心模块...")

        # 1. 初始化接口扫描器
        interface_pool_path = config.get('monitor', {}).get('interface_pool_path', './Interface-pool')
        _scanner = InterfaceScanner(interface_pool_path)
        _logger.info("接口扫描器初始化完成")

        # 2. 初始化Token管理器
        services_config = config.get('services', {})
        token_config = {
            'refresh_threshold': 300,
            'max_workers': 5,
            'refresh_retry_times': 3,
        }
        _token_manager = TokenManager(
            config=token_config,
            services_config=services_config,
            auto_refresh=True
        )

        # 注册认证提供商
        from auth.providers.http_auth_provider import HTTPAuthProvider
        for service_name, service_config in services_config.items():
            try:
                # 为每个服务创建认证提供商
                provider_config = service_config.copy()
                provider_config['service_name'] = service_name
                provider = HTTPAuthProvider(provider_config)
                _token_manager.register_provider(service_name, provider)
                _logger.info(f"已注册 {service_name} 服务认证提供商")
            except Exception as e:
                _logger.error(f"注册 {service_name} 服务认证提供商失败: {e}")

        _logger.info("Token管理器初始化完成")

        # 3. 初始化监控引擎
        monitor_config = {
            'concurrency': config.get('monitor', {}).get('concurrent_threads', 5),
            'timeout': config.get('monitor', {}).get('timeout', 10),
            'request_interval': config.get('monitor', {}).get('request_interval', 0),
        }
        _monitor_engine = MonitorEngine(config=monitor_config, enable_monitoring=False)
        _logger.info("监控引擎初始化完成")

        # 4. 初始化结果分析器
        _analyzer = ResultAnalyzer(config={})
        _logger.info("结果分析器初始化完成")

        # 5. 初始化企业微信推送器
        wechat_config = config.get('wechat', {})
        if wechat_config.get('enabled', False):
            webhook_url = wechat_config.get('webhook_url')
            if webhook_url:
                mentioned_list = wechat_config.get('at_users', [])
                _notifier = WechatNotifier(
                    webhook_url=webhook_url,
                    mentioned_list=mentioned_list
                )
                _logger.info("企业微信推送器初始化完成")
            else:
                _logger.warning("企业微信Webhook URL未配置，推送功能将禁用")
        else:
            _logger.info("企业微信推送功能已禁用")

        _logger.info("所有核心模块初始化完成")
        return True

    except Exception as e:
        _logger.error(f"模块初始化失败: {e}")
        _logger.error(traceback.format_exc())
        return False


def run_monitoring_cycle(config: Dict[str, Any]) -> bool:
    """执行一次完整的监控周期

    Args:
        config: 配置字典

    Returns:
        bool: 监控是否成功完成
    """
    global _scanner, _token_manager, _monitor_engine, _analyzer, _notifier, _logger

    cycle_start = datetime.now()
    monitor_duration = 0.0  # 初始化监控执行时间
    analyze_duration = 0.0  # 初始化分析耗时
    _logger.info(f"=" * 60)
    _logger.info(f"开始监控周期: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
    _logger.info(f"=" * 60)

    try:
        # Step 1: 扫描接口文档
        _logger.info("Step 1: 扫描接口文档...")
        interfaces = _scanner.scan(force=True)
        if not interfaces:
            _logger.warning("未发现任何接口，监控周期结束")
            return False

        _logger.info(f"发现 {len(interfaces)} 个接口")
        _scanner.group_interfaces_by_service(interfaces)

        # Step 2: 获取Token
        _logger.info("Step 2: 获取认证Token...")
        token_map = {}
        failed_services = []  # 记录获取Token失败的服务
        services = ['user', 'nurse', 'admin']
        for service in services:
            try:
                # 强制刷新Token，确保每次监控周期都获取最新Token
                token = _token_manager.get_token(service, force_refresh=True)
                if token:
                    token_map[service] = token
                    _logger.debug(f"获取 {service} 服务Token成功")
                else:
                    _logger.warning(f"获取 {service} 服务Token失败")
                    failed_services.append(service)
            except Exception as e:
                _logger.error(f"获取 {service} 服务Token异常: {e}")
                failed_services.append(service)

        # 如果有服务Token获取失败，发送告警并跳过后续流程
        if failed_services and _notifier:
            _logger.warning(f"以下服务Token获取失败: {failed_services}")
            try:
                alert_content = f"""## 🔴 接口监控告警 - 服务认证异常

以下服务Token获取失败，接口将无法正常检测：

> **{', '.join(failed_services)}**

**发生时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**服务异常！请及时排查！**"""
                _notifier.send_message(alert_content)
                _logger.info("服务异常告警已发送")
            except Exception as e:
                _logger.error(f"发送服务异常告警失败: {e}")

            # 跳过后续的监控执行和报告发送
            _logger.warning("由于服务认证异常，跳过本次监控")
            return True

        # Step 3: 执行监控
        _logger.info("Step 3: 执行接口监控...")
        monitor_start = datetime.now()
        results = _monitor_engine.execute(interfaces, token_map)
        monitor_end = datetime.now()
        monitor_duration = (monitor_end - monitor_start).total_seconds()
        _logger.info(f"接口监控执行时间: {monitor_duration:.2f}秒 ({len(interfaces)}个接口)")

        if not results:
            _logger.warning("监控结果为空")
            return False

        # Step 4: 分析结果
        _logger.info("Step 4: 分析监控结果...")
        analyze_start = datetime.now()
        report = _analyzer.analyze(results, title=f"监控报告 - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        analyze_end = datetime.now()
        analyze_duration = (analyze_end - analyze_start).total_seconds()
        _logger.info(f"分析耗时: {analyze_duration:.2f}秒")

        # Step 5: 推送监控报告（总是发送）
        _logger.info("Step 5: 发送监控报告...")
        if _notifier:
            try:
                # 构建通知信息
                stats = _monitor_engine.get_statistics(results)

                # 判断是否有严重错误（404/500）
                has_critical_errors = any(
                    error.error_type in {'HTTP_404', 'HTTP_500'} or
                    error.status_code in [404, 500]
                    for error in results
                    if hasattr(error, 'error_type')
                )

                if has_critical_errors:
                    _logger.info("发现严重错误，发送告警通知")
                    # 有严重错误，使用告警信息
                    if report.alert_info:
                        alert_info = report.alert_info.copy()
                        alert_info['is_alert'] = True
                        alert_info['alert_type'] = 'error'
                        alert_info['summary'] = f"🚨 接口监控告警 - 发现{len([e for e in results if hasattr(e, 'error_type') and (e.error_type in {'HTTP_404', 'HTTP_500'} or e.status_code in [404, 500])])}个严重错误"
                        alert_info['timeout_interfaces'] = report.timeout_interfaces
                        alert_info['statistics'] = {
                            'total': stats['total'],
                            'duration': f"{monitor_duration:.2f}秒"
                        }
                    else:
                        alert_info = {
                            'is_alert': True,
                            'alert_type': 'error',
                            'summary': f"🚨 接口监控告警 - 发现严重错误",
                            'timeout_interfaces': report.timeout_interfaces,
                            'statistics': {
                                'total': stats['total'],
                                'duration': f"{monitor_duration:.2f}秒"
                            }
                        }
                else:
                    _logger.info("无严重错误，发送正常监控报告")
                    # 无严重错误，发送简化正常报告
                    alert_info = {
                        'is_alert': False,
                        'alert_type': 'normal',
                        'summary': f"✅ 接口监控正常 - 共监控{stats['total']}个接口",
                        'timeout_interfaces': report.timeout_interfaces,
                        'statistics': {
                            'total': stats['total'],
                            'duration': f"{monitor_duration:.2f}秒"
                        }
                    }

                # 发送通知
                wechat_config = config.get('wechat', {})
                push_result = _notifier.send_report(
                    report=report,
                    mentioned_list=wechat_config.get('at_users', []),
                    mentioned_mobile_list=[],
                    alert_info=alert_info
                )

                if push_result.success:
                    _logger.info("监控报告发送成功")
                else:
                    _logger.error(f"监控报告发送失败: {push_result.error_message}")
            except Exception as e:
                _logger.error(f"发送监控报告异常: {e}")
                _logger.error(traceback.format_exc())
        else:
            _logger.warning("企业微信推送器未初始化，跳过监控报告发送")

        # 记录监控统计信息
        stats = _monitor_engine.get_statistics(results)
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()

        # 统计状态码分布
        status_code_stats = _get_status_code_statistics(results)

        _logger.info(f"=" * 60)
        _logger.info(f"监控周期完成: {cycle_end.strftime('%Y-%m-%d %H:%M:%S')}")
        _logger.info(f"总耗时: {duration:.2f}秒 (监控执行: {monitor_duration:.2f}秒, 分析: {analyze_duration:.2f}秒)")
        _logger.info(f"接口总数: {stats['total']}")
        _logger.info(f"成功: {stats['success']}")
        _logger.info(f"失败: {stats['failed']}")
        _logger.info(f"成功率: {stats['success_rate']:.2f}%")
        _logger.info(f"平均响应时间: {stats['avg_response_time']:.2f}秒")

        # 显示状态码统计
        if status_code_stats:
            _logger.info(f"状态码分布:")
            for code, count in sorted(status_code_stats.items()):
                percentage = (count / stats['total']) * 100
                _logger.info(f"  HTTP {code}: {count}次 ({percentage:.1f}%)")

        _logger.info(f"=" * 60)

        return True

    except Exception as e:
        _logger.error(f"监控周期执行失败: {e}")
        _logger.error(traceback.format_exc())
        return False


def _get_status_code_statistics(results):
    """统计状态码分布

    Args:
        results: 监控结果列表

    Returns:
        dict: {状态码: 数量} 的字典
    """
    from collections import Counter

    status_codes = []
    for result in results:
        if result.status_code is not None:
            status_codes.append(result.status_code)
        else:
            # 对于没有状态码的错误（如超时、网络错误），标记为"N/A"
            status_codes.append("N/A")

    if not status_codes:
        return {}

    return dict(Counter(status_codes))


def cleanup():
    """清理资源"""
    global _config_manager, _scanner, _token_manager, _monitor_engine, _analyzer, _notifier, _logger

    if _logger:
        _logger.info("开始清理资源...")

    try:
        if _monitor_engine:
            _monitor_engine.cleanup()
            _logger.info("监控引擎清理完成")

        if _config_manager:
            _config_manager.cleanup()
            _logger.info("配置管理器清理完成")

        # 释放进程锁
        release_process_lock()

        _logger.info("资源清理完成")

    except Exception as e:
        if _logger:
            _logger.error(f"资源清理失败: {e}")


def calculate_next_run_time(interval_minutes: int, execute_on_schedule: bool) -> datetime:
    """计算下次执行时间

    Args:
        interval_minutes: 间隔时间（分钟）
        execute_on_schedule: 是否按准点时间执行

    Returns:
        datetime: 下次执行时间
    """
    now = datetime.now()

    if execute_on_schedule:
        # 按准点时间执行
        # 找到下一个对齐的时间点
        current_minutes = now.minute
        # 计算下一个对齐的分钟
        next_minute = ((current_minutes // interval_minutes) + 1) * interval_minutes

        # 如果跨越到下一天
        if next_minute >= 60:
            next_run = now.replace(
                hour=now.hour + 1,
                minute=next_minute - 60,
                second=0,
                microsecond=0
            )
        else:
            next_run = now.replace(
                minute=next_minute,
                second=0,
                microsecond=0
            )

        # 如果跨越到下一天
        if next_run.hour >= 24:
            next_run = next_run.replace(hour=next_run.hour - 24) + timedelta(days=1)

        # 确保时间在未来
        if next_run <= now:
            next_run += timedelta(minutes=interval_minutes)
    else:
        # 按启动时间间隔执行
        next_run = now + timedelta(minutes=interval_minutes)

    return next_run


def load_config(config_path="../config.yaml"):
    """加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        tuple: (ConfigManager, 配置字典)
    """
    global _config_manager, _logger

    try:
        # 使用ConfigManager加载配置
        _config_manager = ConfigManager(config_path)
        config = _config_manager.get_config_snapshot()
        return config

    except Exception as e:
        if _logger:
            _logger.error(f"配置文件加载失败: {e}")
        raise

def main():
    """
    主函数
    """
    global _logger, _should_stop

    # 初始化日志系统
    logger_manager = initialize()
    _logger = get_logger(__name__)

    _logger.info("=" * 60)
    _logger.info("接口监控脚本启动")
    _logger.info("=" * 60)

    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # 检查进程锁，防止重复启动
    if not check_process_lock():
        _logger.error("检测到已有监控程序在运行，程序退出")
        return 1

    if not acquire_process_lock():
        _logger.error("无法获取进程锁，程序退出")
        return 1

    try:
        # 加载配置
        config = load_config("config.yaml")
        _logger.info("配置加载完成")

        # 验证配置
        monitor_config = config.get('monitor', {})
        interval = monitor_config.get('interval', 15)
        execute_on_schedule = monitor_config.get('execute_on_schedule', True)

        if interval != 15:
            _logger.warning(f"监控间隔为 {interval} 分钟，但PRD要求为15分钟")

        # 初始化所有模块
        if not initialize_modules(config):
            _logger.error("模块初始化失败，程序退出")
            return 1

        # 计算下次执行时间
        interval_seconds = interval * 60
        next_run_time = calculate_next_run_time(interval, execute_on_schedule)

        # 立即执行一次监控
        _logger.info("立即执行一次监控周期...")
        run_monitoring_cycle(config)

        _logger.info("=" * 60)
        _logger.info(f"监控调度器启动成功，间隔 {interval} 分钟")
        _logger.info(f"执行模式: {'准点时间执行' if execute_on_schedule else '间隔执行'}")
        _logger.info(f"下次执行时间: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        _logger.info("按 Ctrl+C 可优雅关闭程序")
        _logger.info("=" * 60)

        # 主调度循环 - 使用精确时间控制
        while not _should_stop:
            try:
                now = datetime.now()
                if now >= next_run_time:
                    _logger.info(f"开始执行监控周期: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    run_monitoring_cycle(config)
                    # 重新计算下次执行时间（按准点或间隔）
                    next_run_time = calculate_next_run_time(interval, execute_on_schedule)
                    _logger.info(f"下次执行时间: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")

                # 等待1秒后检查
                time.sleep(1)
            except KeyboardInterrupt:
                _logger.info("接收到键盘中断信号")
                break
            except Exception as e:
                _logger.error(f"调度器循环异常: {e}")
                _logger.error(traceback.format_exc())
                time.sleep(5)  # 发生异常时等待5秒后重试

        _logger.info("监控调度器已停止")
        return 0

    except Exception as e:
        _logger.error(f"程序启动失败: {e}")
        _logger.error(traceback.format_exc())
        return 1
    finally:
        cleanup()


if __name__ == "__main__":
    sys.exit(main())
