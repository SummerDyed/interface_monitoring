# CLAUDE.md

> Think carefully and implement the most concise solution that changes as little code as possible.

## USE SUB-AGENTS FOR CONTEXT OPTIMIZATION

### 1. file-analyzer sub-agent
Use when asked to read files. Expert in extracting and summarizing critical information from files, particularly log files and verbose outputs. Provides concise, actionable summaries that preserve essential information while dramatically reducing context usage.

### 2. code-analyzer sub-agent
Use when searching code, analyzing code, researching bugs, or tracing logic flow. Expert in code analysis, logic tracing, and vulnerability detection. Provides concise, actionable summaries while dramatically reducing context usage.

### 3. test-runner sub-agent
Use to run tests and analyze test results. Ensures:
- Full test output is captured for debugging
- Main conversation stays clean and focused
- Context usage is optimized
- All issues are properly surfaced
- No approval dialogs interrupt the workflow

## Available Rules

Rules are located in `.claude/rules/`. Read them when needed for specific tasks.

### Core Rules (Read When Applicable)
- `datetime.md` - HIGHEST PRIORITY: Getting real system date/time for frontmatter and timestamps
- `frontmatter-operations.md` - Working with YAML frontmatter in markdown files
- `github-operations.md` - GitHub CLI operations and repository protection

### Workflow Rules (Read When Applicable)
- `agent-coordination.md` - Multiple agents working in parallel
- `branch-operations.md` - Git branch management
- `worktree-operations.md` - Git worktree operations

### Development Rules (Read When Applicable)
- `standard-patterns.md` - Common patterns for commands
- `test-execution.md` - Running tests
- `use-ast-grep.md` - Code structure analysis with ast-grep

### Utility Rules (Read When Applicable)
- `strip-frontmatter.md` - Removing frontmatter before GitHub sync

## Philosophy

### Error Handling
- Fail fast for critical configuration (missing text model)
- Log and continue for optional features (extraction model)
- Graceful degradation when external services unavailable
- User-friendly messages through resilience layer

### Testing
- Always use the test-runner agent to execute tests
- Do not use mock services for anything ever
- Do not move on to the next test until the current test is complete
- If the test fails, consider checking if the test is structured correctly before deciding we need to refactor the codebase
- Tests to be verbose so we can use them for debugging

## Tone and Behavior

- Criticism is welcome. Please tell me when I am wrong or mistaken, or even when you think I might be wrong or mistaken.
- Please tell me if there is a better approach than the one I am taking.
- Please tell me if there is a relevant standard or convention that I appear to be unaware of.
- Be skeptical.
- Be concise.
- Short summaries are OK, but don't give an extended breakdown unless we are working through the details of a plan.
- Do not flatter, and do not give compliments unless I am specifically asking for your judgement.
- Occasional pleasantries are fine.
- Feel free to ask many questions. If you are in doubt of my intent, don't guess. Ask.

## ABSOLUTE RULES

- NO PARTIAL IMPLEMENTATION
- NO SIMPLIFICATION : no "//This is simplified stuff for now, complete implementation would blablabla"
- NO CODE DUPLICATION : check existing codebase to reuse functions and constants Read files before writing new functions. Use common sense function name to find them easily.
- NO DEAD CODE : either use or delete from codebase completely
- IMPLEMENT TEST FOR EVERY FUNCTIONS
- NO CHEATER TESTS : test must be accurate, reflect real usage and be designed to reveal flaws. No useless tests! Design tests to be verbose so we can use them for debuging.
- NO INCONSISTENT NAMING - read existing codebase naming patterns.
- NO OVER-ENGINEERING - Don't add unnecessary abstractions, factory patterns, or middleware when simple functions would work. Don't think "enterprise" when you need "working"
- NO MIXED CONCERNS - Don't put validation logic inside API handlers, database queries inside UI components, etc. instead of proper separation
- NO RESOURCE LEAKS - Don't forget to close database connections, clear timeouts, remove event listeners, or clean up file handles

## Important Instruction Reminders

- Do what has been asked; nothing more, nothing less.
- NEVER create files unless they're absolutely necessary for achieving your goal.
- ALWAYS prefer editing an existing file to creating a new one.
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
