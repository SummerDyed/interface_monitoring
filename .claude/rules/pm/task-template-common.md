# Task Template - Common Structure

> **Universal task file structure (for both frontend and backend)**

---

## 1. File Naming

**Format**: `{number}-{title}.md`
**Examples**: `001-user-login.md`, `002-data-list-page.md`
**Rules**: 3-digit number + hyphen + concise title (≤20 chars)

---

## 2. Frontmatter Structure

```yaml
---
name: Task title
status: open | in-progress | completed
created: 2025-11-13T10:30:00Z
updated: 2025-11-13T15:45:00Z
github: ""
depends_on: []
parallel: true
deprecated: false
---
```

### Field Descriptions

- `name` (string): Task title
- `status` (enum): open / in-progress / completed
- `created` (datetime): ISO 8601 format
- `updated` (datetime): ISO 8601 format
- `github` (string): Issue URL or empty string
- `depends_on` (array): Dependent task numbers `["001", "003"]`
- `parallel` (boolean): Can be developed in parallel
- `deprecated` (boolean): Is deprecated

### Optional Fields (Deprecated Tasks)

```yaml
deprecated: true
deprecated_at: 2025-11-13T10:30:00Z
deprecated_reason: "Feature merged into task #005"
```

### Optional Fields (Conflict Detection)

```yaml
conflicts_with: ["003", "007"]
```

---

## 3. Task File Structure

```markdown
---
[frontmatter]
---

# {Task Title}

## Features (WHAT)

[One-sentence description]

### Core Features
- Feature 1
- Feature 2

### User Value (WHY)
[Why build? What problem does it solve?]

## User Workflow (HOW - User Perspective)

[Detailed interaction steps, see core-principles.md section 2]

## UI Elements Checklist

[Pages/Components/Dialogs/Forms/Feedback]

## Acceptance Criteria

### Feature Acceptance
- [ ] Main flow complete
- [ ] Boundary conditions correct
- [ ] Exceptions have prompts

### Interaction Acceptance
- [ ] Timely operation feedback
- [ ] Clear success/failure prompts
- [ ] Empty state has guidance

### Quality Acceptance
- [ ] Meets project standards
- [ ] Test coverage ≥ 90%
- [ ] No lint errors

## Technical Details

[Frontend/Backend technical details, see task-template-tech.md]

## Dependencies

### Task Dependencies
- Depends on #001: XXX

### External Dependencies
- Third-party library: XXX v1.2.3

## Effort Estimate

- **Size**: XS / S / M / L / XL
- **Hours**: X-Y hours
- **Risk**: Low / Medium / High

### Size Reference

- XS (2-4h): Simple modification
- S (4-8h): Single page/simple feature
- M (1-2d): Multiple pages/medium complexity
- L (2-3d): Complex feature/multiple modules
- XL (3-5d): Core feature/architecture design

## Definition of Done

### Code Complete
- [ ] Feature implemented and committed
- [ ] Code review passed
- [ ] No TODO left

### Tests Pass
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete

### Docs Updated
- [ ] API docs (if applicable)
- [ ] Component docs (if applicable)
- [ ] README (if new dependencies)

### Deployment Verified
- [ ] Local environment verified
- [ ] Dev environment deployed
- [ ] Feature available in Dev
```

---

## 4. Status Management

### Status Definitions

- `open`: Not started, all checkboxes `[ ]`
- `in-progress`: In progress, some `[x]` some `[ ]`
- `completed`: Complete, all checkboxes `[x]`

### Status Flow

```
open → in-progress → completed
  ↓                      ↓
  └──────────────────────┘ (rollback allowed)
```

### Epic Mark Mapping

- `- ✅ Feature A` → `status: completed`
- `- [x] Task B` → `status: completed`
- `- [ ] Feature C` → `status: open`

---

## 5. Content Update Strategy

### KEEP

**Condition**: similarity ≥ 0.85 OR status is completed/in-progress
**Action**: No modification, log only

### UPDATE (Smart Merge)

**Condition**: similarity < 0.85 AND status is open
**Actions**:
- Update `updated` timestamp
- Keep existing implementation details
- Add new content from Epic
- Deduplicate to avoid repetition

### CREATE

**Condition**: Exists in Epic but file not exists
**Action**: Extract info from Epic to generate new file

### ORPHAN

**Condition**: File exists but not in Epic
**Action**: Auto-mark as deprecated

```yaml
deprecated: true
deprecated_at: [current time]
deprecated_reason: "Not found in epic.md"
```

---

## 6. Similarity Algorithm

### Comparison Fields

- `name`: Title text
- `Features`: Core feature description
- `User Workflow`: Interaction steps
- `Dependencies`: Task & external dependencies
- `Technical Details`: Tech specs (Component/API/State/SQL/Model)

### Composite Similarity

```
similarity = (title × 0.3) + (features × 0.2) + (workflow × 0.2) + (deps × 0.15) + (specs × 0.15)
```

### Tech Spec Diff

If existing task missing ≥2 tech specs from Epic → force UPDATE

### Decision Thresholds

- ≥ 0.85: Highly similar → KEEP
- < 0.85: Needs update → UPDATE
- Missing ≥2 specs: Force UPDATE

---

## 7. GitHub Sync

### Not Synced

```yaml
github: ""
```

### Synced

```yaml
github: "https://github.com/owner/repo/issues/123"
```

Synced by `/pm:epic-sync` command.

---

## 8. Important Notes

### ✅ Should

- Use ISO 8601 timestamps (call `datetime.md`)
- Consistent frontmatter field order
- Status synced with checkboxes
- Clear user workflows

### ❌ Should Not

- Manually write timestamps
- Mix status marks
- Put technical details in common template
- Create oversized tasks (> XL should be split)

---

## 9. Related Rules

- **Frontend/Backend**: `task-template-tech.md`
- **Timestamps**: `datetime.md`
- **Decomposition**: `core-principles.md`

---

**Note**: When executing this rule, AI should generate task files in Chinese for team collaboration.
