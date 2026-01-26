---
name: 004-开发接口扫描模块
status: open
created: 2026-01-26T08:16:58Z
updated: 2026-01-26T08:16:58Z
github: ""
depends_on: ["001"]
parallel: true
deprecated: false
---

# 004 - 开发接口扫描模块

**File**: `src/scanner/interface_scanner.py`
**Purpose**: 实现接口文档目录扫描和解析功能，支持JSON/YAML格式，自动提取接口信息并验证格式完整性
**Leverage**: pyyaml库；Python标准库os、hashlib
**Requirements**: PRD-2.1-接口文档管理
**Prompt**: Role: 后端开发工程师 | Task: 开发接口扫描模块，包括递归扫描Interface-pool目录、解析JSON/YAML文件、提取接口信息、验证格式完整性和增量更新机制，实现InterfaceScanner类 | Restrictions: 必须支持JSON和YAML格式，支持嵌套目录结构，内存使用合理 | Success: 扫描准确，解析正确，验证完善，增量更新有效

## Features (WHAT)

实现接口文档目录扫描和解析功能，支持JSON/YAML格式，自动提取接口信息并验证格式完整性。

### Core Features
- 递归扫描Interface-pool目录
- 自动识别和解析JSON/YAML文件
- 提取接口信息（URL、方法、参数、Headers等）
- 接口文档格式验证
- 增量更新和变更检测

### User Value (WHY)
自动发现和解析接口文档，为监控执行提供接口信息，减少手动配置工作。

## User Workflow (HOW - User Perspective)

1. 启动扫描任务，自动扫描Interface-pool目录
2. 解析所有JSON/YAML接口文档文件
3. 验证接口文档格式和完整性
4. 提取接口信息并存储
5. 检测接口文档变更，实现增量更新

## UI Elements Checklist

无前端界面，纯后端扫描模块。

## Acceptance Criteria

### Feature Acceptance
- [ ] 成功扫描Interface-pool目录下所有子目录
- [ ] 正确解析JSON和YAML格式的接口文档
- [ ] 提取所有必需字段（URL、方法、参数等）
- [ ] 验证接口文档格式正确性
- [ ] 支持增量更新，只处理变更文件

### Interaction Acceptance
- [ ] 扫描速度快（1000个文件<10秒）
- [ ] 解析错误时提供详细错误信息
- [ ] 支持批量操作和并发解析

### Quality Acceptance
- [ ] 错误处理完善（文件不存在、格式错误等）
- [ ] 支持嵌套目录结构
- [ ] 内存使用合理（大量文件时<100MB）
- [ ] 日志记录完整，便于问题排查

## Technical Details

### Implementation Plan

**Phase 1: 目录扫描**
1. 使用os.walk()递归遍历目录
2. 过滤出JSON和YAML文件
3. 按服务类型（user/nurse/admin）分类

**Phase 2: 文件解析**
1. 检测文件格式（JSON/YAML）
2. 使用相应解析器（json/yaml.load）
3. 统一数据结构和字段映射

**Phase 3: 信息提取**
1. 提取接口基本信息（name、method、url）
2. 提取请求参数（headers、params）
3. 提取响应示例和状态码
4. 验证必需字段完整性

**Phase 4: 增量更新**
1. 计算文件MD5值
2. 比对文件变更
3. 只处理新增或修改的文件
4. 更新接口信息缓存

### Frontend (if applicable)
无前端组件。

### Backend (if applicable)

- **Module Structure**:
  ```
  src/scanner/
  ├── __init__.py
  ├── interface_scanner.py    # 主扫描器类
  ├── parsers/
  │   ├── __init__.py
  │   ├── json_parser.py      # JSON解析器
  │   └── yaml_parser.py      # YAML解析器
  ├── validators/
  │   ├── __init__.py
  │   └── schema_validator.py # Schema验证器
  └── models/
      └── interface.py        # 接口模型
  ```

- **Core Classes**:
  - InterfaceScanner: 主扫描器，负责目录扫描和文件解析
  - JSONParser: JSON格式解析器
  - YAMLParser: YAML格式解析器
  - SchemaValidator: 接口文档Schema验证器
  - Interface: 接口信息数据模型

- **API Specifications**:
  ```python
  class InterfaceScanner:
      def __init__(self, root_path: str):
          """初始化接口扫描器"""

      def scan(self) -> List[Interface]:
          """扫描目录并返回接口列表"""

      def parse_file(self, file_path: str) -> Interface:
          """解析单个接口文档文件"""

      def validate_schema(self, data: dict) -> bool:
          """验证接口文档Schema"""

      def get_file_hash(self, file_path: str) -> str:
          """计算文件MD5值"""
  ```

- **Data Model**:
  ```python
  @dataclass
  class Interface:
      name: str              # 接口名称
      method: str            # HTTP方法
      url: str              # 接口URL
      service: str          # 服务类型（user/nurse/admin）
      module: str           # 模块名称
      headers: dict         # 请求头
      params: dict          # 请求参数
      response: dict        # 响应示例
      file_path: str        # 文档文件路径
      last_modified: float  # 文件修改时间
  ```

### Common

#### Performance Optimization
- 使用多线程并发解析文件
- 缓存已解析的接口信息
- 延迟加载大文件

#### Testing Strategy
- 单元测试：文件解析、Schema验证
- 集成测试：目录扫描、增量更新
- 性能测试：大量文件的扫描性能

## Dependencies

### Task Dependencies
- 依赖任务001：项目目录结构和接口文档目录创建

### External Dependencies
- pyyaml：YAML解析库
- hashlib：MD5计算（文件变更检测）

## Effort Estimate

- **Size**: M
- **Hours**: 6-7 hours
- **Risk**: Medium

### Size Reference
M (1-2d): 中等复杂度，包含目录扫描、文件解析、验证等多个功能

## Definition of Done

### Code Complete
- [ ] InterfaceScanner类实现完成
- [ ] JSON和YAML解析器实现完成
- [ ] Schema验证器实现完成
- [ ] 增量更新机制实现完成
- [ ] 错误处理和日志记录完善

### Tests Pass
- [ ] 单元测试覆盖率>80%
- [ ] 集成测试全部通过
- [ ] 性能测试达标（1000文件<10秒）

### Docs Updated
- [ ] 接口扫描模块API文档
- [ ] 接口文档格式规范

### Deployment Verified
- [ ] 本地测试环境验证完成
- [ ] 扫描准确率验证完成
- [ ] 增量更新功能验证完成