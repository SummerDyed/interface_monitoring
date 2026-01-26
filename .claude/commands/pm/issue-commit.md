---
allowed-tools: Bash, Read, Write, Grep, Glob, Edit, LS
---

# Issue Commit

Commit changes with proper categorization and link to GitHub issue.

## Usage

**Auto-discovery mode** (recommended):
```
/pm:issue-commit
```
- Auto-extracts issue number from branch name or recent commits
- Prompts for manual input if not found

**Manual mode**:
```
/pm:issue-commit <issue_number>
```
- Directly specify issue number
- Use when issue number is known

## Required Rules

Before executing this command, read and follow:
- `.claude/rules/github-operations.md` - For GitHub CLI operations
- `.claude/rules/standard-patterns.md` - For validation patterns

## Quick Check

Execute these checks in parallel for performance:

1. **Auto-discover issue number** (if not provided):
   - Method 1: Extract from branch name (e.g., `feature/123`, `issue-456`)
   - Method 2: Extract from recent commit messages
   - If both fail: Prompt user for manual input

2. **Validate issue number**:
   - Must be numeric format
   - Verify issue exists on GitHub: `gh issue view $ARGUMENTS`
   - Exit if invalid or inaccessible

3. **Check for uncommitted changes**:
   ```bash
   git status --porcelain
   ```
   If empty: "✗ No changes to commit. Working tree is clean."

4. **Verify not on main/master branch**:
   ```bash
   current_branch=$(git branch --show-current)
   ```
   If main/master: "✗ Cannot commit directly to main/master branch"

5. **Find local task file** (optional):
   - Search for `.claude/epics/*/$ARGUMENTS.md`
   - If not found, search frontmatter for `github:.*issues/$ARGUMENTS`
   - Validate file path safety and writability
   - If found: Extract epic name for later updates
   - If not found: Proceed without task file update

## Instructions

### 1. Analyze Changed Files

Categorize all changed files by type:

```bash
git status --porcelain
```

**Categories:**
- Source files: `.ts`, `.js`, `.py`, `.go`, `.rs`, etc. (excluding tests)
- Test files: Files matching `*test*`, `*spec*`, `.test.`, `.spec.`
- Config files: `.json`, `.yaml`, `.yml`, `.toml`, `.env`
- Documentation: `.md`, `.txt`, `.rst`, `.adoc`
- Other: Everything else

Display categorization summary:
```
Changes to commit:

Source files: {count}
Test files: {count}
Config files: {count}
Documentation: {count}
Other files: {count}

Total: {count} files modified
```

### 2. Review Changes

Show detailed changes for user review:
```bash
git status -s
git diff --stat
```

### 3. Stage Changes

**Auto-execute**: Stage all files
```bash
git add -A
```

Note: Automatically stages all changed files - the most common and recommended approach for focused commits.

### 4. Create Commit Message

Build commit message with issue context:

Get issue details:
```bash
gh issue view $ARGUMENTS --json title --jq '.title'
```

Build and auto-commit with standard message format:
```
Issue #$ARGUMENTS: {issue_title}

Changes:
- {Summarize main changes}

Related to: #$ARGUMENTS
```

**Auto-execute**: Create commit with generated message
```bash
git commit -m "Issue #$ARGUMENTS: {issue_title}

Changes:
- {Summarize main changes}

Related to: #$ARGUMENTS"
```

Note: Automatically uses standardized commit message format with issue reference and change summary.

### 5. Verify Commit

Show commit summary:
```bash
git log -1 --oneline
git show --stat HEAD
```

### 6. Update Task Status

If local task file exists and is writable:

**Check current status:**
```bash
grep "^status:" "$task_file"
```

**Update if needed:**
- If status is not `in_progress`: Update frontmatter to `status: in_progress`
- Create backup before modification
- Restore from backup if update fails

**Add commit reference:**
Append to task file:
```markdown

## Commits
- {git log -1 --oneline HEAD}
```

### 7. Push to Remote

**Auto-execute**: Automatically push to remote repository

Check if remote branch exists:
```bash
git ls-remote --heads origin $(git branch --show-current)
```

If first push (remote branch doesn't exist):
```bash
git push -u origin $(git branch --show-current)
```

If subsequent push (remote branch exists):
```bash
git push origin $(git branch --show-current)
```

Handle errors gracefully:
- If push rejected due to remote changes: Suggest `git pull --rebase`
- If auth required: Show `gh auth login` command
- For other errors: Display error message and suggest manual resolution

Note: Automatic push keeps remote repository in sync and serves as backup.

### 8. Output Summary

```
✓ Commit completed and pushed to remote

Issue: #$ARGUMENTS - {issue_title}
Branch: {current_branch}
Commit: {commit_hash}
Remote: origin/{current_branch}

Files committed:
  Source: {count}
  Tests: {count}
  Config: {count}
  Docs: {count}

Next steps:
- Continue work: Make more changes and run /pm:issue-commit again
- Complete task: When ready, run /pm:issue-close $ARGUMENTS
- View changes: git log --oneline -5
```

## Best Practices

1. **Commit frequently** - Small, focused commits are easier to review
2. **One issue per commit** - Don't mix changes from different issues
3. **Auto-execution first** - Zero human interaction for standard workflows
4. **Standard format** - Consistent commit messages with issue references
5. **Update task status** - Keep local task file in sync with work
6. **Validate inputs** - Always check issue numbers and file paths for safety
7. **Use parallel checks** - Quick Check steps can run concurrently for speed
8. **Maintain backups** - Critical file operations include rollback capability
9. **Auto-push enabled** - Keeps remote in sync and serves as automatic backup

## Common Issues

### Issue Not Found
```
✗ Cannot access issue #$ARGUMENTS
Solution: Check issue number or run: gh auth login
```

### No Changes to Commit
```
✗ No changes to commit. Working tree is clean.
Solution: Make changes first, or check: git status
```

### Commit on Main Branch
```
✗ Cannot commit directly to main/master branch
Solution: Create feature branch: git checkout -b feature/$ARGUMENTS
```

### Push Rejected
```
✗ Push failed - remote has changes
Solution: Pull first: git pull --rebase origin {branch}
Then: git push origin {branch}
```

## Important Notes

- **Zero interaction**: Fully automated workflow from staging to push
- Always commit with issue reference for traceability
- Never commit directly to main/master
- Auto-push keeps remote repository in sync
- Update task status to reflect progress
- **Security first**: Input validation prevents injection attacks
- **Error recovery**: All critical operations include backup/rollback
- **Performance**: Use parallel Quick Check execution when possible
- **File safety**: Always validate file paths and permissions before writing

## Auto-Discovery Examples

### From Branch Name
```
feature/123-add-auth      → Issue #123
issue-456                 → Issue #456
bugfix/789-fix-login      → Issue #789
```

### From Commit Messages
```
"Issue #123: Add authentication"  → Issue #123
"Closes #456"                     → Issue #456
"Fix #789"                        → Issue #789
```
