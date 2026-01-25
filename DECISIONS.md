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
- **Status:** ⚠️ CHANGING - Migrating to blue-green deployment (Q1 2026)

## D-QS-003: Markdown file-based release notes
- **Decision:** Standardize on markdown files for release notes (not database-driven)
- **Why:** Industry standard, atomic deployment with code, version controlled, blue-green compatible
- **When:** 2026-01-25
- **Implementation:** `/release-notes/vX.Y.Z.md` with frontmatter, parsed at runtime
- **Reference:** `RELEASE-NOTES-STANDARDIZATION-REVISED.md`

## D-QS-004: Blue-green deployment migration
- **Decision:** Migrate QuantShift to blue-green deployment model
- **Why:** Zero-downtime deployments, safe testing on STANDBY, matches other apps, enables generic /bump workflow
- **When:** Planned Q1 2026 (after release notes standardization)
- **Implementation:** Second LXC container, HAProxy routing, shared PostgreSQL database
- **Reference:** `BUMP-WORKFLOW-COMPATIBILITY-ANALYSIS.md`

## D-QS-005: Consolidated roadmap
- **Decision:** Single ROADMAP.md as source of truth for all planning
- **Why:** Control plane best practices, single source of truth, clear priorities
- **When:** 2026-01-25
- **Supersedes:** Multiple scattered roadmaps and planning documents
- **Location:** `/ROADMAP.md`
