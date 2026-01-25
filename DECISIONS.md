# QuantShift Repo-Local Decisions

This file tracks decisions specific to working on the QuantShift repo.

For shared architectural decisions that apply to all apps, see `.cloudy-work/_cloudy-ops/context/DECISIONS.md`.

---

## D-QS-001: Container-first development
- **Decision:** All QuantShift development occurs on containers (qs-dashboard)
- **Why:** Consistent environment, no local dependency conflicts
- **When:** Established as standard practice
- **Pattern:** Local Mac for Windsurf/git, containers for builds/tests/execution
- **Canonical path:** `/opt/quantshift`

## D-QS-002: Single container deployment
- **Decision:** QuantShift uses single container (qs-dashboard), not blue-green
- **Why:** Different deployment model than TheoShift/LDC Tools
- **When:** Infrastructure established
- **Container:** qs-dashboard
