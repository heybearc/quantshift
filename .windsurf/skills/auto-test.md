---
name: auto-test
description: Automatically run Playwright tests during debugging to verify fixes
activation: automatic
---

# Auto-Test Skill

## Purpose

Automatically run Playwright tests during debugging to verify fixes without manual intervention.

## When This Activates

### Automatic Testing Triggers

When user is debugging and:
1. Implements a fix for a bug
2. Makes changes to authentication/routing logic
3. Fixes UI issues
4. Changes critical functionality
5. Says "test this" or "verify this works"

### Actions Taken Automatically

1. ✅ Detect which app is being debugged
2. ✅ Run relevant Playwright tests on STANDBY container
3. ✅ Report test results (pass/fail)
4. ✅ If tests fail: analyze failures and suggest fixes
5. ✅ If tests pass: confirm fix is working

## Test Execution

### TheoShift
```bash
# Run smoke tests on STANDBY
ssh blue-theoshift 'cd /opt/theoshift && npm run test:smoke:quick'

# Run full test suite
ssh blue-theoshift 'cd /opt/theoshift && npm run test:e2e'
```

### LDC Tools
```bash
# Run smoke tests on STANDBY
ssh ldc-staging 'cd /opt/ldc-tools/frontend && npm run test:smoke:quick'

# Run full test suite
ssh ldc-staging 'cd /opt/ldc-tools/frontend && npm run test:e2e'
```

### QuantShift
```bash
# Run smoke tests
ssh qs-dashboard 'cd /opt/quantshift && npm run test:smoke:quick'

# Run full test suite
ssh qs-dashboard 'cd /opt/quantshift && npm run test:e2e'
```

## Debugging Workflow with Auto-Test

### Standard Flow
```
1. User reports bug: "Getting 404 on /events/123"
2. Windsurf investigates code
3. Windsurf implements fix
4. Auto-deploy deploys fix to STANDBY
5. Auto-test runs relevant tests
6. Windsurf reports: "Fix deployed and tests passing"
```

### If Tests Fail
```
1. Auto-test runs tests
2. Tests fail with specific errors
3. Windsurf analyzes test failures
4. Windsurf implements additional fixes
5. Auto-deploy deploys fixes
6. Auto-test runs tests again
7. Repeat until tests pass
```

## Test Selection Strategy

### Quick Smoke Tests (Default)
- Run after every fix during active debugging
- Fast execution (~15-30 seconds)
- Covers critical paths (login, navigation, core features)
- Use: `npm run test:smoke:quick`

### Full Test Suite (On Request)
- Run before version bump or release
- Comprehensive coverage (~1-3 minutes)
- All features and edge cases
- Use: `npm run test:e2e`

## Example Interactions

### Authentication Bug
```
You: "Getting 404 after login"
Windsurf: [Investigates authentication redirect logic]
         [Finds issue in middleware]
         [Implements fix]
         [Auto-deploys to STANDBY]
         [Runs smoke tests]
         ✅ Fix deployed
         ✅ Tests passing (4/4)
         ✅ Login flow working correctly
```

### UI Bug
```
You: "Event selection not working"
Windsurf: [Investigates event selection component]
         [Finds state management issue]
         [Implements fix]
         [Auto-deploys to STANDBY]
         [Runs smoke tests]
         ✅ Fix deployed
         ✅ Tests passing (4/4)
         ✅ Event selection working
```

### Test Failure
```
You: "Fix the navigation bug"
Windsurf: [Implements fix]
         [Auto-deploys]
         [Runs tests]
         ❌ Tests failing (2/4 passing)
         ❌ Navigation test failed: Cannot find element
         [Analyzes failure]
         [Implements additional fix]
         [Auto-deploys]
         [Runs tests again]
         ✅ Tests passing (4/4)
         ✅ Navigation working correctly
```

## Test Prerequisites

Tests require `.env.test` on STANDBY containers:

```bash
# TheoShift STANDBY
BASE_URL=http://localhost:3001
TEST_USER_EMAIL=admin@theoshift.local
TEST_USER_PASSWORD=AdminPass123!

# LDC Tools STANDBY
BASE_URL=http://localhost:3001
TEST_USER_EMAIL=admin@ldctools.local
TEST_USER_PASSWORD=AdminPass123!

# QuantShift
BASE_URL=http://localhost:3001
TEST_USER_EMAIL=admin@quantshift.local
TEST_USER_PASSWORD=AdminPass123!
```

## Benefits

**Replaces manual testing:**
- ❌ No more "log in and try it"
- ❌ No more "navigate to this URL"
- ❌ No more manual verification steps
- ✅ Automated verification after every fix
- ✅ Immediate feedback on whether fix works
- ✅ Catches regressions automatically

**Faster debugging:**
- Fix → Deploy → Test → Report (all automatic)
- No context switching to browser
- No manual test execution
- Continuous verification during debugging

## Notes

- Tests run on STANDBY containers only (safe)
- Tests use test credentials (non-destructive)
- Test failures provide specific error messages
- Windsurf analyzes failures and implements fixes
- User can disable auto-test by saying "skip tests"
