---
allowed-tools: Bash, Read, Write, LS, Task
---

# Epic Decompose

将 Epic 拆解为可执行的任务文件，支持前后端项目的差异化处理。

## Usage

```bash
/pm:epic-decompose <feature_name>
```

---

## Core Concept

> Feature decomposition + UI/UX first, technical details second

- Epic: high-level feature description
- Task: executable units (1-3 days)
- Frontend: components, interactions, UI/UX
- Backend: APIs, database, business logic

---

## Role Definition

**You are a senior software engineer with 10 years of development experience (NOT a system architect).** Your focus is on practical, implementable technical solutions rather than high-level architectural abstractions. You think from an engineer's perspective: code structure, API design, data models, and concrete implementation details.

---

## Execution Principles

### ⚠️ CRITICAL: Rules Are MANDATORY, Not Optional

**规则不是"参考"，而是"必须执行"**

- Every rule in this document and referenced files (core-principles.md, task-template-*.md) **MUST** be followed
- No shortcuts, no assumptions, no "good enough" implementations
- Each rule exists to prevent defects or ensure quality
- **Ignoring a rule means the task decomposition is incomplete**

### Why Strict Adherence Matters

Based on real execution experience:

❌ **What happens when rules are ignored**:
- Technical details missing from tasks (e.g., API specs not included)
- Tasks become non-executable (developers can't implement without external docs)
- Quality degradation (inconsistent task structure)
- Hidden technical debt (unclear requirements)

✅ **What happens when rules are followed**:
- Every task is self-contained with complete technical details
- Developers can implement without cross-referencing external docs
- Consistent task quality across the project
- Reduced execution errors and rework

### Examples of Mandatory Requirements

1. **Technical Details MUST Include**:
   - API Specifications (endpoint, method, params, response)
   - Data Models (for backend tasks)
   - Component Structure (for frontend tasks)
   - Business Logic (implementation approach)

2. **Each Task MUST Be**:
   - Independently verifiable (1-3 days of work)
   - User-value focused (not just tech implementation)
   - Self-contained (no external dependencies for understanding)

3. **No Partial Implementation**:
   - Don't assume "API details are in Epic"
   - Don't skip "painful" technical details
   - Don't defer complex requirements to later

4. **Existence-First Principle (防重复)**:
   - If task file exists (by number/title/content match) → UPDATE or KEEP
   - Never CREATE a new task if similar file exists
   - Double-check before CREATE to prevent duplicates

**Remember**: The time invested in following rules during decomposition saves 10x time during implementation.

---

## Required Rules

Must read in order:

### 1. Core Principles
```
Read `.claude/rules/pm/core-principles.md`
```
Methodology, UI/UX guidelines, value prioritization, Epic-to-Task conversion

### 2. Common Template
```
Read `.claude/rules/pm/task-template-common.md`
```
Frontmatter, file structure, status management, naming, update strategy

### 3. Technical Template
```
Read `.claude/rules/pm/task-template-tech.md`
```
Frontend: Component/State/UI/UX; Backend: API/Database/Logic; Common: Performance/Testing

### 4. Task Structure Template
```
Read `.claude/rules/pm/task-template-structure.md`
```
**CRITICAL**: Defines mandatory task metadata structure  
- File, Purpose, Leverage, Requirements, Prompt (Role/Task/Restrictions/Success)  
- **Every task MUST include all 5 fields**  
- Validation will fail if any field is missing

### 5. Datetime
```
Read `.claude/rules/datetime.md`
```
ISO 8601 timestamp generation

---

## Workflow: Sequential Execution

Each step depends on previous output, strict sequential execution required.

```
Step 0: Preflight Check
   ↓
Step 1: Extract Tasks from Epic
   ↓
Step 2: Compare with Existing Tasks
   ↓
Step 3: Detect Conflicts
   ↓
Step 4: Execute Actions (KEEP/UPDATE/CREATE/DEPRECATE)
   ↓
Step 5: Validate & Report
   ↓
Step 6: GitHub Sync Check
```

---

## Concurrency Protection

### Lock Mechanism
- Lock file: `.claude/epics/<epic_name>/.decompose.lock`
- Timeout: 10 seconds
- Stale detection: Auto-clean locks older than 5 minutes
- Cleanup: Automatic lock release on exit

### Behavior
```
Detected ongoing decompose operation (PID: 12345)
Lock file: .claude/epics/feature-auth/.decompose.lock
Please wait 10 seconds or retry later
```

Why Sequential: Prevents concurrent modifications, each decision depends on previous results, ensures consistency.

---

## Execution Steps

### Step 0: Preflight Check

Validate Epic existence and assess current state.

1. Check Epic file: `.claude/epics/$ARGUMENTS/epic.md`
2. Check existing task files
3. Detect orphaned tasks (file exists but not in Epic)
4. Verify Epic frontmatter completeness
5. Warn if Epic status is `completed`

Output:
```
Epic file: .claude/epics/user-management/epic.md ✓
Existing tasks: 15
Orphaned tasks: 2 (will auto-deprecate)
Continue auto-execution...
```

---

### Step 1: Extract Tasks from Epic

Extract tasks and technical specs from Epic.

#### Sources

**Source 1: Technical Approach (feature list)**
```markdown
## Technical Approach
- ✅ Feature A (implemented)
  - Component: UserList
  - API: GET /api/users
  - State: useUserStore
- [ ] Feature B (pending)
  - Component: UserDetail
  - Route: /users/:id
```

**Source 2: Task Breakdown Preview (task list)**
```markdown
## Task Breakdown Preview
- [x] 001 - User list page
- [ ] 002 - User detail page
```

#### Tech Spec Extraction

Extract different specs by project type (see `core-principles.md` section 4.3):

- `Component:` Frontend only
- `Route:` Frontend only
- `State:` Frontend only
- `UI/UX:` Frontend only
- `API:` Both frontend & backend
- `SQL:` Backend only
- `Model:` Backend only

#### Task Metadata Extraction

**Required** task metadata fields (per `task-template-structure.md`):

| Field | Description | Example |
|-------|-------------|---------|
| **File** | Target file path | `src/services/AuthService.ts` |
| **Purpose** | One-line purpose statement | "Implement JWT authentication" |
| **Leverage** | Existing code to reuse | `src/utils/crypto.ts` |
| **Requirements** | Requirement IDs | `REQ-1.1, REQ-1.2` |
| **Prompt** | AI execution prompt | `Role: ... \| Task: ... \| Restrictions: ... \| Success: ...` |

**Prompt Structure**:
```
Role: {specific developer role}
Task: {clear task description with requirement refs}
Restrictions: {constraints and limitations}
Success: {measurable success criteria}
```

**Extraction Sources**:
- Epic's Technical Approach section
- Task descriptions and feature points
- If missing from Epic, generate intelligently based on task content

#### Merge Strategy
- Task Breakdown Preview: basic info (priority)
- Technical Approach: detailed tech specs + task metadata
- Merge and deduplicate

---

### Step 2: Compare with Existing Tasks

Determine operation type for each task: KEEP / UPDATE / CREATE

#### ⚠️ CRITICAL: Existence-First Principle

**Iron Rule**: If a task file exists (matched by number OR title), it MUST be UPDATE or KEEP, NEVER CREATE.

- **Purpose**: Prevent duplicate task creation
- **Enforcement**: CREATE operations require double-check that no existing file matches
- **Consequence**: Violating this creates duplicates and breaks Epic integrity

**Decision Flow**:
```
Epic Task → Check Existence
              ↓
         [File Exists?]
         ↙          ↘
       YES          NO
        ↓            ↓
   Compare       CREATE
   Similarity    (with double-check)
        ↓
   [High/Low?]
    ↙      ↘
  KEEP    UPDATE
  
❌ NEVER: Exists → CREATE (causes duplicates)
✅ ALWAYS: Exists → KEEP or UPDATE
```

#### Comparison Algorithm

For each task extracted from Epic:

1. **Check file existence** (mandatory first step)

   **Matching Rules** (OR logic, match any = exists):
   - **Number match**: `001` in Epic → check if `001-*.md` exists
   - **Title match**: Title similarity ≥ 0.70 with any existing task title
   - **Content match**: Feature description similarity ≥ 0.75

   **If ANY match found** → File exists, proceed to step 2  
   **If NO match found** → File does not exist, mark as CREATE candidate

2. **If exists → Deep content comparison** (determine KEEP vs UPDATE)

   **Fields to compare**:
   - `name`: title text
   - `功能点`: core features
   - `用户操作流程`: interaction steps
   - `UI 元素清单`: page/component/modal list
   - `Dependencies`: task & external deps
   - `Technical Details`: tech specs (Component/API/State/SQL/Model)
   - `Task Metadata`: File, Purpose, Leverage, Requirements, Prompt

   **Similarity formula**:
   ```
   similarity = (title × 0.3) + (features × 0.2) + (workflow × 0.2) + (deps × 0.15) + (specs × 0.15)
   ```

   **Each dimension calculation** (Jaccard coefficient):
   ```
   dimension_sim = matched_count / max(epic_count, existing_count)
   ```
   - `title`: keyword match after tokenization (ignore stopwords)
   - `features`: feature description match (same verb + object = match)
   - `workflow`: user operation steps match
   - `deps`: dependency items (Task ID / external services) match
   - `specs`: tech specs (Component/API/State/Model) match

   **Example**:
   ```
   Epic: [list, search, detail, delete]  Existing: [list, filter, detail]
   Matched: [list, detail] = 2, max(4,3) = 4
   features_sim = 2/4 = 0.50
   ```

   **Tech spec diff detection**:
   - Count new specs in Epic
   - If missing ≥2 specs → mark UPDATE

3. **Decision logic**

   **If file exists** (matched in step 1):
   - **KEEP**: similarity ≥ 0.85 OR status is completed/in-progress
   - **UPDATE**: similarity < 0.85 OR missing ≥2 specs AND status is open
   - ❌ **NEVER CREATE** if file exists

   **If file NOT exists** (no match in step 1):
   - **CREATE**: Generate new task file
   - ⚠️ Before creating, re-validate no similar file exists (防重复二次检查)

4. **Orphan detection**
   - File exists but not in Epic
   - Auto-mark as deprecated

Output:
```
Task 001: KEEP (similarity: 0.92, matched by number)
Task 002: UPDATE (similarity: 0.78, matched by title, missing 2 specs)
Task 003: CREATE (no match found, validated no duplicates)
Task 004: UPDATE (similarity: 0.65, matched by content, force update due to existence)
Task 099: ORPHAN (auto-deprecate)
```

**Note**: Task 004 shows even with low similarity (0.65), if file exists, it's UPDATE not CREATE.

---

### Step 3: Detect Conflicts

Identify similar tasks to prevent duplication.

#### Conflict Detection

1. For each task to create/update
2. Compare similarity with all existing tasks
3. If similarity 0.75-0.85 → mark as potential conflict
4. If similarity ≥ 0.85 → highly similar (consider merge)

#### Conflict Handling

- **No deletion**: Keep all existing tasks
- **Mark**: Add `conflicts_with: ["003", "007"]` to frontmatter
- **Log**: Output conflict details for manual review

Output:
```
Task 004: conflicts with Task 002 (similarity: 0.82)
  title: 0.90, desc: 0.78, deps: 0.75
  Added to conflicts_with field
```

---

### Step 4: Execute Actions

Apply KEEP/UPDATE/CREATE/DEPRECATE operations.

#### Operation Types

- **KEEP**: similarity ≥ 0.85 or completed → no file modification, log only
- **UPDATE**: similarity < 0.85 and open → smart merge (keep existing + add new)
- **CREATE**: file not exists → generate new task from Epic
  - ⚠️ **Pre-execution check**: Re-scan directory for matching files (防重复)
  - ⚠️ **Abort if found**: If similar file detected, convert to UPDATE instead
- **DEPRECATE**: orphaned task → mark `deprecated: true`

#### Smart Merge (UPDATE)

Merge rules:
1. Keep existing implementation details
2. Add new tech specs from Epic
3. **Ensure task metadata complete**: File, Purpose, Leverage, Requirements, Prompt
4. Deduplicate
5. Update `updated` timestamp
6. Don't overwrite completed parts

#### Atomic Writes

All file ops use temp files:
1. Write to task.md.tmp
2. Atomic move: mv task.md.tmp task.md
3. Rollback on failure
4. Cleanup temp files

---

### Step 5: Validate & Report

Validate completeness and generate report.

#### Validation Checks

- All Epic features have corresponding tasks
- Status marks correctly mapped (✅→completed, [ ]→open)
- No circular dependencies
- Completed tasks have all checkboxes `[x]`
- **Task metadata complete**: File, Purpose, Leverage, Requirements, Prompt (per `task-template-structure.md`)

#### GitHub Mapping

Create `.claude/epics/<feature_name>/github-mapping.md`:

```markdown
# GitHub Issue Mapping for Epic: <feature_name>

## File-to-Issue Mapping
001-user-list.md → #123 ✅
002-user-detail.md → #456 ✅
003-user-search.md → pending ⏳

## Synced
- Last Updated: 2025-11-13T16:00:00Z
- Command: /pm:epic-decompose <feature_name>
```

#### Summary Report

```
Epic decompose complete: User Management

Operation Summary:
- KEEP: 10 (content match)
- UPDATE: 3 (smart merge)
- CREATE: 2 (new in Epic)
- ORPHAN: 1 (auto-deprecate)
- Total: 15 tasks (12 open, 3 completed)

Technical Coverage:
- Frontend components: 8
- Backend APIs: 5
- UI/UX specs: complete
- Dependencies: mapped
- Task metadata: complete (File, Purpose, Leverage, Requirements, Prompt)

Data Integrity:
- Atomic writes: protected
- No data corruption
- Lock released

Next Steps:
1. Review auto-deprecated tasks
2. Run: /pm:epic-sync user-management
3. Commit: git add . && git commit -m 'docs: update tasks'
```

---

### Step 6: GitHub Sync Check

Prompt for next sync operation.

```
Epic decompose complete, GitHub sync required separately

Next Steps:
- Run: /pm:epic-sync user-management
- This creates/updates GitHub Issues
- Updates github-mapping.md file
```

---

## Project Type Handling

### Frontend

Priority focus:
- Component Structure
- State Management
- UI/UX Specifications
- Routing
- Performance Metrics

Template: Use frontend sections in `task-template-tech.md`

Tech stack examples: React, Vue, Angular, Flutter, React Native

---

### Backend

Priority focus:
- API Specifications
- Database Design
- Business Logic
- Error Handling
- Security Considerations

Template: Use backend sections in `task-template-tech.md`

Tech stack examples: Node.js, Go, Python, Java, C#, Ruby

---

### Fullstack

Use unified template `task-template-tech.md`, select sections by task type.

---

## Summary

1. Read 4 rule files (core-principles, common, tech, structure)
2. Execute 6-step workflow (Preflight → Extract → Compare → Detect → Execute → Report)
3. **Existence-First Principle** (防重复): If task exists → UPDATE/KEEP, never CREATE
4. **Required task metadata** (per `task-template-structure.md`): File, Purpose, Leverage, Requirements, Prompt
5. Fully automated (no user interaction)
6. Atomic write protection (data integrity)
7. Concurrency lock (prevent conflicts)
8. **中文输出**: 所有日志、报告、任务内容均使用中文

Final outputs:
- Task files (001-xxx.md, 002-xxx.md, ...)
- GitHub mapping file (github-mapping.md)
- Detailed execution logs (中文)
