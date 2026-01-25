# Archived Roadmaps and Planning Documents

**Created:** 2026-01-25  
**Purpose:** Historical roadmaps and planning documents superseded by new control-plane-based roadmap

---

## Contents

### Roadmaps (5 files)
- `IMPLEMENTATION_ROADMAP.md` - Original implementation roadmap (Dec 2025 - Jan 2026)
- `BOT_ENHANCEMENT_ROADMAP.md` - Trading bot enhancement plans
- `ROADMAP_MANAGEMENT.md` - Roadmap management best practices
- `ADMIN_PLATFORM_PROPOSAL.md` - Admin platform proposal and features
- `DEPLOYMENT_STRATEGY_FOR_IMPROVEMENTS.md` - Deployment strategy planning

### Why Archived

**Superseded by:** `/ROADMAP.md` (new control-plane-based roadmap)

**Reason:** Consolidation of all roadmaps, plans, decisions, and bugs into single source of truth following control plane patterns.

**Date:** 2026-01-25

---

## Key Information Extracted

### From IMPLEMENTATION_ROADMAP.md
- **Phase 0-2:** Complete (Configuration, Backtesting, Bot Integration)
- **Phase 3:** Paper trading validation (30 days, started Dec 26, 2025)
- **Phase 4-10:** Future phases (risk management, advanced features, crypto bot, etc.)
- **Admin Platform:** Week 1-2 complete, Week 3-4 planned

### From BOT_ENHANCEMENT_ROADMAP.md
- Advanced risk management (portfolio heat, Kelly Criterion, trailing stops)
- Multi-strategy framework (RSI, breakout, Bollinger Bands)
- Machine learning integration
- Real-time data streaming
- Crypto bot development

### From ROADMAP_MANAGEMENT.md
- Single source of truth structure
- Roadmap hierarchy best practices
- Update workflow and commit conventions
- Weekly/monthly review cadence

### From ADMIN_PLATFORM_PROPOSAL.md
- User management features
- Session management
- Audit logs
- Settings and configuration
- Release notes system

### From DEPLOYMENT_STRATEGY_FOR_IMPROVEMENTS.md
- Deployment planning and strategies
- Infrastructure improvements
- Testing and validation approaches

---

## Migration to New Roadmap

**All relevant information consolidated into:** `/ROADMAP.md`

**New roadmap includes:**
- Strategic initiatives (infrastructure standardization, admin platform, trading bots)
- Timeline summary with priorities
- Success metrics and targets
- Known issues and decisions log
- Next immediate steps

**New structure follows:**
- Control plane patterns
- Industry best practices
- Single source of truth principle
- Clear priority indicators
- Actionable next steps

---

## Retention Policy

**Keep for:** 90 days minimum  
**Review:** April 2026  
**Delete if:** No references found, all information migrated to new roadmap

---

## Restoration

If you need to restore any archived roadmap content:

```bash
# View archive
ls -la _archive/2026-01-25-roadmaps/

# Restore file
git mv _archive/2026-01-25-roadmaps/[file] ./
```

---

**All archived content is tracked in git history.**
