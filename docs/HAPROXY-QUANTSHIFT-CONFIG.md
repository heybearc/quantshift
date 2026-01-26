# HAProxy Configuration for QuantShift Blue-Green Deployment

**Date:** 2026-01-26  
**Purpose:** Configure HAProxy for QuantShift blue-green deployment

---

## Changes Required

### 1. Add ACLs for QuantShift domains (in frontend section)

Add these lines after the existing QuantShift ACLs:

```haproxy
# QuantShift - Main domain
acl is_quantshift hdr(host) -i quantshift.io
acl is_quantshift hdr(host) -i www.quantshift.io
```

### 2. Update existing trader_backend

**Current (INCORRECT - port 3000):**
```haproxy
backend trader_backend
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    
    # Dashboard on dedicated container (LXC 137)
    server dashboard 10.92.3.29:3000 check inter 5s fall 3 rise 2
```

**Replace with (CORRECT - port 3001, routes to BLUE initially):**
```haproxy
backend trader_backend
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    
    # Routes to BLUE initially (can switch to green later)
    server blue 10.92.3.29:3001 check inter 5s fall 3 rise 2
```

### 3. Add new backends for blue and green

Add these two new backend sections:

```haproxy
# QuantShift - Blue Environment (Container 137)
backend quantshift-blue-backend
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    server blue1 10.92.3.29:3001 check

# QuantShift - Green Environment (Container 138)
backend quantshift-green-backend
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    server green1 10.92.3.30:3001 check
```

### 4. Add routing rules (in frontend section)

Add these lines in the routing section (after the QuantShift ACL checks):

```haproxy
# QuantShift - Route main domain to LIVE (initially BLUE)
use_backend trader_backend if is_quantshift
```

---

## Complete Configuration Snippet

Here's the complete section to add/modify in HAProxy config:

```haproxy
# ===== FRONTEND SECTION =====
# Add these ACLs:
    acl is_quantshift hdr(host) -i quantshift.io
    acl is_quantshift hdr(host) -i www.quantshift.io

# Add this routing rule:
    use_backend trader_backend if is_quantshift

# ===== BACKEND SECTION =====
# Update trader_backend:
backend trader_backend
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    server blue 10.92.3.29:3001 check inter 5s fall 3 rise 2

# Add new backends:
backend quantshift-blue-backend
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    server blue1 10.92.3.29:3001 check

backend quantshift-green-backend
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    server green1 10.92.3.30:3001 check
```

---

## How to Switch Between Blue and Green

### To switch from BLUE to GREEN:

Edit `trader_backend` to point to green:
```haproxy
backend trader_backend
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    server green 10.92.3.30:3001 check inter 5s fall 3 rise 2
```

Then reload HAProxy:
```bash
ssh prox "pct exec 136 -- haproxy -c -f /etc/haproxy/haproxy.cfg && pct exec 136 -- systemctl reload haproxy"
```

### To switch from GREEN to BLUE:

Edit `trader_backend` to point to blue:
```haproxy
backend trader_backend
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    http-request set-header X-Forwarded-Host %[req.hdr(host)]
    server blue 10.92.3.29:3001 check inter 5s fall 3 rise 2
```

Then reload HAProxy.

---

## Verification Commands

```bash
# Check HAProxy config syntax
ssh prox "pct exec 136 -- haproxy -c -f /etc/haproxy/haproxy.cfg"

# Check which backend is LIVE
ssh prox "pct exec 136 -- grep -A 5 'backend trader_backend' /etc/haproxy/haproxy.cfg"

# Test health checks
curl -I http://10.92.3.29:3001/api/health  # Blue
curl -I http://10.92.3.30:3001/api/health  # Green
```

---

## Notes

- **Port 3000 → 3001:** Fixed incorrect port in original config
- **Blue is initial LIVE:** trader.cloudigan.net and quantshift.io route to blue initially
- **Zero-downtime switching:** HAProxy reload is seamless
- **Health checks:** Both backends monitored every 5 seconds
