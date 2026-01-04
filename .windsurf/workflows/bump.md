---
description: Automated version bump for QuantShift (just say "bump")
---

# QuantShift Automated Version Bump

**SIMPLE USAGE:** Just say **"bump"** and I'll handle everything automatically.

---

## What Happens When You Say "bump"

### Step 1: I Analyze Recent Work
- Review git commits since last version tag
- Categorize changes:
  - **Breaking changes** → MAJOR version (X.0.0)
  - **New features** → MINOR version (0.X.0)
  - **Bug fixes only** → PATCH version (0.0.X)

### Step 2: I Determine New Version
- Current version: Read from `package.json`
- Calculate next version based on change type
- Example: 1.1.0 → 1.2.0 (new features added)

### Step 3: I Generate Release Notes
- Extract changes from commit messages
- Categorize into:
  - **Added**: New features
  - **Changed**: Modified features
  - **Fixed**: Bug fixes
  - **Removed**: Deprecated features
  - **Security**: Security improvements
- Create descriptive title and summary

### Step 4: I Update Version Files
- Update `apps/admin-web/package.json`
- Version automatically propagates to `lib/version.ts`

### Step 5: I Create Release Note in Database
- Generate `scripts/create-release-[version].ts`
- Copy to container and execute
- Release note published automatically
- Version banner will appear for users

### Step 6: I Commit and Tag
```bash
git add -A
git commit -m "chore: Bump version to X.X.X

[Auto-generated release summary]"
git tag -a vX.X.X -m "Release version X.X.X"
git push origin main
git push origin vX.X.X
```

### Step 7: I Deploy to Production
```bash
ssh root@10.92.3.29
cd /opt/quantshift
git pull origin main
cd apps/admin-web
npm run build
pm2 restart quantshift-admin
```

### Step 8: I Verify
- Check PM2 status
- Confirm version banner appears
- Verify release notes are visible

---

## Example Interaction

**You:** bump

**Me:**
- ✅ Analyzed 15 commits since v1.1.0
- ✅ Detected: New features (Help system, automated workflows)
- ✅ Version type: MINOR
- ✅ New version: 1.2.0
- ✅ Generated release notes with 9 added items, 2 changed items
- ✅ Updated package.json to 1.2.0
- ✅ Created and published release note to database
- ✅ Committed and tagged as v1.2.0
- ✅ Deployed to production
- ✅ Version banner active

**Done!** Version 1.2.0 is live.

---

## Version Type Rules

### MAJOR (X.0.0)
- Breaking API changes
- Major architecture rewrites
- Incompatible changes
- Database schema breaking changes

### MINOR (0.X.0)
- New features
- New pages or components
- New API endpoints
- Backward compatible enhancements

### PATCH (0.0.X)
- Bug fixes only
- Performance improvements
- Documentation updates
- Minor UI tweaks

---

## Release Note Storage

- **Format:** Database (PostgreSQL)
- **Table:** `ReleaseNote` (Prisma model)
- **Fields:** version, title, description, type, changes (JSON), isPublished
- **Access:** Via `/release-notes` page (linked from Help)
- **Banner:** Automatically shown on new published releases

---

## Single Container Deployment

QuantShift uses **one container** (LXC 137 - 10.92.3.29):
- No blue-green deployment
- No STANDBY/LIVE switching
- Simple: Pull → Build → Restart
- Fast deployment (< 2 minutes)

---

## Notes

- **Fully automated:** You just say "bump"
- **Smart detection:** I determine version type from commits
- **Database-based:** Release notes stored in PostgreSQL
- **Auto-publish:** Release notes published immediately
- **Version banner:** Appears automatically for users
- **Help integration:** Release notes accessible via Help page

---

## Troubleshooting

**Build fails:**
- I'll show you the error and fix it before proceeding

**Version conflict:**
- I'll detect if version already exists and increment appropriately

**Database error:**
- I'll retry with proper authentication

**Deployment fails:**
- I'll check PM2 logs and restart if needed
