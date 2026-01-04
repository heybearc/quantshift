---
description: QuantShift version bump, release notes, and deployment workflow
---

# QuantShift Version Bump & Release Workflow

This workflow handles version bumping, release note creation, help documentation updates, and deployment for the QuantShift admin platform.

**IMPORTANT:** QuantShift runs on a **single container** (LXC 137 - 10.92.3.29), so there is NO blue-green deployment. This is a simplified workflow compared to JW Attendant Scheduler or LDC Construction Tools.

---

## When to Use This Workflow

Run this workflow when you want to:
- Bump the version number (major, minor, or patch)
- Create release notes for new features
- Update help documentation
- Deploy to production with version banner

---

## Step 1: Determine Version Type

Ask the user which type of version bump:
- **MAJOR** (X.0.0): Breaking changes or major new features
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes and minor improvements

---

## Step 2: Update Version Number

Update version in `apps/admin-web/package.json`:

```bash
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift/apps/admin-web
# Current version is in package.json "version" field
# Update to new version (e.g., "1.0.0" → "1.1.0")
```

Also update `lib/version.ts` if it exists, or create it:

```typescript
export const APP_VERSION = '1.1.0';
export const APP_NAME = 'QuantShift Admin Platform';
export const RELEASE_DATE = '2026-01-03';
```

---

## Step 3: Create Release Notes

1. Navigate to the admin platform (or use API)
2. Go to **Release Notes** page
3. Click **"Create Release Note"**
4. Fill in:
   - **Version**: Match the version from Step 2
   - **Title**: Brief title (e.g., "Admin Platform Week 1-4 Features")
   - **Description**: Summary of changes
   - **Type**: Major/Minor/Patch
   - **Release Date**: Today's date
   - **Changes**: Categorize by type:
     - **Added**: New features
     - **Changed**: Modified features
     - **Fixed**: Bug fixes
     - **Removed**: Deprecated features
     - **Security**: Security improvements

5. **Save and Publish**

---

## Step 4: Update Help Documentation

Review and update `/app/help/page.tsx` if new features were added:
- Add new sections for new features
- Update existing sections with new capabilities
- Add screenshots or examples if needed

---

## Step 5: Build and Test

```bash
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift/apps/admin-web
npm run build
# Verify build succeeds
```

---

## Step 6: Commit and Tag

```bash
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift
git add -A
git commit -m "chore: Bump version to X.X.X

- Updated package.json version
- Created release notes for version X.X.X
- Updated help documentation
- [List major changes]"

git tag -a vX.X.X -m "Release version X.X.X"
git push origin main
git push origin vX.X.X
```

---

## Step 7: Deploy to Production (Single Container)

```bash
# SSH to QuantShift container
ssh root@10.92.3.29

# Navigate to app directory
cd /opt/quantshift

# Pull latest code
git pull origin main

# Build the app
cd apps/admin-web
npm run build

# Restart PM2
pm2 restart quantshift-admin

# Verify status
pm2 status
```

---

## Step 8: Verify Deployment

1. Visit the admin platform
2. Check that the version banner appears (if implemented)
3. Verify release notes are visible
4. Test new features
5. Check help documentation is updated

---

## Version Banner Component

The version banner should automatically appear when a new release note is published. It shows:
- New version number
- Release summary
- Link to full release notes
- Dismissible by user (stored in localStorage)

---

## Example Version Bump

**Scenario:** Completed Week 1-4 admin features, want to release as v1.1.0

1. **Version Type**: MINOR (new features, backward compatible)
2. **Update package.json**: `"version": "1.1.0"`
3. **Create Release Note**:
   - Version: 1.1.0
   - Title: "Admin Platform - Weeks 1-4 Complete"
   - Type: Minor
   - Added: User Management, Sessions, Audit Logs, Health Monitor, API Status, General Settings
4. **Commit**: `git commit -m "chore: Bump version to 1.1.0"`
5. **Tag**: `git tag -a v1.1.0 -m "Release version 1.1.0"`
6. **Deploy**: SSH to container, pull, build, restart PM2
7. **Verify**: Check version banner and release notes

---

## Notes

- **No blue-green deployment**: QuantShift uses a single container
- **No /bump, /release, /sync workflows**: Those are for multi-container apps
- **Simple deployment**: Pull → Build → Restart
- **Version banner**: Automatically shows on login after new release
- **Help docs**: Keep updated with each major/minor release

---

## Troubleshooting

**Build fails:**
- Check for TypeScript errors
- Verify all dependencies are installed
- Review build logs for specific errors

**PM2 restart fails:**
- Check PM2 logs: `pm2 logs quantshift-admin`
- Verify port 3001 is available
- Check for runtime errors

**Version banner doesn't appear:**
- Verify release note is published
- Check localStorage isn't blocking banner
- Clear browser cache and reload
