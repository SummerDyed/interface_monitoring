---
allowed-tools: Bash, Read, Write, LS
---

# Issue Analyze

Perform technical analysis and create implementation plan for an issue.

## Usage
```
/pm:issue-analyze <issue_number>
```

## Preflight Checks

Complete these validation steps silently (don't report progress to user).

### 1. Verify Issue Task File Exists

**Check locations:**
- First: `.claude/epics/*/$ARGUMENTS.md` (new naming convention)
- Fallback: Search for `github:.*issues/$ARGUMENTS` in frontmatter (old naming)

**If not found:**
"❌ No local task for issue #$ARGUMENTS. Run: /pm:import first"

### 2. Check for Existing Analysis

**Check:** `.claude/epics/*/issues/$ARGUMENTS/analysis.md` exists

**If exists:**
"⚠️ Analysis already exists for issue #$ARGUMENTS. Overwrite? (yes/no)"
- Only proceed with explicit 'yes'
- If no, show existing analysis location

## Instructions

You are a technical architect analyzing an issue to create a comprehensive implementation plan.

### 1. Read Issue Context

**Objective:** Gather all information about the issue

**Actions:**
- Get issue details from GitHub (title, body, labels)
- Read local task file to understand:
  - Technical requirements
  - Acceptance criteria
  - Dependencies
  - Effort estimation

### 2. Technical Analysis

**Objective:** Analyze technical aspects and design approach

**Architecture Analysis:**

Identify architectural layers involved:
- **Domain layer**: Business logic, models, entities
- **Data layer**: Data sources, repositories, APIs
- **Presentation layer**: UI components, pages, state management
- **Infrastructure layer**: Network, storage, configuration

**Design decisions:**
- Which design patterns to use? (Repository, Factory, Singleton, etc.)
- State management approach? (Riverpod, Bloc, Provider, StatefulWidget)
- Data flow and communication patterns

**File Impact Analysis:**

Identify affected files:
- Which new files need to be created?
- Which existing files need modification?
- Configuration updates? (routing, dependencies, etc.)
- Test files required?

**Dependency Analysis:**

Map dependencies:
- Which existing modules/services does this depend on?
- New third-party libraries needed?
- Impact on other modules?
- Integration points?

**Testing Requirements:**

Define testing strategy:
- Test types needed (Unit, Widget, Integration, E2E)
- Coverage targets (≥90%)
- Mock data requirements
- Test scenarios

### 3. Create Analysis File

**Objective:** Document comprehensive technical analysis

**Location:** `.claude/epics/<epic_name>/issues/$ARGUMENTS/analysis.md`

**File Structure:**

#### Frontmatter
```yaml
---
issue: $ARGUMENTS
title: [Issue title from GitHub]
analyzed: [ISO 8601 datetime from `date -u`]
estimated_hours: [Total estimated hours]
---
```

#### Content Sections

**1. Overview**
- Brief description of the work required
- Key objectives
- Scope boundaries

**2. Architecture Analysis**

**Affected Layers:**
- List which architectural layers are involved
- Explain what needs to be done in each layer
- Justify architectural decisions

**Design Patterns:**
- Which patterns will be used and why
- How they fit the existing architecture
- Benefits and trade-offs

**State Management:**
- Chosen approach (Riverpod, Bloc, Provider, etc.)
- Rationale for the choice
- State structure and flow

**3. Affected Files**

**New Files:**
- Complete paths for all new files
- Purpose of each file
- File organization rationale

**Modified Files:**
- Complete paths for all modified files
- What changes in each file
- Justification for changes

**4. Technical Approach**

**Implementation Steps:**
- Break down into logical steps
- For each step:
  - What to do
  - Which files involved
  - Key implementation details

**Key Technical Points:**
- Critical technical challenges
- Solutions or approaches
- References or examples

**API Interfaces (if applicable):**
- List required API endpoints
- HTTP methods, paths, parameters
- Request/response formats
- Error handling

**Data Models (if applicable):**
- Domain models needed
- Data transfer objects
- Schema definitions
- Validation rules

**5. Dependencies**

**External Dependencies:**
- Other modules/services required
- Third-party libraries (with versions)
- API integrations
- Infrastructure requirements

**Impact on Other Modules:**
- Which modules will be affected
- Nature of the impact
- Compatibility considerations

**6. Testing Strategy**

**Unit Tests:**
- Classes/functions requiring unit tests
- Coverage target (≥90%)
- Test scenarios

**Widget/Component Tests:**
- UI components to test
- Interaction scenarios
- Visual regression considerations

**Integration Tests:**
- End-to-end workflows to test
- Integration points to verify
- Data consistency checks

**Mock Requirements:**
- What needs to be mocked
- Mock data structure
- Mock service setup

**7. Risk Assessment**

**Technical Risks:**
- Identify potential technical challenges
- Rate impact (High/Medium/Low)
- Mitigation strategies

**Compatibility Risks:**
- Impact on existing features
- Breaking changes
- Migration requirements
- Backward compatibility

**Performance Risks:**
- Potential performance impacts
- Optimization needs
- Scalability considerations

**8. Time Estimation**

Breakdown by activity:
- Development time
- Testing time
- Code review and adjustments
- Documentation
- Total estimated hours

**9. Notes and Considerations**

- Special considerations
- Warnings or caveats
- Recommendations
- Alternative approaches considered

### 4. Validate Analysis

**Objective:** Ensure analysis is complete and practical

**Completeness Check:**
- [ ] All major work items covered
- [ ] File list complete and accurate
- [ ] Technical approach is feasible
- [ ] Risks identified and addressed
- [ ] Time estimation is reasonable
- [ ] Testing strategy is comprehensive

**Quality Check:**
- [ ] Follows existing architecture patterns
- [ ] Design decisions are justified
- [ ] Solution is practical, not over-engineered
- [ ] Dependencies are clearly documented
- [ ] Risk mitigation is practical

### 5. Output Summary

After creating analysis, output:

```
✅ Technical Analysis Complete - Issue #$ARGUMENTS

📋 Analysis Summary:
  - Architectural Layers: [Domain/Data/Presentation/Infrastructure]
  - New Files: X
  - Modified Files: Y
  - Estimated Hours: Z

🏗️ Implementation Approach:
  Step 1: [Brief description]
  Step 2: [Brief description]
  Step 3: [Brief description]

⚠️  Key Risks:
  - [Risk 1]
  - [Risk 2]

📁 Analysis File:
  .claude/epics/<epic_name>/issues/$ARGUMENTS/analysis.md

Next Step: Start implementation with /pm:issue-start $ARGUMENTS
```

## Important Notes

**Analysis Best Practices:**
- Focus on feasibility and practicality
- Don't over-engineer the solution
- Follow existing code patterns and architecture
- Include testing and debugging time in estimates
- Prefer clear implementation plans over complex architecture

**File Management:**
- Analysis files are local only (not synced to GitHub)
- Store in issues directory for organization
- Can be referenced during implementation

**Language Requirements:**
- **Command and technical terms**: English
- **Documentation content**: Can use Chinese for team clarity if preferred
- **Code examples**: English (standard practice)

---

Create practical, actionable technical analysis that guides implementation effectively.
