# Promote to Control Plane

**Date:** 2026-01-25  
**Source:** QuantShift  
**Discovered by:** Cory Allen

---

## Policy: Version Auto-Sync Pattern

**Type:** policy  
**Target:** _cloudy-ops/policy/version-management.md  
**Affects:** all  
**Priority:** medium

### Context

Applications need to display version numbers in footers, navigation, and other UI elements. Maintaining version numbers in multiple places (package.json, lib/version.ts, etc.) leads to version drift and inconsistencies.

### Discovery/Pattern

Use `package.json` as the single source of truth for version numbers. Auto-import the version instead of hardcoding it.

**Implementation:**

```typescript
// lib/version.ts
import packageJson from '../package.json';

export const APP_VERSION = packageJson.version; // ✅ Auto-syncs
export const APP_NAME = 'AppName';

// ❌ DON'T DO THIS:
// export const APP_VERSION = '1.2.0'; // Hardcoded - will drift
```

**Usage in components:**

```typescript
import { APP_VERSION, APP_NAME } from '@/lib/version';

// Footer, navigation, etc.
<p>{APP_NAME} v{APP_VERSION}</p>
```

### Benefits

1. **Single source of truth** - Version only defined in package.json
2. **No drift** - Footer automatically updates when package.json is bumped
3. **Less maintenance** - No need to update multiple files
4. **Prevents errors** - Can't forget to update version in UI

### Implementation Checklist

For all apps (TheoShift, LDC Tools, QuantShift):

- [ ] Create `lib/version.ts` with auto-sync pattern
- [ ] Import version from package.json
- [ ] Update all UI components to use `APP_VERSION`
- [ ] Remove hardcoded version strings
- [ ] Test version display after bumping package.json

### Related Decisions

- D-015: Auto-commit and push pattern (solo development)
- Release notes standard (version must match package.json)

### References

- Implemented in QuantShift: `apps/web/lib/version.ts`
- Used in: `components/navigation.tsx` (footer)

---

## Notes

This pattern was discovered while fixing version inconsistencies in QuantShift. The footer was showing v1.2.0 (hardcoded) while package.json was also v1.2.0, but they could easily drift apart during version bumps.

Auto-syncing from package.json ensures the version is always correct and eliminates a common source of bugs.
