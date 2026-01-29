---
name: generate-tests
description: Dynamically generate Playwright tests based on code changes and features
activation: automatic
---

# Generate Tests Skill

## Purpose

Dynamically generate Playwright tests based on:
- Code changes in current session
- Features being implemented
- Bugs being fixed
- Refactoring work (e.g., renaming patterns)

## When This Activates

### Automatic Generation

1. **During major refactoring:**
   - User says "refactor X to Y across the app"
   - Example: "Replace all 'attendant' with 'volunteer'"
   - Generate tests to verify all instances changed

2. **After implementing new features:**
   - User completes a new feature implementation
   - Generate tests to verify feature works end-to-end

3. **Before /test-release:**
   - Analyze recent commits since last release
   - Generate custom test suite for changes made
   - Verify all changes work correctly

4. **After fixing bugs:**
   - Generate regression test for the bug
   - Ensure bug doesn't reoccur

## Test Generation Process

### 1. Analyze Changes
```bash
# Get recent commits since last release/tag
git log --oneline v3.3.0..HEAD

# Get detailed diff
git diff v3.3.0..HEAD

# Analyze changed files
git diff --name-only v3.3.0..HEAD
```

### 2. Identify Test Scenarios

**For refactoring (e.g., attendant → volunteer):**
- UI text changes (buttons, labels, headings)
- Route changes (/attendants → /volunteers)
- API endpoint changes
- Database field references
- Component prop names
- Form field names

**For new features:**
- User flow from start to finish
- Edge cases and error handling
- Integration with existing features
- Permission/authentication checks

**For bug fixes:**
- Reproduce the original bug scenario
- Verify fix resolves the issue
- Test related functionality

### 3. Generate Test Code

Create Playwright test file dynamically:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Generated Tests - [Feature/Refactor Name]', () => {
  // Login helper
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/signin');
    await page.fill('input[id="email"]', process.env.TEST_USER_EMAIL);
    await page.fill('input[id="password"]', process.env.TEST_USER_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForNavigation();
  });

  // Generated test cases based on changes
  test('Verify [specific change]', async ({ page }) => {
    // Test implementation
  });
});
```

### 4. Run Generated Tests
```bash
# Save generated test
# Run on STANDBY
ssh [container] 'cd [app-path] && npm run test:e2e -- tests/generated-[timestamp].spec.ts'
```

### 5. Analyze Results

**If tests pass:**
- Report success
- Keep generated test for regression suite
- Mark changes as verified

**If tests fail:**
- Analyze failure
- Identify what was missed
- Implement fix
- Regenerate/update tests
- Run again

## Example: Attendant → Volunteer Refactor

### Analysis
```
Changes detected:
- 47 files modified
- Pattern: "attendant" → "volunteer" (case variations)
- Routes: /attendants → /volunteers
- API: /api/attendants → /api/volunteers
- Components: AttendantList → VolunteerList
- Props: attendantId → volunteerId
```

### Generated Test Scenarios
```typescript
test.describe('Attendant → Volunteer Refactor Verification', () => {
  test('UI text updated - navigation menu', async ({ page }) => {
    await page.goto('/');
    const navText = await page.textContent('nav');
    expect(navText).toContain('Volunteers');
    expect(navText).not.toContain('Attendants');
  });

  test('Route /volunteers works', async ({ page }) => {
    await page.goto('/volunteers');
    await expect(page.locator('h1')).toContainText('Volunteers');
  });

  test('Old route /attendants redirects or 404s', async ({ page }) => {
    const response = await page.goto('/attendants');
    expect([301, 302, 404]).toContain(response.status());
  });

  test('Volunteer list displays correctly', async ({ page }) => {
    await page.goto('/volunteers');
    await expect(page.locator('[data-testid="volunteer-list"]')).toBeVisible();
  });

  test('Create volunteer form uses correct terminology', async ({ page }) => {
    await page.goto('/volunteers/new');
    const formText = await page.textContent('form');
    expect(formText).toContain('volunteer');
    expect(formText).not.toContain('attendant');
  });

  test('API endpoint /api/volunteers works', async ({ page }) => {
    const response = await page.request.get('/api/volunteers');
    expect(response.ok()).toBeTruthy();
  });

  test('Database queries return volunteer data', async ({ page }) => {
    await page.goto('/volunteers');
    const volunteers = await page.locator('[data-testid="volunteer-item"]').count();
    expect(volunteers).toBeGreaterThan(0);
  });

  test('No console errors referencing "attendant"', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().toLowerCase().includes('attendant')) {
        errors.push(msg.text());
      }
    });
    
    await page.goto('/volunteers');
    await page.waitForTimeout(2000);
    
    expect(errors.length).toBe(0);
  });
});
```

### Execution Flow
```
1. Analyze git diff for attendant → volunteer changes
2. Generate 8 test scenarios
3. Create tests/generated-volunteer-refactor.spec.ts
4. Deploy to STANDBY
5. Run generated tests
6. Results: 6/8 passing, 2 failing
   - Failed: Old route /attendants still accessible
   - Failed: One form still says "attendant"
7. Analyze failures
8. Implement fixes for missed instances
9. Deploy fixes
10. Run tests again
11. Results: 8/8 passing
12. Report: Refactor complete and verified
```

## Integration Points

### With Auto-Deploy
```
1. User: "Replace all attendant with volunteer"
2. Windsurf: [Performs refactor across codebase]
3. Auto-deploy: Deploys to STANDBY
4. Generate-tests: Analyzes changes, generates tests
5. Auto-test: Runs generated tests
6. Report: "Refactor complete, 8/8 tests passing"
```

### With /test-release
```
1. User: "/test-release theoshift"
2. Analyze commits since last release
3. Generate custom test suite for changes
4. Run existing smoke tests
5. Run generated custom tests
6. Report comprehensive results
7. If failures: implement fixes and retest
```

## Test File Management

**Generated test files:**
- Location: `tests/generated-[feature]-[timestamp].spec.ts`
- Kept for regression testing
- Can be reviewed and refined by user
- Automatically cleaned up after 30 days (configurable)

**Test naming convention:**
```
tests/generated-volunteer-refactor-20260129.spec.ts
tests/generated-event-filtering-20260129.spec.ts
tests/generated-auth-fix-20260129.spec.ts
```

## Prompt for Test Generation

When generating tests, I will:

1. **Analyze the change:**
   - What was changed?
   - What functionality is affected?
   - What could break?

2. **Identify test scenarios:**
   - Happy path
   - Edge cases
   - Error conditions
   - Integration points
   - UI/UX verification

3. **Generate test code:**
   - Use Playwright best practices
   - Include proper selectors
   - Add assertions
   - Handle async operations
   - Include error handling

4. **Run and iterate:**
   - Execute tests
   - Analyze failures
   - Fix issues
   - Regenerate/update tests
   - Repeat until passing

## Benefits

**Comprehensive verification:**
- Tests cover actual changes made
- Not just generic smoke tests
- Catches edge cases specific to the change

**Automated regression prevention:**
- Generated tests become part of test suite
- Future changes verified against these tests
- Prevents reintroduction of bugs

**Faster development:**
- No manual test writing
- Immediate verification
- Catches issues before release

**Refactoring confidence:**
- Large refactors verified automatically
- Ensures nothing was missed
- Comprehensive coverage

## User Control

**Enable for session:**
```bash
# Generate tests for all changes
touch .generate-tests
```

**Disable:**
```bash
rm .generate-tests
```

**Manual trigger:**
- "Generate tests for these changes"
- "Create tests for this refactor"
- "Verify this feature with tests"
