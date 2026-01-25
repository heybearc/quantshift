# Release Notes Implementation Guide

**Decision:** D-QS-003 - Markdown file-based release notes  
**Date:** 2026-01-25  
**Status:** Implemented

## Overview

QuantShift uses markdown files for release notes, providing version-controlled, atomic deployment of release information alongside code changes.

## Structure

```
/release-notes/
├── README.md          # How to create release notes
├── v1.0.0.md         # Initial release
└── v1.1.0.md         # Current release

/apps/admin-web/
├── lib/release-notes.ts              # Parser utility
├── components/VersionBanner.tsx      # Banner component
└── app/release-notes/page.tsx        # Display page
```

## Required Dependencies

Add to `apps/admin-web/package.json`:

```json
{
  "dependencies": {
    "gray-matter": "^4.0.3",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  }
}
```

Install:
```bash
cd apps/admin-web
npm install gray-matter react-markdown remark-gfm
```

## Usage

### Creating a New Release

1. Create new markdown file: `release-notes/vX.Y.Z.md`
2. Use frontmatter format:
   ```markdown
   ---
   version: "X.Y.Z"
   date: "YYYY-MM-DD"
   type: "major|minor|patch"
   ---
   
   # Release vX.Y.Z
   
   ## Features
   - Feature descriptions
   
   ## Improvements
   - Improvement descriptions
   
   ## Bug Fixes
   - Bug fix descriptions
   ```

3. Commit and deploy:
   ```bash
   git add release-notes/vX.Y.Z.md
   git commit -m "chore: release vX.Y.Z"
   git push origin main
   ```

### Displaying Release Notes

**Version Banner:**
- Automatically appears on dashboard for new releases
- Stored in localStorage (per-user dismissal)
- Links to full release notes page

**Release Notes Page:**
- Route: `/release-notes`
- Displays all releases in chronological order
- Parses markdown at build time
- Card-based UI with version badges

## Integration Points

### Dashboard Integration

Add to `apps/admin-web/app/dashboard/page.tsx`:

```typescript
import { getLatestReleaseNote } from '@/lib/release-notes';
import VersionBanner from '@/components/VersionBanner';

export default function Dashboard() {
  const latestRelease = getLatestReleaseNote();
  
  return (
    <div>
      {latestRelease && (
        <VersionBanner
          version={latestRelease.version}
          date={latestRelease.date}
          title={`Release v${latestRelease.version}`}
        />
      )}
      {/* Rest of dashboard */}
    </div>
  );
}
```

### Navigation Integration

Add link to navigation:

```typescript
{
  name: 'Release Notes',
  href: '/release-notes',
  icon: FileText,
}
```

## Advantages

✅ **Atomic deployment** - Release notes deploy with code  
✅ **Version controlled** - Git tracks all changes  
✅ **Blue-green compatible** - Files copy to both containers  
✅ **Simple** - No database migrations needed  
✅ **Portable** - Markdown files work anywhere  
✅ **Developer-friendly** - Easy to edit and review

## Future Enhancements

- Automated release note generation from git commits
- Integration with `/bump` workflow
- RSS feed for release notes
- Email notifications for new releases

## References

- Decision: `DECISIONS.md` - D-QS-003
- Analysis: `_archive/2026-01-25-outdated-docs/` (database approach rejected)
- Implementation: This document
