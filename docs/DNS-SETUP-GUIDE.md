# DNS Setup Guide for QuantShift

**Date:** 2026-01-26  
**Purpose:** Configure DNS for QuantShift blue-green deployment

---

## Current DNS Status

**Internal DNS (dc-01.cloudigan.com - 10.92.0.10):**
- ✅ `blue.quantshift.io` → 10.92.3.3 (NPM)
- ✅ `green.quantshift.io` → 10.92.3.3 (NPM)
- ❌ `quantshift.io` → Not configured
- ❌ `www.quantshift.io` → Not configured

**External DNS (Namecheap):**
- Waiting for propagation

---

## Internal DNS Setup (Immediate)

### Add to dc-01 DNS Zone (quantshift.io)

**Records needed:**
```
quantshift.io           A    10.92.3.3
www.quantshift.io       A    10.92.3.3
```

**PowerShell commands (on dc-01):**
```powershell
# Add apex record
Add-DnsServerResourceRecordA -Name "@" -ZoneName "quantshift.io" -IPv4Address "10.92.3.3"

# Add www record
Add-DnsServerResourceRecordA -Name "www" -ZoneName "quantshift.io" -IPv4Address "10.92.3.3"

# Verify
Get-DnsServerResourceRecord -ZoneName "quantshift.io" | Where-Object {$_.HostName -in "@","www","blue","green"}
```

---

## External DNS Setup (Namecheap)

### For Public Internet Access

**A Records to add:**
```
@                       A    [Your Public IP]
www                     A    [Your Public IP]
blue                    A    [Your Public IP]
green                   A    [Your Public IP]
```

**OR use CNAME to existing domain:**
```
quantshift.io           CNAME    cloudigan.net
www.quantshift.io       CNAME    cloudigan.net
blue.quantshift.io      CNAME    cloudigan.net
green.quantshift.io     CNAME    cloudigan.net
```

---

## Testing Internal DNS

### Test from your Mac:
```bash
# Should resolve to 10.92.3.3
dig @10.92.0.10 quantshift.io +short
dig @10.92.0.10 www.quantshift.io +short
dig @10.92.0.10 blue.quantshift.io +short
dig @10.92.0.10 green.quantshift.io +short
```

### Test via /etc/hosts (Temporary Workaround)

If DNS isn't working, add to `/etc/hosts`:
```
10.92.3.3    quantshift.io www.quantshift.io
10.92.3.3    blue.quantshift.io green.quantshift.io
```

Then test:
```bash
curl -I http://quantshift.io
curl -I http://blue.quantshift.io
curl -I http://green.quantshift.io
```

---

## Namecheap Propagation Issues

### Common Causes:

1. **TTL too high:** Check if TTL is set to 1800 or lower
2. **Nameservers not updated:** Verify Namecheap nameservers are set
3. **DNS not saved:** Ensure you clicked "Save All Changes"
4. **Cached records:** Clear local DNS cache

### Check Propagation Status:
```bash
# Check from multiple DNS servers
dig @8.8.8.8 quantshift.io +short        # Google DNS
dig @1.1.1.1 quantshift.io +short        # Cloudflare DNS
dig @208.67.222.222 quantshift.io +short # OpenDNS
```

### Online Tools:
- https://www.whatsmydns.net/#A/quantshift.io
- https://dnschecker.org/#A/quantshift.io

---

## Recommended Approach

### Phase 1: Internal Testing (Now)
1. Add `quantshift.io` A record to dc-01 DNS
2. Test via internal network
3. Validate blue-green switching works
4. Complete all testing internally

### Phase 2: External Access (When Namecheap propagates)
1. Wait for Namecheap DNS propagation
2. Update NPM SSL certificates for public domains
3. Test external access
4. Go live publicly

---

## Workaround: Use /etc/hosts

**Add to `/etc/hosts` on your Mac:**
```
10.92.3.3    quantshift.io
10.92.3.3    www.quantshift.io
10.92.3.3    blue.quantshift.io
10.92.3.3    green.quantshift.io
```

**Test immediately:**
```bash
curl -I http://quantshift.io
# Should work even without DNS propagation
```

---

## NPM Configuration (Works with /etc/hosts)

You can configure NPM proxy hosts now using the domains, even if DNS isn't propagated. NPM will accept the Host header and route correctly.

**Test NPM routing:**
```bash
# Test via Host header (bypasses DNS)
curl -H "Host: quantshift.io" http://10.92.3.3
curl -H "Host: blue.quantshift.io" http://10.92.3.3
curl -H "Host: green.quantshift.io" http://10.92.3.3
```

---

## Next Steps

1. **Add internal DNS records** (dc-01)
2. **Configure NPM proxy hosts** (works without external DNS)
3. **Test via /etc/hosts or Host headers**
4. **Wait for Namecheap propagation** (for public access)
5. **Update SSL certificates** (when DNS propagates)
