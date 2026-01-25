# Release Notes Standardization Analysis

**Date:** 2026-01-25  
**Purpose:** Evaluate industry standards for release notes and recommend standardized approach across apps

**Context:** Planning to convert QuantShift to blue-green deployment and standardize release notes across TheoShift, LDC Tools, and QuantShift.

---

## Current State Analysis

### TheoShift & LDC Tools: File-Based Approach

**Implementation:**
- Markdown files in `/release-notes/vX.Y.Z.md`
- Git-tracked, versioned with code
- Displayed via static file serving or parsed at runtime

**Pros:**
- ✅ Simple, no database dependency
- ✅ Version controlled with code
- ✅ Easy to review in PRs
- ✅ Works offline
- ✅ Portable across environments
- ✅ No migration needed between environments

**Cons:**
- ❌ No dynamic querying (latest, by date, by type)
- ❌ No user-specific tracking (dismissed banners)
- ❌ Harder to build features like "What's New" feed
- ❌ No analytics on which releases users viewed
- ❌ Requires parsing markdown at runtime for display

### QuantShift: Database-Driven Approach

**Implementation:**
- Prisma schema with `ReleaseNote` model
- `scripts/create-release.ts` inserts into database
- Version banner queries latest published release
- User dismissal tracked in localStorage

**Pros:**
- ✅ Dynamic querying (latest, filter by type, search)
- ✅ Rich metadata (published status, created by, date)
- ✅ User tracking possible (views, dismissals)
- ✅ Easy to build admin UI for release management
- ✅ Structured data (JSON changes array)
- ✅ Can track user-specific "last seen version"

**Cons:**
- ❌ Database dependency (migration complexity)
- ❌ Not version controlled with code
- ❌ Requires database access to view
- ❌ More complex deployment (DB migration + code)
- ❌ Environment-specific (dev/staging/prod have different data)

---

## Industry Standard Analysis

### What Major Companies Do

**GitHub:**
- File-based: `CHANGELOG.md` in repository
- Also: Web-based release notes UI (database-backed)
- **Hybrid approach:** Files for developers, database for users

**GitLab:**
- Database-driven release notes
- Markdown support for formatting
- Rich metadata (milestones, issues linked)

**Vercel/Netlify:**
- Database-driven changelog
- API-accessible
- User-facing UI with filtering

**npm/Node.js:**
- File-based: `CHANGELOG.md` in repository
- Simple, developer-focused

**Stripe:**
- Database-driven API changelog
- Versioned API documentation
- Rich filtering and search

### Industry Standard Verdict

**For Developer Tools/Libraries:** File-based (`CHANGELOG.md`)  
**For SaaS/Web Applications:** Database-driven with UI  
**For Enterprise Applications:** Hybrid (files + database)

**Your apps are SaaS/Web Applications** → **Database-driven is industry standard**

---

## Blue-Green Deployment Implications

### File-Based Release Notes + Blue-Green

**Deployment flow:**
1. Commit code + release note markdown file
2. Deploy to STANDBY
3. Test on STANDBY (release notes visible)
4. Switch traffic to STANDBY
5. STANDBY becomes LIVE

**Pros:**
- ✅ Release notes deploy atomically with code
- ✅ No database migration needed
- ✅ Easy rollback (git revert)
- ✅ Same release notes on STANDBY and LIVE

**Cons:**
- ❌ Can't unpublish release notes without code deploy
- ❌ No user-specific tracking
- ❌ Limited dynamic features

### Database-Driven Release Notes + Blue-Green

**Deployment flow:**
1. Commit code changes
2. Deploy to STANDBY
3. Run database migration on STANDBY database
4. Insert release note into database
5. Test on STANDBY
6. Switch traffic to STANDBY
7. STANDBY becomes LIVE

**Challenges:**
- ⚠️ **Shared database:** LIVE and STANDBY share same database
- ⚠️ **Migration timing:** When to run migrations?
- ⚠️ **Release note visibility:** When to publish?

**Solutions:**

**Option A: Shared Database (Recommended)**
- LIVE and STANDBY containers share same PostgreSQL database
- Migrations run before deploying to STANDBY
- Release notes published after traffic switch
- **Pro:** Simple, no data sync needed
- **Con:** Database is single point of failure

**Option B: Separate Databases**
- Each container has own database
- Sync data between databases
- Complex, not recommended

---

## Recommended Approach: Hybrid Model

### Best of Both Worlds

**For version control and deployment:**
- Keep markdown files in `/release-notes/vX.Y.Z.md` (git-tracked)
- Include in repository for code review and history

**For runtime and user features:**
- Parse markdown files and insert into database on deployment
- Use database for querying, filtering, user tracking
- Build admin UI for release management

**Implementation:**

```typescript
// scripts/sync-release-notes.ts
// Runs during deployment to sync markdown files to database

import fs from 'fs';
import path from 'path';
import { PrismaClient } from '@prisma/client';
import matter from 'gray-matter'; // Parse frontmatter

const prisma = new PrismaClient();

async function syncReleaseNotes() {
  const releaseNotesDir = path.join(process.cwd(), 'release-notes');
  const files = fs.readdirSync(releaseNotesDir).filter(f => f.endsWith('.md'));
  
  for (const file of files) {
    const content = fs.readFileSync(path.join(releaseNotesDir, file), 'utf-8');
    const { data, content: markdown } = matter(content);
    
    // Upsert to database
    await prisma.releaseNote.upsert({
      where: { version: data.version },
      update: {
        title: data.title,
        description: data.description,
        type: data.type,
        releaseDate: new Date(data.releaseDate),
        isPublished: data.isPublished,
        content: markdown,
        changes: data.changes
      },
      create: {
        version: data.version,
        title: data.title,
        description: data.description,
        type: data.type,
        releaseDate: new Date(data.releaseDate),
        isPublished: data.isPublished,
        createdBy: 'System',
        content: markdown,
        changes: data.changes
      }
    });
  }
  
  console.log(`✅ Synced ${files.length} release notes to database`);
}

syncReleaseNotes();
```

**Markdown file format:**
```markdown
---
version: "1.3.0"
title: "Enhanced User Management"
description: "New user roles and permissions system"
type: "minor"
releaseDate: "2026-01-25"
isPublished: true
changes:
  - type: "added"
    items:
      - "Role-based access control"
      - "Custom permissions"
  - type: "fixed"
    items:
      - "User session timeout bug"
---

# What's New in Version 1.3.0

**Released:** January 25, 2026

## ✨ New Features

### Role-Based Access Control
Users can now be assigned custom roles with specific permissions...

[Full markdown content here]
```

---

## Standardization Recommendation

### Adopt Hybrid Model Across All Apps

**For TheoShift, LDC Tools, QuantShift:**

1. **Source of truth:** Markdown files in `/release-notes/vX.Y.Z.md`
   - Git-tracked, versioned with code
   - Easy to review in PRs
   - Portable and simple

2. **Runtime storage:** PostgreSQL database
   - Parsed from markdown files during deployment
   - Enables dynamic features (filtering, search, user tracking)
   - Supports admin UI for release management

3. **Deployment process:**
   ```bash
   # Part of /bump workflow
   1. Create /release-notes/vX.Y.Z.md (markdown file)
   2. Commit and push to GitHub
   3. Deploy to STANDBY
   4. Run sync-release-notes.ts (parse markdown → database)
   5. Test on STANDBY
   6. Switch traffic
   ```

4. **Shared Prisma schema:**
   ```prisma
   model ReleaseNote {
     id            String   @id @default(cuid())
     version       String   @unique
     title         String
     description   String
     type          String   // major, minor, patch
     releaseDate   DateTime
     isPublished   Boolean  @default(false)
     createdBy     String
     content       String   @db.Text // Full markdown content
     changes       Json     // Structured changes array
     createdAt     DateTime @default(now())
     updatedAt     DateTime @updatedAt
   }
   ```

---

## Migration Path

### Phase 1: Standardize Schema (All Apps)

**Add to existing Prisma schemas:**
- TheoShift: Add `ReleaseNote` model
- LDC Tools: Add `ReleaseNote` model
- QuantShift: Already has it ✅

**Run migrations:**
```bash
npx prisma migrate dev --name add_release_notes
```

### Phase 2: Create Markdown Files (TheoShift, LDC Tools)

**Convert existing release notes to markdown:**
- Create `/release-notes/` directory
- Write markdown files for past releases
- Add frontmatter with metadata

### Phase 3: Create Sync Script (All Apps)

**Add `scripts/sync-release-notes.ts`:**
- Shared implementation across all apps
- Parses markdown files
- Upserts to database
- Runs during deployment

### Phase 4: Update /bump Workflow

**Modify generic `/bump` workflow:**
```markdown
## Step 5: Create Release Notes

Create `/release-notes/vX.Y.Z.md` with frontmatter:

\`\`\`markdown
---
version: "X.Y.Z"
title: "Release Title"
description: "Brief description"
type: "major|minor|patch"
releaseDate: "YYYY-MM-DD"
isPublished: true
changes:
  - type: "added"
    items: ["Feature 1"]
  - type: "fixed"
    items: ["Bug fix 1"]
---

# What's New in Version X.Y.Z
...
\`\`\`

## Step 7: Deploy to STANDBY

After deployment, sync release notes:
\`\`\`bash
ssh [STANDBY] 'cd /opt/[app] && npx tsx scripts/sync-release-notes.ts'
\`\`\`
```

### Phase 5: Build Admin UI (Optional)

**Create admin interface for release management:**
- View all releases
- Edit release notes (updates markdown file + database)
- Publish/unpublish releases
- Preview release notes

---

## Benefits of Hybrid Approach

### For Developers

✅ **Git-tracked:** Release notes in version control  
✅ **Code review:** Release notes reviewed in PRs  
✅ **Simple editing:** Markdown is easy to write  
✅ **Portable:** Works offline, no database needed for editing  
✅ **Rollback:** Git revert works for release notes too

### For Users

✅ **Dynamic features:** Search, filter, "What's New" feed  
✅ **User tracking:** Track which releases user has seen  
✅ **Rich UI:** Beautiful release notes display  
✅ **Notifications:** Version banner on new releases  
✅ **Admin management:** Publish/unpublish without code deploy

### For Operations

✅ **Single source of truth:** Markdown files  
✅ **Automatic sync:** Database updated on deployment  
✅ **Blue-green compatible:** Works with shared database  
✅ **Environment consistency:** Same release notes across environments  
✅ **Backup:** Database is just a cache, markdown files are source

---

## Comparison: Pure File vs Pure Database vs Hybrid

| Feature | File-Based | Database | Hybrid |
|---------|-----------|----------|--------|
| Version controlled | ✅ | ❌ | ✅ |
| Code review | ✅ | ❌ | ✅ |
| Dynamic querying | ❌ | ✅ | ✅ |
| User tracking | ❌ | ✅ | ✅ |
| Offline editing | ✅ | ❌ | ✅ |
| Admin UI | ❌ | ✅ | ✅ |
| Rollback | ✅ | ❌ | ✅ |
| Blue-green friendly | ✅ | ⚠️ | ✅ |
| Complexity | Low | Medium | Medium |
| Maintenance | Low | Medium | Medium |

**Winner:** Hybrid approach combines best of both

---

## Implementation Timeline

### Week 1: Schema Standardization
- Add `ReleaseNote` model to TheoShift and LDC Tools
- Run migrations on all apps
- Verify schema consistency

### Week 2: Markdown Migration
- Create `/release-notes/` directories
- Convert existing release notes to markdown
- Add frontmatter metadata

### Week 3: Sync Script Development
- Create `scripts/sync-release-notes.ts`
- Test parsing and database insertion
- Add to deployment process

### Week 4: Workflow Integration
- Update generic `/bump` workflow
- Test on all three apps
- Document new process

### Week 5: Admin UI (Optional)
- Build release notes management interface
- Add to admin portals
- Enable publish/unpublish functionality

---

## Recommended Decision

### Adopt Hybrid Model Now

**Why:**
1. **Future-proof:** Works with blue-green deployment
2. **Industry standard:** SaaS apps use database-driven release notes
3. **Best of both:** Git-tracked source + dynamic features
4. **Standardized:** Same approach across all apps
5. **Scalable:** Easy to add features (search, notifications, analytics)

### Migration Strategy

**For QuantShift:**
- Keep existing database model ✅
- Add markdown files for existing releases
- Create sync script
- Update to use hybrid approach

**For TheoShift & LDC Tools:**
- Add database model (migration)
- Keep existing markdown files ✅
- Create sync script
- Update to use hybrid approach

**Result:** All three apps use same hybrid approach

---

## Conclusion

**Industry Standard:** Database-driven release notes for SaaS applications

**Recommended Approach:** Hybrid model (markdown files + database)

**Benefits:**
- ✅ Version controlled (markdown files)
- ✅ Dynamic features (database)
- ✅ Blue-green compatible
- ✅ Standardized across apps
- ✅ Future-proof

**Next Steps:**
1. Approve hybrid model approach
2. Add `ReleaseNote` schema to TheoShift/LDC Tools
3. Create `scripts/sync-release-notes.ts` (shared)
4. Update generic `/bump` workflow
5. Test on next release

**Status:** Ready to implement standardization
