# QuantShift Repo-Local Decisions

This file tracks decisions specific to working on the QuantShift repo.

For shared architectural decisions that apply to all apps, see `.cloudy-work/_cloudy-ops/context/DECISIONS.md`.

---

## D-QS-001: Container-first development
- **Decision:** All QuantShift development occurs on containers (qs-dashboard)
- **Why:** Consistent environment, no local dependency conflicts
- **When:** Established as standard practice
- **Pattern:** Local Mac for Windsurf/git, containers for builds/tests/execution
- **Canonical path:** `/opt/quantshift/apps/web` (Next.js), `/opt/quantshift/apps/bots` (Python bots)

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

## D-QS-006: Hot-standby git parity for bot containers
- **Decision:** Configure identical git capabilities on both bot containers (LXC 100 and LXC 101)
- **Why:** True hot-standby failover requires both containers to independently pull, commit, and push code
- **When:** 2026-01-25
- **Implementation:** Shared git credentials, identical user config, full submodule initialization on both containers
- **Containers:** LXC 100 (primary), LXC 101 (standby) - both at `/opt/quantshift`
- **Capabilities:** Both can pull from GitHub, commit changes, push updates, access governance files
- **Consequence:** If either container fails, the other can immediately take over all development and deployment operations

## D-QS-007: Industry-standard monorepo structure
- **Decision:** Restructure to industry-standard monorepo with all apps in `apps/` directory
- **Why:** Eliminate confusion, consistent organization, matches industry best practices
- **When:** 2026-01-25
- **Implementation:** Move Next.js app from root to `apps/web/`, Python bots already in `apps/bots/`
- **Structure:** `apps/web/` (Next.js), `apps/bots/` (Python), `packages/` (shared code)
- **Impact:** Updated deployment scripts, PM2 config, documentation, container paths
- **Benefit:** Crystal clear organization, no future confusion about app locations
- **Critical lesson:** .env files don't move with git - must be recreated on container after restructure
- **Container .env location:** `/opt/quantshift/apps/web/.env` (not in git, contains DATABASE_URL, JWT_SECRET)

## D-QS-008: User-Facing Release Notes Standard

**Date:** 2026-01-25  
**Status:** Implemented  
**Context:** Release notes were developer-focused (technical details, infrastructure changes) instead of user-facing (benefits, features, improvements).

**Decision:**
- Release notes must be written for end users, not developers
- Focus on benefits and what users can do, not implementation details
- Use clear, simple language without technical jargon
- Follow standard format: New Features, Improvements, Bug Fixes
- Created control plane standard at `.cloudy-work/_cloudy-ops/standards/RELEASE-NOTES-STANDARD.md`
- Standard applies to all Cloudy-Work apps (TheoShift, LDC Tools, QuantShift)

**Rationale:**
- Users don't care about "Configured LXC 101 as hot-standby" - they care about "99.9% uptime"
- Release notes are communication tools, not technical documentation
- Consistent format across all apps improves user experience

**Implementation:**
- Rewrote v1.0.0, v1.1.0, v1.2.0 to be user-facing
- Banner now shows latest version from markdown files (not database)
- All future releases must follow the standard

---

## D-QS-009: Blue-Green Deployment Infrastructure

**Date:** 2026-01-26  
**Status:** ✅ Implemented  
**Context:** QuantShift was using single container deployment (qs-dashboard). Needed to migrate to blue-green model for zero-downtime deployments and to align with TheoShift/LDC Tools patterns.

**Decision:**
- Implement blue-green deployment infrastructure for QuantShift admin web application
- CT 137 renamed to `quantshift-blue` @ 10.92.3.29:3001 (Blue environment)
- CT 138 cloned as `quantshift-green` @ 10.92.3.30:3001 (Green environment)
- HAProxy (10.92.3.26) routes traffic to LIVE environment
- Both environments share PostgreSQL database (10.92.3.21)
- NPM handles SSL termination, routes to HAProxy
- Blue is initial LIVE environment

**Rationale:**
- Zero-downtime deployments - deploy to STANDBY, test, then switch
- Quick rollback capability - switch back to previous environment instantly
- Safe testing - validate new releases on STANDBY before going LIVE
- Consistency - matches TheoShift and LDC Tools deployment patterns
- Enables generic `/bump` workflow integration

**Implementation:**
- Cloned CT 137 to CT 138 (full disk clone)
- Configured HAProxy backends for blue and green
- Fixed HAProxy health check (uses `/` instead of `/api/health`)
- Updated NPM proxy host for trader.cloudigan.net to route through HAProxy
- Both environments operational and healthy

**References:**
- `docs/BLUE-GREEN-SWITCHING.md` - Switching runbook
- `docs/HAPROXY-QUANTSHIFT-CONFIG.md` - HAProxy configuration
- `docs/NPM-PROXY-HOSTS-CONFIG.md` - NPM configuration
- `docs/DNS-SETUP-GUIDE.md` - DNS setup

**Supersedes:** D-QS-002 (Single container deployment)  
**Related:** D-QS-004 (Blue-green deployment migration - now complete)
