---
applies_to: all_repos
priority: critical
enforcement: mandatory
---

# HAProxy Verification Rule

## Principle

**HAProxy configuration is the ONLY source of truth for LIVE/STANDBY status.**

Before ANY deployment, traffic switch, or environment-specific operation, Windsurf MUST verify the current LIVE/STANDBY state via HAProxy.

---

## Why This Rule Exists

**Problem:**
- Documentation (APP-MAP.md) shows typical mappings but becomes stale
- Blue-green deployments mean traffic routing changes regularly
- Deploying to wrong environment causes production outages
- Assumptions about which container is LIVE are dangerous

**Solution:**
- Always check HAProxy config before deployment operations
- HAProxy controls actual traffic routing
- HAProxy config is runtime truth, documentation is reference only

**Decision:** D-008 in `_cloudy-ops/context/DECISIONS.md`

---

## When to Verify HAProxy

### MANDATORY Verification (Before These Actions)

**1. Deployment operations:**
- Deploying code to STANDBY
- Running tests on STANDBY
- Any SSH operation to a specific container

**2. Traffic switching:**
- Before switching traffic (verify current state)
- After switching traffic (verify switch succeeded)

**3. Debugging:**
- Before investigating issues on a specific environment
- Before making changes to a specific container

**4. Workflow execution:**
- `/bump` - verify STANDBY before deployment
- `/test-release` - verify STANDBY before testing
- `/release` - verify LIVE before switching
- `/sync` - verify both LIVE and STANDBY

### OPTIONAL Verification (But Recommended)

- Status checks
- Read-only operations
- Documentation updates

---

## How to Verify HAProxy

### Method 1: MCP Server (Preferred)

```
Use MCP tool: get_deployment_status

Example:
You: "What's the current LIVE/STANDBY status for TheoShift?"
Windsurf: [Calls mcp0_get_deployment_status with app="theoshift"]

Result:
✅ LIVE: green-theoshift (Container 132)
✅ STANDBY: blue-theoshift (Container 134)
```

### Method 2: Shell Script (Fallback)

```bash
_cloudy-ops/scripts/verify-live-standby.sh <app-name>

Example:
_cloudy-ops/scripts/verify-live-standby.sh theoshift

Result:
✅ HAProxy Routing (Source of Truth):
   LIVE:    green-theoshift
   STANDBY: blue-theoshift
```

### Method 3: Direct HAProxy Query (Manual)

```bash
ssh prox "pct exec 136 -- grep 'use_backend.*if is_<app>' /etc/haproxy/haproxy.cfg"

Example:
ssh prox "pct exec 136 -- grep 'use_backend.*if is_theoshift' /etc/haproxy/haproxy.cfg"

Result:
use_backend theoshift_green if is_theoshift
# This means: green is LIVE, blue is STANDBY
```

---

## Enforcement

### Before Deployment

**WRONG (Assumption-based):**
```
You: "Deploy TheoShift to STANDBY"

Windsurf: [Assumes blue is STANDBY based on documentation]
         [SSHs to blue-theoshift]
         [Deploys code]
         ❌ WRONG - might have deployed to LIVE!
```

**CORRECT (HAProxy-verified):**
```
You: "Deploy TheoShift to STANDBY"

Windsurf: 
1. [Calls get_deployment_status for theoshift]
2. [Verifies: LIVE=green, STANDBY=blue]
3. [SSHs to blue-theoshift (verified STANDBY)]
4. [Deploys code]
✅ CORRECT - deployed to verified STANDBY
```

### Before Traffic Switch

**WRONG (Assumption-based):**
```
You: "Switch TheoShift traffic to STANDBY"

Windsurf: [Assumes current routing]
         [Switches traffic]
         ❌ WRONG - might have switched wrong direction!
```

**CORRECT (HAProxy-verified):**
```
You: "Switch TheoShift traffic to STANDBY"

Windsurf:
1. [Calls get_deployment_status for theoshift]
2. [Verifies: LIVE=green, STANDBY=blue]
3. [Confirms: switching green→blue]
4. [Executes switch]
5. [Verifies: LIVE=blue, STANDBY=green]
✅ CORRECT - verified before and after
```

---

## Response Pattern

### Always State Current Status

**Before any deployment operation, state:**

```
Current HAProxy status for [app]:
  LIVE: [container-name]
  STANDBY: [container-name]

Proceeding to deploy to STANDBY ([container-name])...
```

**Example:**
```
Current HAProxy status for TheoShift:
  LIVE: green-theoshift (Container 132)
  STANDBY: blue-theoshift (Container 134)

Proceeding to deploy to STANDBY (blue-theoshift)...
```

### If Verification Fails

**If HAProxy check fails or returns unexpected results:**

```
⚠️ HAProxy verification failed for [app]

Error: [specific error]

Cannot proceed with deployment until HAProxy status is verified.

Recommended actions:
1. Check HAProxy configuration manually
2. Verify app is configured in HAProxy
3. Check network connectivity to HAProxy container
```

---

## Common Mistakes to Avoid

### ❌ DON'T: Rely on Documentation

```
# APP-MAP.md says blue is typically STANDBY
# So I'll deploy to blue
❌ WRONG - documentation may be stale
```

### ❌ DON'T: Assume Based on Previous State

```
# Last time I checked, green was LIVE
# So blue must be STANDBY
❌ WRONG - traffic may have switched since then
```

### ❌ DON'T: Use Container Names as Truth

```
# Container is named "ldc-staging"
# So it must be STANDBY
❌ WRONG - naming doesn't determine routing
```

### ✅ DO: Always Verify via HAProxy

```
# Check HAProxy config
# Determine current LIVE/STANDBY
# Then proceed with operation
✅ CORRECT - verified runtime truth
```

---

## Integration with Workflows

### /bump Workflow

```
Step 1: Verify HAProxy status
Step 2: Confirm STANDBY container
Step 3: Deploy to verified STANDBY
Step 4: Version bump
```

### /test-release Workflow

```
Step 1: Verify HAProxy status
Step 2: Confirm STANDBY container
Step 3: Run tests on verified STANDBY
Step 4: Report results
```

### /release Workflow

```
Step 1: Verify HAProxy status (before switch)
Step 2: Confirm current LIVE and STANDBY
Step 3: Execute traffic switch
Step 4: Verify HAProxy status (after switch)
Step 5: Confirm switch succeeded
```

### /sync Workflow

```
Step 1: Verify HAProxy status
Step 2: Identify LIVE container (source)
Step 3: Identify STANDBY container (target)
Step 4: Sync LIVE → STANDBY
```

---

## Error Handling

### If HAProxy Returns Unexpected State

```
Example: Both containers show as LIVE, or neither shows as LIVE

Response:
⚠️ Unexpected HAProxy state detected for [app]

HAProxy config shows: [actual config]
Expected: Single LIVE backend, single STANDBY backend
Actual: [describe issue]

This indicates a configuration problem.

STOP - Do not proceed with deployment.

Recommended actions:
1. Review HAProxy configuration manually
2. Check for recent HAProxy changes
3. Verify blue-green setup is correct
4. Contact infrastructure admin if needed
```

### If HAProxy is Unreachable

```
Response:
❌ Cannot reach HAProxy to verify LIVE/STANDBY status

Error: [connection error]

STOP - Do not proceed with deployment.

Recommended actions:
1. Verify network connectivity: ping prox
2. Verify HAProxy container is running: ssh prox "pct status 136"
3. Verify SSH access: ssh prox
4. Try manual verification once connectivity restored
```

---

## Summary

**Golden Rule:**
> Never deploy, switch traffic, or perform environment-specific operations without first verifying current LIVE/STANDBY status via HAProxy.

**Verification Methods (in order of preference):**
1. MCP Server: `get_deployment_status`
2. Shell Script: `verify-live-standby.sh`
3. Direct Query: HAProxy config grep

**Always state current status before proceeding with operations.**

**If verification fails, STOP and report the issue.**

---

## Applies To

- ✅ All app repositories (TheoShift, LDC Tools, QuantShift)
- ✅ All deployment workflows (/bump, /release, /sync, /test-release)
- ✅ All debugging sessions involving specific containers
- ✅ All traffic switching operations
- ✅ Any operation that targets LIVE or STANDBY specifically

**No exceptions.**
