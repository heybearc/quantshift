# QuantShift - Windsurf Boot Context

**App:** QuantShift  
**Port:** 3001  
**Container:** qs-dashboard  
**Canonical path:** `/opt/quantshift`

---

## Quick Reference

**SSH Access:**
```bash
ssh qs-dashboard
```

**Container-First Rule:**
- ❌ NO builds, tests, or execution on local Mac
- ✅ ALL development work happens on containers
- ✅ Local Mac is for Windsurf IDE and git operations only

---

## Workflows Available

- `/start-day` - Load context and prepare for work
- `/mid-day` - Update context during the day
- `/end-day` - Close out day and prepare for tomorrow
- `/bump` - Version bump and deploy
- `/test-release` - Run automated tests before release
- `/container-dev` - Enforce container-first development

---

## Context Files

**Shared context** (all apps):
- `.cloudy-work/_cloudy-ops/context/CURRENT-STATE.md`
- `.cloudy-work/_cloudy-ops/context/APP-MAP.md`
- `.cloudy-work/_cloudy-ops/context/DECISIONS.md`
- `.cloudy-work/_cloudy-ops/context/RUNBOOK-SHORT.md`

**Repo-local context** (QuantShift specific):
- `TASK-STATE.md` - Current work, next steps
- `DECISIONS.md` - QuantShift specific decisions
- `.windsurf/BOOT.md` - This file

---

## First Steps

1. Run `/start-day` to load full context
2. SSH to qs-dashboard for work
3. Use Windsurf for editing, container for execution
