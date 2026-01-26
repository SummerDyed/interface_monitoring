---
allowed-tools: Bash, Read, Write, LS, WebFetch
---

# Epic Start

智能启动并执行 Epic 任务，具备依赖分析、进度追踪、质量门控等高级能力。

## Usage
```
/pm:epic-start <epic_name> [--resume] [--dry-run] [--parallel-check]
```

**Options:**
- `--resume`: 从上次中断处继续执行
- `--dry-run`: 仅分析，不实际执行
- `--parallel-check`: 检查可并行执行的任务

## 🔴 MANDATORY PRE-FLIGHT CHECKS

### 1. Environment Validation

```bash
# 1.1 验证 GitHub CLI 认证状态
gh auth status || echo "❌ GitHub CLI not authenticated. Run: gh auth login"

# 1.2 验证 epic 存在
test -f .claude/epics/$ARGUMENTS/epic.md || { echo "❌ Epic not found. Run: /pm:prd-parse $ARGUMENTS"; exit 1; }

# 1.3 验证 GitHub 同步状态
grep -q "github:" .claude/epics/$ARGUMENTS/epic.md || { echo "❌ Epic not synced. Run: /pm:epic-sync $ARGUMENTS first"; exit 1; }

# 1.4 检查未提交更改
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ You have uncommitted changes. Please commit or stash them first."
  git status --short
  exit 1
fi

# 1.5 验证当前分支状态
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Current branch: $current_branch"

# 1.6 检查远程同步状态
git fetch origin --quiet
if [ "$(git rev-list HEAD...origin/$current_branch --count 2>/dev/null)" != "0" ]; then
  echo "⚠️ Branch out of sync with remote. Consider: git pull --rebase"
fi
```

### 2. Resume Detection

检查是否存在中断的执行状态：
```bash
execution_file=".claude/epics/$ARGUMENTS/execution-status.md"
if [ -f "$execution_file" ]; then
  echo "📋 Found existing execution status"
  # 读取上次执行状态
  last_status=$(grep -E "^status:" "$execution_file" | head -1 | cut -d: -f2 | tr -d ' ')
  last_issue=$(grep -E "^current_issue:" "$execution_file" | head -1 | cut -d: -f2 | tr -d ' ')
  
  if [ "$last_status" = "in_progress" ]; then
    echo "🔄 Previous execution was interrupted at Issue #$last_issue"
    echo "   Use --resume to continue, or delete $execution_file to start fresh"
  fi
fi
```

## Instructions

### 1. Build Dependency Graph & Categorize Issues

**Objective:** 构建完整的依赖图并智能分类任务

**1.1 读取所有任务文件：**
```bash
# 获取所有任务文件
task_files=$(find .claude/epics/$ARGUMENTS -maxdepth 1 -name "[0-9]*.md" -type f | sort -V)
```

**1.2 解析每个任务的元数据：**
对于每个任务文件，提取：
- `issue_number`: 从文件名获取
- `status`: frontmatter 中的状态
- `depends_on`: 依赖的 issue 列表
- `priority`: 优先级 (P0-P3)
- `effort`: 工作量估算
- `github_state`: GitHub issue 的实际状态

**1.3 构建依赖图：**
```
Dependency Graph:
├── #101 (Ready) - 无依赖
├── #102 (Ready) - 无依赖  
├── #103 (Blocked) - 依赖 #101
├── #104 (Blocked) - 依赖 #101, #102
└── #105 (Blocked) - 依赖 #103, #104
```

**1.4 智能分类：**

| Category | Criteria | Action |
|----------|----------|--------|
| **🟢 Ready** | 无未满足依赖，status=pending/todo | 可立即开始 |
| **🟡 In Progress** | status=in_progress | 检查是否需要继续 |
| **🔴 Blocked** | 有未完成的依赖 | 显示阻塞原因 |
| **⚪ Completed** | status=completed/closed | 跳过 |
| **🟣 Needs Analysis** | 无 analysis.md | 需先运行分析 |

**1.5 检测可并行任务：**
```bash
# 识别没有相互依赖的就绪任务
# 这些任务理论上可以并行处理（在不同分支）
parallel_candidates=$(analyze_parallel_tasks "$task_files")
if [ -n "$parallel_candidates" ]; then
  echo "💡 Parallel-capable issues detected: $parallel_candidates"
  echo "   Consider using separate branches for parallel development"
fi
```

### 2. Pre-Execution Analysis

**Objective:** 确保所有就绪任务都有完整的技术分析

**2.1 检查分析文件：**
```bash
for issue in $ready_issues; do
  analysis_file=".claude/epics/$ARGUMENTS/issues/$issue/analysis.md"
  if [ ! -f "$analysis_file" ]; then
    echo "⚠️ Missing analysis for #$issue - Creating..."
    # 自动触发分析
    # /pm:issue-analyze $issue
  else
    # 验证分析完整性
    required_sections=("Technical Approach" "Affected Files" "Implementation Plan")
    for section in "${required_sections[@]}"; do
      grep -q "## $section" "$analysis_file" || echo "⚠️ #$issue analysis missing: $section"
    done
  fi
done
```

**2.2 生成工作量摘要：**
```
📊 Epic Workload Summary:
  Total Issues: 8
  Ready: 3 (est. 12h)
  Blocked: 4 (est. 20h)  
  Completed: 1
  
  Estimated Total Remaining: 32h
  Critical Path: #101 → #103 → #105 (16h)
```

### 3. Initialize Execution Tracking

**Objective:** 创建详细的执行状态文件

**3.1 创建/更新 execution-status.md：**

```markdown
---
epic: $ARGUMENTS
started: {ISO 8601 datetime}
updated: {ISO 8601 datetime}
status: in_progress
branch: {current_branch}
current_issue: null
total_issues: {count}
completed_count: 0
estimated_remaining_hours: {total_hours}
---

# 🚀 Epic Execution Status: $ARGUMENTS

## Progress Overview
```
[██░░░░░░░░] 20% (2/10 issues completed)
Estimated remaining: 24h
Critical path: #103 → #105 → #108
```

## Current Session
- **Started**: {datetime}
- **Branch**: {branch_name}
- **Working on**: Issue #{issue} - {title}

## Issue Queue

### 🟢 Ready (No Dependencies)
| Issue | Title | Priority | Effort | Analysis |
|-------|-------|----------|--------|----------|
| #101 | Feature A | P1 | 4h | ✅ |
| #102 | Feature B | P2 | 3h | ✅ |

### 🟡 In Progress
| Issue | Title | Started | Last Update |
|-------|-------|---------|-------------|
| #103 | Feature C | 2024-01-15 | 10 min ago |

### 🔴 Blocked
| Issue | Title | Blocked By | Unblocks |
|-------|-------|------------|----------|
| #104 | Feature D | #101, #102 | #106 |
| #105 | Feature E | #103 | #107, #108 |

### ⚪ Completed
| Issue | Title | Completed | Duration |
|-------|-------|-----------|----------|
| #100 | Setup | 2024-01-14 | 2h |

## Execution Log
- [{timestamp}] Epic execution started
- [{timestamp}] Issue #101 started
- [{timestamp}] Issue #101 completed (2h 15m)
- [{timestamp}] Issues #103, #104 unblocked
```

### 4. Smart Issue Selection

**Objective:** 智能选择下一个要处理的任务

**4.1 选择算法：**

优先级排序规则（按顺序应用）：
1. **Resume check**: 如果有 --resume 且存在中断的任务，继续该任务
2. **Critical path**: 位于关键路径上的任务优先
3. **Unblock potential**: 能解锁更多任务的优先
4. **Priority level**: P0 > P1 > P2 > P3
5. **Effort**: 工作量小的优先（快速获得进展）
6. **Dependency depth**: 被依赖次数多的优先

**4.2 选择输出：**
```
🎯 Selected Next Issue: #101 - "Implement user authentication"

Selection Rationale:
  ✓ No unmet dependencies
  ✓ On critical path (blocks 3 other issues)
  ✓ Priority: P1
  ✓ Estimated effort: 4h
  ✓ Analysis complete and verified
  
Alternatives available:
  - #102 (P2, 3h) - Not on critical path
  - #106 (P1, 2h) - Blocked by #101
```

### 5. Execute Issue Workflow

**Objective:** 执行单个任务的完整工作流

**5.1 Pre-Issue Checks：**
```bash
# 确认工作区干净
test -z "$(git status --porcelain)" || { echo "❌ Uncommitted changes detected"; exit 1; }

# 验证分析文件存在且完整
test -f ".claude/epics/$ARGUMENTS/issues/$issue/analysis.md" || { echo "❌ Analysis missing"; exit 1; }

# 更新执行状态
update_execution_status "current_issue" "$issue"
```

**5.2 执行 issue-start：**
```bash
echo "🔧 Starting Issue #$issue: $title"
echo "   Analysis: .claude/epics/$ARGUMENTS/issues/$issue/analysis.md"
echo "   Task: .claude/epics/$ARGUMENTS/$issue.md"
echo ""
echo "Executing: /pm:issue-start $issue"
# 调用 issue-start 命令
```

**5.3 Quality Gates (Post-Issue)：**

完成任务后，验证以下质量门：
```bash
# Gate 1: 所有测试通过
flutter test || npm test || pytest  # 根据项目类型

# Gate 2: Linter 零错误
flutter analyze || npm run lint || pylint

# Gate 3: 覆盖率达标 (≥90%)
coverage_check "$issue"

# Gate 4: progress.md 已更新
test -f ".claude/epics/$ARGUMENTS/issues/$issue/progress.md" || echo "⚠️ Missing progress.md"

# Gate 5: GitHub issue 已同步
gh issue view $issue --json state | grep -q '"state":"' || echo "⚠️ GitHub sync needed"
```

### 6. Update Progress & Continue

**Objective:** 更新进度并处理下一个任务

**6.1 Issue 完成处理：**
```bash
# 更新 execution-status.md
echo "- [$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Issue #$issue completed" >> "$execution_file"

# 更新统计
completed_count=$((completed_count + 1))
update_execution_status "completed_count" "$completed_count"
update_execution_status "current_issue" "null"

# 检查新解锁的任务
newly_unblocked=$(check_unblocked_issues "$issue")
if [ -n "$newly_unblocked" ]; then
  echo "🔓 Issues unblocked by #$issue: $newly_unblocked"
fi

# 同步 GitHub Epic 进度
gh issue comment {epic_number} --body "Progress Update: Issue #$issue completed ($completed_count/$total_issues)"
```

**6.2 继续下一个任务：**
```bash
# 重新评估就绪队列
ready_issues=$(get_ready_issues)

if [ -z "$ready_issues" ]; then
  if [ "$completed_count" -eq "$total_issues" ]; then
    echo "🎉 All issues completed! Epic finished."
    finalize_epic
  else
    echo "⏸️ No ready issues. All remaining issues are blocked."
    show_blocked_status
  fi
else
  # 选择并开始下一个任务
  next_issue=$(select_next_issue "$ready_issues")
  echo "➡️ Proceeding to next issue: #$next_issue"
  # 循环回步骤 5
fi
```

### 7. Finalize Epic (When All Complete)

**Objective:** Epic 完成后的收尾工作

```bash
# 7.1 更新 execution-status.md
update_execution_status "status" "completed"
update_execution_status "completed_at" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# 7.2 生成完成报告
generate_completion_report

# 7.3 更新 GitHub Epic
gh issue comment {epic_number} --body "🎉 Epic Completed!

All $total_issues issues have been resolved.

Summary:
- Total time: {duration}
- Issues completed: $total_issues
- Test coverage: {avg_coverage}%

Ready for final review and merge."

# 7.4 提示后续操作
echo "
🎉 Epic Complete: $ARGUMENTS

Next steps:
  1. Review all changes: gh pr list --search 'epic:$ARGUMENTS'
  2. Merge epic: /pm:epic-merge $ARGUMENTS
  3. Close epic: /pm:epic-close $ARGUMENTS
"
```

## Output Format

### Startup Output
```
🚀 Epic Execution: $ARGUMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 Environment:
   Branch: feature/epic-$ARGUMENTS
   Git Status: Clean ✓
   GitHub CLI: Authenticated ✓

📊 Epic Overview:
   Total Issues: 10
   ├── 🟢 Ready: 3
   ├── 🟡 In Progress: 1
   ├── 🔴 Blocked: 5
   └── ⚪ Completed: 1
   
   Estimated Remaining: 28h
   Critical Path: #101 → #103 → #107 (14h)

🎯 Starting Issue: #101 - "User Authentication"
   Priority: P1
   Effort: 4h
   Blocks: #103, #104, #105
   Analysis: ✅ Complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Executing: /pm:issue-start 101
```

### Progress Update Output
```
✅ Issue #101 Completed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Progress: [████░░░░░░] 40% (4/10)

🔓 Newly Unblocked:
   - #103: API Integration
   - #104: Data Models

🎯 Next Issue: #102 - "User Profile"
   Priority: P2
   Effort: 3h
   
⏱️ Time Spent: 3h 45m
⏱️ Estimated Remaining: 24h 15m

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Continue? [Y/n/skip/pause]
```

## Error Handling

### Environment Errors
```
❌ Pre-flight Check Failed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Issues Found:
   1. Uncommitted changes in working directory
   2. Branch out of sync with remote

💡 Resolution:
   git add . && git commit -m "WIP: Save current work"
   git pull --rebase origin main
   
Or to stash and continue:
   git stash push -m "epic-start stash"
```

### Execution Errors
```
❌ Issue #103 Failed Quality Gates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Failed Gates:
   ✗ Test coverage: 72% (required: 90%)
   ✗ Linter: 3 errors

💡 Options:
   1. Fix issues: /pm:issue-start 103 --continue
   2. Skip and proceed: epic-start --skip 103
   3. Mark as blocked: /pm:blocked 103 "Coverage issue"

📋 Execution paused. Status saved to:
   .claude/epics/$ARGUMENTS/execution-status.md
```

### Recovery
```
🔄 Resume Available
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Previous execution was interrupted:
  - Last issue: #103
  - Status: in_progress
  - Time: 2024-01-15 14:30:00

💡 Options:
   1. Resume: /pm:epic-start $ARGUMENTS --resume
   2. Start fresh: rm .claude/epics/$ARGUMENTS/execution-status.md
   3. View status: /pm:epic-status $ARGUMENTS
```

## Important Notes

### Workflow Principles
- **Sequential by default**: 按依赖顺序逐个处理任务
- **Quality first**: 必须通过所有质量门才能继续
- **Persistent state**: 执行状态持久化，支持中断恢复
- **Auto-sync**: 自动同步 GitHub issue 状态

### Best Practices
- 每个任务完成后立即提交
- 保持 execution-status.md 实时更新
- 遇到阻塞及时标记并处理
- 定期 pull 远程更新避免冲突

### Integration Points
- **issue-start**: 任务执行的核心入口
- **issue-analyze**: 任务分析（如缺失则自动触发）
- **epic-status**: 查看当前进度
- **epic-close**: Epic 完成后关闭

### Language Notes
- **UI/Output**: 使用中文，便于团队沟通
- **Code/Commands**: 使用英文（标准实践）
- **Documentation**: 可中英混合，技术术语保持英文

