# QuantShift Release Note System

**Purpose:** Document QuantShift-specific release note functionality that differs from generic bump workflow.

**Created:** 2026-01-25 (extracted from quantshift-version-bump.md before deletion)

---

## Database-Driven Release Notes

QuantShift uses a **Prisma-based release note system** that stores release information in the database.

### Schema
Release notes are stored in the database with:
- `version` - Semantic version (e.g., "1.1.0")
- `title` - User-friendly title
- `description` - Summary of changes
- `type` - major|minor|patch
- `releaseDate` - Date of release
- `isPublished` - Boolean flag
- `createdBy` - Creator identifier
- `changes` - JSON array with structure:
  ```json
  [
    { "type": "added", "items": ["Feature 1", "Feature 2"] },
    { "type": "changed", "items": ["Change 1"] },
    { "type": "fixed", "items": ["Bug fix 1"] }
  ]
  ```

### Automated Creation Script

**File:** `scripts/create-release.ts` (already exists)

**Usage:**
```bash
# On container
cd /opt/quantshift
npx tsx scripts/create-release.ts
```

**What it does:**
1. Connects to Prisma database
2. Creates release note entry
3. Sets `isPublished: true` to trigger version banner
4. Disconnects cleanly

**Current implementation:** See `@/Users/cory/Projects/quantshift/scripts/create-release.ts`

---

## Version Banner System

### How It Works
- **Trigger:** New release note with `isPublished: true`
- **Display:** Banner appears on login/page load
- **Content:** Version number, release summary, link to full notes
- **Dismissal:** User can dismiss (stored in localStorage)
- **Persistence:** Banner reappears for new versions only

### Implementation Notes
- Version banner component likely in `apps/admin-web/components/`
- Checks database for latest published release note
- Compares with localStorage dismissed versions
- Shows banner if version is newer than last dismissed

---

## Version Tracking

**File:** `lib/version.ts` (already exists)

**Current implementation:**
```typescript
export const APP_VERSION = '1.2.0';
export const APP_NAME = 'QuantShift';
```

**Purpose:** Centralized version constant for UI display

---

## Integration with Generic /bump Workflow

### What's Missing from Generic /bump
The generic `/bump` workflow (`.cloudy-work/.windsurf/workflows/bump.md`) is designed for apps with:
- Blue-green deployment (TheoShift, LDC Tools)
- File-based release notes (markdown files)
- MCP server deployment automation

### QuantShift Differences
1. **Single container** (qs-dashboard) - no blue-green
2. **Database release notes** - not file-based
3. **Version banner system** - database-driven UI feature
4. **Prisma script** - automated DB insertion

### Next Steps for Evaluation

**TODO: Evaluate if generic /bump workflow needs QuantShift-specific variant**

Questions to answer:
1. Does MCP server `deploy_to_standby` work with single-container apps?
2. Should we add database release note creation to /bump workflow?
3. Should we create a QuantShift-specific /bump variant?
4. Can generic /bump handle non-blue-green deployments?

**Options:**
- **Option A:** Extend generic /bump to handle both deployment models
- **Option B:** Create QuantShift-specific /bump variant in `.windsurf/workflows/`
- **Option C:** Keep generic /bump, add QuantShift release notes as separate workflow step

---

## Recommendation

**Preserve this documentation** and evaluate during next bump cycle whether:
1. Generic /bump workflow is sufficient for QuantShift
2. Database release note creation should be integrated into bump workflow
3. QuantShift needs a local workflow variant

**Do not rush integration** - test generic /bump first on next release.

---

## Files Referenced
- `scripts/create-release.ts` - Release note creation script ✅ EXISTS
- `lib/version.ts` - Version constants ✅ EXISTS
- `apps/admin-web/components/` - Version banner component (location TBD)
- Prisma schema - Release note model

---

**Status:** Documentation preserved. Ready to delete obsolete workflow.
