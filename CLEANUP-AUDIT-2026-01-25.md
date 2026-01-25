# QuantShift Repository Cleanup Audit

**Date:** 2026-01-25  
**Purpose:** Comprehensive audit to cleanup obsolete documentation while preserving application integrity

---

## Current State Analysis

**Repository structure:**
- Root has 33+ markdown documentation files
- Multiple apps exist: `admin-web/`, `dashboard/`, `bots/`, `admin-api/`
- Recent restructure (Jan 5-6, 2026) consolidated apps
- Cloudy-Work submodule added (Jan 25, 2026)

**Key findings:**
1. Many docs reference old structure (`apps/admin-web`, `apps/dashboard`)
2. Both `admin-web/` and `dashboard/` directories still exist
3. Documentation describes completed phases/restructures
4. Multiple overlapping roadmaps and status files

---

## File Categorization

### ✅ KEEP (Active/Current Documentation)

**Essential operational docs:**
- `README.md` - Main repo documentation (current, accurate)
- `DECISIONS.md` - Repo-local decisions (D-QS-001, D-QS-002)
- `TASK-STATE.md` - Current work tracking
- `QUANTSHIFT-RELEASE-SYSTEM.md` - Preserved release note system (created today)
- `CHANGELOG.md` - Version history (keep updated)

**Configuration files (DO NOT TOUCH):**
- `.gitignore`
- `.gitmodules`
- `package.json`
- `package-lock.json`
- `tsconfig.json`
- `next.config.js`
- `playwright.config.ts`
- `postcss.config.js`
- `tailwind.config.js`
- `ecosystem.config.js`
- `pyproject.toml`
- `.env.example`
- `.env.test`
- `.env.email`

**Scripts (DO NOT TOUCH):**
- `deploy.sh`
- `convert_admin_dark_theme.sh`
- `fix_admin_pages.sh`
- `test-redis.js`
- `backtest_ma_crossover.py`
- `test_email_notifications.py`
- `test_phase0.py`

---

### 📦 ARCHIVE (Historical Reference - Completed Work)

**Restructure documentation (Jan 5-6, 2026):**
- `RESTRUCTURE-COMPLETE.md` - Restructure completion report
- `RESTRUCTURE-PLAN.md` - Original restructure plan
- `DEPLOYMENT-SUCCESS.md` - Deployment success report
- `PRODUCTION_DEPLOYMENT_COMPLETE.md` - Production deployment report

**Phase documentation (Dec 26, 2025 - Jan 6, 2026):**
- `PHASE1_BACKTEST_ANALYSIS.md` - Backtest results (failed validation)
- `PHASE2_INTEGRATION_PLAN.md` - Integration plan
- `PHASE5_IMPLEMENTATION_PLAN.md` - Implementation plan
- `PHASE6_ADMIN_PLATFORM.md` - Admin platform development plan
- `PHASE6_PROGRESS.md` - Phase 6 progress tracking
- `PHASE_2_UI_ENHANCEMENT_PLAN.md` - UI enhancement plan

**Old status/roadmap files:**
- `CURRENT_STATE.md` - Dec 26, 2025 snapshot (outdated)
- `CURRENT-STATUS-AND-ROADMAP.md` - Jan 6, 2026 status (outdated)
- `PLATFORM_BUILD_STATUS.md` - Build status snapshot

**Reason:** Historical value for understanding decisions, but not actively needed for development.

---

### ⚠️ QUARANTINE (Review Before Delete)

**Potentially redundant with current structure:**
- `IMPLEMENTATION_ROADMAP.md` - May overlap with current plans
- `ROADMAP_MANAGEMENT.md` - Roadmap management approach
- `ADMIN_PLATFORM_PROPOSAL.md` - Original proposal (pre-implementation)
- `BOT_ENHANCEMENT_ROADMAP.md` - Bot enhancement plans
- `DEPLOYMENT_STRATEGY_FOR_IMPROVEMENTS.md` - Deployment strategy

**Testing/development guides (may be superseded):**
- `TESTING_AUTH.md` - Auth testing guide
- `TESTING_GUIDE.md` - General testing guide
- `CONTAINER_DEVELOPMENT_WORKFLOW.md` - Container dev workflow
- `NEXTJS_SETUP.md` - Next.js setup guide

**Integration guides:**
- `BOT_INTEGRATION_GUIDE.md` - Bot integration documentation
- `ENTERPRISE_USER_MANAGEMENT.md` - Enterprise user management
- `RELEASE_NOTES_SYSTEM.md` - Release notes system (may overlap with QUANTSHIFT-RELEASE-SYSTEM.md)

**Other guides:**
- `ARCHITECTURE.md` - Architecture documentation (check if current)
- `DEPLOYMENT_GUIDE.md` - Deployment guide (check against current process)
- `PLATFORM_GUIDE.md` - Platform guide

**Reason:** Need to verify if content is still relevant or superseded by newer docs/practices.

---

### 🗑️ DELETE (Obsolete/Redundant)

**None identified yet** - All files need review before deletion to ensure no breaking references.

---

## Verification Checklist

Before moving/deleting any files, verify:

1. **No code imports** - Check if any `.ts`, `.tsx`, `.js` files import from these docs
2. **No script references** - Check if deployment/build scripts reference these files
3. **No workflow references** - Check if `.windsurf/workflows/` reference these files
4. **No README links** - Check if README.md or other active docs link to these files

---

## Apps Directory Analysis

**Current structure:**
```
apps/
├── admin-api/     (22 items) - Backend API
├── admin-web/     (123 items) - Main Next.js app (ACTIVE)
├── bots/          (77 items) - Trading bots
├── dashboard/     (114 items) - Old dashboard app (UNCLEAR STATUS)
```

**Questions to resolve:**
1. Is `apps/dashboard/` still used or was it consolidated into root?
2. Is `apps/admin-web/` the active app or was it moved to root `/app/`?
3. What is the relationship between root-level files and `apps/admin-web/`?

**Evidence:**
- Root has `app/`, `components/`, `lib/` directories (Next.js structure)
- Root `package.json` has Next.js scripts
- `apps/admin-web/` also has complete Next.js structure
- `apps/dashboard/` has test files and old structure

**Hypothesis:** 
- Root-level Next.js app is the ACTIVE application
- `apps/admin-web/` may be old structure not yet cleaned up
- `apps/dashboard/` is definitely old structure (has test results, old docs)

**Action needed:** Verify which structure is actually deployed and running.

---

## Next Steps

1. **Verify active application structure** - Determine which app directory is actually running
2. **Check for breaking references** - Grep for imports/links to docs being moved
3. **Create archive structure** - `_archive/YYYY-MM-DD-description/`
4. **Create quarantine structure** - `_quarantine/review-YYYY-MM-DD/`
5. **Move files systematically** - Archive first, then quarantine
6. **Test application** - Ensure nothing breaks
7. **Update TASK-STATE.md** - Document cleanup completion

---

## Proposed Directory Structure

```
_archive/
├── 2026-01-25-restructure-docs/
│   ├── RESTRUCTURE-COMPLETE.md
│   ├── RESTRUCTURE-PLAN.md
│   ├── DEPLOYMENT-SUCCESS.md
│   └── PRODUCTION_DEPLOYMENT_COMPLETE.md
├── 2026-01-25-phase-docs/
│   ├── PHASE1_BACKTEST_ANALYSIS.md
│   ├── PHASE2_INTEGRATION_PLAN.md
│   ├── PHASE5_IMPLEMENTATION_PLAN.md
│   ├── PHASE6_ADMIN_PLATFORM.md
│   ├── PHASE6_PROGRESS.md
│   └── PHASE_2_UI_ENHANCEMENT_PLAN.md
└── 2026-01-25-old-status/
    ├── CURRENT_STATE.md
    ├── CURRENT-STATUS-AND-ROADMAP.md
    └── PLATFORM_BUILD_STATUS.md

_quarantine/
└── review-2026-01-25/
    ├── IMPLEMENTATION_ROADMAP.md
    ├── ROADMAP_MANAGEMENT.md
    ├── ADMIN_PLATFORM_PROPOSAL.md
    ├── BOT_ENHANCEMENT_ROADMAP.md
    ├── DEPLOYMENT_STRATEGY_FOR_IMPROVEMENTS.md
    ├── TESTING_AUTH.md
    ├── TESTING_GUIDE.md
    ├── CONTAINER_DEVELOPMENT_WORKFLOW.md
    ├── NEXTJS_SETUP.md
    ├── BOT_INTEGRATION_GUIDE.md
    ├── ENTERPRISE_USER_MANAGEMENT.md
    ├── RELEASE_NOTES_SYSTEM.md
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT_GUIDE.md
    └── PLATFORM_GUIDE.md
```

---

## Risk Assessment

**LOW RISK:**
- Moving completed phase docs to archive
- Moving old status snapshots to archive

**MEDIUM RISK:**
- Quarantining guides that may have active references
- Moving architecture/deployment docs

**HIGH RISK:**
- Deleting anything without thorough verification
- Moving files that scripts/workflows reference

**MITIGATION:**
- Use git to track all moves (easy rollback)
- Verify no breaking references before moving
- Test application after each batch of moves
- Keep quarantine for 30 days before deletion

---

## Status

**Current:** Audit complete, awaiting user approval to proceed with cleanup.

**Recommended approach:**
1. Start with LOW RISK archive moves
2. Verify application still works
3. Move MEDIUM RISK files to quarantine
4. Review quarantine files individually before final decision
5. Never delete without explicit approval
