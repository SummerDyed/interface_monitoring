---
allowed-tools: Bash, Read, Write, LS, Task
---

# Epic Sync

Synchronize epic tasks with GitHub Issues in sequential order.

## Synchronization Objective

**Maintain 1:1 consistency between local task files and GitHub Issues.**

- Each local task file → Exactly one GitHub Issue
- All content and status must match between local and GitHub
- Tasks processed in strict sequential order (001 → 002 → 003...)
- Never parallelize or batch operations

### File Naming Convention

**Task files MUST be named using the format: `{issue_id}-{title}.md`**

Examples:
- `123-implement_authentication.md` - GitHub Issue #123
- `456-database_architecture.md` - GitHub Issue #456
- `789-frontend_interface.md` - GitHub Issue #789

**Sync Behavior:**
1. **Before first sync**: Files use sequential numbers: `001-task_name.md`, `002-task_name.md`
2. **After ANY sync**: Files are renamed to: `{issue_id}-{title}.md`
3. **Consistency**: File name MUST ALWAYS reflect the current GitHub Issue ID and title
4. **Rename enforcement**: 
   - **CREATE**: Rename immediately after Issue creation
   - **UPDATE**: Check and rename if needed during update
   - **SYNCED**: Check and rename if needed even when content unchanged
   - This check is MANDATORY in every sync operation, not optional

## Usage

```
/pm:epic-sync <feature_name> [--check-only | --sync-all]
```

**Arguments:**
- `<feature_name>`: Epic directory name under `.claude/epics/`
- `--check-only`: Dry-run mode, show what would be synced without making changes
- `--sync-all`: (Default) Automatic sync mode, fully automated execution

**Default behavior**: `--sync-all` (fully automated, sequential execution, no user interaction)

## Core Principles

### Separation of Concerns

GitHub synchronization is separate from task decomposition:
- `epic-decompose`: Only manages local task files (fully automated)
- `epic-sync`: Only manages GitHub Issue synchronization (fully automated)

### Sequential Execution Guarantee

- All sync operations MUST be executed in strict sequential order by task number (001, 002, 003, ...)
- Never batch or parallelize sync operations
- Each task sync must complete before proceeding to the next
- This ensures predictable state and prevents race conditions

### Automation Guarantee

Both tools execute without any user interaction or prompts. All decisions are made automatically based on epic content and task state.

---

## Execution Workflow

### Step 1: Validate Environment

**Objective**: Verify GitHub CLI availability and repository access.

**Operations:**

1. **Check GitHub CLI installation**
   - Tool: `Bash`
   - Command: `command -v gh`
   - If not found: Exit with error "GitHub CLI (gh) is not installed. Install from: https://cli.github.com/"

2. **Check GitHub authentication**
   - Tool: `Bash`
   - Command: `gh auth status`
   - If not authenticated: Exit with error "Not authenticated with GitHub. Run: gh auth login"

3. **Verify repository access**
   - Tool: `Bash`
   - Command: `gh repo view`
   - If no access: Exit with error "No repository access or not in a git repository"

4. **Safety check: Prevent CCPM template sync**
   - Tool: `Bash`
   - Command: `git remote get-url origin`
   - If remote URL contains "ccpm" or "automazeio": Exit with error "Syncing to CCPM template repository is not allowed"

**Output**: Environment validated, ready to proceed.

---

### Step 2: Load Epic and Task Data

**Objective**: Load epic metadata and all task files from the epic directory.

**Operations:**

1. **Verify epic exists**
   - Tool: `Read`
   - File: `.claude/epics/{feature_name}/epic.md`
   - If not found: Exit with error "Epic not found"

2. **Extract epic metadata**
   - Tool: `Read`
   - File: `.claude/epics/{feature_name}/epic.md`
   - Extract fields from frontmatter:
     - `name:` → EPIC_NAME
     - `github:` → EPIC_GITHUB_URL (may be empty)
     - `last_sync:` → EPIC_LAST_SYNC (ISO 8601 timestamp, may be empty)
   - Display: "📋 Epic: {EPIC_NAME}"
   - Display: "🔗 GitHub: {EPIC_GITHUB_URL or 'Not yet synced'}"

3. **Load all task files**
   - Tool: `LS` then `Read`
   - Directory: `.claude/epics/{feature_name}/`
   - List all `.md` files, exclude `epic.md` and `github-mapping.md`
   - For each task file, extract from frontmatter:
     - Task number (from filename or frontmatter)
     - `name:` → task_name
     - `status:` → task_status
     - `github:` → task_github (may be empty)
     - `updated:` → task_updated (ISO 8601 timestamp)
   - Store task data structure: `task_num|task_name|task_status|task_github|task_updated|task_file_path`

**Output**: 
- EPIC_NAME, EPIC_GITHUB_URL, EPIC_LAST_SYNC
- Array of all task data

---

### Step 3: Analyze Sync Status (Automated Decision)

**Objective**: Determine if sync is needed and proceed automatically.

**Decision Logic:**

1. **Check for tasks needing sync**:
   - Count tasks with empty `github:` field AND status = "open" (need CREATE)
   - Count tasks with non-empty `github:` field AND task_updated > EPIC_LAST_SYNC (need UPDATE)
   - Count tasks with non-empty `github:` field AND task_updated <= EPIC_LAST_SYNC (already SYNCED)
   - Total sync needed = CREATE count + UPDATE count
   
2. **Automated decision**:
   - If EPIC_LAST_SYNC is empty OR total sync needed > 0:
     - If EPIC_GITHUB_URL is not empty:
       - Display: "⚠️  Epic already synced to GitHub: {EPIC_GITHUB_URL}"
     - Display: "ℹ️  Found {total_sync_needed} task(s) needing sync ({CREATE_count} new, {UPDATE_count} updates)."
     - Display: "Auto-proceeding with sync (no user interaction required)"
     - Continue to Step 4
   - Else (EPIC_LAST_SYNC exists AND total sync needed = 0):
     - Display: "✅ All tasks are already synced and up-to-date."
     - Display: "Auto-exiting (no action needed)"
     - Exit with success

**Output**: Decision made, proceed or exit.

---

### Step 4: Sort and Determine Sync Strategy

**Objective**: Process tasks in sequential order and determine action for each task.

**CRITICAL CONSTRAINT**: Process tasks in strict sequential order (001 → 002 → 003 → ...). Never parallelize.

**Operations:**

1. **Sort tasks by number**
   - Sort task array by task_num (numeric sort)
   - Ensure processing order: 001, 002, 003, ...

2. **Determine strategy for each task** (in sorted order):
   
   For each task, determine action based on:
   
   - **Action: CREATE**
     - Condition: task_github is empty AND task_status = "open"
     - Meaning: New task needs GitHub Issue creation
   
   - **Action: UPDATE**
     - Condition: task_github is not empty AND task_updated > EPIC_LAST_SYNC
     - Meaning: Existing Issue needs content update
   
   - **Action: SYNCED**
     - Condition: task_github is not empty AND task_updated <= EPIC_LAST_SYNC
     - Meaning: Already in sync, no action needed
   
   - **Action: SKIP**
     - Condition: task_github is empty AND task_status != "open"
     - Meaning: Completed task not yet synced, skip it

3. **Display sync plan**:
   - Display: "📋 Processing tasks in sequential order..."
   - For each task: Display "→ Task #{task_num}: {action}"

**Output**: Sorted task list with determined action for each.

---

### Step 5: Execute Sync Operations (Sequential)

**CRITICAL CONSTRAINTS**: 
1. Execute all sync operations in the order determined by Step 4. Each operation must complete before starting the next.
2. **MANDATORY FILE RENAMING**: For EVERY task (CREATE, UPDATE, SYNCED), MUST check and ensure filename follows `{issue_id}-{title}.md` format. This is NOT optional.

**Operations:**

Display: "🔄 Executing sync operations in sequential order..."

**Process each task in sequence:**

For each task in sorted order:

#### Action: CREATE (Create new GitHub Issue)

1. **Read task content**
   - Tool: `Read`
   - File: {task_file_path}
   - Extract frontmatter and body content
   - Strip frontmatter from body (GitHub Issue body should NOT contain frontmatter)

2. **Create GitHub Issue**
   - Tool: `Bash`
   - Command: `gh issue create --title "[{task_num}] {task_name}" --body "{body}" --label "epic:{feature_name}"`
   - Capture output to extract issue URL
   - Alternative: Use `gh issue create ... --json url` and parse JSON output
   - Title format: `[001] Task Name`
   - Label: `epic:{feature_name}` (if label exists, otherwise create without label)
   - Capture: issue_url from output (extract from command output or JSON)

3. **Extract Issue ID**
   - From issue_url, extract numeric ID at end
   - Example: `https://github.com/owner/repo/issues/123` → issue_id = 123

4. **Update task file frontmatter**
   - Tool: `Read` then `Write`
   - File: {task_file_path}
   - Update field: `github: {issue_url}`
   - Use atomic write pattern: write to temp file, then move

5. **Rename task file**
   - Tool: `Bash`
   - Old name: `001-task_name.md` (or `{task_num}-{task_name}.md`)
   - New name: `{issue_id}-{task_name}.md`
   - Command: `mv {old_path} {new_path}`

6. **Display result**:
   - Display: "  ✅ Created: {issue_url}"
   - Display: "  📝 Renamed: {old_filename} → {new_filename}"

#### Action: UPDATE (Update existing GitHub Issue)

1. **Extract Issue number**
   - From task_github URL, extract numeric ID
   - Example: `https://github.com/owner/repo/issues/456` → issue_num = 456

2. **Read task content**
   - Tool: `Read`
   - File: {task_file_path}
   - Extract frontmatter and body content
   - Strip frontmatter from body

3. **Update GitHub Issue**
   - Tool: `Bash`
   - Command: `gh issue edit {issue_num} --body "{body}"`
   - Only update body content, title remains unchanged

4. **MANDATORY: Ensure filename consistency**
   - Expected filename: `{issue_num}-{task_name}.md`
   - Current filename: from task_file_path
   - **MUST rename if different**: Use `mv` command to rename file
   - This is NOT optional - all synced files MUST follow `{issue_id}-{title}.md` format

5. **Display result**:
   - Display: "  ✅ Updated: {issue_url}"
   - If renamed: Display: "  📝 Renamed: {old_filename} → {new_filename}"

#### Action: SYNCED (Already synced)

1. **MANDATORY: Ensure filename consistency**
   - Expected filename: `{issue_num}-{task_name}.md`
   - Current filename: from task_file_path
   - **MUST rename if different**: Use `mv` command to rename file
   - Even if content is synced, filename MUST match `{issue_id}-{title}.md` format

2. **Display result**:
   - Display: "✓ Task #{task_num}: Already synced"
   - If renamed: Display: "  📝 Renamed: {old_filename} → {new_filename}"

#### Action: SKIP (Skip completed task)

- Display: "⏭️  Task #{task_num}: Skipped"
- No operations needed

#### Rate Limiting Protection

After each CREATE or UPDATE operation:
- Tool: `Bash`
- Command: `sleep 0.5`
- Purpose: Respect GitHub API rate limits

**Track results:**
- Count successful operations
- Count failed operations
- Continue to next task even if current task fails

**Output**: All tasks processed, counts of success/failure.

---

### Step 6: Update Epic Sync Timestamp

**Objective**: Record the sync completion time in epic metadata.

**Operations:**

1. **Get current UTC timestamp**
   - Tool: `Bash`
   - Command: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
   - Format: ISO 8601 (example: `2025-11-05T10:30:45Z`)
   - **IMPORTANT**: Must use `.claude/rules/datetime.md` for correct timestamp generation

2. **Update epic.md frontmatter**
   - Tool: `Read` then `Write`
   - File: `.claude/epics/{feature_name}/epic.md`
   - Update field: `last_sync: {current_timestamp}`
   - Use atomic write pattern: write to temp file, then move

3. **Display result**:
   - Display: "✅ Epic sync timestamp updated: {current_timestamp}"

**Output**: Epic sync timestamp updated.

---

### Step 7: Display Summary

**Objective**: Show complete sync results.

**Display format:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 GitHub Sync Complete: {feature_name}

Operations:
- 🆕 Created: {create_count} new issues
- 🔄 Updated: {update_count} existing issues
- ✅ Synced: {synced_count} already in sync
- ⏭️  Skipped: {skipped_count} skipped
- 📝 Renamed: {rename_count} files to {issue_id}-{title}.md format

Results:
- ✅ Successful: {success_count}
- ❌ Failed: {failure_count}

Next steps:
- View issues: gh issue list --label 'epic:{feature_name}'
- View epic: {EPIC_GITHUB_URL}
- Continue working: /pm:issue-start {feature_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Output**: Summary displayed.

---

### Step 8: Update GitHub Mapping File

**Objective**: Keep `github-mapping.md` synchronized with actual GitHub Issues and task files.

**Operations:**

1. **Check if github-mapping.md exists**
   - Tool: `Read`
   - File: `.claude/epics/{feature_name}/github-mapping.md`
   - If not found: Skip this step (file may not exist yet)

2. **Update task entries for all synced tasks**
   - For each task that was CREATED, UPDATED, or SYNCED (with filename change):
     - Extract: issue_id, issue_url, task_name, task_status, task_file_path
     - Update the corresponding entry in github-mapping.md:
       - Replace placeholder text like "pending GitHub Issue" or "(待创建 GitHub Issue)" with actual issue URL
       - Update file name from `{task_num}-{name}.md` to `{issue_id}-{name}.md` if changed
       - Update status if changed
       - Update documentation paths if needed (issues/{issue_id}/...)

3. **Update summary statistics**
   - Update task counts (Completed, Open, Deprecated)
   - Update file-to-issue mapping table
   - Update critical path with issue numbers
   - Update architecture evolution section

4. **Update sync metadata**
   - Update "Last Updated" timestamp
   - Update "Last Epic Sync" timestamp
   - Add sync operation details to "Changes" section
   - Record created/updated issue numbers

5. **Update Next Steps section**
   - Mark completed actions (e.g., "✅ Issue created")
   - Update file paths if renamed

6. **Display result**:
   - Display: "✅ GitHub mapping file updated: github-mapping.md"

**Update Pattern:**

For each task entry, update:
```markdown
- #295: Database Consistency Validation Task ⏳ **Pending**
  - URL: https://github.com/owner/repo/issues/295
  - File: 295-database_consistency_validation.md
  - Status: open
```

**File-to-Issue Mapping Table:**
```markdown
295-database_consistency_validation.md → #295 ⏳ 🔴
```

**Sync Metadata:**
```markdown
## Synced
- **Last Updated**: {current_timestamp}
- **Command**: /pm:epic-sync {feature_name}
- **Last Epic Sync**: {current_timestamp}
- **Changes**:
  - ✅ Epic sync completed
  - ✅ Created new Issue: #295 (Database Consistency Validation Task)
  - ✅ Updated {count} existing Issues
  - ✅ File renamed: {old_name} → {new_name}
```

**Output**: GitHub mapping file updated with latest sync information.

---

## Error Handling

### GitHub API Errors

**Rate Limiting:**
- If `gh issue create` returns "rate limit" error:
  - Display: "⚠️  GitHub API rate limit exceeded"
  - Display: "Please wait before retrying or use --check-only mode"
  - Exit with error

**Permission Errors:**
- If `gh issue create` returns "permission" error:
  - Display: "❌ Error: Insufficient permissions to create issues"
  - Display: "Check your GitHub repository access and permissions"
  - Exit with error

**Network Errors:**
- If `gh issue list` fails:
  - Display: "⚠️  Network error: Cannot connect to GitHub"
  - Display: "Check your internet connection and try again"
  - Exit with error

### Task-Level Error Handling

**Continue on error strategy:**
- If one task sync fails, log the error
- Continue with next task in sequence
- Report all failures in final summary

**File operation errors:**
- If file rename fails after successful Issue creation:
  - Display: "⚠️  Created but rename failed: {issue_url}"
  - Mark as partial failure
  - Continue with next task

---

## Data Integrity Guarantees

### Sequential Execution
- Process tasks in strict order (001 → 002 → 003...) to maintain consistency
- Never parallelize or batch operations
- Each task sync must complete before processing next task

### One-to-One Mapping
- Each local task file corresponds to exactly one GitHub Issue
- File name reflects Issue ID: `{issue_id}-{title}.md`
- GitHub URL stored in task frontmatter `github:` field

### Atomic Operations
- All file writes use atomic pattern: write to temp file, then move
- Pattern: `{file}.tmp` → `mv {file}.tmp {file}`
- Prevents partial writes and corruption

### Consistency Guarantee

After successful sync, local task state always matches GitHub Issue state:
- **Content matches**: Task file body = GitHub Issue body
- **Status matches**: Task status reflects Issue state
- **File name matches**: `{issue_id}-{title}.md` format
- **Metadata matches**: `github:` field contains correct Issue URL

### Frontmatter Handling

**Critical rule**: When syncing to GitHub, frontmatter MUST be stripped from body content.

- GitHub Issue body should only contain markdown content
- Frontmatter (YAML between `---` lines) stays in local file only
- See `.claude/rules/strip-frontmatter.md` for implementation details

---

## Check-Only Mode

When `--check-only` flag is provided:

**Behavior:**
1. Execute Steps 1-4 normally
2. In Step 5: Do NOT execute any sync operations
3. Display what WOULD be done:
   - "Would create Issue for Task #001: {name}"
   - "Would update Issue #123 for Task #002: {name}"
   - "Task #003 already synced"
4. Skip Step 6 (no timestamp update)
5. Skip Step 8 (no github-mapping.md update)
6. Display summary showing planned operations

**Purpose**: Dry-run mode for validation without making changes.

---

## Required Rules

Before executing this workflow, read:

1. **`.claude/rules/github-operations.md`**
   - GitHub CLI operations
   - Repository protection rules
   - Issue creation patterns

2. **`.claude/rules/datetime.md`**
   - HIGHEST PRIORITY rule
   - Getting real system date/time for timestamps
   - ISO 8601 format requirements

3. **`.claude/rules/strip-frontmatter.md`**
   - Removing frontmatter before GitHub sync
   - Preserving frontmatter in local files

4. **`.claude/rules/frontmatter-operations.md`**
   - Working with YAML frontmatter
   - Atomic update patterns

---

## Workflow Constraints Summary

**MUST:**
- Process tasks in sequential order (001 → 002 → 003...)
- **ALWAYS ensure ALL task files use `{issue_id}-{title}.md` format** - check and rename in EVERY sync operation (CREATE, UPDATE, SYNCED)
- Strip frontmatter before syncing to GitHub
- Use atomic file writes (temp file + move)
- Sleep 0.5s between GitHub API calls
- Continue on single task failure
- Update epic `last_sync` timestamp after successful sync
- **Update `github-mapping.md` after sync operations** - keep file-to-issue mapping synchronized

**MUST NOT:**
- Parallelize or batch sync operations
- Sync to CCPM/automazeio repositories
- Include frontmatter in GitHub Issue body
- Prompt user for decisions (fully automated)
- Stop execution if one task fails

**GUARANTEES:**
- 1:1 mapping between local files and GitHub Issues
- File names always match Issue IDs
- Content consistency after sync
- Atomic operations prevent corruption
- `github-mapping.md` reflects current sync state
