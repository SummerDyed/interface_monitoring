# 企业微信推送模块文档

## 概述

企业微信推送模块提供完整的企业微信机器人推送功能，支持Markdown格式消息、@人员配置、失败重试机制等特性。模块设计遵循模块化原则，提供了清晰的API接口和丰富的配置选项。

## 功能特性

- ✅ **Webhook API调用**: 封装企业微信Webhook API，支持HTTPS请求
- ✅ **Markdown消息**: 支持Markdown格式的消息推送
- ✅ **@人员**: 支持@指定人员和@所有人
- ✅ **重试机制**: 指数退避重试策略，提高推送成功率
- ✅ **错误处理**: 完善的错误分类和处理机制
- ✅ **消息格式化**: 自动将监控报告转换为美观的Markdown消息
- ✅ **连接测试**: 提供连接测试功能，验证配置是否正确
- ✅ **上下文管理**: 支持with语句，自动管理资源

## 模块结构

```
src/notifier/
├── __init__.py                    # 模块初始化
├── wechat_notifier.py             # 主要推送器类
├── webhook_client.py               # Webhook客户端
├── message_formatter.py           # 消息格式化器
└── models/
    ├── __init__.py
    └── wechat_message.py          # 消息数据模型
```

## 核心组件

### 1. WechatNotifier

主要的推送器类，集成了消息格式化和Webhook客户端。

#### 初始化

```python
from src.notifier import WechatNotifier

notifier = WechatNotifier(
    webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key",
    mentioned_list=["@user1"],              # 默认@人员列表
    mentioned_mobile_list=["13800138000"],  # 默认手机号列表
    timeout=10,                             # 请求超时时间（秒）
    max_retries=3,                          # 最大重试次数
    max_message_length=4000                 # 最大消息长度
)
```

#### 主要方法

**send_report()**: 发送监控报告

```python
from src.analyzer import MonitorReport

report = MonitorReport(
    title="接口监控报告",
    timestamp=datetime.now(),
    total_count=100,
    success_count=95,
    failure_count=5,
    success_rate=95.0,
    errors=[...],
    stats=...
)

alert_info = {
    'recipients': ['user-team@company.com'],
    'priority': 'HIGH',
    'summary': '5个接口异常'
}

result = notifier.send_report(report, alert_info=alert_info)

if result.success:
    print(f"推送成功: {result.message_id}")
else:
    print(f"推送失败: {result.error_message}")
```

**send_message()**: 发送自定义消息

```python
message = """
## 🔔 告警通知

发现5个接口异常，请及时处理。

**时间**: 2026-01-27 12:00:00
"""

result = notifier.send_message(
    content=message,
    mentioned_list=["@admin"],  # 临时@人员
    mentioned_mobile_list=["13800138000"]
)
```

**test_connection()**: 测试连接

```python
is_connected = notifier.test_connection()
if is_connected:
    print("连接成功，配置正确")
else:
    print("连接失败，请检查配置")
```

### 2. WebhookClient

Webhook API客户端，负责实际的HTTP请求和重试逻辑。

#### 特性

- **重试策略**: 指数退避重试（1秒 → 2秒 → 5秒）
- **错误分类**: 区分可重试和不可重试错误
- **连接池**: 使用requests.Session提高性能
- **超时处理**: 可配置请求超时时间

#### 错误处理

可重试错误:
- HTTP 500/502/503/504
- 连接超时
- 网络连接错误

不可重试错误:
- access_token无效（40001）
- access_token过期（40002）
- 其他API业务错误

### 3. MessageFormatter

消息格式化器，将监控报告转换为企业微信Markdown格式。

#### 格式化特性

- **智能截断**: 消息过长时自动使用简化版本
- **错误分组**: 按错误类型自动分组显示
- **统计信息**: 自动提取和格式化统计信息
- **@人员处理**: 自动添加@人员列表
- **表情符号**: 使用表情符号增强可读性

#### 消息模板

完整版模板（消息较短时）:
```markdown
## 🔔 接口监控告警

**监控时间**: 2026-01-27 12:00:00
**总接口数**: 100
**成功数**: 95
**失败数**: 5
**成功率**: 95.00%

## ⚠️ 异常详情

### HTTP_500 (2个)
- **getUser**: Server Error (HTTP 500)
- **createOrder**: DB Error (HTTP 500)

## 📊 统计信息

服务健康度
- 🟢 user: 99.00% (100/101)
- 🟡 order: 95.00% (95/100)

---
*由接口监控系统自动发送*
```

简化版模板（消息过长时）:
```markdown
## 🔔 接口监控告警

**时间**: 2026-01-27 12:00:00
**成功率**: 95.00%
**异常数**: 5

- HTTP_500: 2个
- HTTP_404: 3个
```

### 4. 数据模型

#### WechatMessage

企业微信消息数据模型

```python
from src.notifier import WechatMessage

message = WechatMessage(
    msgtype="markdown",
    markdown={"content": "消息内容"},
    mentioned_list=["@user1"],          # @用户ID列表
    mentioned_mobile_list=["13800138000"]  # @手机号列表
)

# 添加@人员
message.add_mention(user_id="@user2", mobile="13900139000")

# 转换为字典
data = message.to_dict()

# 转换为JSON
json_str = message.to_json()
```

#### PushResult

推送结果数据模型

```python
from src.notifier import PushResult

# 创建成功结果
result = PushResult.success_result(
    message_id="msg123",
    response_data={"errcode": 0},
    retry_count=1
)

# 创建失败结果
result = PushResult.failure_result(
    error_message="API Error",
    retry_count=2,
    response_data={"errcode": 40001}
)

# 检查结果
if result.success:
    print(f"推送成功: {result.message_id}")
else:
    print(f"推送失败: {result.error_message}")
    print(f"重试次数: {result.retry_count}")
```

## 使用示例

### 基础使用

```python
from src.notifier import WechatNotifier

# 创建推送器
notifier = WechatNotifier(
    webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key"
)

# 发送消息
message = "这是一条测试消息"
result = notifier.send_message(message)

# 检查结果
if result.success:
    print(f"推送成功: {result.message_id}")
else:
    print(f"推送失败: {result.error_message}")

# 清理资源
notifier.close()
```

### 使用监控报告

```python
from src.notifier import WechatNotifier
from src.analyzer import MonitorReport

# 创建推送器
notifier = WechatNotifier(
    webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key",
    mentioned_list=["@ops-team"]
)

# 发送监控报告
alert_info = {
    'recipients': ['user-team@company.com', 'dev-team@company.com'],
    'priority': 'HIGH',
    'summary': '5个接口异常'
}

result = notifier.send_report(report, alert_info=alert_info)

if result.success:
    print(f"报告推送成功")
else:
    print(f"报告推送失败: {result.error_message}")

notifier.close()
```

### 使用上下文管理器

```python
with WechatNotifier(
    webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key"
) as notifier:
    # 在with块内使用推送器
    result = notifier.send_message("测试消息")
    print(f"推送结果: {result.success}")

# with块结束后自动调用close()
```

### 从配置创建

```python
from src.notifier import create_notifier_from_config

config = {
    'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key',
    'mentioned_list': ['@admin'],
    'timeout': 15,
    'max_retries': 3
}

notifier = create_notifier_from_config(config)
```

### 连接测试

```python
notifier = WechatNotifier(
    webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key"
)

if notifier.test_connection():
    print("连接成功，可以正常推送")
else:
    print("连接失败，请检查配置")

notifier.close()
```

### 高级使用

```python
# 发送带@人员的消息
result = notifier.send_message(
    content="紧急告警！",
    mentioned_list=["@admin", "@ops"],
    mentioned_mobile_list=["13800138000"]
)

# 发送自定义格式消息（绕过格式化器）
from src.notifier import WechatMessage

custom_message = WechatMessage(
    markdown={"content": "自定义格式"},
    mentioned_list=["@custom"]
)
result = notifier.webhook_client.send_message(custom_message)
```

## 配置选项

### WechatNotifier配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| webhook_url | str | - | 企业微信Webhook URL（必填） |
| mentioned_list | List[str] | [] | 默认@用户ID列表 |
| mentioned_mobile_list | List[str] | [] | 默认@手机号列表 |
| timeout | int | 10 | 请求超时时间（秒） |
| max_retries | int | 3 | 最大重试次数 |
| max_message_length | int | 4000 | 最大消息长度 |

### 重试配置

```python
from src.notifier.webhook_client import RetryConfig

# 自定义重试配置
RetryConfig.MAX_ATTEMPTS = 5
RetryConfig.BACKOFF_STRATEGY = [1, 2, 5, 10]  # 自定义退避策略
RetryConfig.RETRYABLE_STATUS_CODES = [500, 502, 503, 504]  # 可重试的状态码
```

## 最佳实践

### 1. 资源管理

使用上下文管理器或显式调用close()释放资源:

```python
# 推荐：使用上下文管理器
with WechatNotifier(webhook_url="...") as notifier:
    notifier.send_message("消息")

# 或显式释放资源
notifier = WechatNotifier(webhook_url="...")
try:
    notifier.send_message("消息")
finally:
    notifier.close()
```

### 2. 错误处理

根据错误类型采取不同策略:

```python
result = notifier.send_message("消息")

if result.success:
    # 推送成功
    print(f"推送成功: {result.message_id}")
else:
    # 推送失败，检查是否可重试
    if "access_token" in result.error_message:
        # access_token错误，无需重试，需要刷新token
        print("需要刷新access_token")
    else:
        # 其他错误，可以重试
        print(f"推送失败，可重试: {result.error_message}")
```

### 3. 消息长度控制

监控报告可能很长，需要控制消息长度:

```python
# 创建推送器时设置最大消息长度
notifier = WechatNotifier(
    webhook_url="...",
    max_message_length=4000  # 企业微信限制
)

# 发送报告时会自动使用简化版本
result = notifier.send_report(report)
```

### 4. @人员配置

合理配置@人员列表:

```python
# 方案1：全局@人员
notifier = WechatNotifier(
    webhook_url="...",
    mentioned_list=["@admin"]  # 所有消息都@admin
)

# 方案2：按消息@人员
notifier = WechatNotifier(webhook_url="...")

result = notifier.send_message(
    content="紧急消息",
    mentioned_list=["@ops"]  # 只这条消息@ops
)
```

### 5. 连接测试

部署前测试连接:

```python
notifier = WechatNotifier(webhook_url="...")

if not notifier.test_connection():
    raise Exception("企业微信Webhook配置错误")

# 测试成功后继续...
```

## 常见问题

### Q1: 推送失败，提示"access_token无效"

A1: 这是企业微信Webhook的access_token无效或过期。需要检查Webhook地址是否正确，或重新创建机器人获取新的access_token。

### Q2: 推送失败，提示"消息过长"

A2: 企业微信对消息长度有限制（通常为4KB）。解决方案：
1. 设置`max_message_length`参数启用自动截断
2. 简化消息内容
3. 使用简化版模板

### Q3: @人员不生效

A3: 检查@人员格式是否正确：
- 用户ID格式: `@user001`
- 手机号格式: `13800138000`
- 确保用户在群聊中且未被禁言

### Q4: 如何提高推送成功率

A4: 建议：
1. 启用重试机制（默认3次）
2. 设置合理的超时时间（建议10-15秒）
3. 使用连接池和Keep-Alive
4. 区分可重试和不可重试错误

### Q5: 如何自定义消息格式

A5: 可以直接构造`WechatMessage`对象或修改`MessageFormatter`类的模板:

```python
from src.notifier import WechatMessage

message = WechatMessage(
    markdown={"content": "自定义格式消息"}
)
result = notifier.webhook_client.send_message(message)
```

## API参考

详见源代码docstring:
- `src/notifier/wechat_notifier.py`
- `src/notifier/webhook_client.py`
- `src/notifier/message_formatter.py`
- `src/notifier/models/wechat_message.py`

## 许可证

本模块为接口监控系统的组成部分，遵循项目整体许可证。
