# 接口监控告警逻辑总结

## 概述

根据需求，**只推送404和500错误**（包括HTTP状态码和业务码）作为告警。本文档详细说明告警判断逻辑和实现。

## 告警规则

### 1. 告警触发条件

只有以下错误才会触发告警：

#### HTTP状态码告警
- **404错误** - 页面或资源不存在
- **500错误** - 服务器内部错误

#### HTTP错误类型告警
- `HTTP_404` - 对应404状态码
- `HTTP_500` - 对应500状态码

#### 业务码告警
- 响应数据中的业务码字段值为 `404` 或 `500`
- 支持的字段名：`error_code`, `code`, `status_code`, `errorCode`, `business_code`, `result_code`, `ret_code`

### 2. 告警优先级

| 错误类型 | 优先级 | 说明 |
|---------|--------|------|
| 500错误 | CRITICAL | 服务器内部错误，最高优先级 |
| 404错误 | HIGH | 资源不存在，高优先级 |
| 其他错误 | LOW | 不触发告警 |

### 3. 告警接收人

#### 按服务分发
- `user` 服务 → user-team@company.com
- `admin` 服务 → admin-team@company.com
- `nurse` 服务 → nurse-team@company.com
- `order` 服务 → order-team@company.com
- `payment` 服务 → payment-team@company.com

#### 额外通知（仅500错误）
- 开发团队：dev-team@company.com
- 运维团队：ops-team@company.com

## 核心实现

### 1. 告警判断函数

```python
def should_send_alert(report: MonitorReport) -> bool:
    """判断是否需要发送告警

    只推送404和500错误作为告警
    """
    for error in report.errors:
        # 检查HTTP错误类型
        if error.error_type in ['HTTP_404', 'HTTP_500']:
            return True

        # 检查HTTP状态码
        if error.status_code in [404, 500]:
            return True

        # 检查业务码
        if _check_business_error_code(error):
            return True

    return False
```

### 2. 业务码检查

```python
def _check_business_error_code(error: ErrorInfo) -> bool:
    """检查业务错误码是否为404或500"""
    if error.response_data:
        business_code_fields = [
            'error_code', 'code', 'status_code', 'errorCode',
            'business_code', 'result_code', 'ret_code'
        ]

        for field in business_code_fields:
            if field in error.response_data:
                value = error.response_data[field]
                if str(value) in ['404', '500', 404, 500]:
                    return True

    return False
```

### 3. 告警信息处理

```python
def process_alert(report: MonitorReport) -> Dict[str, Any]:
    """处理告警推送"""
    # 判断是否需要告警
    if not should_send_alert(report):
        return {'should_alert': False, 'reason': '无404/500错误'}

    # 获取告警信息
    priority = get_alert_priority(report)
    recipients = get_alert_recipients(report)
    summary = get_alert_summary(report)
    alert_errors = filter_alert_errors(report)  # 仅包含404/500错误

    return {
        'should_alert': True,
        'priority': priority,
        'recipients': recipients,
        'summary': summary,
        'error_count': len(alert_errors),
        'alert_errors': alert_errors,
        'report': report,
    }
```

## 集成方式

### 1. 在 ResultAnalyzer 中使用

```python
class ResultAnalyzer:
    def analyze(self, results, title=None):
        # ... 执行分析 ...

        # 判断是否需要告警（仅404和500错误）
        alert_info = process_alert(report)

        # 添加告警信息到报告
        report.alert_info = alert_info

        return report
```

### 2. 获取告警信息

```python
analyzer = ResultAnalyzer()
report = analyzer.analyze(results)

if report.alert_info['should_alert']:
    print(f"需要告警: {report.alert_info['priority']}")
    print(f"接收人: {report.alert_info['recipients']}")
    print(f"告警摘要: {report.alert_info['summary']}")

    # 调用推送模块
    send_to_wechat(report.alert_info, report.content)
```

## 测试结果

### 测试场景1：只有404错误
- ✅ 触发告警
- ✅ 优先级：HIGH
- ✅ 摘要："1个404错误"

### 测试场景2：只有500错误
- ✅ 触发告警
- ✅ 优先级：CRITICAL
- ✅ 摘要："1个500错误"
- ✅ 额外通知运维和开发团队

### 测试场景3：404和500混合
- ✅ 触发告警
- ✅ 优先级：CRITICAL（因为有500）
- ✅ 摘要："1个500错误，1个404错误"
- ✅ 过滤出2个告警错误

### 测试场景4：其他错误（503/超时）
- ✅ 不触发告警
- ✅ 原因："无404/500错误"

### 测试场景5：业务码告警
- ✅ HTTP状态码200，但业务码404/500
- ✅ 正确识别并触发告警

## 文件结构

```
src/analyzer/
├── alert_logic.py          # 告警逻辑核心实现
├── result_analyzer.py      # 集成告警判断
├── models/report.py       # MonitorReport增加alert_info字段
├── example_usage.py       # 使用示例
└── __init__.py            # 导出告警相关函数
```

## 推送模块集成

在008-企业微信推送模块中，可以使用以下方式集成：

```python
from src.analyzer import process_alert, ReportGenerator

def handle_monitor_result(results):
    """处理监控结果并推送告警"""
    # 分析结果
    analyzer = ResultAnalyzer()
    report = analyzer.analyze(results)

    # 处理告警
    alert_info = process_alert(report)

    if alert_info['should_alert']:
        # 生成Markdown报告
        generator = ReportGenerator()
        markdown = generator.generate(report)

        # 推送到企业微信
        for recipient in alert_info['recipients']:
            wechat_pusher.send(
                to=recipient,
                title=f"接口监控告警 - {alert_info['priority']}",
                content=alert_info['summary'],
                markdown=markdown
            )
```

## 总结

✅ **只推送404和500错误** - 符合需求
✅ **支持HTTP状态码和业务码** - 灵活覆盖
✅ **按优先级排序** - CRITICAL > HIGH > LOW
✅ **自动分发接收人** - 按服务团队分发
✅ **自动过滤非告警错误** - 减少噪音
✅ **完整集成到分析流程** - 无缝对接
✅ **详细测试验证** - 可靠性保证

告警逻辑已完全实现并集成到结果分析模块中，可以直接与008推送模块配合使用。
