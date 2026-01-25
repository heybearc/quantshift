# /bump Workflow Compatibility Analysis for QuantShift

**Date:** 2026-01-25  
**Purpose:** Evaluate if generic `/bump` workflow can work with QuantShift's single-container deployment

**CRITICAL:** `/bump` is a **shared workflow** (symlink to `.cloudy-work/.windsurf/workflows/bump.md`). Cannot modify without breaking TheoShift and LDC Tools.

---

## Executive Summary

**Verdict:** ✅ **Generic /bump workflow CAN work with QuantShift** with minor adaptations

**Approach:** Create QuantShift-specific **wrapper/supplement** workflow, not a replacement

**Recommendation:** Option C - Keep generic /bump, add QuantShift-specific steps as separate workflow

---

## Generic /bump Workflow Analysis

### What It Assumes (Blue-Green Model)

**Step 7: Deploy to STANDBY**
```bash
# Identify STANDBY first
mcp3_get_deployment_status

# Deploy to STANDBY only
ssh root@[STANDBY_IP] "cd /opt/theoshift && git pull && npm run build && pm2 restart theoshift"
```

**Key assumptions:**
1. **Two containers:** LIVE and STANDBY that can swap
2. **HAProxy routing:** Traffic can switch between containers
3. **MCP server:** `deploy_to_standby` tool detects STANDBY via HAProxy
4. **File-based release notes:** Markdown files in `/release-notes/`
5. **Testing on STANDBY:** Before switching traffic

### What It Does Well (Universal)

✅ **Version bump** - Works for any app  
✅ **Help documentation analysis** - Works for any app  
✅ **Commit and push** - Works for any app  
✅ **Test enforcement** - Works for any app  
✅ **User approval gates** - Works for any app

---

## QuantShift Reality Check

### Deployment Model: Single Container

**Container:** qs-dashboard (LXC 137 - 10.92.3.29)  
**No STANDBY:** Only one container running the app  
**No HAProxy routing:** Direct access to single container  
**Deployment:** Direct deploy to production (no blue-green swap)

### QuantShift-Specific Features

1. **Database-driven release notes** (not file-based)
   - Prisma schema with ReleaseNote model
   - `scripts/create-release.ts` to insert into DB
   - Version banner triggered by `isPublished: true`

2. **Version tracking** 
   - `lib/version.ts` with APP_VERSION constant
   - Must be updated alongside package.json

3. **Single-container deployment**
   - No STANDBY to test on
   - Deploy directly to production
   - Brief downtime acceptable (PM2 restart)

---

## Compatibility Analysis

### What Works As-Is

✅ **Step 0:** Load governance - Works  
✅ **Step 1:** Analyze recent changes - Works  
✅ **Step 2:** Determine version type - Works  
✅ **Step 3:** Help documentation analysis - Works  
✅ **Step 4:** Update version in package.json - Works  
✅ **Step 6:** Commit everything - Works (adjust branch name)  
✅ **Step 9:** Report and wait for approval - Works

### What Needs Adaptation

⚠️ **Step 5:** Create release notes
- Generic: Creates markdown file in `/release-notes/vX.Y.Z.md`
- QuantShift: Needs database insertion via `scripts/create-release.ts`
- **Solution:** Add QuantShift-specific step after generic workflow

⚠️ **Step 7:** Deploy to STANDBY
- Generic: Deploys to STANDBY container via MCP
- QuantShift: No STANDBY - deploy directly to production
- **Solution:** Skip MCP deployment, use direct SSH deploy

⚠️ **Step 8:** Run tests on STANDBY
- Generic: Tests run on STANDBY before traffic switch
- QuantShift: No STANDBY to test on
- **Solution:** Run tests on production after deploy (smoke tests)

### What Doesn't Apply

❌ **MCP `deploy_to_standby` tool**
- Designed for blue-green deployments
- Queries HAProxy for STANDBY container
- QuantShift has no STANDBY to detect

❌ **Traffic switching** (Step 9)
- Generic: Switch HAProxy from LIVE to STANDBY
- QuantShift: No traffic to switch (single container)

---

## MCP Server Compatibility

### Question: Does `deploy_to_standby` work with single-container apps?

**Answer:** ❌ **NO** - MCP server expects blue-green deployment model

**Evidence from MCP tool description:**
```
Deploy code to STANDBY server with automated health checks
```

**What it does:**
1. Detects current STANDBY (queries HAProxy)
2. Creates backup
3. Pulls latest code from GitHub
4. Installs dependencies
5. Builds application
6. Restarts PM2 service
7. Runs health checks

**Problem for QuantShift:**
- Step 1 fails: No HAProxy config for QuantShift
- No STANDBY container to detect
- MCP tool would error or not find target

**Conclusion:** Cannot use MCP `deploy_to_standby` for QuantShift

---

## Recommended Approach

### Option C: Keep Generic /bump + QuantShift Supplement

**Why this is best:**
1. ✅ Doesn't modify shared workflow (safe for other apps)
2. ✅ Reuses 90% of generic workflow logic
3. ✅ Adds only QuantShift-specific steps
4. ✅ Clear separation of concerns
5. ✅ Easy to maintain

### Implementation Strategy

**Create:** `.windsurf/workflows/bump-quantshift.md` (local to QuantShift repo)

**Structure:**
```markdown
# QuantShift Version Bump Workflow

**Purpose:** QuantShift-specific wrapper for generic /bump workflow

## Step 1-6: Use Generic /bump Workflow

Follow generic /bump workflow steps 1-6:
- Load governance
- Analyze changes
- Determine version type
- Help documentation analysis
- Update package.json version
- Commit changes

## Step 7: QuantShift-Specific Release Notes

**Create database release note:**
1. Edit `scripts/create-release.ts` with new version info
2. Run on container: `ssh qs-dashboard 'cd /opt/quantshift && npx tsx scripts/create-release.ts'`
3. Verify release note created in database

**Update version constant:**
1. Edit `lib/version.ts` - update APP_VERSION
2. Commit: `git add lib/version.ts && git commit -m "chore: update version constant"`

## Step 8: Deploy to Production (Single Container)

**Direct deployment (no STANDBY):**
```bash
ssh qs-dashboard 'cd /opt/quantshift && \
  git pull origin main && \
  npm install && \
  npm run build && \
  pm2 restart quantshift-admin'
```

**Verify deployment:**
```bash
ssh qs-dashboard 'pm2 status quantshift-admin'
ssh qs-dashboard 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/login'
```

## Step 9: Run Smoke Tests (Post-Deploy)

**Note:** QuantShift has no STANDBY, so tests run on production after deploy

```bash
ssh qs-dashboard 'cd /opt/quantshift && npm run test:smoke:quick'
```

**If tests fail:**
- Investigate logs: `ssh qs-dashboard 'pm2 logs quantshift-admin --lines 50'`
- Fix issues and redeploy
- Re-run smoke tests

## Step 10: Verify Release

**Check version banner:**
- Visit https://trader.cloudigan.net/login
- Verify version banner appears with new version
- Verify release notes accessible

**Manual verification:**
- Test new features
- Verify help documentation
- Check for errors in PM2 logs

## Step 11: Report Completion

✅ Version X.Y.Z Deployed to Production

- Version: X.Y.Z
- Release notes: Created in database
- Deployment: Production (qs-dashboard)
- Tests: Smoke tests passing
- Version banner: Verified working

## Notes

- **No STANDBY:** QuantShift uses single-container deployment
- **Brief downtime:** PM2 restart causes ~2-3 second downtime (acceptable)
- **Database release notes:** Different from file-based approach
- **Post-deploy testing:** Tests run on production after deploy
```

---

## Comparison: Generic vs QuantShift-Specific

| Step | Generic /bump | QuantShift Variant |
|------|---------------|-------------------|
| 1-6 | ✅ Use as-is | ✅ Use as-is |
| Release notes | Markdown file | Database + `create-release.ts` |
| Version tracking | package.json only | package.json + `lib/version.ts` |
| Deployment | MCP to STANDBY | Direct SSH to production |
| Testing | Pre-deploy on STANDBY | Post-deploy on production |
| Traffic switch | HAProxy swap | N/A (single container) |
| Downtime | Zero (blue-green) | ~2-3 seconds (PM2 restart) |

---

## Action Plan

### Immediate (Today)

1. **Create** `.windsurf/workflows/bump-quantshift.md` (local workflow)
2. **Document** QuantShift-specific deployment steps
3. **Test** on next version bump (dry run)

### Before Next Release

1. **Prepare** `scripts/create-release.ts` template
2. **Verify** smoke tests work on container
3. **Document** rollback procedure for single-container

### Future Consideration

**If QuantShift grows:**
- Add second container (LXC 138) for blue-green deployment
- Then can use generic /bump workflow fully
- Migrate to MCP-based deployment

---

## Decision Matrix

### Should we modify generic /bump? ❌ NO

**Reasons:**
- Shared workflow used by TheoShift and LDC Tools
- Breaking changes affect multiple apps
- Blue-green assumptions are correct for those apps
- QuantShift is the exception, not the rule

### Should we create QuantShift-specific variant? ✅ YES

**Reasons:**
- Single-container deployment is fundamentally different
- Database release notes are QuantShift-specific
- Local workflow doesn't affect other apps
- Can reuse 90% of generic workflow logic
- Clear documentation of differences

### Should we extend MCP server? ⏸️ MAYBE LATER

**Reasons to wait:**
- MCP server works well for blue-green deployments
- QuantShift is only single-container app currently
- Adding single-container support adds complexity
- Can revisit if more single-container apps added

---

## Risks and Mitigations

### Risk 1: Brief Production Downtime

**Impact:** ~2-3 seconds during PM2 restart  
**Mitigation:** 
- Deploy during low-traffic periods
- Notify users of maintenance window
- Keep restart time minimal (pre-build before restart)

### Risk 2: No Pre-Production Testing

**Impact:** Bugs deploy directly to production  
**Mitigation:**
- Rigorous local testing before deploy
- Smoke tests immediately after deploy
- Quick rollback procedure documented
- Monitor PM2 logs during deploy

### Risk 3: Database Release Notes Failure

**Impact:** Version banner doesn't appear  
**Mitigation:**
- Test `create-release.ts` script before deploy
- Verify database connection before running
- Manual verification after deploy
- Rollback: Delete release note from DB if needed

---

## Rollback Procedure (QuantShift-Specific)

**If deployment fails:**

```bash
# 1. Check current commit
ssh qs-dashboard 'cd /opt/quantshift && git log -1 --oneline'

# 2. Rollback to previous commit
ssh qs-dashboard 'cd /opt/quantshift && git reset --hard HEAD~1'

# 3. Rebuild and restart
ssh qs-dashboard 'cd /opt/quantshift && npm run build && pm2 restart quantshift-admin'

# 4. Verify rollback
ssh qs-dashboard 'curl -s http://localhost:3001/login | head -20'

# 5. Delete bad release note from database (if created)
ssh qs-dashboard 'cd /opt/quantshift && npx prisma studio'
# Manually delete release note entry
```

---

## Conclusion

**Verdict:** ✅ **Create QuantShift-specific workflow variant**

**Approach:**
1. Keep generic `/bump` workflow unchanged (shared, don't break other apps)
2. Create `.windsurf/workflows/bump-quantshift.md` (local to QuantShift)
3. Reuse steps 1-6 from generic workflow
4. Add QuantShift-specific steps for:
   - Database release notes
   - Version constant update
   - Direct production deployment
   - Post-deploy smoke tests

**Benefits:**
- ✅ Safe for other apps (no shared workflow changes)
- ✅ Tailored to QuantShift's single-container model
- ✅ Documents QuantShift-specific release process
- ✅ Reuses generic workflow logic where applicable
- ✅ Clear, maintainable, testable

**Next Step:** Create `.windsurf/workflows/bump-quantshift.md` with implementation details

---

**Status:** Analysis complete. Ready to implement QuantShift-specific workflow variant.
