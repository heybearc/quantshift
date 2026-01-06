# Daily Testing Workflow - Simple Guide

## 🎯 How to Use This System

### Before Every Deployment (1-2 minutes)

```bash
# Just run this command
cd applications/quantshift/apps/dashboard
BASE_URL=http://10.92.3.29:3001 \
TEST_USER_EMAIL=admin@quantshift.local \
TEST_USER_PASSWORD='AdminPass123!' \
npm run test:smoke:quick
```

**If tests pass:** ✅ Deploy  
**If tests fail:** ❌ Ask me "Fix the failing [test name] test"

---

## 🤖 How to Request Tests

### After Deploying a New Feature

Just say:

```
"Create tests for [feature name]"
```

**Examples:**
- "Create tests for the new portfolio analytics"
- "Add tests for the risk management page"
- "Test the trade execution workflow"

I'll create the tests automatically.

---

## 📊 How to Check Test Status

### See What's Failing

```
"What test failures need fixing?"
```

I'll show you:
- Which tests are failing
- Why they're failing
- Priority level
- Estimated fix time

---

## 🔧 How to Fix Failing Tests

### Simple Request

```
"Fix the failing [test name] test"
```

**Examples:**
- "Fix the failing dashboard card test"
- "Fix all medium priority test failures"
- "Debug the API timeout test"

I'll fix it automatically.

---

## 📋 Where Failures Are Tracked

### 3 Places:

1. **HTML Report** (automatic)
   ```bash
   npm run test:report
   ```

2. **TEST-FAILURE-TRACKING.md** (this repo)
   - Lists all failures
   - Shows priorities
   - Tracks fix status

3. **Your TODO List** (automatic)
   - Failed tests → TODO items
   - Organized by priority

---

## 🗓️ Regular Schedule

### Daily (Before Deployment)
```bash
npm run test:smoke:quick  # 1-2 minutes
```

### Weekly (Comprehensive)
```bash
npm run test:e2e  # 5-10 minutes
```

Then say: "Update test failure tracking"

### Monthly
Say: "Review and update all tests"

---

## 🎓 Quick Commands

| What You Want | What to Say |
|---------------|-------------|
| Create tests | "Create tests for [feature]" |
| Fix tests | "Fix the failing [test] test" |
| Check status | "What test failures need fixing?" |
| Run tests | Use bash commands above |
| View report | `npm run test:report` |
| Debug test | "Debug why [test] is failing" |

---

## 📝 Example Workflow

### Scenario: You just deployed a new trading dashboard

**Step 1:** Create tests
```
You: "Create tests for the new trading dashboard"
Me: [Creates comprehensive tests automatically]
```

**Step 2:** Run tests
```bash
npm run test:e2e
```

**Step 3:** Check results
```
You: "What test failures need fixing?"
Me: "2 tests failing: [details]"
```

**Step 4:** Fix failures
```
You: "Fix all test failures"
Me: [Fixes tests automatically]
```

**Step 5:** Verify
```bash
npm run test:smoke:quick
```

**Done!** ✅

---

## 🎯 That's It!

**You don't need to:**
- ❌ Write tests manually
- ❌ Track failures manually
- ❌ Debug tests manually
- ❌ Update documentation manually

**I handle all of that.**

**You just need to:**
- ✅ Run tests before deployment
- ✅ Ask me to create tests for new features
- ✅ Ask me to fix failing tests

---

## 📞 Common Questions

### "How do I know what needs testing?"

Ask me: "What features don't have tests yet?"

### "How do I prioritize test fixes?"

Check `TEST-FAILURE-TRACKING.md` - I prioritize them for you.

### "Can I run tests locally?"

Yes! Just change `BASE_URL=http://localhost:3000`

### "What if tests are too slow?"

Tell me: "Tests are too slow, optimize them"

### "Should I use Playwright or Cypress?"

Read `PLAYWRIGHT-EVALUATION.md` - TL;DR: Stick with Playwright

---

## 🎉 Summary

**Before:** Manual testing, losing track, 30-60 minutes per deployment

**After:** Automated testing, AI-tracked, 1-2 minutes per deployment

**Your job:** Run one command before deployment

**My job:** Everything else

---

**Last Updated:** January 5, 2026  
**Status:** Production Ready  
**Maintenance:** Fully Automated
