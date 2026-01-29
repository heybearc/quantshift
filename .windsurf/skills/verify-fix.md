---
name: verify-fix
description: Verify bug fixes using automated tests instead of manual testing
activation: automatic
---

# Verify Fix Skill

## Purpose

Automatically verify bug fixes using Playwright tests instead of suggesting manual testing.

## When This Activates

After implementing any fix during debugging:
- Authentication issues
- Routing/navigation bugs
- UI component issues
- API endpoint errors
- State management bugs
- Any user-reported issue

## Verification Process

### 1. Deploy Fix
```
Auto-deploy handles deployment to STANDBY
```

### 2. Run Tests
```bash
# Quick smoke tests (default)
ssh [container] 'cd [app-path] && npm run test:smoke:quick'

# Or full suite if requested
ssh [container] 'cd [app-path] && npm run test:e2e'
```

### 3. Analyze Results

**If tests pass:**
```
✅ Fix deployed
✅ Tests passing (X/X)
✅ [Specific functionality] working correctly
```

**If tests fail:**
```
❌ Tests failing (X/Y passing)
❌ [Test name] failed: [Error message]

Analyzing failure...
[Implement additional fix]
[Deploy and test again]
```

## Response Pattern

### Standard Verification

```
Implemented fix for [issue].

Deploying to STANDBY...
✅ Deployed

Running smoke tests...
✅ All tests passing (4/4)
✅ Login flow working
✅ Navigation working
✅ Event selection working
✅ No JavaScript errors

Fix verified and ready.
```

### With Test Failures

```
Implemented fix for [issue].

Deploying to STANDBY...
✅ Deployed

Running smoke tests...
❌ Tests failing (3/4 passing)

Failed test: Navigation test
Error: Timeout waiting for element 'button[data-testid="next"]'

Analyzing...
Found issue: Button was renamed in recent refactor.
Implementing additional fix...

✅ Fix deployed
✅ Tests passing (4/4)
✅ Navigation working correctly
```

## What NOT To Say

❌ **Never suggest:**
- "Log in and test it"
- "Navigate to this URL"
- "Try clicking this button"
- "See if it works now"
- "Check the browser"
- "Enter your credentials"

## What TO Say

✅ **Always:**
- "Running tests to verify fix..."
- "Tests passing - fix verified"
- "Tests failing - implementing additional fix"
- "Fix deployed and verified via automated tests"

## Test Selection

### Quick Smoke Tests (Default)
- Run after every fix
- Fast execution (15-30 seconds)
- Critical paths only
- Use for active debugging

### Full Test Suite (On Request)
- Run before version bump
- Comprehensive coverage (1-3 minutes)
- All features and edge cases
- Use for pre-release validation

## Container Mapping

**TheoShift STANDBY:**
- Container: `blue-theoshift`
- Path: `/opt/theoshift`
- Tests: `npm run test:smoke:quick`

**LDC Tools STANDBY:**
- Container: `ldc-staging`
- Path: `/opt/ldc-tools/frontend`
- Tests: `npm run test:smoke:quick`

**QuantShift:**
- Container: `qs-dashboard`
- Path: `/opt/quantshift`
- Tests: `npm run test:smoke:quick`

## Benefits

**Replaces manual testing:**
- No browser interaction
- No manual credential entry
- No URL navigation
- Immediate verification

**Provides confidence:**
- Automated verification after every fix
- Tests cover critical paths
- Catches regressions
- Clear pass/fail status

**Faster debugging:**
- Fix → Deploy → Test → Report (all automatic)
- No context switching
- Continuous verification
- Immediate feedback

## User Control

User can skip tests by saying:
- "skip tests"
- "don't test"
- "I'll test manually"

Otherwise, tests run automatically after every fix.
