---
allowed-tools: Bash, Read, Write, LS
---

# PRD Parse

Convert PRD to technical implementation epic.

## Usage
```
/pm:prd-parse <feature_name>
```

## Required Rules

**IMPORTANT:** Before executing this command, read and follow:
- `.claude/rules/datetime.md` - For getting real current date/time
- `.claude/commands/pm/prd-parse-functional-checklist.md` - For comprehensive feature mining

## Preflight Checklist

Before proceeding, complete these validation steps silently (don't report progress to user).

### Validation Steps

1. **Verify <feature_name> parameter provided**
   - If missing: "❌ <feature_name> was not provided. Please run: /pm:prd-parse <feature_name>"
   - Stop if not provided

2. **Verify PRD exists**
   - Check `.claude/prds/$ARGUMENTS.md` exists
   - If not found: "❌ PRD not found: $ARGUMENTS. Create it with: /pm:prd-new $ARGUMENTS"
   - Stop if missing

3. **Validate PRD frontmatter**
   - Verify has: name, description, status, created
   - If invalid: "❌ Invalid PRD frontmatter. Check: .claude/prds/$ARGUMENTS.md"
   - Show what's missing

4. **Validate PRD content completeness**
   - Verify essential sections: User Stories, Functional Requirements, Success Criteria
   - If missing critical sections: "⚠️ PRD missing: [list]. Epic coverage may be incomplete."

5. **Enhanced feature mining** (Reference: prd-parse-functional-checklist.md)
   - Extract ALL explicit functional requirements
   - Mine functional variants, extensions, boundary cases
   - Extract ALL API interface designs (often overlooked)
   - Extract ALL DDL data model designs (often overlooked)
   - Identify functional dependencies and relationships

   **Feature inventory:**
   - Core features (P0)
   - Feature variants and extensions
   - API specifications
   - DDL table structures
   - Boundary conditions and edge cases
   - Functional dependencies

   **API interface completeness:**
   - Extract ALL APIs from PRD
   - Create complete API inventory: endpoints, methods, parameters
   - Verify API coverage for every feature
   - Check CRUD completeness, validation, error handling
   - Map APIs to microservices
   - **Blocking rule:** If critical API missing, STOP

   **API Extraction Actions:**
   1. **Identify API sources:**
      - Scan PRD sections: "Interface Design", "API List", "System Interactions"
      - Identify action verbs: "call", "request", "fetch", "submit", "sync"
      - Reverse derive from user stories: User Action → Frontend Event → Backend API
   2. **Structured output:** Generate for each API:
      ```yaml
      - endpoint: /api/v1/xxx
        method: POST
        description: Feature description
        request:
          headers: [Authorization: Bearer xxx]
          params: {field: type, required: bool, validation: rule}
        response:
          success: {code: 200, data: {schema}}
          errors: [{code: 40001, message: "Business error description"}]
        auth: JWT/OAuth/API-Key
        rate_limit: 100/min
        idempotent: true/false
      ```
   3. **Additional specs:**
      - Unified error codes (business code + HTTP status)
      - Authentication method documentation
      - Rate limiting strategy
      - API versioning strategy (v1/v2 compatibility)
      - Mock data definition (for frontend integration)

   **DDL data model completeness:**
   - Extract ALL data tables from PRD
   - Create complete table inventory: fields, types, constraints
   - Verify data model coverage for every feature
   - Check field completeness, indexes, constraints
   - Map table relationships and foreign keys
   - **Blocking rule:** If critical table missing, STOP

   **DDL Extraction Actions:**
   1. **Identify data entities:**
      - Scan PRD sections: "Data Model", "Entity Relationships", "Field Specifications"
      - Identify nouns: "user", "order", "record", "config" → map to tables
      - Reverse derive table fields from API request/response fields
   2. **Structured output:** Generate for each table:
      ```sql
      CREATE TABLE table_name (
        id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
        -- Business fields (extract from PRD)
        field_name TYPE [NOT NULL] [DEFAULT x] COMMENT 'Field description',
        -- Audit fields (mandatory)
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
        updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
        deleted_at DATETIME NULL COMMENT 'Soft delete time',
        -- Index design
        INDEX idx_xxx (field1, field2) COMMENT 'Index purpose'
      ) COMMENT='Table description';
      ```
   3. **Additional specs:**
      - Index strategy: primary key, unique, composite, covering index
      - Sharding strategy: by time/ID/tenant (if applicable)
      - Field constraints: NOT NULL, DEFAULT, UNIQUE
      - Enum values: dictionary table or field comment
      - Large field handling: TEXT/BLOB storage approach
      - Data migration: compatibility plan for new fields

6. **Feature value assessment**
   - For each feature, assess:
     * Business value (revenue/cost/competitive advantage)
     * User value (problem-solving/efficiency/experience)
     * Strategic value (core business/long-term goals)
   - Assign priority: P0 core / P1 important / P2 value-add
   - Identify high-value features that must not be missed
   - Validate P0 features explicitly covered in Epic

7. **Feature completeness validation**
   - Cross-reference PRD requirements with mined features
   - Verify no valuable features omitted
   - Ensure feature-value mapping complete
   - **Blocking rule:** If ANY P0/high-value features missing, STOP

8. **Check for existing epic**
   - Check `.claude/epics/$ARGUMENTS/epic.md` exists
   - If exists: "⚠️ Epic '$ARGUMENTS' already exists. Overwrite? (yes/no)"
   - Only proceed with explicit 'yes'
   - If no: "View existing epic: /pm:epic-show $ARGUMENTS"

9. **Verify directory permissions**
   - Ensure `.claude/epics/` exists or can be created
   - If cannot create: "❌ Cannot create epic directory. Check permissions."

## Instructions

**Role Definition:** You are a senior software engineer with 10 years of development experience (NOT a system architect). Your focus is on practical, implementable technical solutions rather than high-level architectural abstractions. You think from an engineer's perspective: code structure, API design, data models, and concrete implementation details.

You are converting a PRD into a detailed implementation epic for: **$ARGUMENTS**

**⚠️ CRITICAL REQUIREMENTS:**
- **Response Language**: ALWAYS respond to user in Chinese
- **Zero-Omission Principle**: Every feature in PRD MUST be covered
- **Mandatory Review**: Perform line-by-line review against PRD
- **Completeness First**: Better more tasks than miss functionality

### 1. Read the PRD

**Objective:** Understand all requirements completely

**Actions:**
- Load PRD from `.claude/prds/$ARGUMENTS.md`
- Analyze all requirements and constraints
- Understand user stories and success criteria
- Extract PRD description from frontmatter
- **Create feature inventory**: List every feature for review

### 2. Technical Analysis

**Objective:** Map PRD requirements to technical components

**Actions:**
- Identify architectural decisions needed
- Determine technology stack and approaches
- **Map every PRD feature to technical components**
- Identify integration points and dependencies
- **Verify mapping completeness**: Confirm all features mapped

### 3. Create Epic File

**Objective:** Generate comprehensive technical implementation plan

**Location:** `.claude/epics/$ARGUMENTS/epic.md`

**File Structure:**

#### Frontmatter
```yaml
---
name: $ARGUMENTS
status: backlog
created: [ISO 8601 datetime from `date -u`]
progress: 0%
prd: .claude/prds/$ARGUMENTS.md
github: [Placeholder - updated during sync]
---
```

**Frontmatter guidelines:**
- **name**: Exact feature name (same as $ARGUMENTS)
- **status**: Always "backlog" for new epics
- **created**: Get real datetime with `date -u +"%Y-%m-%dT%H:%M:%SZ"`
- **progress**: Always "0%" for new epics
- **prd**: Reference source PRD path
- **github**: Placeholder for sync

#### Content Sections

**1. Overview**
- Brief technical summary of implementation approach
- Key objectives and scope

**2. Architecture Decisions**
- Key technical decisions with rationale
- Technology choices and justifications
- Design patterns to use
- Trade-offs considered

**3. System Architecture**

**Requirement:** Visualize system architecture using **mermaid graph TB**

**What to include:**
- All major system components
- Data flow between components
- External system integrations
- Key functions or operations in each component

**Format guidance:**
- Use subgraphs for logical groupings (Frontend, Backend, Data, External, etc.)
- Show component responsibilities and key functions
- Indicate data flow with arrows
- Use styling to distinguish component types

**Architecture notes:**
- Explain each layer's purpose
- Document key integration points
- Describe protocols and patterns used

**4. Technical Approach**

**Requirement:** Reference which PRD requirements each section addresses

**Subsections:**

**Frontend Components** (if applicable)
- UI components needed (PRD ref: ...)
- State management approach
- User interaction patterns

**Backend Services** (if applicable)
- API endpoints required (PRD ref: ...)
- Data models and schema (PRD ref: ...)
- Business logic components

**Infrastructure**
- Deployment considerations
- Scaling requirements (PRD ref: ...)
- Monitoring and observability

**5. Implementation Strategy**

**Phases:**
- Development phases breakdown
- Risk mitigation strategies
- Testing approach (unit/integration/e2e)

**6. Task Breakdown Preview**

**Objective:** Break epic into 5-10 concrete, actionable tasks

**Requirements:**
- Each task MUST trace to specific PRD requirements
- Add comments: "Implements: PRD User Story X" or "Covers: PRD Req X.X"
- Group logically by layer, feature, or phase

**Grouping approaches:**
- **By Layer**: Database → Backend → Frontend → Integration → Testing
- **By Feature**: Core → Extensions → Optimizations
- **By Phase**: Setup → Implementation → Validation → Deployment

**Task format:**
```markdown
### Phase X: [Name] (Est: X hours)
- [ ] [Number] - [Task Title]
  - [Deliverables]
  - **PRD Coverage:** [Which requirements/stories this implements]
  - Effort: [Size estimate]
```

**Task qualities:**
- Clear scope and deliverables
- Sized appropriately (1-3 days, 8-24h)
- Explicit PRD coverage references
- Logical dependencies
- Parallelization opportunities identified
- Critical path documented

**7. Dependencies**

**List:**
- External service dependencies
- Internal team dependencies
- Prerequisite work
- Potential blockers

**8. Success Criteria (Technical)**

**Define measurable criteria:**
- Performance benchmarks (e.g., API < 100ms)
- Quality gates (e.g., coverage ≥90%)
- Testable acceptance criteria
- Non-functional requirements

### 4. Quality Validation

**Objective:** Ensure ZERO features omitted

**⚠️ MANDATORY: PRD Coverage Review**

Perform comprehensive line-by-line review:

**Step 0: Enhanced Feature Mining Validation**
- [ ] All mined features documented and tracked
- [ ] Functional variants, extensions, boundary cases listed
- [ ] All functional dependencies identified
- [ ] **All P0 features explicitly covered in Epic**
- [ ] **All high-value features have implementation tasks**
- [ ] Feature-value assessment reflected in prioritization
- [ ] If any P0/high-value missing, STOP and correct

**Step 1: Feature Inventory Comparison**
- [ ] Checklist of EVERY PRD feature created
- [ ] Each feature verified in epic (Technical Approach or Tasks)
- [ ] Mark: ✅ covered or ❌ missing
- [ ] If ANY ❌, STOP and add before proceeding

**Step 2: Section-by-Section PRD Review**
- [ ] PRD "User Stories" → all covered in epic
- [ ] PRD "Functional Requirements" → all mapped to tasks
- [ ] PRD "Non-Functional Requirements" → in Architecture/Infrastructure
- [ ] PRD "Success Criteria" → technical acceptance criteria
- [ ] PRD "Constraints" → in Dependencies/Implementation Strategy

**Step 3: Cross-Reference Validation**
- [ ] Every PRD bullet has corresponding epic item
- [ ] Every user story has implementing tasks
- [ ] Every API/integration in PRD in technical approach
- [ ] Every data model/entity has database/backend tasks

**Step 4: Technical Detail Validation**
Execute checks and output diff report:
- [ ] API count: count(PRD APIs) vs count(Epic APIs)
- [ ] CRUD completeness: verify Create/Read/Update/Delete for each entity
- [ ] Field coverage: diff(API request/response fields, DDL table fields), output missing
- [ ] Index coverage: verify each query condition has corresponding index
- [ ] Foreign key relations: verify table relationships reflected in DDL
- [ ] Error code completeness: verify each API exception has error code

**Output format:**
```
| Check Item | PRD Count | Epic Count | Gap |
|------------|-----------|------------|-----|
| APIs       | X         | Y          | Missing: xxx |
| Tables     | X         | Y          | Missing: xxx |
| Fields     | X         | Y          | Missing: xxx |
```
**BLOCKING:** If any gap > 0, STOP and complete before proceeding

**Quality Checklist:**

**PRD Alignment:**
- [ ] All requirements addressed
- [ ] User stories map to components
- [ ] Success criteria translated
- [ ] Non-functional requirements considered

**Architecture Quality:**
- [ ] Mermaid graph TB diagram exists
- [ ] All external systems shown
- [ ] Technology choices justified
- [ ] Architecture decisions explain trade-offs
- [ ] Security and data flows documented

**Task Breakdown Quality:**
- [ ] All implementation areas covered
- [ ] Clear scope and deliverables
- [ ] **Explicit PRD Coverage references**
- [ ] Appropriate sizing (1-3 days each)
- [ ] Logical dependencies
- [ ] Parallelization identified
- [ ] Critical path documented
- [ ] **All PRD requirements covered by tasks**

**Implementation Strategy Quality:**
- [ ] Phases clearly defined
- [ ] Risk mitigation included
- [ ] Testing approach covers all levels
- [ ] Deployment addressed

**Dependencies Quality:**
- [ ] External services listed with protocols
- [ ] Internal dependencies identified
- [ ] Prerequisites documented
- [ ] Blockers highlighted

**Success Criteria Quality:**
- [ ] Benchmarks quantified
- [ ] Quality gates measurable
- [ ] Acceptance criteria testable
- [ ] Non-functional included

### 5. Post-Creation

After creating epic:

**1. Output Coverage Report:**
```
✅ PRD Coverage Review Complete

📋 Enhanced Feature Coverage:
- Total PRD Features (Explicit): X
- Mined Features (Variants/Extensions): X
- Boundary Cases: X
- **Total Features**: X
- Covered in Epic: X
- **Coverage Rate: 100%** ✅

🎯 Priority Distribution:
- P0 Core: X (X%)
- P1 Important: X (X%)
- P2 Value-Add: X (X%)

🔍 Section Coverage:
- User Stories: X/X ✅
- Functional Requirements: X/X ✅
- Feature Variants: X/X ✅
- Dependencies: X/X ✅
- Boundary Cases: X/X ✅
- Value Features: X/X ✅

⚠️ If ANY < 100%, LIST missing items and STOP
```

**2. Confirm creation:**
"✅ Epic created: .claude/epics/$ARGUMENTS/epic.md"

**3. Show summary:**
- Task categories count
- Key architecture decisions

**4. Suggest next step:**
"Ready to break down into tasks? Run: /pm:epic-decompose $ARGUMENTS"

## Error Recovery

If any step fails:
- Clearly explain what went wrong
- If PRD incomplete, list missing sections
- If technical approach unclear, identify needed clarification
- Never create epic with incomplete information

**If Feature Omissions Detected:**
- STOP epic creation immediately
- List ALL omitted features with PRD references
- Explain why initially missed
- Revise epic to include ALL missing features
- Re-run coverage review to confirm 100%

## Important Notes

**⚠️ ZERO-OMISSION is TOP PRIORITY:**
- **NEVER sacrifice coverage for simplicity**
- Missing PRD requirement is worst failure
- Coverage review (Step 4) catches omissions - take seriously

**Task Optimization:**
- Aim for ≤10 tasks
- Identify simplification opportunities
- Leverage existing functionality when possible
- **BUT**: If PRD feature needs own task, create it

**Content Guidelines:**
- Keep descriptions concise
- Focus on high-level concepts
- Avoid large code blocks
- Epic describes "what" and "why", not "how"
- Save implementation details for task files

---

Focus on creating technically sound implementation plan addressing all PRD requirements while being practical and achievable.
