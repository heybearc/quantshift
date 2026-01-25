# Archive Directory

**Created:** 2026-01-25  
**Purpose:** Historical documentation from QuantShift development

---

## Contents

### 2026-01-25-pre-restructure/
**Zombie app directories from incomplete Jan 5-6, 2026 restructure:**
- `apps-admin-web/` - Old admin web app (1.4MB)
- `apps-dashboard/` - Old dashboard app (4.6MB)

**Why archived:**
- Jan 5, 2026: Restructure consolidated these apps to root `/app/` directory
- Apps were migrated but old directories never deleted
- Root app is what's actually deployed and running
- These directories contained outdated code (6MB total)

### 2026-01-25-restructure-docs/
**Restructure completion documentation:**
- `RESTRUCTURE-COMPLETE.md` - Restructure completion report
- `RESTRUCTURE-PLAN.md` - Original restructure plan
- `DEPLOYMENT-SUCCESS.md` - Deployment success report
- `PRODUCTION_DEPLOYMENT_COMPLETE.md` - Production deployment report

**Why archived:**
- Historical record of Jan 5-6, 2026 restructure
- Work is complete, docs are reference only
- Not needed for active development

### 2026-01-25-phase-docs/
**Phase development documentation:**
- `PHASE1_BACKTEST_ANALYSIS.md` - Backtest results (Dec 26, 2025)
- `PHASE2_INTEGRATION_PLAN.md` - Integration plan
- `PHASE5_IMPLEMENTATION_PLAN.md` - Implementation plan
- `PHASE6_ADMIN_PLATFORM.md` - Admin platform development plan
- `PHASE6_PROGRESS.md` - Phase 6 progress tracking
- `PHASE_2_UI_ENHANCEMENT_PLAN.md` - UI enhancement plan

**Why archived:**
- Historical development phases (Dec 2025 - Jan 2026)
- Phases are complete
- Reference value only

### 2026-01-25-old-status/
**Old status snapshots:**
- `CURRENT_STATE.md` - Dec 26, 2025 snapshot
- `CURRENT-STATUS-AND-ROADMAP.md` - Jan 6, 2026 status
- `PLATFORM_BUILD_STATUS.md` - Build status snapshot

**Why archived:**
- Outdated status information
- Superseded by `TASK-STATE.md` and `.cloudy-work` context
- Historical reference only

---

## Retention Policy

**Keep for:** 90 days minimum  
**Review:** March 2026  
**Delete if:** No references found, no historical value identified

---

## Restoration

If you need to restore any archived content:
```bash
# View archive
ls -la _archive/

# Restore file
git mv _archive/[directory]/[file] ./

# Restore directory
git mv _archive/[directory]/[folder] ./[folder]
```

---

**All archived content is tracked in git history.**
