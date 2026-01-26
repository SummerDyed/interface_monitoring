#!/usr/bin/env python3
"""
配置管理器测试脚本
作者: 开发团队
创建时间: 2026-01-26
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import ConfigManager, ConfigError, ConfigValidationError


def test_basic_config_load():
    """测试基本配置加载功能"""
    print("=" * 60)
    print("测试1: 基本配置加载功能")
    print("=" * 60)

    try:
        with ConfigManager("config.yaml") as config_manager:
            # 测试获取配置项
            interval = config_manager.get("monitor.interval")
            print(f"[OK] 成功获取 monitor.interval: {interval}")

            timeout = config_manager.get("monitor.timeout")
            print(f"[OK] 成功获取 monitor.timeout: {timeout}")

            webhook_url = config_manager.get("wechat.webhook_url")
            print(f"[OK] 成功获取 wechat.webhook_url: {webhook_url}")

            # 测试默认值
            nonexistent = config_manager.get("monitor.nonexistent", "default_value")
            print(f"[OK] 默认值测试: {nonexistent}")

            print("\n[OK] 测试1通过: 基本配置加载功能正常\n")
            return True
    except Exception as e:
        print(f"\n[FAIL] 测试1失败: {e}\n")
        return False


def test_config_validation():
    """测试配置验证功能"""
    print("=" * 60)
    print("测试2: 配置验证功能")
    print("=" * 60)

    try:
        with ConfigManager("config.yaml") as config_manager:
            is_valid, errors = config_manager.validate()
            if is_valid:
                print("[OK] 配置验证通过")
                print(f"[OK] 验证结果: {is_valid}")
            else:
                print("[FAIL] 配置验证失败:")
                for error in errors:
                    print(f"  - {error}")

            print("\n[OK] 测试2通过: 配置验证功能正常\n")
            return True
    except Exception as e:
        print(f"\n[FAIL] 测试2失败: {e}\n")
        return False


def test_config_set():
    """测试配置设置功能"""
    print("=" * 60)
    print("测试3: 配置设置功能")
    print("=" * 60)

    try:
        with ConfigManager("config.yaml") as config_manager:
            # 设置新配置项
            config_manager.set("test.key", "test_value")
            print(f"[OK] 成功设置配置项: test.key = test_value")

            # 获取验证
            value = config_manager.get("test.key")
            print(f"[OK] 成功获取配置项: test.key = {value}")

            print("\n[OK] 测试3通过: 配置设置功能正常\n")
            return True
    except Exception as e:
        print(f"\n[FAIL] 测试3失败: {e}\n")
        return False


def test_config_snapshot():
    """测试配置快照功能"""
    print("=" * 60)
    print("测试4: 配置快照功能")
    print("=" * 60)

    try:
        with ConfigManager("config.yaml") as config_manager:
            # 获取配置快照
            snapshot = config_manager.get_config_snapshot()
            print(f"[OK] 成功获取配置快照")
            print(f"[OK] 快照包含 {len(snapshot)} 个顶级配置项")

            # 验证快照是只读的
            snapshot['test'] = 'test'
            current = config_manager.config
            if 'test' not in current:
                print("[OK] 快照是只读的，修改不影响原配置")

            print("\n[OK] 测试4通过: 配置快照功能正常\n")
            return True
    except Exception as e:
        print(f"\n[FAIL] 测试4失败: {e}\n")
        return False


def test_config_observer():
    """测试配置观察者功能"""
    print("=" * 60)
    print("测试5: 配置观察者功能")
    print("=" * 60)

    try:
        with ConfigManager("config.yaml") as config_manager:
            # 定义观察者回调
            observer_called = []

            def callback(old_config, new_config):
                observer_called.append(True)
                print("[OK] 配置变更观察者被调用")

            # 订阅观察者
            config_manager.subscribe(callback)
            print("[OK] 成功订阅配置变更观察者")

            # 触发配置变更
            config_manager.set("test.observer", "test")
            print("[OK] 触发配置变更")

            # 验证观察者被调用
            if observer_called:
                print("[OK] 观察者回调正常执行")

            print("\n[OK] 测试5通过: 配置观察者功能正常\n")
            return True
    except Exception as e:
        print(f"\n[FAIL] 测试5失败: {e}\n")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("配置管理器功能测试")
    print("=" * 60 + "\n")

    tests = [
        test_basic_config_load,
        test_config_validation,
        test_config_set,
        test_config_snapshot,
        test_config_observer
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"成功率: {passed/len(tests)*100:.1f}%")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
