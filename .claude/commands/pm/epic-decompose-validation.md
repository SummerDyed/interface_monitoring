---
allowed-tools: Bash, Read, LS, Grep, Edit, Multi-Edit, Find
---

# Epic Decompose Validation

> Validate that epic decomposition produces executable, self-contained tasks with complete technical details.

---

## Role Definition

**You are a senior software engineer with 10 years of development experience (NOT a system architect).** Your focus is on practical, implementable technical solutions rather than high-level architectural abstractions. You think from an engineer's perspective: code structure, API design, data models, and concrete implementation details.

---

## Required Rules

Read before validation:

```
Read `.claude/rules/pm/task-template-structure.md`
```

This template defines the **canonical task structure**:
- **File**: Target file path (e.g., `src/types/feature.ts`)
- **Purpose**: Clear one-line purpose statement
- **Leverage**: Existing code/utilities to reuse
- **Requirements**: Requirement IDs this task implements
- **Prompt**: AI execution prompt with `Role | Task | Restrictions | Success`

---

## Validation Objectives

1. **Completeness** - Every task contains all required fields (frontmatter, technical details, acceptance criteria)
2. **Self-Containment** - Tasks cannot reference external files (e.g., "see Epic.md"), must be independently understandable
3. **Executability** - Developers can implement immediately without additional clarification
4. **Consistency** - All tasks follow unified structure, conform to template specifications

---

## Validation Scope

### Target
- **Task Files**: All `NNN-*.md` files in epic directory (e.g., `001-task-name.md`)
- **NOT**: `epic.md`, `github-mapping.md`

### Success Criteria
- **ALL tasks pass** → Ready for `/pm:epic-sync`
- **ANY task fails** → Must fix before proceeding
- **100% coverage** → Every task validated

---

## Execution Steps

### Step 1: Scan Task Files

```bash
# 从项目根目录执行
find .claude/epics/$epic_name -name '[0-9][0-9][0-9]-*.md' -type f
```

Output: List all task files to validate (absolute paths).

### Step 2: Validate Each Task

Apply all validation checks to every task file.

**Validation Algorithm**:

```
FOR each task_file:
  1. Read file content
  2. Parse YAML frontmatter:
     - Extract required fields (name, status, created, updated, github, depends_on, parallel, deprecated)
     - Validate ISO 8601 date format
     - Check depends_on references valid task numbers
  3. Parse task body:
     - Extract File, Purpose, Leverage, Requirements, Prompt metadata
     - Validate Prompt format: Role | Task | Restrictions | Success
  4. Check Technical Details section exists:
     - If API task → verify API specification table present
     - If Backend task → verify Data Model + Database Schema
     - If Frontend/Flutter task → verify Component Structure + State Management
  5. Grep for external references:
     - Pattern: "(see|refer|check).*epic\.md" (case-insensitive)
     - Pattern: "TBD|TODO|to be determined" (in spec fields)
  6. Validate Acceptance Criteria:
     - Check for measurable metrics (%, ms, count)
     - Verify SMART criteria format
  7. Calculate score:
     - Each category worth max points
     - Deduct for missing/invalid items
     - Critical violations → automatic fail (<60)
  8. Store result with line numbers for issues
END FOR

Return: validation_report with per-task scores + issues
```

### Step 3: Cross-Task Checks

- Verify dependency graph (no cycles)
- Check consistency across tasks
- Validate complete epic coverage

### Step 4: Generate Report

Output validation results with pass/fail status and actionable fixes.

---

## Validation Checklist

### 1. Frontmatter (Required Fields)

```yaml
---
name: Task title
status: open | in-progress | completed
created: 2025-11-27T00:00:00Z
updated: 2025-11-27T00:00:00Z
github: ""
depends_on: []
parallel: false
deprecated: false
---
```

**Rules**:
- All fields present
- Valid ISO 8601 dates
- Valid `depends_on` task numbers

---

### 2. Task Metadata (per task-template-structure.md)

**Required Fields**:

| Field | Description | Example |
|-------|-------------|---------|
| **File** | Target file path | `src/services/AuthService.ts` |
| **Purpose** | One-line purpose | "Implement JWT authentication" |
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

**Rules**:
- All 5 metadata fields present
- File path is specific (not generic)
- Leverage references existing files
- Prompt follows Role/Task/Restrictions/Success format

---

### 3. Technical Details (CRITICAL)

**This is the most important validation.** Tasks must be immediately implementable.

#### For API Tasks

Must include complete API specification:

```markdown
### API Specification

**Endpoint**: `POST /api/v1/users/login`

**Request**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | yes | User email |
| password | string | yes | Password |

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Success Response** (200):
```json
{
  "token": "eyJhbG...",
  "user": { "id": 1, "email": "user@example.com" }
}
```

**Error Response** (401):
```json
{
  "error": "INVALID_CREDENTIALS",
  "message": "Email or password incorrect"
}
```
```

#### For Backend Tasks

Must include:
- **Data Model**: Go struct / TypeScript interface / Python class
- **Database Schema**: SQL CREATE TABLE with indexes
- **Business Logic**: Implementation approach with code examples
- **Error Handling**: Error codes and handling strategy

#### For Frontend Tasks

Must include:
- **Component Structure**: Hierarchy with props definition
- **State Management**: State shape, actions, reducers
- **Routing**: Route config, params, guards
- **UI/UX**: Interaction flows, validation rules

#### For Flutter/Dart Tasks

Must include:
- **Widget Structure**: StatelessWidget vs StatefulWidget, widget tree hierarchy
- **State Management**: Provider/Bloc/Riverpod pattern with state classes
- **Navigation**: Route names, arguments, MaterialPageRoute config
- **Pubspec Dependencies**: Required packages with version constraints (e.g., `flutter_bloc: ^8.1.0`)
- **Asset References**: Images, fonts, config files in `assets/` with pubspec.yaml registration
- **Platform Specifics**: iOS/Android-specific code using `Platform.isAndroid` checks if needed

**Example Flutter Widget Spec**:
```dart
// File: lib/src/features/auth/presentation/login_screen.dart
class LoginScreen extends StatefulWidget {
  final VoidCallback onLoginSuccess;
  const LoginScreen({Key? key, required this.onLoginSuccess}) : super(key: key);
}

// State Management (Bloc)
class LoginBloc extends Bloc<LoginEvent, LoginState> {
  final AuthRepository authRepository;
  // ...
}
```

#### For All Tasks

Must include:
- **Implementation Plan**: Phase breakdown, step-by-step
- **Testing Strategy**: Unit/integration test approach
- **Edge Cases**: Error scenarios and handling

**Rules**:
- Technical details section present
- API specs included if task involves API calls
- Code examples for complex logic
- No placeholders ("TBD", "to be determined")

---

### 4. Self-Containment (Zero External References)

Task must be independently implementable without reading other files.

**Invalid Patterns** (MUST NOT appear):
```
❌ "See Epic.md for API details"
❌ "Refer to PRD section 3.2"
❌ "Implementation similar to existing module"
❌ "Parameters TBD"
❌ "Details to be discussed"
❌ "Check design doc for specs"
```

**Rules**:
- Zero references to Epic.md or external docs
- All specs complete (no TBD fields)
- Standalone implementation possible

---

### 5. Acceptance Criteria

**Required Structure**:

```markdown
## Acceptance Criteria

### Feature Acceptance
- [ ] User can login with email/password
- [ ] JWT token expires after 24h
- [ ] Failed login shows error message

### Quality Acceptance
- [ ] Unit test coverage ≥ 90%
- [ ] API response time < 200ms
- [ ] No TypeScript errors
```

**Rules**:
- Criteria are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- No generic phrases ("works correctly", "functions properly")
- Metrics provided (%, ms, count)

---

### 6. Dependencies

**Task Dependencies**:
- Valid task numbers in `depends_on`
- No circular dependencies
- Appropriate granularity

**External Dependencies**:
- Specific library versions (not "latest")
- Full API URLs (not placeholders)
- Named services and integration points

---

### 7. Effort Estimate

**Required Fields**:
- **Size**: XS (2-4h) | S (4-8h) | M (1-2d) | L (2-3d) | XL (3-5d)
- **Hours**: Range estimate
- **Risk**: Low | Medium | High

---

### 8. Definition of Done

**Required Categories**:
- [ ] Code complete (no TODO/FIXME)
- [ ] Tests pass (unit + integration)
- [ ] Docs updated
- [ ] Deployment verified

---

## Error Handling

**File Reading Errors**:
- **Missing file**: Report as critical error, mark task as INVALID
- **Permission denied**: Skip with warning, require manual check
- **Encoding issues**: Attempt UTF-8 decode, fallback to ASCII

**Parsing Errors**:
- **Invalid YAML frontmatter**: Report line number, suggest fix
- **Malformed JSON in examples**: Non-critical warning, suggest correction
- **Corrupted markdown**: Attempt to parse sections individually

**Validation Failures**:
- **Timeout (>30s per task)**: Skip remaining checks, report partial results
- **Circular dependencies**: Detect using graph traversal, report cycle path
- **Missing Epic source**: Cannot auto-fix, mark items as `[NEEDS_EPIC_INPUT]`

**Recovery Strategy**:
```
IF file_read_error:
  → Log error, continue with next task
IF parse_error:
  → Report error with line number, continue validation
IF auto_fix_fails:
  → Mark field as [NEEDS_INPUT], add TODO comment
IF all_tasks_fail:
  → Generate diagnostic report, suggest Epic review
```

---

## Score Thresholds

| Score | Status | Action |
|-------|--------|--------|
| 90-100 | ✅ Excellent | Ready for implementation |
| 75-89 | ⚠️ Acceptable | Minor fixes recommended |
| 60-74 | ⚠️ Needs Work | Fix before implementation |
| <60 | ❌ Failed | Must fix before proceeding |

### Critical Violations (Automatic Fail)

- Missing API specifications for API tasks
- Missing Technical Details section
- External references to Epic.md (pattern: `(see|refer|check).*epic\.md`)
- Incomplete specs (TBD/TODO in required fields)
- Missing Prompt field or invalid format (must have Role|Task|Restrictions|Success)
- No Definition of Done
- Invalid YAML frontmatter (cannot parse)
- Missing required metadata fields (File, Purpose, Requirements)

---

## Report Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Epic Validation: <epic_name>
Generated: {timestamp}

Overall Score: {score}/100

Tasks: {total}
✅ Passed: {count}
⚠️  Warnings: {count}
❌ Failed: {count}

Critical Issues: {count}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Per-Task Results:

Task 001 - User Authentication
Score: 95/100 ✅
✅ Frontmatter: Complete
✅ Task Metadata: Complete (File, Purpose, Leverage, Requirements, Prompt)
✅ Technical Details: API specs included
✅ Self-Containment: No external refs
⚠️  Acceptance: Missing metrics

Task 003 - Permission Management  
Score: 45/100 ❌
❌ CRITICAL: Missing API specifications
❌ CRITICAL: External reference found ("see Epic.md")
❌ CRITICAL: Missing Prompt field

Action Required:
1. Add complete API specifications
2. Remove external references
3. Add Prompt with Role/Task/Restrictions/Success
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Auto-Remediation

This agent **automatically fixes** validation failures. No manual intervention required.

### Auto-Fix Process

When a task fails validation, the agent will:

1. **Identify the issue** from validation checklist
2. **Read Epic source** (`.claude/epics/<epic_name>/epic.md`) for missing content
3. **Apply fix** directly to the task file
4. **Re-validate** to confirm fix
5. **Report** what was fixed

### Fix Actions by Issue Type

| Issue | Auto-Fix Action |
|-------|----------------|
| Missing Frontmatter | Generate from task content + current timestamp |
| Missing Task Metadata | Extract File, Purpose, Leverage, Requirements from task body; Generate Prompt |
| Invalid Prompt Format | Restructure existing content to `Role \| Task \| Restrictions \| Success` |
| Missing API Specs | Extract from Epic's Technical Approach section |
| Missing Technical Details | Extract from Epic based on task type (Frontend/Backend/Flutter) |
| External Reference | **Inline** the referenced content from Epic into task |
| TBD/Placeholder | Extract actual value from Epic or mark as `[NEEDS_INPUT]` for user |
| Missing Acceptance Criteria | Generate SMART criteria from task's Core Features |
| Missing DoD | Add standard DoD template |
| Missing Flutter Specs | Extract widget/state management details from Epic, add pubspec dependencies |
| Invalid Date Format | Convert to ISO 8601 (YYYY-MM-DDTHH:MM:SSZ) |

### Fix Workflow

```
Step 1: Validate all tasks
   ↓
Step 2: For each failed task:
   ├─ Read Epic source
   ├─ Apply auto-fix
   └─ Write updated task file
   ↓
Step 3: Re-validate fixed tasks
   ↓
Step 4: Generate final report
   ├─ ✅ All passed → Ready for /pm:epic-sync
   └─ ❌ Some failed → List items requiring manual input
```

### Manual Input Required

Some issues cannot be auto-fixed and require user input:

- Missing API specs not found in Epic
- Business logic not documented
- Ambiguous requirements

These will be marked as `[NEEDS_INPUT]` in the task file with a TODO comment explaining what's needed.

---

## Usage

```bash
# Validate ALL tasks in epic
/pm:validate-epic <epic_name>

# Validate with auto-fix disabled (report only)
/pm:validate-epic <epic_name> --no-fix

# Validate specific task
/pm:validate-epic <epic_name> --task 001

# Workflow
/pm:epic-decompose feature → /pm:validate-epic feature → /pm:epic-sync feature
```

---

## Key Principle

> **After validation passes, every task file should be immediately actionable by any developer without asking "what does this mean?" or "where are the API specs?"**

The goal: Complete technical specifications in every task, zero ambiguity, zero external dependencies.

---

## Output Language

**中文输出**: All validation reports, logs, and error messages in Chinese.

---

## Performance Guidelines

- **Batch Processing**: Validate tasks in parallel where possible (max 5 concurrent)
- **Timeout**: 30s per task, 5min for entire epic
- **Caching**: Cache Epic source to avoid repeated reads
- **Incremental**: Only re-validate tasks modified since last run (check `updated` field)

---
