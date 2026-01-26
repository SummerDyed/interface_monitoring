# 自动发现功能测试指南

## 🎯 测试目标

验证 `/pm:issue-commit` 命令的自动发现功能是否正常工作。

---

## 📋 测试环境准备

### 前置条件
- ✅ 已安装 GitHub CLI (`gh`)
- ✅ 已登录 GitHub (`gh auth login`)
- ✅ 在 Git 项目中
- ✅ 有权限创建 issue 和推送代码

---

## 🧪 测试用例 1: 从分支名自动发现

### 步骤

```bash
# 1. 创建一个带 issue 编号的分支
git checkout -b feature/123-user-authentication
# 或
git checkout -b issue-456-payment-fix

# 2. 在该分支上做一些代码修改
echo "# Test change" >> test_file.md
git add test_file.md
git commit -m "Initial test commit"

# 3. 运行自动发现提交命令
/pm:issue-commit

# 4. 预期输出
🔍 Auto-discovered issue from branch: #123
✓ Issue verified: {"number":123,"title":"用户认证功能","state":"open"}
✓ Changes detected, proceeding with commit
✓ Branch validated: feature/123-user-authentication
✓ Found task in epic: authentication
```

### 验证点
- [ ] 是否显示 "🔍 Auto-discovered issue from branch: #123"
- [ ] 是否验证 issue 存在
- [ ] 是否继续正常的提交流程

---

## 🧪 测试用例 2: 从提交信息自动发现

### 步骤

```bash
# 1. 切换到普通分支（不带编号）
git checkout -b feature/user-profile

# 2. 创建包含 issue 引用的提交
echo "# Profile page" >> profile.md
git add profile.md
git commit -m "Add user profile page - Issue #789"

# 3. 运行自动发现命令
/pm:issue-commit

# 4. 预期输出
🔍 Auto-discovered issue from recent commit: #789
✓ Issue verified: {"number":789,...}
...
```

### 验证点
- [ ] 是否显示 "🔍 Auto-discovered issue from recent commit: #789"
- [ ] 是否正确从提交信息中提取编号

---

## 🧪 测试用例 3: 多种提交格式

### 测试提交格式

```bash
# 格式1: Issue #123
git commit -m "Fix login bug - Issue #123"

# 格式2: Closes #456
git commit -m "Add password reset (Closes #456)"

# 格式3: Fixes #789
git commit -m "Update UI components (#789)"

# 格式4: Resolves #101
git commit -m "Resolve memory leak - Resolves #101"

# 运行命令
/pm:issue-commit
```

### 验证点
- [ ] 所有格式都能正确识别 issue 编号
- [ ] 使用第一个匹配的编号

---

## 🧪 测试用例 4: 自动回退到手动输入

### 步骤

```bash
# 1. 切换到不带编号的分支
git checkout -b develop

# 2. 运行自动发现命令
/pm:issue-commit

# 3. 预期输出
⚠ No related issue found automatically.
Please provide issue number manually: [光标等待输入]

# 4. 输入 issue 编号
123

# 5. 继续正常流程
✓ Issue verified: {"number":123,...}
...
```

### 验证点
- [ ] 是否提示手动输入
- [ ] 输入后是否继续正常流程

---

## 🧪 测试用例 5: 手动指定模式（兼容性）

### 步骤

```bash
# 直接指定 issue 编号（原有模式）
/pm:issue-commit 999

# 预期输出（不显示自动发现消息）
✓ Issue verified: {"number":999,...}
...
```

### 验证点
- [ ] 手动指定时跳过自动发现
- [ ] 兼容原有使用方式

---

## 🧪 测试用例 6: 分支名中的多个编号

### 步骤

```bash
# 分支名包含多个数字（只取第一个）
git checkout -b feature/123-and-456-login
/pm:issue-commit

# 预期输出
🔍 Auto-discovered issue from branch: #123
```

### 验证点
- [ ] 是否只取第一个编号
- [ ] 忽略后续数字

---

## 🚨 错误场景测试

### 场景 1: 无效分支名

```bash
git checkout -b feature/new-function
/pm:issue-commit

# 应该回退到手动输入
⚠ No related issue found automatically.
Please provide issue number manually: _
```

### 场景 2: issue 不存在

```bash
git checkout -b feature/999999-unknown
/pm:issue-commit

# 在验证步骤会失败
🔍 Auto-discovered issue from branch: #999999
✗ Cannot access issue #999999. Check number or run: gh auth login
```

### 场景 3: 非数字内容

```bash
git checkout -b feature/abc-def
/pm:issue-commit
# 回退到手动输入
```

---

## 📊 测试结果记录表

| 测试用例 | 预期结果 | 实际结果 | 状态 |
|---------|---------|---------|------|
| 分支名自动发现 | 显示 🔍 消息并提取编号 | ⏳ | - |
| 提交信息自动发现 | 显示 🔍 消息并提取编号 | ⏳ | - |
| 多种提交格式 | 都能识别 | ⏳ | - |
| 自动回退 | 提示手动输入 | ⏳ | - |
| 手动指定兼容性 | 跳过自动发现 | ⏳ | - |
| 多编号分支 | 取第一个编号 | ⏳ | - |
| 无效分支名 | 回退手动输入 | ⏳ | - |
| 不存在的 issue | 验证失败提示 | ⏳ | - |

---

## 🎯 成功标准

所有测试用例通过的条件：
1. ✅ 自动发现功能能正确从分支名提取编号
2. ✅ 自动发现功能能正确从提交信息提取编号
3. ✅ 自动发现失败时能正确回退到手动输入
4. ✅ 手动指定模式完全兼容
5. ✅ 错误场景有合适的处理和提示

---

## 🐛 问题反馈

如果发现问题，请记录：
1. 具体的操作步骤
2. 实际输出 vs 预期输出
3. 错误信息
4. 环境信息（Git 版本、GitHub CLI 版本等）

---

## 💡 测试技巧

### 1. 使用干净的测试仓库
```bash
git init test-repo
cd test-repo
git remote add origin <your-repo-url>
```

### 2. 快速创建测试 issue
```bash
gh issue create --title "Test Issue $(date +%s)" --body "Auto-discovery test"
```

### 3. 使用临时分支
```bash
git checkout -b test/auto-discovery-$(date +%s)
```

### 4. 查看 Git 日志
```bash
git log --oneline -5  # 查看最近的提交
git branch -a         # 查看所有分支
```

---

## 🎉 测试完成后

测试通过后，您应该能够：
- ✨ 享受零手动输入的便捷提交
- 🎯 确保所有代码变更正确关联 issue
- 📝 保持清晰的提交历史追踪
- 🚀 提升团队开发效率

---

*测试指南创建时间: 2025-11-05*
*适用于: `/pm:issue-commit` 命令 v2.0+*
