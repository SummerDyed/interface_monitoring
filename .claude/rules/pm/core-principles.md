# Epic Decompose - Core Principles

> **Core: Feature decomposition + UI/UX interaction first**

---

## 1. Feature Decomposition Principles

- **User perspective first**: Start from user needs
- **Independent delivery value**: Each task independently verifiable
- **Reasonable granularity**: 1-3 days of work
- **Testability**: Clear acceptance criteria

### Decomposition Steps

1. **Identify user stories**: As [role], I want [feature], so that [value]
2. **Split interaction flows**: Main flow + branch flows + edge cases
3. **Identify UI components**: New/modified pages and components
4. **Analyze technical dependencies**: APIs/state/third-party libraries

---

## 2. UI/UX Interaction Description Standards

### Required Elements

```markdown
### User Workflow
1. **Trigger**: User clicks "YY" button on XX page
2. **Interaction steps**:
   - Step 1: Open dialog
   - Step 2: Input information
   - Step 3: Validation rules
   - Step 4: Display feedback
3. **Navigation**: Success → navigate to XX, Failure → stay with prompt
4. **Feedback**: Loading/Success/Error prompts
5. **Exception handling**: Network errors, insufficient permissions, empty data
```

### UI Elements Checklist

- **Pages**: New or modified pages
- **Components**: Independent UI components
- **Dialogs**: Modal/Dialog/BottomSheet
- **Forms**: Data input
- **Feedback**: Toast/Snackbar/Message

---

## 3. User Value Assessment

### Priority = User Value × Urgency × Feasibility

```markdown
## User Value (WHY)
**Problem**: Users encounter YY problem in XX scenario
**Quantification**: Affects N users/day, saves M minutes/operation, improves P% conversion
**Priority**: High/Medium/Low (based on 3-dimension scoring)
```

---

## 4. Epic to Task Conversion

### 4.1 Extraction Sources

**Source 1: Technical Approach (feature list)**
```markdown
- ✅ Feature A → status: completed
- [ ] Feature B → status: open
```

**Source 2: Task Breakdown Preview (task list)**
```markdown
- [x] 001 - Task A → status: completed
- [ ] 002 - Task B → status: open
```

### 4.2 Tech Spec Extraction

- `Component:` Frontend | Record at: Technical Details → Component Structure
- `Route:` Frontend | Record at: Technical Details → Routing
- `State:` Frontend | Record at: Technical Details → State Management
- `UI/UX:` Frontend | Record at: Description → User Workflow
- `API:` Both | Record at: Technical Details → API Specifications
- `SQL:` Backend | Record at: Technical Details → Database Design
- `Model:` Backend | Record at: Technical Details → Data Model
- `Dependency:` Both | Record at: Dependencies

### 4.3 Merge Strategy

- Task Breakdown Preview: basic info (priority)
- Technical Approach: tech specs
- Merge and deduplicate

---

## 5. Quality Standards

### Feature Completeness
- Main flow complete, exception branches handled, edge cases validated

### Interaction Friendliness
- Timely operation feedback, clear error prompts, guided empty states

### User Experience
- Operation steps ≤ 3 (main flow)
- Critical operations require confirmation
- Real-time form validation feedback

---

## 6. Anti-patterns

| ❌ Wrong | ✅ Correct |
|---------|----------|
| Split by tech modules ("Implement Service layer") | Split by user features ("Users can batch delete data") |
| Too large ("Complete entire module") | Independently deliverable (1-3 days) |
| Only tech implementation ("Implement XX API") | Clear frontend display and interaction |
| Missing user perspective | Start from user operations |

---

## 7. Task Examples Comparison

### ❌ Bad Task

```markdown
# Task: Implement data management module
## Description
- Implement data CRUD API
- Add data list page
## Acceptance Criteria
- Code committed, tests pass
```

**Issues**: Too large, missing user perspective, missing interaction description

### ✅ Good Task

```markdown
# Task: Users can view and filter data list
## Features
Users can view all data records and filter by status/type.

## User Workflow
1. Enter "Data Management" page
2. List displays (20 items per page)
3. Click "Filter" → open filter panel
4. Select status/type → click "Confirm"
5. List refreshes, empty state shown if no data

## UI Elements
- Data list page (modified)
- Filter panel (new)
- Data card (reused)
- Empty state page (reused)

## Acceptance Criteria
- [ ] List pagination correct
- [ ] Filter function works
- [ ] Empty state normal
- [ ] Mobile/Web responsive
```

---

## 8. Usage Notes

**When to use**: Decompose tasks, review tasks, unclear descriptions

**Related rules**:
- `task-template-common.md` - Task structure
- `task-template-tech.md` - Technical details
- `datetime.md` - Timestamps

---

**Note**: When executing this rule, AI should generate task files in Chinese for team collaboration.
