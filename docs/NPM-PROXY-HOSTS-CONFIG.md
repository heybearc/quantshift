# NPM Proxy Host Configuration for QuantShift

**Date:** 2026-01-26  
**Purpose:** Configure Nginx Proxy Manager for QuantShift blue-green deployment

---

## Proxy Hosts to Create/Update

### 1. **quantshift.io** (Main Production Domain)

**Domain Names:**
```
quantshift.io
www.quantshift.io
```

**Scheme:** `http`  
**Forward Hostname/IP:** `10.92.3.26` (HAProxy)  
**Forward Port:** `80`  
**Cache Assets:** Yes  
**Block Common Exploits:** Yes  
**Websockets Support:** Yes (if needed)

**SSL:**
- Force SSL: Yes
- HTTP/2 Support: Yes
- HSTS Enabled: Yes
- Certificate: Let's Encrypt or existing wildcard cert

**Advanced (if needed):**
```nginx
# Preserve original host header
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

---

### 2. **blue.quantshift.io** (Direct Blue Access)

**Domain Names:**
```
blue.quantshift.io
```

**Scheme:** `http`  
**Forward Hostname/IP:** `10.92.3.29` (quantshift-blue)  
**Forward Port:** `3001`  
**Cache Assets:** Yes  
**Block Common Exploits:** Yes  
**Websockets Support:** Yes

**SSL:**
- Force SSL: Yes
- HTTP/2 Support: Yes
- Certificate: Let's Encrypt or wildcard cert

**Purpose:** Direct access to blue environment for testing/validation

---

### 3. **green.quantshift.io** (Direct Green Access)

**Domain Names:**
```
green.quantshift.io
```

**Scheme:** `http`  
**Forward Hostname/IP:** `10.92.3.30` (quantshift-green)  
**Forward Port:** `3001`  
**Cache Assets:** Yes  
**Block Common Exploits:** Yes  
**Websockets Support:** Yes

**SSL:**
- Force SSL: Yes
- HTTP/2 Support: Yes
- Certificate: Let's Encrypt or wildcard cert

**Purpose:** Direct access to green environment for testing/validation

---

### 4. **trader.cloudigan.net** (Legacy - Update)

**Action:** Update existing proxy host

**Current:** Points to `10.92.3.29:3000` (incorrect port)  
**Update to:** Point to `10.92.3.26:80` (HAProxy)

**OR**

**Alternative:** Redirect to `quantshift.io`

**Redirect Configuration (if using redirect):**
```nginx
return 301 https://quantshift.io$request_uri;
```

---

## Summary of Changes

| Domain | Target | Port | Purpose |
|--------|--------|------|---------|
| quantshift.io | HAProxy (10.92.3.26) | 80 | Main production (LIVE) |
| www.quantshift.io | HAProxy (10.92.3.26) | 80 | Main production (LIVE) |
| blue.quantshift.io | Blue CT (10.92.3.29) | 3001 | Direct blue access |
| green.quantshift.io | Green CT (10.92.3.30) | 3001 | Direct green access |
| trader.cloudigan.net | HAProxy (10.92.3.26) | 80 | Legacy (or redirect) |

---

## Traffic Flow

### Production Traffic (quantshift.io)
```
User → NPM (10.92.3.3) → HAProxy (10.92.3.26) → LIVE Backend (blue or green)
```

### Direct Blue Access (blue.quantshift.io)
```
User → NPM (10.92.3.3) → Blue Container (10.92.3.29:3001)
```

### Direct Green Access (green.quantshift.io)
```
User → NPM (10.92.3.3) → Green Container (10.92.3.30:3001)
```

---

## Testing After Configuration

### Test Main Domain
```bash
curl -I https://quantshift.io
# Should return HTTP 200 from blue environment
```

### Test Blue Direct
```bash
curl -I https://blue.quantshift.io
# Should return HTTP 200 from 10.92.3.29:3001
```

### Test Green Direct
```bash
curl -I https://green.quantshift.io
# Should return HTTP 200 from 10.92.3.30:3001
```

### Test Legacy Domain
```bash
curl -I https://trader.cloudigan.net
# Should return HTTP 200 or 301 redirect
```

---

## DNS Requirements

Ensure these DNS records exist in your quantshift.io zone:

```
quantshift.io           A/CNAME → Your public IP / NPM
www.quantshift.io       A/CNAME → Your public IP / NPM
blue.quantshift.io      A/CNAME → Your public IP / NPM
green.quantshift.io     A/CNAME → Your public IP / NPM
```

---

## Notes

- **HAProxy handles blue-green switching** - NPM just routes to HAProxy
- **Blue/green subdomains bypass HAProxy** - Direct container access for testing
- **Zero-downtime deployments** - Switch backends in HAProxy, not NPM
- **SSL termination at NPM** - HAProxy receives plain HTTP on port 80
