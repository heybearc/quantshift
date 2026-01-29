---
name: verify-haproxy
description: Verify LIVE/STANDBY status via HAProxy before deployment operations
activation: automatic
priority: critical
---

# Verify HAProxy Skill

## Purpose

Automatically verify current LIVE/STANDBY status via HAProxy before any deployment, testing, or traffic switching operation.

## Activation

**Automatically activated when:**
- User mentions deploying to STANDBY
- User mentions deploying to LIVE
- User requests traffic switch
- User runs /bump, /test-release, /release, or /sync workflows
- User asks about current environment status
- User mentions specific container names (blue-theoshift, ldc-staging, etc.)

**Manual activation:**
- "Check HAProxy status for [app]"
- "What's the current LIVE/STANDBY for [app]?"
- "Verify environment status"

## Process

### Step 1: Identify App

```
User mentions: "Deploy TheoShift to STANDBY"

Extract app name: theoshift
```

### Step 2: Query HAProxy

**Preferred method: MCP Server**

```
Call: mcp0_get_deployment_status
Parameters: { app: "theoshift" }

Response:
{
  "app": "theoshift",
  "live": {
    "container": "green-theoshift",
    "id": 132,
    "ip": "10.92.3.22",
    "health": "healthy"
  },
  "standby": {
    "container": "blue-theoshift",
    "id": 134,
    "ip": "10.92.3.24",
    "health": "healthy"
  }
}
```

**Fallback method: Shell script**

```
Run: _cloudy-ops/scripts/verify-live-standby.sh theoshift

Parse output:
LIVE: green-theoshift
STANDBY: blue-theoshift
```

### Step 3: Report Status

**Always state current status before proceeding:**

```
Current HAProxy status for TheoShift:
  LIVE: green-theoshift (Container 132)
  STANDBY: blue-theoshift (Container 134)

Proceeding to deploy to STANDBY (blue-theoshift)...
```

### Step 4: Proceed with Operation

**Use verified information for deployment:**

```
# Now we know STANDBY = blue-theoshift
ssh blue-theoshift 'cd /opt/theoshift && git pull && npm run build && pm2 restart theoshift'
```

## Response Patterns

### Deployment to STANDBY

```
You: "Deploy TheoShift to STANDBY"

Windsurf:
🔍 Verifying HAProxy status...

Current status for TheoShift:
  ✅ LIVE: green-theoshift (Container 132)
  ✅ STANDBY: blue-theoshift (Container 134)

Deploying to STANDBY (blue-theoshift)...
[deployment steps]
```

### Traffic Switch

```
You: "Switch TheoShift traffic"

Windsurf:
🔍 Verifying current HAProxy status...

Current status for TheoShift:
  LIVE: green-theoshift → will become STANDBY
  STANDBY: blue-theoshift → will become LIVE

Switching traffic from green to blue...
[switch steps]

🔍 Verifying switch succeeded...

New status for TheoShift:
  ✅ LIVE: blue-theoshift (Container 134)
  ✅ STANDBY: green-theoshift (Container 132)

Traffic switch complete.
```

### Status Check

```
You: "What's the current environment status for LDC Tools?"

Windsurf:
🔍 Checking HAProxy configuration...

Current status for LDC Tools:
  ✅ LIVE: ldc-prod (Container 133, IP 10.92.3.23)
     - Receiving production traffic
     - Health: Healthy
  
  ✅ STANDBY: ldc-staging (Container 135, IP 10.92.3.25)
     - Ready for deployment
     - Health: Healthy

Last traffic switch: [timestamp from state file]
```

## Error Handling

### HAProxy Unreachable

```
You: "Deploy to STANDBY"

Windsurf:
🔍 Verifying HAProxy status...

❌ Cannot reach HAProxy

Error: Connection timeout to prox host

STOP - Cannot verify LIVE/STANDBY status.

Recommended actions:
1. Check network connectivity: ping prox
2. Verify SSH access: ssh prox
3. Check HAProxy container: ssh prox "pct status 136"

Cannot proceed with deployment until HAProxy is verified.
```

### Unexpected Configuration

```
You: "Deploy to STANDBY"

Windsurf:
🔍 Verifying HAProxy status...

⚠️ Unexpected HAProxy configuration detected

HAProxy shows: use_backend theoshift_blue if is_theoshift
               use_backend theoshift_green if is_theoshift

Both backends are configured as LIVE (or neither is).

STOP - Configuration error detected.

This indicates a problem with HAProxy configuration.

Recommended actions:
1. Review HAProxy config manually
2. Check for recent configuration changes
3. Verify blue-green setup is correct

Cannot proceed with deployment.
```

### App Not Found

```
You: "Deploy NewApp to STANDBY"

Windsurf:
🔍 Verifying HAProxy status...

❌ No HAProxy configuration found for NewApp

App may not be configured in HAProxy yet.

Cannot determine LIVE/STANDBY status.

Recommended actions:
1. Verify app name (check APP-MAP.md)
2. Check if app is configured in HAProxy
3. If new app, configure HAProxy first

Cannot proceed with deployment.
```

## Integration with Workflows

### Auto-Deploy Hook

```
# In auto-deploy.sh
# Before deployment, verify HAProxy

echo "🔍 Verifying HAProxy status..."
STANDBY=$(verify-live-standby.sh $APP | grep STANDBY | awk '{print $2}')

echo "Deploying to verified STANDBY: $STANDBY"
ssh $STANDBY "cd /opt/$APP && git pull && ..."
```

### /bump Workflow

```
Step 1: Load governance
Step 2: Verify HAProxy status ← THIS SKILL
Step 3: Confirm STANDBY container
Step 4: Deploy to verified STANDBY
Step 5: Version bump
```

### /test-release Workflow

```
Step 1: Hard-fail checks
Step 2: Verify HAProxy status ← THIS SKILL
Step 3: Confirm STANDBY container
Step 4: Run tests on verified STANDBY
Step 5: Report results
```

## Benefits

**Prevents production outages:**
- Never deploy to LIVE by mistake
- Always know which container is which
- Verified before every operation

**Eliminates assumptions:**
- No guessing based on documentation
- No relying on previous state
- No trusting container names

**Provides confidence:**
- Clear visibility into current state
- Explicit confirmation before actions
- Verification after traffic switches

**Catches configuration issues:**
- Detects HAProxy misconfigurations
- Identifies connectivity problems
- Alerts to unexpected states

## App-Specific Details

### TheoShift
```
App name: theoshift
Blue: blue-theoshift (Container 134, IP 10.92.3.24)
Green: green-theoshift (Container 132, IP 10.92.3.22)
HAProxy backend: theoshift_blue, theoshift_green
```

### LDC Tools
```
App name: ldctools (or ldc-tools)
Blue: ldc-staging (Container 135, IP 10.92.3.25)
Green: ldc-prod (Container 133, IP 10.92.3.23)
HAProxy backend: ldctools_blue, ldctools_green
```

### QuantShift
```
App name: quantshift
Container: qs-dashboard (Container 137)
Note: Single container, not blue-green (yet)
```

## Notes

- Always use MCP server if available (preferred)
- Fall back to shell script if MCP unavailable
- Never proceed without verification
- Always state current status before operations
- Verify again after traffic switches
- Report any unexpected configurations immediately
