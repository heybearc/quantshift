# QuantShift Release Notes

This directory contains release notes for QuantShift in markdown format.

## Format

Each release note file follows this structure:

```markdown
---
version: "X.Y.Z"
date: "YYYY-MM-DD"
type: "major|minor|patch"
---

# Release vX.Y.Z

## Features
- New feature descriptions

## Improvements
- Enhancement descriptions

## Bug Fixes
- Bug fix descriptions

## Breaking Changes (if any)
- Breaking change descriptions
```

## Creating a New Release

1. **Determine version number:**
   - Major (X.0.0): Breaking changes
   - Minor (X.Y.0): New features, backward compatible
   - Patch (X.Y.Z): Bug fixes only

2. **Create release note file:**
   ```bash
   # Create file: release-notes/vX.Y.Z.md
   # Use template above
   ```

3. **Update package.json version** (if applicable)

4. **Commit and tag:**
   ```bash
   git add release-notes/vX.Y.Z.md
   git commit -m "chore: release vX.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```

## Version History

- v1.1.0 - Hot-standby infrastructure and governance system
- v1.0.0 - Initial QuantShift platform launch

## Display

Release notes are displayed:
- On the dashboard (version banner for new releases)
- On the `/release-notes` page (all releases)

The system automatically parses markdown files and displays them in the UI.
