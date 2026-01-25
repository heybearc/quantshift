# Quarantine Directory

**Created:** 2026-01-25  
**Purpose:** Documentation requiring review before final decision (archive vs delete vs restore)

---

## Contents

### review-2026-01-25/

**Roadmaps and proposals (5 files):**
- `IMPLEMENTATION_ROADMAP.md` - Development roadmap
- `ROADMAP_MANAGEMENT.md` - Roadmap management approach
- `ADMIN_PLATFORM_PROPOSAL.md` - Original admin platform proposal
- `BOT_ENHANCEMENT_ROADMAP.md` - Bot enhancement plans
- `DEPLOYMENT_STRATEGY_FOR_IMPROVEMENTS.md` - Deployment strategy

**Testing/development guides (4 files):**
- `TESTING_AUTH.md` - Auth testing guide
- `TESTING_GUIDE.md` - General testing guide
- `CONTAINER_DEVELOPMENT_WORKFLOW.md` - Container dev workflow
- `NEXTJS_SETUP.md` - Next.js setup guide

**Integration guides (3 files):**
- `BOT_INTEGRATION_GUIDE.md` - Bot integration documentation
- `ENTERPRISE_USER_MANAGEMENT.md` - Enterprise user management
- `RELEASE_NOTES_SYSTEM.md` - Release notes system (may overlap with QUANTSHIFT-RELEASE-SYSTEM.md)

**Architecture/deployment guides (3 files):**
- `ARCHITECTURE.md` - Architecture documentation
- `DEPLOYMENT_GUIDE.md` - Deployment guide
- `PLATFORM_GUIDE.md` - Platform guide

---

## Review Criteria

For each file, determine:

1. **Is content still accurate?**
   - Does it reflect current structure?
   - Are paths/commands correct?
   - Is information outdated?

2. **Is it superseded by newer docs?**
   - Check `README.md`
   - Check `.cloudy-work/_cloudy-ops/context/` docs
   - Check `QUANTSHIFT-RELEASE-SYSTEM.md`

3. **Does it have unique value?**
   - Historical context?
   - Implementation details not documented elsewhere?
   - Reference for future work?

4. **Is it referenced anywhere?**
   - Check code imports
   - Check scripts
   - Check other documentation

---

## Decision Options

**RESTORE:** Move back to root if still relevant and accurate  
**ARCHIVE:** Move to `_archive/` if historical value but not actively needed  
**DELETE:** Remove if obsolete, redundant, or superseded

---

## Review Timeline

**Review by:** February 1, 2026  
**Auto-archive if not reviewed:** March 1, 2026  
**Delete archived after:** 90 days from archive date

---

## Restoration

If you need to restore quarantined content:
```bash
# View quarantine
ls -la _quarantine/review-2026-01-25/

# Restore file
git mv _quarantine/review-2026-01-25/[file] ./

# Archive instead
git mv _quarantine/review-2026-01-25/[file] _archive/[appropriate-directory]/
```

---

**All quarantined content is tracked in git history.**
