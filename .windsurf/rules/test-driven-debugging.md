---
title: Test-Driven Debugging (Global Rule)
tags: [debugging, testing, automation]
---

# Test-Driven Debugging (Global Rule)

## Core Principle

**Always use automated tests to verify fixes. Never suggest manual testing.**

This is a SYSTEMIC rule that applies to ALL applications (TheoShift, LDC Tools, QuantShift).

## The Problem

Windsurf was suggesting manual testing during debugging:
- "Log in and try it"
- "Navigate to this URL"
- "Enter these credentials"
- "Check if it works in the browser"

**This interrupts debugging flow and wastes time.**

## The Solution

**Use Playwright automated tests to verify fixes.**

Every app has:
- Smoke tests (quick, critical paths)
- Full test suite (comprehensive)
- Test credentials configured
- Tests run on STANDBY containers

## Debugging Workflow

### Standard Flow (Automatic)

```
1. User reports bug
2. Investigate code
3. Implement fix
4. Auto-deploy to STANDBY
5. Run smoke tests automatically
6. Report results
```

**No manual testing. No browser interaction. Fully automated.**

### If Tests Fail

```
1. Analyze test failure output
2. Implement additional fix
3. Auto-deploy
4. Run tests again
5. Repeat until tests pass
```

## When to Run Tests

### Always Run (Automatic)
- After implementing authentication fixes
- After fixing routing/navigation issues
- After UI component changes
- After critical functionality changes
- When user says "test this" or "verify this"

### Run on Request
- Full test suite before version bump
- Full test suite before release
- When user explicitly asks for comprehensive testing

## Test Commands

### Quick Smoke Tests (15-30 seconds)
```bash
# TheoShift
ssh blue-theoshift 'cd /opt/theoshift && npm run test:smoke:quick'

# LDC Tools
ssh ldc-staging 'cd /opt/ldc-tools/frontend && npm run test:smoke:quick'

# QuantShift
ssh qs-dashboard 'cd /opt/quantshift && npm run test:smoke:quick'
```

### Full Test Suite (1-3 minutes)
```bash
# TheoShift
ssh blue-theoshift 'cd /opt/theoshift && npm run test:e2e'

# LDC Tools
ssh ldc-staging 'cd /opt/ldc-tools/frontend && npm run test:e2e'

# QuantShift
ssh qs-dashboard 'cd /opt/quantshift && npm run test:e2e'
```

## Response Templates

### After Implementing Fix

**Good Response:**
```
Implemented fix for authentication redirect issue.

Deploying to STANDBY...
✅ Deployed

Running smoke tests...
✅ All tests passing (4/4)
✅ Login flow working correctly
✅ Navigation working correctly

Fix verified and ready.
```

**Bad Response:**
```
Implemented fix for authentication redirect issue.

To test:
1. Go to https://blue.theoshift.com/auth/signin
2. Log in with admin@theoshift.local
3. Navigate to /events/select
4. Verify it works
```

### When Tests Fail

**Good Response:**
```
Deployed fix to STANDBY.

Running smoke tests...
❌ Tests failing (2/4 passing)

Failure details:
- Login test: PASSED
- Navigation test: FAILED - Cannot find element 'button[data-testid="select-event"]'

Analyzing failure...
Found issue: Button selector changed in recent refactor.
Implementing additional fix...

✅ Fix deployed
✅ Tests passing (4/4)
```

## Benefits

**Replaces manual testing:**
- No browser interaction during debugging
- No manual credential entry
- No URL navigation
- No "try it and see" approach

**Provides immediate feedback:**
- Tests run automatically after deployment
- Clear pass/fail status
- Specific error messages when tests fail
- Continuous verification during debugging

**Catches regressions:**
- Tests verify entire critical path
- Not just the specific bug being fixed
- Ensures no new bugs introduced

## Enforcement

**This rule applies to ALL debugging sessions across ALL apps.**

When debugging:
1. ❌ Never suggest manual testing
2. ✅ Always run automated tests after fixes
3. ✅ Always report test results
4. ✅ Always analyze test failures if they occur
5. ✅ Always implement additional fixes if tests fail

## Exception

User can skip tests by saying:
- "skip tests"
- "don't test this"
- "I'll test manually"

Otherwise, tests run automatically.
