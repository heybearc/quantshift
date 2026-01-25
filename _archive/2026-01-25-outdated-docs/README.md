# Archived Documentation - 2026-01-25

**Reason:** Outdated documentation that no longer reflects current architecture or decisions.

## Archived Files

### BOT_INTEGRATION_GUIDE.md
- **Why:** Describes database-driven bot integration approach
- **Issue:** Contradicts D-QS-003 (markdown file-based release notes)
- **Status:** Historical reference only

### DEPLOYMENT_GUIDE.md
- **Why:** Outdated deployment instructions
- **Issue:** References old container setup, pre-hot-standby configuration
- **Status:** Superseded by current infrastructure (LXC 100/101 hot-standby)

### ENTERPRISE_USER_MANAGEMENT.md
- **Why:** Future feature specification (100+ user fields)
- **Issue:** Not current implementation, overly complex for current needs
- **Status:** May be useful for future enterprise features

### NEXTJS_SETUP.md
- **Why:** Outdated setup guide
- **Issue:** Current system already deployed and configured
- **Status:** Historical reference for initial setup

### PLATFORM_GUIDE.md
- **Why:** Describes old Redis-based architecture
- **Issue:** Current system uses PostgreSQL only, no Redis state management
- **Status:** Superseded by current architecture

### TESTING_AUTH.md
- **Why:** Describes FastAPI backend architecture
- **Issue:** Current system is Next.js-only (no FastAPI)
- **Status:** Historical reference for abandoned approach

### TESTING_GUIDE.md
- **Why:** Outdated testing procedures
- **Issue:** References old local Mac development (violates container-first policy)
- **Status:** Superseded by container-based testing workflow

## Current Documentation

See these files for current, accurate documentation:
- `/docs/architecture/ARCHITECTURE.md` - Broker-agnostic strategy framework
- `/docs/workflows/CONTAINER_DEVELOPMENT_WORKFLOW.md` - Container-first development
- `/.cloudy-work/_cloudy-ops/global-rules.md` - Global development rules
- `/DECISIONS.md` - Current architectural decisions

## Deleted Files

### RELEASE_NOTES_SYSTEM.md
- **Why:** Directly contradicted D-QS-003 (markdown file-based release notes)
- **Action:** Deleted completely to avoid confusion
- **Decision:** D-QS-003 explicitly chose markdown files over database approach

---

**Archived by:** Windsurf AI  
**Date:** 2026-01-25  
**Review Status:** Complete
