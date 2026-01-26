---
allowed-tools: Bash, Read, Write, LS
---

# Code Quality

对 Issue 关联的代码变更执行质量检测与评分。

## Usage

```
/pm:code-quality <issue_number> [--fix] [--report] [--github]
```

## 输入

- **`<issue_number>`** - Issue 编号，如 `265`

## 数据来源

1. **任务文件**: `.claude/epics/<epic_name>/$ARGUMENTS.md`
2. **分析文件**: `.claude/epics/<epic_name>/issues/$ARGUMENTS/analysis.md`
3. **进度文件**: `.claude/epics/<epic_name>/issues/$ARGUMENTS/progress.md`

从上述文件中提取 commit hash，解析关联的改动文件列表。

## 可选参数

- `--fix` - 执行安全修复（格式化、import 排序）
- `--report` - 输出报告到 issue 目录下
- `--github` - 评论 Issue 并打标签

---

## Role Definition

**You are a Quality Automation Engineer.** Your job is to:
1. Execute automated quality checks (linter, coverage, complexity, duplication, standards)
2. Collect and aggregate metrics from various tools
3. Score code changes against defined criteria
4. Generate actionable reports

You do NOT make subjective judgments. You run tools, measure data, and report facts.

---

## Workflow

### Step 0: 环境检测与文件解析

**目标**: 识别项目类型，解析目标文件列表

**检测项目类型**（按优先级）:
- `pubspec.yaml` → Flutter/Dart
- `package.json` → Node.js (JS/TS)
- `pyproject.toml` / `requirements.txt` → Python
- `go.mod` → Go
- 其他 → Unknown

**解析目标文件**:
1. 读取 `analysis.md` 和 `progress.md`
2. 提取 commit hash（7-40位十六进制）
3. 通过 `git show --name-only` 获取每个 commit 的改动文件
4. 过滤出代码文件（`.dart`, `.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.go`）
5. 去重得到最终文件列表

**输出**: `✓ 目标文件数: {count} | 项目: {type}`

**错误处理**:
- 任务文件不存在 → 终止
- analysis.md 不存在 → 终止
- 无关联 commit → 终止
- 无代码文件 → 终止

---

### Step 1: Linter 检测 (25分)

**目标**: 检测静态代码问题

**方法**: 根据项目类型选择对应 linter 工具执行分析

| 项目类型 | 推荐工具 |
|---------|---------|
| Flutter | `flutter analyze` |
| Node.js | `eslint` |
| Python  | `ruff` / `flake8` |
| Go      | `golangci-lint` |

**评分标准**:
| 条件 | 得分 |
|------|------|
| 无 error 且无 warning | 25 |
| 无 error，warning ≤5 | 23 |
| 无 error，warning ≤10 | 20 |
| error ≤3 | 15 |
| error ≤10 | 10 |
| error >10 | 5 |

**降级策略**: 工具不存在时跳过，给满分

---

### Step 2: Coverage 检测 (25分)

**目标**: 评估测试覆盖率

**方法**: 运行测试并收集覆盖率报告

| 项目类型 | 推荐方式 |
|---------|---------|
| Flutter | `flutter test --coverage` + lcov |
| Node.js | `npm test -- --coverage` |
| Python  | `pytest --cov` |
| Go      | `go test -coverprofile` |

**评分标准**:
| 平均覆盖率 | 得分 |
|-----------|------|
| ≥90% | 25 |
| ≥80% | 22 |
| ≥70% | 18 |
| ≥60% | 14 |
| ≥50% | 10 |
| <50% | 5 |

**额外输出**: 列出覆盖率 <90% 的文件

**降级策略**: 无法检测时给满分

---

### Step 3: Complexity 检测 (20分)

**目标**: 识别代码复杂度问题

**检测项**:
1. **深嵌套**: 缩进 ≥4层（16空格）的控制语句 (`if`, `for`, `while`, `switch`, `try`)
2. **长函数**: 函数体 >50行

**评分标准**:
| 问题数 | 得分 |
|-------|------|
| 0 | 20 |
| ≤3 | 17 |
| ≤6 | 14 |
| ≤10 | 10 |
| >10 | 5 |

---

### Step 4: Duplication 检测 (15分)

**目标**: 检测代码重复

**方法**: 使用 `jscpd` 或类似工具检测重复代码块（最小5行）

**评分标准**:
| 重复率 | 得分 |
|-------|------|
| <3% | 15 |
| <5% | 13 |
| <10% | 10 |
| <15% | 7 |
| ≥15% | 3 |

**降级策略**: 工具不存在时给满分

---

### Step 5: Standards 检测 (15分)

**目标**: 检查命名规范

**检测项**:
| 语言 | 文件名规范 | 类名规范 |
|-----|-----------|---------|
| Dart | snake_case | PascalCase |
| TS/JS | kebab-case / camelCase | PascalCase |
| Python | snake_case | PascalCase |
| Go | snake_case | - |

**评分标准**:
| 问题数 | 得分 |
|-------|------|
| 0 | 15 |
| ≤3 | 13 |
| ≤6 | 10 |
| ≤10 | 7 |
| >10 | 3 |

---

### Step 6: 汇总与输出

**计算总分**:
```
总分 = Linter + Coverage + Complexity + Duplication + Standards
```

**等级划分**:
| 总分 | 等级 |
|-----|------|
| ≥90 | A |
| 80-89 | B |
| 70-79 | C |
| 60-69 | D |
| <60 | F |

**输出格式**:
```
===== 代码质量报告 =====
总分: {score}/100 | 等级: {grade}
Linter={x}/25 | Coverage={x}/25 | Complexity={x}/20 | Dup={x}/15 | Standards={x}/15
低覆盖(<90%): {file_list}
```

---

### Step 7: 可选操作

#### `--fix` 自动修复

根据项目类型执行安全修复:
- **Flutter**: `dart format` + `dart fix --apply`
- **Node.js**: `eslint --fix`
- **Python**: `black` / `ruff format`
- **Go**: `gofmt -w`

#### `--report` 生成报告

输出到 `.claude/epics/<epic_name>/issues/$ARGUMENTS/reports/quality_{YYYYMMDD_HHMMSS}.md`:
```yaml
---
issue: {number}
generated: {timestamp}
score: {score}/100
grade: {grade}
---
# 评分摘要
- Linter: {x}/25
- Coverage: {x}/25
- Complexity: {x}/20
- Duplication: {x}/15
- Standards: {x}/15

## 覆盖率缺口
{files_below_90%}

## 问题详情
{linter_issues}
{complexity_issues}
{standards_issues}
```

#### `--github` 同步 GitHub

1. 发布评论（含评分表格）
2. 移除旧的 `quality/*` 标签
3. 添加新标签 `quality/{grade}`

---

## 原则

- **宽容降级**: 工具缺失时跳过并给满分，不阻塞流程
- **安全修复**: `--fix` 只做格式化等无风险操作
- **环境自适应**: 根据实际环境选择可用工具

