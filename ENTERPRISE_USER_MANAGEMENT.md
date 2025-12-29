# Enterprise-Grade User Management System
## QuantShift Trading Platform

**Status:** Design Complete - Ready for Implementation  
**Version:** 1.0  
**Date:** December 29, 2025

---

## 🎯 Executive Summary

This document outlines a comprehensive, enterprise-grade user management system for QuantShift that meets industry standards for trading platforms. The system includes 100+ user fields covering identity, security, trading, compliance, and administrative controls.

**Key Features:**
- Multi-factor authentication (MFA/2FA)
- Advanced password security with expiry and history
- Trading platform integration with Alpaca
- Risk management and position limits
- KYC/AML compliance workflow
- Comprehensive audit logging
- Role-based access control
- IP whitelisting and device management

---

## 📊 Complete Feature List

### 1. IDENTITY & AUTHENTICATION ⭐ CRITICAL
- Username and email login
- Phone number with country code
- Time zone and language preferences
- Profile photo/avatar
- Multi-factor authentication (TOTP, SMS, Email)
- Password complexity (12+ chars, mixed case, numbers, symbols)
- Password expiry (90 days) with history (last 5)
- Force password change on first login
- Account lockout (5 attempts, 30-minute lockout)
- Email and phone verification
- Trusted device management
- Session timeout and concurrent session limits

### 2. TRADING PLATFORM INTEGRATION ⭐ CRITICAL
- Alpaca account ID linking
- API credentials (encrypted storage)
- Account type (Paper/Live)
- Risk tolerance (Conservative/Moderate/Aggressive/Custom)
- Max position size limits
- Max portfolio allocation percentage
- Daily loss limits
- Max open positions
- Trading permissions (place/modify/cancel orders)
- Max order size limits
- Asset class restrictions (Stocks/Options/Crypto)
- Trading hours enforcement
- Strategy whitelisting

### 3. COMPLIANCE & REGULATORY ⭐ HIGH
- KYC/AML status tracking
- Identity document upload (ID, proof of address)
- Document verification workflow
- Accredited investor status
- Pattern day trader flagging
- Trading agreement acceptance with versioning
- Risk disclosure acceptance
- Terms of service tracking
- Compliance audit trail

### 4. SECURITY CONTROLS ⭐ CRITICAL
- IP whitelisting (optional)
- Device fingerprinting
- Login history with geolocation
- Failed login attempt tracking
- Account suspension with reason
- API key management
- Encrypted credential storage
- Session hijacking prevention
- Security audit logging

### 5. ADMINISTRATIVE FEATURES ⭐ HIGH
- Account status (Active/Suspended/Locked/Archived)
- Admin approval workflow
- Account expiry dates
- Trial period management
- Subscription tier tracking
- Bulk user operations
- User impersonation for support
- Comprehensive audit logging

### 6. NOTIFICATIONS & ALERTS ⭐ MEDIUM
- Email notifications
- SMS notifications
- Push notifications
- Granular alert preferences:
  - Trade executions
  - Position updates
  - Risk limit breaches
  - Account alerts
  - System notifications

---

## 🗄️ Database Schema (100+ Fields)

### Core Identity (8 fields)
- username, email, passwordHash, fullName
- phoneNumber, phoneCountryCode, timeZone, preferredLanguage

### Authentication & Security (25 fields)
- Email/phone verification tokens and expiry
- Password management (expiry, history, reset tokens)
- MFA (enabled, secret, backup codes, method)
- Account lockout (attempts, locked until, last failed)
- Session management (max concurrent, timeout minutes)
- IP whitelisting (whitelist array, enabled flag)
- Trusted devices array

### Trading Platform (15 fields)
- Alpaca account (ID, type, API keys encrypted, status)
- Risk management (tolerance, max position, allocation, loss limit, max positions)
- Trading permissions (can place/modify/cancel, max order size)
- Asset classes allowed, trading hours only flag
- Allowed strategies array

### Compliance & KYC (12 fields)
- KYC status, verified date, verified by
- Document URLs (identity, proof of address)
- Accredited investor, pattern day trader flags
- Agreement acceptances (trading, risk disclosure, TOS)
- Agreement dates and versions

### Notifications (4 fields)
- Email/SMS/Push notification toggles
- Notification preferences JSON

### Administrative (10 fields)
- Requires approval, approved by/at
- Suspended at/by, suspension reason
- Account expires at, trial ends at
- Subscription tier

### Tracking (6 fields)
- Created/updated timestamps
- Last login with IP and device
- Last seen release version

### Supporting Models
- **LoginHistory** - All login attempts with success/failure
- **ApiKey** - User API keys with permissions
- **Session** - Active sessions (existing)
- **AuditLog** - Comprehensive audit trail (existing)

### New Enums
- **UserRole**: SUPER_ADMIN, ADMIN, TRADER, VIEWER, API_USER
- **AccountStatus**: ACTIVE, INACTIVE, PENDING_APPROVAL, SUSPENDED, LOCKED, ARCHIVED
- **AccountType**: PAPER, LIVE
- **TradingAccountStatus**: ACTIVE, INACTIVE, RESTRICTED, CLOSED
- **RiskTolerance**: CONSERVATIVE, MODERATE, AGGRESSIVE, CUSTOM
- **KycStatus**: NOT_STARTED, IN_PROGRESS, PENDING_REVIEW, APPROVED, REJECTED, EXPIRED
- **MfaMethod**: TOTP, SMS, EMAIL

---

## 🎨 User Interface Components

### 1. Enhanced User Management Page
- Advanced filtering and search
- Quick stats cards (total, active, pending, suspended)
- Bulk actions (approve, suspend, delete)
- Export to CSV/Excel
- Pagination for large datasets

### 2. Add User Modal (5 Tabs)

**Tab 1: Basic Information**
- Email, Username, Full Name
- Phone Number (with country code picker)
- Password (with strength meter)
- Time Zone, Preferred Language

**Tab 2: Security & Access**
- Role selection
- Account status
- Email/Phone verified checkboxes
- Requires approval toggle
- Force password change
- MFA settings
- Session limits

**Tab 3: Trading Configuration**
- Alpaca Account ID
- Account Type (Paper/Live)
- Risk Tolerance
- Position and allocation limits
- Trading permissions checkboxes
- Asset class multi-select

**Tab 4: Compliance**
- KYC Status
- Regulatory flags
- Agreement checkboxes
- Document upload

**Tab 5: Notifications**
- Email/SMS/Push toggles
- Alert preferences

### 3. Edit User Modal
- Same 5-tab structure
- Additional: Account history timeline
- Recent activity log
- Suspension controls
- View-only fields (created date, last login)

### 4. User Profile Page
- Comprehensive information display
- Activity timeline
- Login history with map
- Trading statistics
- Compliance status
- Document viewer
- Action buttons (Edit, Suspend, Delete, Impersonate)

### 5. User Security Tab
- MFA setup wizard
- Trusted devices list
- Active sessions with terminate
- Login history table
- IP whitelist management
- API key management
- Security audit log

### 6. User Trading Tab
- Alpaca account details
- Current positions
- Trade history
- Risk metrics and P&L charts
- Trading permissions matrix

---

## 🔐 Security Standards

### Password Requirements
- Minimum 12 characters
- Uppercase, lowercase, number, special character
- Cannot contain username or email
- Cannot reuse last 5 passwords
- Expires after 90 days
- Check against common password list

### Account Lockout
- 5 failed attempts triggers lockout
- 30-minute lockout duration
- Reset counter on successful login
- Notify user and admin

### MFA Implementation
- TOTP (Time-based One-Time Password)
- 30-second time window, 6-digit codes
- QR code for setup
- 10 backup codes (single-use)
- Recovery email option

### Session Management
- Max 3 concurrent sessions
- 60-minute inactivity timeout
- 12-hour absolute timeout
- Renew on activity
- Require re-auth for sensitive operations

### Encryption
- Passwords: bcrypt (12 rounds)
- API Keys: AES-256-GCM
- MFA Secrets: AES-256-GCM
- PII: Field-level encryption
- TLS 1.3 for all connections

---

## 📋 Implementation Plan (4 Weeks)

### Week 1: Database & Core Security
1. Update Prisma schema with all fields
2. Create and run migrations
3. Implement password complexity validation
4. Add password expiry and history
5. Build account lockout logic
6. Add login history tracking

### Week 2: MFA & User Interface
1. Implement TOTP MFA infrastructure
2. Build tabbed Add User modal
3. Build tabbed Edit User modal
4. Add session management
5. Implement IP whitelisting

### Week 3: Trading & Compliance
1. Alpaca account integration
2. API credential encryption
3. Risk management controls
4. Trading permissions enforcement
5. KYC workflow
6. Document upload system

### Week 4: Advanced Features
1. User profile page
2. Security tab
3. Trading tab
4. API key management
5. Bulk operations
6. Export functionality
7. Comprehensive testing

---

## 🧪 Testing Checklist

### Security
- [ ] Password complexity enforcement
- [ ] Password expiry and history
- [ ] Account lockout
- [ ] MFA enrollment and validation
- [ ] Session timeout
- [ ] IP whitelisting
- [ ] Encryption verification
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection

### Functionality
- [ ] User CRUD operations
- [ ] Role-based access control
- [ ] Trading permissions
- [ ] Risk limit validation
- [ ] KYC workflow
- [ ] Document upload
- [ ] Notifications
- [ ] Bulk operations
- [ ] Search and filtering

### Performance
- [ ] User list pagination (1000+ users)
- [ ] Search response time < 500ms
- [ ] Login with MFA < 2 seconds
- [ ] Database query optimization

### Compliance
- [ ] Audit log completeness
- [ ] GDPR compliance
- [ ] Data retention policies
- [ ] SOC 2 requirements

---

## 🎯 Success Metrics

- Zero unauthorized access incidents
- 100% MFA adoption for admins
- < 0.1% false positive lockouts
- < 2 seconds page load time
- < 3 clicks to create user
- 100% audit log coverage
- < 24 hour KYC approval time

---

## 📚 Next Steps

1. ✅ Review and approve this design
2. ⏳ Update Prisma schema
3. ⏳ Run database migrations
4. ⏳ Implement core security features
5. ⏳ Build enhanced UI components
6. ⏳ Integrate trading platform features
7. ⏳ Add compliance workflows
8. ⏳ Complete testing and deployment

**Estimated Timeline:** 4 weeks  
**Priority:** CRITICAL - Foundation for platform security

---

**Document Owner:** Development Team  
**Last Updated:** December 29, 2025
