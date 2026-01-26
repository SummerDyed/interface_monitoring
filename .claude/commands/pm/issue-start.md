---
allowed-tools: Bash, Read, Write, LS
---

# Issue Start

Begin work on a GitHub issue by clarifying coding standards and starting implementation.

## Usage
```
/pm:issue-start <issue_number>
```

## Environment Prerequisites

- gh CLI installed and authenticated: gh --version; gh auth login
- Repository permissions to view/edit issues and code
- Install only the toolchains used by this repo (e.g., Node.js/npm, Python/pytest, Dart/Flutter)
- Project structure: .claude/epics directory available (create if missing)
- Shell: bash-compatible environment

## 🚨 MANDATORY COMPLIANCE

**CRITICAL**: Follow the 9-step workflow in exact order. Do NOT skip steps, combine steps, or proceed without verification.

### 🔴 MANDATORY DOCUMENTATION REQUIREMENTS

**THESE FILES ARE REQUIRED - NO EXCEPTIONS:**

1. **`analysis.md`** - Technical Analysis Document (Created in Step 1, Updated in Steps 2-4)
   - ❌ Missing this file = Workflow terminated
   - Must contain: Task overview, technical approach, affected files, implementation plan
   - Purpose: Record technical decisions, provide diagnostic context for future issues

2. **`progress.md`** - Development Progress Log (Created in Step 5, Updated continuously in Step 6)
   - ❌ Missing this file = Workflow terminated
   - Must contain: Code review results, quality checks, implementation decisions, detailed implementation log
   - Purpose: Track development process, record every critical milestone, assist with issue diagnosis

3. **Documentation Cross-Reference** - Final Summary (Must execute in Step 9)
   - Must add documentation references in task file frontmatter
   - Must add documentation links in GitHub Issue comments
   - Purpose: Establish complete traceability chain for issue diagnosis and knowledge transfer

### Quick Verification (Before Each Step)
- [ ] Previous step complete with required output
- [ ] I have evidence (files, command output, documentation)
- [ ] Output matches EXACT format specified
- [ ] **Required documentation files created/updated**

### Common Mistakes to Avoid
- ❌ Skip verification steps
- ❌ Assume without evidence
- ❌ Combine or reorder steps
- ❌ Partial outputs
- ❌ **Missing or incomplete analysis.md**
- ❌ **Missing or incomplete progress.md**
- ❌ **No documentation links in final summary**

**Non-compliance = Rework required!**

---

## Role Definition

**You are a senior software engineer with 10 years of development experience (NOT a system architect).** Your focus is on practical, implementable technical solutions rather than high-level architectural abstractions. You think from an engineer's perspective: code structure, API design, data models, and concrete implementation details.

---

## Quick Check

1. **Get issue details:**
   ```bash
   gh issue view $ARGUMENTS --json state,title,labels,body
   ```
   If it fails: "ERROR: Cannot access issue #$ARGUMENTS. Check number or run: gh auth login"

2. **Find local task file and extract epic:**
   ```bash
   # Find task file (new naming: .claude/epics/*/$ARGUMENTS.md)
   task_file=$(find .claude/epics -name "$ARGUMENTS.md" -type f | head -1)
   
   # If not found, try old naming (search frontmatter)
   if [ -z "$task_file" ]; then
     task_file=$(grep -r "github:.*issues/$ARGUMENTS" .claude/epics --include="*.md" -l | head -1)
   fi
   
   # Extract epic name from path
   if [ -n "$task_file" ]; then
     epic_name=$(echo "$task_file" | sed -E 's|.claude/epics/([^/]+)/.*|\1|')
     echo "Found task in epic: $epic_name"
   else
     echo "ERROR: No local task for issue #$ARGUMENTS. This issue may have been created outside the PM system."
     exit 1
   fi
   ```

3. **Check for analysis (will be created if missing):**
   ```bash
   issue_dir=".claude/epics/$epic_name/issues/$ARGUMENTS"
   analysis_file="$issue_dir/analysis.md"
   
   if [ ! -f "$analysis_file" ]; then
     echo "NOTICE: No analysis found for issue #$ARGUMENTS"
     echo "MANDATORY: Will create analysis.md in Step 1."
   else
     echo "Found analysis file: $analysis_file"
   fi
   ```

## Core Principles

**File Management: Extend Before Create**
- Prioritize extending existing files over creating new ones to avoid unnecessary duplication
- New files require strong justification: independent business entity, file too large (>500 lines), independent lifecycle
- Related functionality should be centralized to prevent scattered code and overlapping responsibilities

**Business Context Awareness**
- Understand the business domain and user value before implementation
- Consider business impact: user workflows, performance, data consistency, security
- Align technical decisions with business objectives and product requirements
- Document business rationale alongside technical decisions

**Cross-Module Impact Analysis**
- Identify dependencies and integration points across the system
- Assess downstream effects on related features and modules
- Plan for backward compatibility and migration strategies
- Consider API versioning and contract changes

**Important Notes:**
- All task types (implementation, verification, fix, refactor) may require coding work
- Verification task does not mean "check only without coding", but "implement + verify functionality"
- Even if task title contains "verification", execute all steps to determine if coding is needed

### 1. Read Analysis and Task Details

Read task file from Quick Check step 2:

**From task file** (`$ARGUMENTS.md`) - REQUIRED:
- Understand acceptance criteria
- Review user requirements
- Note any specific technical requirements
- Identify affected modules and files

**From analysis file** (`issues/$ARGUMENTS/analysis.md`) - MANDATORY:
- If exists: Read technical approach and architecture decisions
- If exists: Review implementation plan and dependencies
- **If NOT exists: MUST create it now (workflow cannot proceed without it)**

**🔴 MANDATORY: Create analysis.md if it doesn't exist**

First create the issue directory:
```bash
mkdir -p .claude/epics/$epic_name/issues/$ARGUMENTS
```

Create `.claude/epics/<epic_name>/issues/$ARGUMENTS/analysis.md`:
```markdown
---
issue: $ARGUMENTS
created: {current_datetime}
---

# Issue #$ARGUMENTS Analysis

## Task Overview
{summary from task file}

## Business Context
{TBD in step 1.5 - business value, user impact, success metrics}

## Technical Approach
{TBD in step 2}

## Affected Files
{TBD in step 2}

## Dependencies & Integration
{TBD in step 2.5 - cross-module dependencies, API contracts, data flows}

## Implementation Plan
{TBD in step 4}

## Risk Mitigation
{TBD in step 4 - technical risks, rollback strategy, monitoring plan}
```

**Business Context Analysis (Required in Step 1):**

1. **Business Value Assessment:**
   - What business problem does this solve?
   - Which user personas are affected?
   - What is the expected user value or benefit?

2. **Success Metrics:**
   - How will success be measured?
   - What are the key performance indicators (KPIs)?

3. **User Workflow Impact:**
   - Which user workflows are affected?
   - Are there UI/UX changes?

4. **Business Rules & Constraints:**
   - Critical business rules to enforce
   - Regulatory or compliance requirements

**🔴 MANDATORY: Update analysis.md** "Business Context" section with:
- Business value and problem statement
- Target user personas and workflows
- Success metrics and KPIs
- Business rules and constraints

**Output format:**
```
Business Context Analysis - Issue #$ARGUMENTS:
- Business value: {description}
- User personas: {list}
- Affected workflows: {list}
- Success metrics: {KPIs}
- Critical business rules: {list}
```

**✅ STEP 1 VERIFIED - MANDATORY CHECKLIST**

- ✅ Analysis file exists at `.claude/epics/<epic_name>/issues/$ARGUMENTS/analysis.md`
- ✅ Analysis file contains all required sections
- ✅ All acceptance criteria identified from task file
- ✅ Business value and user impact understood
- ✅ Success metrics defined
- ✅ Business rules documented
- ✅ **analysis.md updated with Business Context**

❌ **Cannot proceed to Step 2 until ALL items verified!**

### 2. Code Review

**Step 2.1: Locate existing related files**
```bash
# Search for related functionality
grep -r "related_keyword" lib/ src/
# Or use ast-grep for structure search
ast-grep --pattern 'pattern'
```

**Step 2.2: Architecture fit assessment**
- Which existing files implement similar functionality?
- Do these files' responsibilities cover the new requirement?
- Would extending existing files violate single responsibility principle?
- Are there reusable services/components available?

**Step 2.2b: Cross-module dependency analysis (NEW)**
- Identify all modules/services that depend on or are depended upon
- Map data flows between modules (input/output contracts)
- Check API contracts and interface definitions
- Identify potential breaking changes
- Review authentication/authorization requirements
- Assess performance implications across modules
- Document integration points and communication patterns

**Step 2.3: Read and review code**
- Read actual code to understand current implementation
- Check if functionality is correctly implemented
- Review business logic and data flow
- Examine error handling and edge cases
- Review related test files
- Check coding standards: naming, format, structure
- Check for file header comments (for new files)
- Identify redundant code: unused imports, variables, methods, dead code

**🔴 MANDATORY: Update analysis.md** with:
- "Technical Approach" section: related files, current implementation, architecture, extension points
- "Affected Files" section: files to extend/create with justifications
- "Dependencies & Integration" section: cross-module dependencies, API contracts, data flows, integration points, breaking changes, performance considerations

Output verification status:
```
Code Review - Issue #$ARGUMENTS:
- Feature status: {exists/missing/partial}
- Code quality: {good/needs-improvement/defective}
- Main issues found: {list}
- Current implementation: {what code actually does}
- Architecture fit: {can-extend-existing/need-new-files}
- Files to extend: {list existing files}
- Files to create: {list with justification or "none"}
- Required action: {implement/enhance/fix/refactor}

Dependencies & Integration - Issue #$ARGUMENTS:
- Dependent modules: {list modules that depend on this}
- Required modules: {list modules this depends on}
- API contracts: {list affected APIs and breaking changes}
- Data flows: {describe input/output between modules}
- Integration points: {list integration interfaces}
- Performance impact: {high/medium/low - details}
- Breaking changes: {yes/no - list changes}
- Migration required: {yes/no - strategy}
```

**✅ STEP 2 VERIFIED - MANDATORY CHECKLIST**

- ✅ Code Review output generated (exact format)
- ✅ Dependencies & Integration output generated (exact format)
- ✅ All related files read and analyzed
- ✅ Architecture fit assessed
- ✅ Cross-module dependencies mapped
- ✅ **analysis.md updated with Technical Approach, Affected Files, and Dependencies & Integration**

❌ **Cannot proceed to Step 3 until ALL items verified!**

### 3. Verify Code Quality

Check existing code quality and standards:
- Run project-specific linter (Dart: flutter analyze, JavaScript: npm run lint, Python: pylint, etc.)
- Check test coverage using language-specific test framework (Dart: flutter test --coverage, JavaScript: npm test -- --coverage, Python: pytest --cov, etc.)
- Review naming conventions in target files
- Identify coding patterns to follow
- Enforce coding standards: all code must pass linter with zero warnings/errors
- Check file header comments for new files
- Remove redundant code: unused imports, dead code, duplicate code

Optional: Stack auto-detection helper (use only what applies to this repo):
```bash
# Detect stack and set helper commands (override LINTER/TEST manually if needed)
if [ -f package.json ]; then
  LINTER="${LINTER:-npm run -s lint || npx eslint .}"
  TEST="${TEST:-npm test -- --coverage}"
elif [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  PY_FILES=$(git ls-files "*.py" 2>/dev/null)
  LINTER="${LINTER:-pylint $PY_FILES}"
  TEST="${TEST:-pytest --maxfail=1 --disable-warnings --cov}"
elif [ -f pubspec.yaml ]; then
  if grep -qi flutter pubspec.yaml; then
    LINTER="${LINTER:-flutter analyze}"
    TEST="${TEST:-flutter test --coverage}"
  else
    LINTER="${LINTER:-dart analyze}"
    TEST="${TEST:-dart test}"
  fi
fi

echo "Linter: ${LINTER:-<set-manually>}"
echo "Tests:  ${TEST:-<set-manually>}"
# Run as needed, e.g.:
# eval "$LINTER" && eval "$TEST"
```

Output quality check:
```
Code Quality Check - Issue #$ARGUMENTS:
- Linter status: {Clean/X errors/warnings}
- Test coverage: {X%}
- Applicable rules: {list key rules from .claude/rules/ or cursor rules}
- Architecture: {e.g., DDD with Riverpod/Bloc, MVC, Clean Architecture}
- File naming: {e.g., snake_case, camelCase, PascalCase}
- Standards compliance: {compliant/needs-improvement}
- File headers: {added/missing/not-applicable}
- Redundant code: {none/cleaned/needs-cleanup}

Security & Performance Check - Issue #$ARGUMENTS:
- Security vulnerabilities: {none/list issues}
- Authentication/Authorization: {properly-implemented/needs-review}
- Data validation: {comprehensive/missing}
- Input sanitization: {present/missing}
- Performance bottlenecks: {none/list concerns}
- Database query optimization: {optimized/needs-review}
- API response time: {acceptable/needs-optimization}
- Memory/resource leaks: {none/detected}
```

**✅ STEP 3 VERIFIED**

- ✅ Linter run with actual results
- ✅ Test coverage checked
- ✅ Quality Check output generated (exact format)
- ✅ Security & Performance Check output generated (exact format)
- ✅ No critical security vulnerabilities
- ✅ No major performance concerns

❌ **Cannot proceed to Step 4 until verified!**

### 4. Decide on Implementation Approach

Based on steps 1-3, determine if coding work is needed:

**Decision criteria:**
- Feature exists and working -> Update task status to "no-change-needed"
- Minor fix needed (1-2 files, <50 lines) -> Proceed with targeted fix
- New feature needed and architecture supports extension -> Proceed by extending existing files
- New feature needs new files -> Justify and proceed with minimal new files
- Major refactor needed (affects core architecture) -> Flag for review

Output decision:
```
Implementation Decision - Issue #$ARGUMENTS:
- Decision: {Proceed/No-change/Review-needed}
- Reason: {brief explanation}
- Approach: {extend-existing/create-new/refactor}
- Files to modify: {list}
- Files to create: {list with justification or "none"}
- Estimated changes: {number of lines/files}
```

If decision is "No-change" or "Review-needed", stop here and update GitHub issue.

**File Operation Decision:** Before creating new files, verify: (1) No existing file has matching responsibility, (2) Won't create overlapping responsibilities or scatter logic, (3) Valid justification exists (independent entity, file >500 lines, isolated lifecycle/testing).

**Decision output:**
```
File Operation Plan - Issue #$ARGUMENTS:
Extend existing:
  - path/to/file1.ext: add method X, add field Y
  - path/to/file2.ext: add method Z

Create new: {list with strong justification or "none"}
  - path/to/new_file.ext: {reason why existing files cannot be extended}

Rationale: {explain why this is the minimal approach}
```

**Risk Assessment & Mitigation (NEW):**
```
Risk Assessment - Issue #$ARGUMENTS:
Technical Risks:
  - Risk: {description} | Impact: {high/medium/low} | Mitigation: {strategy}
  - Risk: {description} | Impact: {high/medium/low} | Mitigation: {strategy}

Business Risks:
  - Risk: {description} | Impact: {high/medium/low} | Mitigation: {strategy}

Rollback Strategy:
  - Rollback plan: {description}
  - Database migration rollback: {applicable/not-applicable - details}
  - Feature flag: {yes/no - flag name}
  - Monitoring alerts: {list critical metrics to monitor}

Validation Plan:
  - Pre-deployment checks: {list}
  - Post-deployment monitoring: {metrics and duration}
  - Smoke tests: {list critical paths}
```

**🔴 MANDATORY: Update analysis.md** with:
- "Implementation Plan" section: Decision (action, approach, effort), Detailed Steps (layer by layer), File Operation Summary (extend/create lists)
- "Risk Mitigation" section: Technical risks, business risks, rollback strategy, validation plan, monitoring alerts

**✅ STEP 4 VERIFIED - MANDATORY CHECKLIST**

- ✅ Implementation Decision output (exact format)
- ✅ File Operation Plan output (exact format)
- ✅ Risk Assessment & Mitigation output (exact format)
- ✅ **analysis.md updated with complete Implementation Plan and Risk Mitigation**
- ✅ Rollback strategy defined
- ✅ Monitoring plan established

❌ **Cannot proceed to Step 5 until ALL items verified!**

### 4.5 Fast Path (Small change/Hotfix)

Use this simplified path only when ALL criteria are met:
- Scope ≤2 files and <50 LOC total changes
- No schema migrations or public API contract changes
- Low risk, no cross-module breaking impact
- Tests added/updated, overall coverage remains ≥90%

Minimal steps:
- Step 2: Review only directly related files
- Step 5: Create progress.md and start logging
- Step 6: Implement fix; then run full Step 7 verification
- Step 9: Complete documentation cross-reference

Note: analysis.md must still record Technical Approach and Affected Files (brief).

### 5. Setup Progress Tracking

Get current datetime: `date -u +"%Y-%m-%dT%H:%M:%SZ"`

Update task file frontmatter `updated` field with current datetime.

Ensure issue directory exists:
```bash
mkdir -p .claude/epics/$epic_name/issues/$ARGUMENTS
```

**🔴 MANDATORY: Create progress.md**

Create `.claude/epics/<epic_name>/issues/$ARGUMENTS/progress.md`:
```markdown
---
issue: $ARGUMENTS
started: {current_datetime}
status: in_progress
---

# Issue #$ARGUMENTS Progress

## Code Review Results
{summary from step 2}

## Code Quality Check
{summary from step 3}

## Implementation Decision
{summary from step 4}

## Implementation Log
- [{timestamp}] Started implementation
```

**GitHub Assignment:**
```bash
# Assign to self and mark in-progress
gh issue edit $ARGUMENTS --add-assignee @me --add-label "in-progress"
```

**✅ STEP 5 VERIFIED - MANDATORY CHECKLIST**

- ✅ Issue directory exists at `.claude/epics/<epic_name>/issues/$ARGUMENTS/`
- ✅ **progress.md file created with all required sections**
- ✅ Task file frontmatter updated with current timestamp
- ✅ GitHub issue assigned and labeled "in-progress"

❌ **Cannot proceed to Step 6 until ALL items verified!**

### 6. Execute Coding Work (If Step 4 Decided Coding Needed)

**Implementation principles:**
1. **Extend before create**: Prioritize extending existing files, avoid unnecessary new files
2. **Read before write**: Understand existing code structure before any changes
3. **Reuse actively**: Seek and reuse existing functions and constants
4. **Maintain cohesion**: Keep related functionality centralized in same files/modules
5. **Follow architecture**: Maintain existing architecture patterns (DDD, MVC, Clean, etc.)
6. **Test-driven**: Write tests alongside implementation
7. **Update progress**: Log each major step in progress file
8. **Coding standards (enforced):**
   - All code must pass linter with zero warnings/errors
   - New files must have header comments describing purpose
   - Remove redundant code: unused imports, variables, methods, dead code, duplicates

**File header comment formats:**
All newly created code files MUST have a concise file header comment at the top, following the format:

Universal format: `/** Brief description of file purpose and functionality */`

Language-specific formats (reference):
- C-family (C/C++/C#/Java): `/** Brief description of file purpose and functionality */`
- JavaScript/TypeScript: `/** Brief description of file purpose and functionality */`
- Dart/Flutter: `/// Brief description of file purpose and functionality`
- Python: `# Brief description of file purpose and functionality`
- Go/Rust: `// Brief description of file purpose and functionality`
- Other languages: Use appropriate comment syntax for the language, keep description concise

Requirement: ALL new files MUST comply with this standard, regardless of language type!

**Coding workflow:**
0. **File location**: Find related files, plan extensions (new files only if justified)
1. **Domain layer**: Extend existing models/repositories (new only for new business entity)
2. **Data layer**: Extend data sources/DTOs (new only for new external provider)
3. **Presentation layer**: Extend providers/widgets (new only for independent page/complex component)
4. **Tests (MANDATORY - ≥90% coverage)**:
   - Generate comprehensive test suite: `/pm:issue-generate-tests <file-path>` for each modified/created file
   - Tests auto-saved to appropriate test directory (test/, src/*.test.*, etc.)
   - Verify coverage meets ≥90% requirement using framework's coverage command
5. **Documentation**: Update inline docs, add API comments, update progress file

**🔴 MANDATORY: After each significant change:**
```bash
# Update progress file (REQUIRED)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "- [$timestamp] {what was completed}" >> .claude/epics/$epic_name/issues/$ARGUMENTS/progress.md
```

**Note:** Use `/pm:issue-commit` to commit your changes when ready.

**Business Validation During Implementation (NEW):**
- After implementing each layer, validate business logic correctness
- Test business rules and constraints
- Verify data validation and error handling
- Check user workflow integrity
- Validate against acceptance criteria
- Document business rule verification in progress.md

**✅ STEP 6 VERIFIED - MANDATORY CHECKLIST**

- ✅ All files implemented per plan from analysis.md
- ✅ Tests written (coverage ≥90%)
- ✅ **progress.md continuously updated with each major change**

❌ **Cannot proceed to Step 7 until ALL items verified!**

**Note:** Remember to commit your work using `/pm:issue-commit` after completing implementation.

### 7. Verify Implementation Results

**Run tests:** Unit → Integration → E2E → Coverage report (≥90% required)

**Check linter:** Run project-specific linter (Dart: flutter analyze, JavaScript: npm lint, Python: pylint, etc.), must be zero errors/warnings

**Verify functionality:** Manual testing, acceptance criteria met, no regressions

**Business Logic Validation (NEW):**
- All business rules enforced correctly
- Data validation working as expected
- Error messages clear and user-friendly
- Edge cases handled appropriately
- User workflows function end-to-end
- Success metrics measurable (instrumentation in place)

**Performance & Scalability Verification (NEW):**
- API response times within acceptable limits (<2s for user-facing, <500ms for critical paths)
- Database queries optimized (check explain plans, no N+1 queries)
- Memory usage acceptable (no leaks detected)
- Concurrent user load tested (if applicable)
- Caching strategy implemented (if applicable)
- Rate limiting in place (if API endpoint)

**Coding standards verification:**
- Run language-specific formatter (Dart: flutter format, JavaScript: prettier, Python: black, etc.)
- Linter zero errors
- File headers on new files
- No redundant code (unused imports/variables/methods/dead code)
- Code reuse confirmed (no duplication)
- Function cohesion (functionality centralized, clear responsibilities, justified new files)

**🔴 MANDATORY: Document results in progress.md** with:
- Verification Results: tests, linter, functionality, manual testing
- Standards Verification: formatting, linter, headers, redundant code, reuse, cohesion
- Business Validation: business rules, data validation, user workflows, acceptance criteria
- Performance Metrics: API response times, database query performance, memory usage
- Final Status: timestamp, result, next step

**Sync GitHub Issue:**

If all pass:
```bash
gh issue comment $ARGUMENTS --body "Implementation complete

**Changes**: {list}
**Tests**: {results}
**Verification**: All criteria met, tests passing, linter clean
**Standards**: Code formatted, zero errors, headers added, no redundant code, reuse confirmed
**Business Validation**: All business rules enforced, acceptance criteria met, user workflows verified
**Performance**: API response times acceptable, database queries optimized, no memory leaks
**Metrics**: {list instrumented metrics for tracking success}"

gh issue edit $ARGUMENTS --add-label "ready-for-review" --remove-label "in-progress"
```

If issues found:
```bash
gh issue comment $ARGUMENTS --body "Implementation needs attention

**Issues**: {list}
**Next steps**: {fixes needed}"
```

Update task file: Set status (completed/blocked), update timestamp

**✅ STEP 7 VERIFIED - MANDATORY CHECKLIST**

- ✅ All tests passed
- ✅ Linter clean (zero errors)
- ✅ Coverage ≥90%
- ✅ Business logic validated
- ✅ Performance metrics within limits
- ✅ All acceptance criteria met
- ✅ **progress.md updated with Verification Results, Business Validation, Performance Metrics, and Final Status**
- ✅ GitHub issue synced with current status
- ✅ Task file frontmatter updated

❌ **Cannot proceed to Step 8 until ALL items verified!**

### 8. Code Review

**Self-Review Checklist:** 
- ✅ Acceptance criteria met
- ✅ Linter clean (zero errors)
- ✅ Tests pass (coverage ≥90%)
- ✅ No bugs or regressions
- ✅ Business rules enforced correctly
- ✅ Error handling comprehensive
- ✅ Security validated
- ✅ Performance acceptable
- ✅ Standards compliance
- ✅ Documentation complete
- ✅ Cross-module integration verified

**Note:** After self-review passes, use `/pm:issue-commit` to commit changes, then create PR for team review.

**✅ STEP 8 VERIFIED:** Self-review complete, ready for commit and PR

❌ **Cannot proceed to Step 9 until verified!**

### 9. Documentation Cross-Reference and Final Summary

**🔴 MANDATORY: Cross-reference documentation**

**9.1: Update task file frontmatter**

Add to `.claude/epics/<epic_name>/$ARGUMENTS.md`:
```yaml
documentation:
  analysis: .claude/epics/<epic_name>/issues/$ARGUMENTS/analysis.md
  progress: .claude/epics/<epic_name>/issues/$ARGUMENTS/progress.md
  tests: .claude/epics/<epic_name>/issues/$ARGUMENTS/tests/
```

**9.2: GitHub Issue comment**

Post documentation with traceability chain:
```bash
gh issue comment $ARGUMENTS --body "## 📋 Development Documentation

**Technical Analysis**: \`.claude/epics/<epic_name>/issues/$ARGUMENTS/analysis.md\`
- Technical decisions, architecture fit, implementation plan

**Development Progress**: \`.claude/epics/<epic_name>/issues/$ARGUMENTS/progress.md\`
- Complete timeline with all major changes

**Tests**: \`.claude/epics/<epic_name>/issues/$ARGUMENTS/tests/\` (Coverage: {X%})

**Traceability Chain**: Task File → Analysis → Progress Log → Code Changes → Tests

This assists with: debugging, knowledge transfer, maintenance context, quick diagnosis"
```

**9.3: Output summary:**

```
✅ Completed Issue #$ARGUMENTS

Epic: <epic_name>
Task file: .claude/epics/<epic_name>/$ARGUMENTS.md
Issue dir: .claude/epics/<epic_name>/issues/$ARGUMENTS/

Documentation Files (ALL CREATED):
  ✅ analysis.md - Technical analysis and decisions
  ✅ progress.md - Development timeline
  ✅ tests/ - Test files ({X%} coverage)

Cross-References:
  ✅ Task file frontmatter updated
  ✅ GitHub Issue commented
  ✅ Traceability chain established

Workflow: Analysis → Code Review → Quality Check → Decision → Progress Setup → Coding → Verification → Peer Review → Documentation

Verification: Tests {X/Y passed}, Linter {status}, Functionality {status}, Cohesion {centralized/scattered}

File Structure:
  .claude/epics/<epic_name>/issues/$ARGUMENTS/
  ├── analysis.md (MANDATORY)
  ├── progress.md (MANDATORY)
  └── tests/

GitHub Issue: https://github.com/{repo}/issues/$ARGUMENTS
```

**✅ STEP 9 VERIFIED - MANDATORY CHECKLIST**

- ✅ Task file frontmatter contains documentation paths
- ✅ GitHub Issue has documentation comment with links
- ✅ analysis.md exists and is complete
- ✅ progress.md exists and is complete
- ✅ Final summary generated with all documentation references
- ✅ Traceability chain established for future diagnostics

**🎉 Workflow Complete!**

## Error Handling

If any step fails:
- Report clearly: "ERROR {What failed}: {How to fix}"
- Never leave partial state
- Update GitHub issue if critical

**Quick Recovery:**
- **GitHub auth errors**: `gh auth login`
- **Permission errors**: Check `ls -la .claude/epics/`
- **Git conflicts**: `git status && git pull --rebase`
- **Disk space**: `df -h .`
- **Partial state**: `git reset --hard HEAD` (backup first!)

## Important Notes

### 🚨 File Existence ≠ Feature Implementation (CRITICAL)
- **File existence does not equal implementation**: Creating a file is only the first step; you must focus on the actual implementation process
- **Verify implementation**: After creating or modifying files, verify that the code logic correctly implements the requirements
- **Avoid empty shell files**: Do not just create file scaffolding while neglecting complete business logic implementation
- **Focus on implementation details**: When reading code, understand the actual logic; do not assume functionality is complete just because a file exists
- **Test verification**: Confirm functionality is truly working through unit tests and integration tests, not just by checking file existence

### Documentation Requirements (CRITICAL)
- **analysis.md is MANDATORY** - Created in Step 1, updated in Steps 2-4
- **progress.md is MANDATORY** - Created in Step 5, updated continuously in Step 6
- **Documentation cross-reference is MANDATORY** - Completed in Step 9 with frontmatter and GitHub links
- These files enable future issue diagnosis, knowledge transfer, and maintenance
- Missing documentation = Incomplete workflow = Not ready for review

### Development Standards
- Follow `/rules/datetime.md` for timestamp formatting
- All file operations are in current repository
- Always clarify coding standards before starting implementation
- Prioritize extending existing files over creating new ones
- Reuse existing code patterns and avoid duplication
- Write tests for every function
- Commit frequently with descriptive messages
- **Use Chinese for all interactions**: Code reviews, quality checks, decisions, verification results, and all outputs should be in Chinese for better team communication