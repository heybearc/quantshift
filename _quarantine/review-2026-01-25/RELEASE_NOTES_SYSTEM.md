# QuantShift Release Notes System

## Overview
QuantShift uses a **database-driven release notes system** that provides better functionality than markdown files:

- ✅ Centralized database storage
- ✅ User-specific banner dismissal tracking
- ✅ Automated generation from git commits
- ✅ Modern card-based UI
- ✅ Authenticated API access

## Database Schema

### ReleaseNote Table
```prisma
model ReleaseNote {
  id          String   @id @default(cuid())
  version     String   @unique
  title       String
  description String
  type        String   @default("patch") // major, minor, patch
  changes     Json     // Array of {type: string, description: string}
  releaseDate DateTime @default(now())
  isPublished Boolean  @default(false)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

### User Tracking
Users have a `lastSeenReleaseVersion` field that tracks which release they've seen, enabling smart banner display.

## How to Create a New Release

### 1. Update package.json version
```bash
cd /opt/quantshift/apps/admin-web
# Edit package.json and increment version (e.g., 0.2.0 -> 0.3.0)
```

### 2. Run the release script
```bash
npm run release
```

This script (`scripts/generate-release-notes.ts`):
- Reads git commits since last release
- Categorizes commits by type (feat, fix, improvement, etc.)
- Creates a new ReleaseNote entry in the database
- Automatically publishes it

### 3. Commit and deploy
```bash
git add -A
git commit -m "chore: bump version to v0.3.0"
git push origin main
npm run build
pm2 restart quantshift-admin
```

## Commit Message Format

For best results, use conventional commit format:

- `feat: Add new trading algorithm` → Feature
- `fix: Resolve position calculation bug` → Bug Fix
- `improvement: Optimize database queries` → Improvement
- `refactor: Restructure auth module` → Improvement
- Other commits → Other Changes

## Components

### 1. Release Notes Page (`/release-notes`)
- Public-facing page showing all published releases
- Card-based layout with version badges
- Changes grouped by type (features, improvements, fixes, other)
- Accessible to all authenticated users

### 2. Release Banner Component
- Appears on dashboard for users who haven't seen the latest release
- Shows release title and description
- "View Details" button links to `/release-notes`
- Dismiss button updates user's `lastSeenReleaseVersion`

### 3. API Endpoints

#### GET `/api/release-notes`
Returns all published releases, sorted by date descending.
- Requires: Authentication (`access_token` cookie)
- Returns: `{ success: true, data: ReleaseNote[] }`

#### GET `/api/release-notes/latest`
Returns the latest release and whether to show banner for current user.
- Requires: Authentication
- Returns: `{ success: true, data: ReleaseNote, showBanner: boolean }`

#### POST `/api/release-notes/dismiss`
Dismisses the banner for the current user.
- Requires: Authentication
- Body: `{ releaseId: string }`
- Updates: `user.lastSeenReleaseVersion`

## Database vs Markdown Comparison

### Database Advantages (QuantShift)
✅ User-specific banner dismissal tracking
✅ Centralized storage with Prisma ORM
✅ Automated generation from git commits
✅ Easy querying and filtering
✅ Structured data with type safety
✅ No file parsing needed

### Markdown Advantages (LDC Tools)
✅ Simple file-based storage
✅ Easy to edit manually
✅ Git-friendly diffs
✅ No database migrations needed
✅ Portable and human-readable

## Recommendation

**Use database approach for:**
- Multi-user applications needing per-user tracking
- Applications with existing database infrastructure
- When you want automated generation from commits
- When you need structured querying

**Use markdown approach for:**
- Simple applications or documentation sites
- When you want manual control over formatting
- When database overhead isn't justified
- Static site generators

## Files Modified

- `app/release-notes/page.tsx` - Display page
- `components/ReleaseBanner.tsx` - Banner component
- `app/dashboard/page.tsx` - Added banner to dashboard
- `components/navigation.tsx` - Removed "Manage Releases" link
- `app/api/release-notes/latest/route.ts` - Latest release API
- `app/api/release-notes/route.ts` - All releases API
- `app/api/release-notes/dismiss/route.ts` - Dismiss banner API
- `scripts/generate-release-notes.ts` - Automated generation script

## Testing

1. **View release notes**: Navigate to `/release-notes`
2. **See banner**: Login and check dashboard (if you haven't seen latest version)
3. **Dismiss banner**: Click X button, verify it doesn't reappear
4. **Generate release**: Run `npm run release` after making commits
5. **API access**: All endpoints require authentication with `access_token` cookie

## Current Releases in Database

```sql
SELECT version, title, is_published FROM release_notes ORDER BY release_date DESC;
```

- v0.2.0 - Add arched QUANTSHIFT title to logo
- v1.0.0 - QuantShift Platform Launch (initial release)
