# 全量接口监控程序

## 项目简介

全量接口监控程序是一个轻量级、易配置的接口连通性监控工具。基于Python开发，通过定时任务机制自动扫描接口文档、执行接口连通性测试、监控异常状态，并在发现问题时通过企业微信机器人及时推送告警。本系统支持对所有接口进行全面、实时的批量监控。

## 核心功能

- 📡 **接口监控**: 自动扫描接口文档，执行批量监控
- 🔐 **认证管理**: Token自动获取、缓存和刷新
- ⏰ **定时任务**: 15分钟间隔自动监控（可配置）
- 📊 **结果分析**: 异常状态识别（500/404/503/超时/网络错误）
- 💬 **企业微信推送**: 实时告警通知
- 🚀 **并发执行**: 支持多线程并发监控

## 技术栈

- Python 3.7+
- requests (HTTP请求)
- schedule (定时任务)
- pyyaml (配置管理)
- concurrent.futures (并发控制)

## 项目结构

```
interface_monitoring/
├── src/                    # 源码目录
│   ├── config/             # 配置管理模块
│   ├── monitor/            # 监控执行模块
│   ├── auth/              # 认证管理模块
│   ├── scanner/            # 接口扫描模块
│   ├── analyzer/           # 结果分析模块
│   └── notifier/           # 推送通知模块
├── config.yaml             # 主配置文件
├── requirements.txt        # 依赖列表
├── logs/                   # 日志目录
├── Interface-pool/         # 接口文档目录
│   ├── user/              # 用户服务接口
│   ├── nurse/             # 护士服务接口
│   └── admin/             # 管理员服务接口
├── scripts/               # 脚本目录
│   ├── install.sh         # 安装脚本
│   ├── start.sh           # 启动脚本
│   └── stop.sh            # 停止脚本
└── tests/                 # 测试目录
```

## 快速开始

### 1. 安装依赖

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

### 2. 配置参数

编辑 `config.yaml` 文件，修改以下关键配置：

- **企业微信Webhook地址**: `wechat.webhook_url`
- **服务认证信息**: `services.*.{username, password}`
- **监控间隔**: `monitor.interval`

### 3. 启动服务

```bash
./scripts/start.sh
```

### 4. 停止服务

```bash
./scripts/stop.sh
```

## 配置说明

### 监控配置

```yaml
monitor:
  interval: 15        # 监控间隔（分钟）
  timeout: 10        # 请求超时（秒）
  concurrent_threads: 5  # 并发线程数
  retry_times: 3     # 重试次数
```

### 企业微信配置

```yaml
wechat:
  webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
  enabled: true
  at_users: ["user1", "user2"]
  message_format: "detail"
```

### 服务认证配置

```yaml
services:
  user:
    token_url: "https://api.example.com/user/token"
    username: "your_username"
    password: "your_password"
```

## 接口文档格式

在 `Interface-pool/` 目录下按服务类型组织接口文档，支持JSON和YAML格式：

```json
{
  "name": "接口名称",
  "method": "GET|POST|PUT|DELETE",
  "url": "/api/v1/path",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "key": "value"
  },
  "description": "接口描述"
}
```

## 日志查看

```bash
# 监控日志
tail -f logs/monitor.log

# 错误日志
tail -f logs/error.log
```

## 开发指南

### 运行测试

```bash
pytest tests/ --cov=src
```

### 代码格式化

```bash
black src/
pylint src/
```

## 常见问题

**Q: 如何添加新的服务类型？**

A: 在 `config.yaml` 的 `services` 节点下添加新的服务配置，并在 `Interface-pool/` 下创建对应的目录。

**Q: 如何自定义监控间隔？**

A: 修改 `config.yaml` 中的 `monitor.interval` 配置项，单位为分钟。

**Q: 监控失败如何排查？**

A: 查看 `logs/error.log` 文件，检查错误日志信息。

## 许可证

MIT License

## 作者

开发团队

## 更新日志

### v1.0.0 (2026-01-26)
- 初始版本发布
- 支持基础接口监控功能
- 支持企业微信告警
- 支持多服务认证管理
