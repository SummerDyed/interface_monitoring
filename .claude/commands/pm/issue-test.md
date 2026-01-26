---
allowed-tools: Bash, Read, Write, LS
---

# Issue Test

Execute E2E and API testing after development to verify data consistency.

## Usage
```
/pm:issue-test <issue_number>
```

## 🚨 MANDATORY COMPLIANCE

Follow the 9-step workflow in exact order. Do NOT skip steps or proceed without verification.

### 🔴 MANDATORY FILES

1. **`test_plan.md`** - Test strategy (Step 1)
   - ❌ Missing = Workflow terminated
   - Must contain: Test scope, E2E scenarios, API endpoints, database queries

2. **Unit Test Coverage** - Code-level tests (Step 2.5 - Prerequisites)
   - ❌ Coverage <90% = E2E testing blocked
   - Must verify: Unit tests exist, coverage ≥90%, all tests passing

3. **Test Reports** - Versioned test reports (Step 5)
   - Directory: `.claude/epics/<epic_name>/issues/$ARGUMENTS/reports/`
   - Naming: `test_report_{YYYYMMDD_HHMMSS}.md`
   - Must contain: Test results, API requests, database consistency, performance

4. **API Request Log** - `api_request_log_{timestamp}.json`
   - Content: Full request/response, status codes, response time, errors
   - Purpose: Complete API traceability

5. **Database Consistency Log** - `db_consistency_{timestamp}.json`
   - Content: Pre/post snapshots, SQL queries, execution results, data diffs
   - Purpose: Data integrity validation

6. **Documentation Cross-Reference** - Final summary (Step 8)
   - Update task frontmatter with test paths
   - Add GitHub Issue links
   - Purpose: Complete traceability chain

### Quick Verification
- [ ] Previous step complete with required output
- [ ] Evidence available (files, logs)
- [ ] Output matches specified format
- **Required documentation created/updated**

**Non-compliance = Rework required!**

---

## Role Definition

**You are a senior QA/Test engineer with 10 years of testing experience.** Your focus is on quality assurance, finding edge cases, and ensuring system reliability. You think from a tester's perspective: breaking the system, validating data consistency, verifying boundary conditions, and ensuring comprehensive test coverage. Your goal is to find bugs before users do.

---

## 9-Step Workflow

### Step 1: Read Task & Analysis

**Required actions:**
- Read task file: `$ARGUMENTS.md`
- Read analysis: `issues/$ARGUMENTS/analysis.md`
- Extract: Implementation details, acceptance criteria, testable features

**🔴 MANDATORY: Create test_plan.md**
```bash
mkdir -p .claude/epics/$epic_name/issues/$ARGUMENTS
```

**Create** `.claude/epics/<epic_name>/issues/$ARGUMENTS/test_plan.md`:
```markdown
---
issue: $ARGUMENTS
created: {datetime}
---

# Issue #$ARGUMENTS Test Plan

## Test Scope
{summary}

## E2E Test Scenarios
{TBD step 2}

## API Endpoints
{TBD step 2}

## Database Consistency Checks
{TBD step 3}

## Test Environment
- Base URL: {TBD}
- Database: {TBD}
- Test Data: {TBD}
```

**✅ VERIFIED:** Test plan created, files reviewed, criteria identified

❌ **Cannot proceed until verified!**

---

### Step 2: Analyze Implementation

**Required actions:**
```bash
# Find implementation files
find lib/ src/ -type f -name "*.dart" | grep -E "(controller|service|repository|provider)" | head -20

# Identify:
# - HTTP endpoints in controller/service files
# - Route definitions
# - CRUD operations
# - Authentication requirements
```

**Define E2E scenarios:**
- Map user workflows
- Identify key actions
- Define expected outcomes
- Note edge cases

**🔴 MANDATORY: Update test_plan.md** with E2E scenarios and API endpoints

**Output format:**
```
Test Target Analysis - Issue #$ARGUMENTS:
- Files: {count}
- API endpoints: {count}
- E2E scenarios: {count}
- Authentication: {required/not-required}
```

**✅ VERIFIED:** Analysis complete, test_plan updated

❌ **Cannot proceed until verified!**

---

### Step 2.5: Verify Unit Test Coverage (Prerequisites)

**Objective:** Ensure code-level tests exist before E2E testing

**Requirements:**
- All unit tests must pass
- Code coverage ≥90%
- Tests exist for all modified/created files

**Actions:**
1. Detect project test framework (Flutter, JavaScript/TypeScript, Python, etc.)
2. Run test suite with coverage enabled
3. Analyze coverage report
4. Verify coverage meets minimum threshold

**Decision logic:**
- If tests fail → Fix tests before proceeding
- If coverage <90% → Run `/pm:issue-generate-tests` for files with insufficient coverage
- If coverage ≥90% → Proceed to Step 3

**Output format:**
```
Unit Test Coverage - Issue #$ARGUMENTS:
- Test framework: {detected framework}
- Total tests: {count}
- Tests passed: {count}
- Coverage: {percentage}%
- Status: {Pass/Fail}
- Action required: {none/fix-tests/generate-tests}
```

**✅ VERIFIED:** All unit tests pass, coverage ≥90%

❌ **Cannot proceed until verified!**

---

### Step 3: Parse Database & Plan Consistency

**Objective:** Understand database structure and plan data consistency checks

**Actions:**
1. Load database configuration from environment variables or .env file
2. Find database schema files (migrations, schema definitions, SQL files)
3. Identify tables affected by this issue
4. Design pre-test and post-test consistency checks

**Plan consistency checks:**
- Define baseline database state before testing
- Plan verification queries for after testing
- Identify data integrity constraints to validate
- Document expected data changes

**🔴 MANDATORY: Update test_plan.md** with database consistency checks section

**Output format:**
```
Database Configuration - Issue #$ARGUMENTS:
- Host: {host}
- Port: {port}
- Database: {name}
- User: {user}
- Affected tables: {list}
- Consistency checks planned: {count}
```

**✅ VERIFIED:** DB config extracted, checks planned, test_plan updated

❌ **Cannot proceed until verified!**

---

### Step 4: Setup Environment & Validation

**Objective:** Ensure test environment is ready and accessible

**Verify environment:**
1. Test database connectivity
2. Verify API endpoints are accessible
3. Check required services are running
4. Validate environment configuration

**Prepare test data:**
- Create test accounts if needed
- Generate sample data for testing
- Backup current database state
- Initialize test fixtures

**Output format:**
```
Environment Validation - Issue #$ARGUMENTS:
- Database: {✅ Connected / ❌ Failed}
- API: {✅ Accessible / ❌ Unreachable}
- Services: {list status}
- Test data: {Ready / Need preparation}
```

**✅ VERIFIED:** Environment validated, test data prepared

❌ **Cannot proceed until verified!**

---

### Step 5: Setup Versioned Test Reports

**Objective:** Create timestamped test report structure for traceability

**Actions:**
1. Generate timestamp for report versioning (ISO 8601 format)
2. Create reports directory structure
3. Initialize test report markdown file
4. Initialize API request log (JSON)
5. Initialize database consistency log (JSON)
6. Update GitHub issue with testing status

**Directory structure:**
```
.claude/epics/<epic_name>/issues/$ARGUMENTS/reports/
├── test_report_{timestamp}.md
└── test_logs/
    ├── api_request_log_{timestamp}.json
    ├── db_consistency_{timestamp}.json
    └── e2e_{timestamp}.log
```

**Test report structure:**
- Frontmatter: issue number, report ID, timestamp, status
- Environment section: DB config, API URL, version
- Placeholders for: API logs, DB consistency, results, performance, issues

**Log file formats:**
- **API log**: JSON with issue, report_id, start_time, api_requests array, summary
- **DB log**: JSON with issue, report_id, start_time, pre_test, post_test, checks array, summary

**GitHub update:**
- Comment: "Testing started - version: {timestamp}"
- Add label: "testing"

**✅ VERIFIED:** Report structure created, logs initialized, GitHub updated

❌ **Cannot proceed until verified!**

---

### Step 6: Execute Tests

**Objective:** Run comprehensive tests and capture all results

**6.1: Capture Pre-Test Database State**
- Query database for current state snapshot
- Record table counts, row counts, key metrics
- Save to db_log pre_test section

**6.2: Execute E2E Tests**
- Run integration tests if they exist
- Capture test output to log file
- Record pass/fail status
- Log execution time

**6.3: Execute API Tests with Logging**
- For each API endpoint identified in Step 2:
  - Send request with appropriate method and headers
  - Capture: status code, response body, response time
  - Log to api_log with timestamp
  - Track success/failure status
- Calculate summary: total requests, successful, failed, avg response time

**6.4: Execute Database Consistency Checks**
- Capture post-test database state snapshot
- Compare pre-test vs post-test
- Run consistency verification queries from test plan
- Document any data discrepancies
- Log to db_log post_test section
- Calculate consistency status

**Output tracking:**
- All test execution details logged to appropriate files
- Real-time updates to test report
- Timestamps for each major step

**✅ VERIFIED:** E2E tests run, API tests logged, DB checked, report updated

❌ **Cannot proceed until verified!**

---

### Step 7: Analyze Results

**Objective:** Analyze all test results and determine overall status

**E2E Test Analysis:**
- Parse E2E log file for pass/fail indicators
- Count passed tests
- Count failed tests
- Extract failure details

**API Test Analysis:**
- Read API log JSON file
- Calculate total requests, successful, failed
- Calculate average response time
- Identify failed requests with details

**Database Consistency Analysis:**
- Compare pre-test and post-test snapshots
- Verify data integrity
- Identify any discrepancies
- Determine consistency status

**Overall Status Determination:**
- If any E2E tests failed → Overall: Failed
- If any API requests failed → Overall: Failed
- If database inconsistent → Overall: Failed
- Otherwise → Overall: Passed

**Complete Test Report:**
- Add conclusion section to test report
- Include execution timestamp and version
- Add summary section with all test results
- List all log file locations
- Add next steps based on status

**GitHub Synchronization:**

**If tests passed:**
- Comment with success summary (E2E, API, DB stats)
- Include report file paths
- Add label: "tested"
- Remove label: "testing"
- Indicate ready for deployment

**If tests failed:**
- Comment with failure summary
- List specific failures (E2E, API, DB)
- Include report location
- Add label: "needs-fix"
- Remove label: "testing"

**Output format:**
```
Test Analysis - Issue #$ARGUMENTS:
- E2E: {X passed, Y failed}
- API: {X success, Y failed, Z avg ms}
- DB: {consistent/inconsistent}
- Overall status: {Passed/Failed}
- Report: test_report_{timestamp}.md
```

**✅ VERIFIED:** Results analyzed, report complete, GitHub synced

❌ **Cannot proceed until verified!**

---

### Step 8: Cross-Reference & Summary

**Objective:** Establish complete documentation traceability

**8.1: Update Task File Frontmatter**
- Add testing section to task file frontmatter
- Include paths to test_plan.md
- Add test report entry with:
  - Report version (timestamp)
  - Paths to all report files
  - Test status
  - Execution timestamp

**8.2: GitHub Documentation Comment**
- Post comprehensive documentation comment
- Include test plan location and purpose
- List all test report files with paths
- Document traceability chain
- Explain purpose for future reference

**8.3: Generate Summary Output**
- Epic name and task file location
- List all created documentation files
- Cross-reference status
- Workflow summary
- File structure diagram
- GitHub issue link

**Traceability Chain:**
```
Task File → Test Plan → Test Execution → Logs → Analysis → Report → Documentation
```

**Purpose:**
- Quick issue diagnosis
- Knowledge transfer
- Maintenance context
- Historical reference

**Output format:**
```
✅ Testing Complete - Issue #$ARGUMENTS

Documentation Created:
  ✅ test_plan.md
  ✅ test_report_{timestamp}.md
  ✅ api_request_log_{timestamp}.json
  ✅ db_consistency_{timestamp}.json
  ✅ e2e_{timestamp}.log

Cross-References:
  ✅ Task frontmatter updated
  ✅ GitHub issue documented
  ✅ Traceability established

Results:
  - E2E: {stats}
  - API: {stats}
  - DB: {status}
  - Status: {Passed/Failed}

GitHub: https://github.com/{repo}/issues/$ARGUMENTS
```

**✅ VERIFIED:** Documentation cross-referenced, summary complete

**🎉 Testing Workflow Complete!**

---

## Error Handling

On failure:
- Report: "ERROR {failed}: {fix}"
- Never leave partial state
- Update GitHub if critical

**Recovery:**
- **DB errors**: Check .env, verify credentials
- **API errors**: Verify API_BASE_URL, check service
- **Test failures**: Review logs, analyze, fix
- **Environment**: Restart services, reinit data

## Important Notes

### Documentation (CRITICAL)
- **test_plan.md MANDATORY** - Step 1
- **Timestamped reports MANDATORY** - Step 5, supports multiple tests
- **API logs MANDATORY** - Complete request/response
- **DB logs MANDATORY** - Data changes
- **Cross-reference MANDATORY** - Step 8

Missing documentation = Incomplete testing = Not production-ready

### Test Standards
- Plan before execute
- Capture all outputs
- Verify DB consistency after tests
- Document performance
- **Use English**

### Coverage Requirements
- E2E: All critical workflows
- API: All endpoints
- DB: All affected tables
- Performance: <2s response

### Key Features

**Multiple Test Support:**
- Time-stamped versions
- History preserved
- Version comparison
- Trend analysis

**Complete API Logging:**
- Method, URL, headers, body
- Response, status, time, errors
- JSON format

**DB Consistency Tracking:**
- Pre/post snapshots
- Change records
- Table statistics

**Rule Clarity:**
- MANDATORY identifiers
- Verification checkpoints
- Clear naming
- Complete workflow
- Traceability chain

## Language Requirements

- **Primary Language**: All responses and output must be in Chinese
- **Documentation**: Comments, logs, and generated content should use Chinese
- **User Communication**: Interact with users in Chinese at all times
- **Error Messages**: Display error messages and warnings in Chinese