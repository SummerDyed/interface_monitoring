---
allowed-tools: Read, Write, Edit, Bash
argument-hint: [file-path]
description: Generate comprehensive test suite with unit, integration, and edge case coverage
---

# Generate Tests

Generate comprehensive test suite for: $ARGUMENTS

## Objective

Create complete test coverage for the target file, ensuring code quality and reliability through systematic testing.

## Requirements

### Coverage Standards
- **Minimum coverage**: 90% line coverage
- **Test types**: Unit tests, integration tests, edge cases
- **Test quality**: Tests must be meaningful, not just coverage metrics

### Test Scope
1. **Unit tests** - All public functions and methods
2. **Integration tests** - Component interactions and data flow
3. **Edge cases** - Boundary conditions, null/empty inputs, error scenarios
4. **Mocks** - External dependencies (APIs, databases, file system)

## Process

### 1. Analyze Target File

**Actions:**
- Read and understand the target file structure
- Identify all testable components (functions, methods, classes)
- Determine dependencies that need mocking
- Review existing test patterns in the project

**Output:**
- List of components to test
- Dependencies requiring mocks
- Test file location determination

### 2. Design Test Strategy

**Consider:**
- What are the critical code paths?
- What inputs could cause failures?
- What edge cases exist?
- How do components interact?
- What external dependencies exist?

**Output:**
- Test organization structure
- Mock strategy
- Edge cases to cover

### 3. Generate Test File

**Requirements:**
- Follow project test naming conventions
- Use project's test framework and patterns
- Organize tests logically (by component/feature)
- Include setup/teardown where needed
- Add descriptive test names

**Test structure:**
- Group related tests
- Use AAA pattern (Arrange, Act, Assert)
- Keep tests focused and independent
- Make assertions clear and specific

### 4. Implement Test Cases

**For each component:**

**Unit Tests:**
- Test with valid inputs
- Test with invalid inputs
- Test boundary values
- Test return values and side effects

**Integration Tests:**
- Test component interactions
- Test data flow between components
- Test state management

**Edge Cases:**
- Null/undefined inputs
- Empty collections
- Maximum/minimum values
- Concurrent operations
- Error conditions

**Mocks:**
- Mock external APIs
- Mock database operations
- Mock file system
- Mock time-dependent operations

### 5. Verify Quality

**Test execution:**
- All tests must pass
- No flaky tests
- Fast execution time

**Coverage check:**
- Measure code coverage
- Ensure ≥90% coverage
- Verify all critical paths tested

**Code review:**
- Tests are readable and maintainable
- Test names describe behavior
- Assertions are clear
- No redundant tests

## Test Quality Guidelines

### Good Tests Are:
- **Independent** - Can run in any order
- **Repeatable** - Same result every time
- **Fast** - Quick feedback loop
- **Clear** - Obvious what's being tested
- **Focused** - Test one thing at a time

### Avoid:
- ❌ Testing implementation details
- ❌ Overly complex test setup
- ❌ Multiple assertions testing different things
- ❌ Relying on test execution order
- ❌ Tests that don't add value

## Framework-Specific Guidelines

### Flutter (Dart)
- Use `flutter_test` package
- Mock with `mockito` or `mocktail`
- Use `test()` and `group()` for organization
- Use `setUp()` and `tearDown()` for common setup
- Test widgets with `testWidgets()`

### JavaScript/TypeScript
- Use project's test framework (Jest, Vitest, etc.)
- Use Testing Library for React/Vue components
- Mock modules with framework's mock utilities
- Test async code properly with async/await

### Python
- Use `pytest` or `unittest`
- Mock with `unittest.mock` or `pytest-mock`
- Use fixtures for shared setup
- Test async code with `pytest-asyncio`

## Output Format

```
✅ Test Generation Complete

Target: {file_path}
Test File: {test_file_path}

Test Summary:
- Unit tests: {count}
- Integration tests: {count}
- Edge case tests: {count}
- Mocks created: {count}

Coverage: {percentage}%
Status: {Pass/Fail}

Next Steps:
- Run: {test command}
- Review: Check test quality and readability
```

## Verification Checklist

Before completing:
- [ ] Test file created in correct location
- [ ] All public methods/functions tested
- [ ] Edge cases covered
- [ ] External dependencies mocked
- [ ] All tests pass
- [ ] Coverage ≥90%
- [ ] Tests are readable and maintainable
- [ ] Test names are descriptive

## Important Notes

### Test Philosophy
- Tests are documentation - they explain how code should behave
- Tests provide safety net for refactoring
- Good tests catch bugs early
- Bad tests create maintenance burden

### Coverage vs Quality
- 90% coverage is minimum, not goal
- Focus on testing critical paths thoroughly
- Don't write tests just to increase coverage
- Meaningful tests > coverage metrics

### Maintenance
- Keep tests simple and focused
- Update tests when code changes
- Remove tests for deleted code
- Refactor tests when they become hard to maintain

---

**Remember:** The goal is confidence in code correctness, not just green checkmarks.
