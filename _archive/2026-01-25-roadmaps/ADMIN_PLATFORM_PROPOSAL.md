# QuantShift Admin Control Center - Architecture Proposal

**Date:** December 26, 2025  
**Status:** Proposal for Discussion

---

## Executive Summary

**Recommendation: YES - Build an Admin Control Center**

Moving from CLI-only to a web-based admin platform is the right evolution for QuantShift. This will provide:
- Professional user experience
- Easier configuration management
- Better monitoring and control
- Multi-user support
- Scalability for future features

---

## Why Build an Admin Platform?

### Current Pain Points:
1. **Configuration via YAML files** - Error-prone, requires SSH access
2. **No user management** - Single user only
3. **Manual log checking** - SSH into container to view logs
4. **No visual monitoring** - Can't see bot performance at a glance
5. **Email config requires env vars** - Not user-friendly
6. **No access control** - Anyone with SSH can modify everything

### Benefits of Admin Platform:
1. **User-Friendly** - Web UI instead of editing YAML files
2. **Secure** - Authentication, role-based access control
3. **Centralized** - All bot management in one place
4. **Visual** - Charts, graphs, real-time monitoring
5. **Multi-User** - Team collaboration support
6. **Audit Trail** - Track who changed what and when
7. **Mobile-Friendly** - Monitor from anywhere

---

## Proposed Architecture

### Technology Stack (Industry Standard):

**Frontend:**
- **Next.js 14** (React framework with SSR)
- **TypeScript** (Type safety)
- **Tailwind CSS** (Modern styling)
- **shadcn/ui** (Beautiful components)
- **Recharts** (Performance charts)
- **React Query** (Data fetching)

**Backend:**
- **FastAPI** (Python - integrates with existing bot)
- **PostgreSQL** (Already have it for bot data)
- **Redis** (Already have it for bot state)
- **JWT Authentication** (Secure, stateless)

**Infrastructure:**
- **Docker** (Containerized deployment)
- **Nginx** (Reverse proxy)
- **Hot-Standby** (Same as bot infrastructure)

---

## Core Features

### Phase 1: Authentication & User Management

**Features:**
- Login/logout with email + password
- JWT token-based authentication
- Password reset via email
- User roles: Admin, Viewer
- User invitation system
- Session management

**Pages:**
- `/login` - Login page
- `/register` - Registration (invite-only)
- `/forgot-password` - Password reset
- `/users` - User management (admin only)

**Time:** 3-5 days

---

### Phase 2: Bot Monitoring Dashboard

**Features:**
- Real-time bot status (running/stopped)
- Live account balance and equity
- Open positions with P&L
- Recent trades history
- Performance metrics (win rate, profit factor, Sharpe)
- Equity curve chart
- Trade distribution chart

**Pages:**
- `/dashboard` - Main overview
- `/trades` - Trade history
- `/positions` - Open positions
- `/performance` - Detailed analytics

**Time:** 5-7 days

---

### Phase 3: Configuration Management

**Features:**
- Email configuration UI
  - SMTP settings
  - Recipient management
  - Notification preferences
  - Test email functionality
- Strategy configuration
  - MA periods (5/20)
  - Risk per trade
  - Position sizing
  - Filters (enable/disable)
- Symbol watchlist management
- Risk management settings

**Pages:**
- `/settings/email` - Email configuration
- `/settings/strategy` - Strategy parameters
- `/settings/risk` - Risk management
- `/settings/symbols` - Watchlist

**Time:** 5-7 days

---

### Phase 4: Bot Control

**Features:**
- Start/stop bot
- Restart bot
- View live logs
- Manual trade execution (emergency)
- Force close positions
- Pause trading

**Pages:**
- `/control` - Bot control panel
- `/logs` - Live log viewer

**Time:** 3-5 days

---

### Phase 5: Advanced Features

**Features:**
- Scanner results viewer
- Backtest runner UI
- Strategy comparison
- Alert management
- Webhook integrations
- API access for external tools

**Time:** 7-10 days

---

## User Roles & Permissions

### Admin Role:
- Full access to everything
- User management
- Bot control (start/stop)
- Configuration changes
- Manual trading

### Viewer Role:
- View dashboard
- View trades and positions
- View performance metrics
- Cannot change settings
- Cannot control bot

### Future Roles:
- **Trader** - Can execute manual trades
- **Analyst** - Can run backtests
- **Developer** - API access

---

## Security Considerations

### Authentication:
- JWT tokens with expiration
- Refresh token rotation
- Password hashing (bcrypt)
- Rate limiting on login
- Account lockout after failed attempts

### Authorization:
- Role-based access control (RBAC)
- API endpoint protection
- Action audit logging
- Session management

### Data Protection:
- HTTPS only
- Encrypted credentials storage
- API key rotation
- Secure cookie handling

---

## Database Schema

### Users Table:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

### Email Recipients Table:
```sql
CREATE TABLE email_recipients (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Audit Log Table:
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    changes JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Structure

### Authentication Endpoints:
```
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
GET    /api/auth/me
```

### User Management:
```
GET    /api/users
POST   /api/users
GET    /api/users/:id
PUT    /api/users/:id
DELETE /api/users/:id
POST   /api/users/invite
```

### Bot Control:
```
GET    /api/bot/status
POST   /api/bot/start
POST   /api/bot/stop
POST   /api/bot/restart
GET    /api/bot/logs
```

### Configuration:
```
GET    /api/config/email
PUT    /api/config/email
POST   /api/config/email/test
GET    /api/config/strategy
PUT    /api/config/strategy
GET    /api/config/risk
PUT    /api/config/risk
```

### Trading Data:
```
GET    /api/trades
GET    /api/trades/:id
GET    /api/positions
GET    /api/performance
GET    /api/account
```

---

## Implementation Timeline

### Week 1-2: Foundation
- Project setup (Next.js + FastAPI)
- Database schema
- Authentication system
- Basic user management

### Week 3: Dashboard
- Bot status monitoring
- Account overview
- Trade history
- Performance charts

### Week 4: Configuration
- Email config UI
- Strategy settings
- Risk management
- Symbol watchlist

### Week 5: Bot Control
- Start/stop functionality
- Log viewer
- Manual controls

### Week 6: Polish & Testing
- UI/UX improvements
- Security hardening
- Performance optimization
- Documentation

**Total Time: 6 weeks for full platform**

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                        │
│                   (Nginx / HAProxy)                      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌───────▼────────┐
│   Primary      │       │   Standby      │
│   Container    │◄─────►│   Container    │
│                │       │                │
│ - Next.js UI   │       │ - Next.js UI   │
│ - FastAPI      │       │ - FastAPI      │
│ - Trading Bot  │       │ - Trading Bot  │
└───────┬────────┘       └───────┬────────┘
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌───────▼────────┐
│   PostgreSQL   │       │     Redis      │
│   (Shared)     │       │   (Shared)     │
└────────────────┘       └────────────────┘
```

---

## Cost-Benefit Analysis

### Development Cost:
- **Time:** 6 weeks (150-200 hours)
- **Complexity:** Medium (using proven stack)
- **Maintenance:** Low (standard web app)

### Benefits:
- **User Experience:** 10x improvement
- **Scalability:** Support multiple users
- **Monitoring:** Real-time visibility
- **Configuration:** No more YAML editing
- **Security:** Proper access control
- **Professional:** Production-ready platform

### ROI:
- **Immediate:** Easier bot management
- **Short-term:** Better monitoring and control
- **Long-term:** Platform for additional features
- **Future:** Could offer as SaaS product

---

## Alternative Approaches

### Option 1: Use Existing Platform (Grafana + Custom UI)
**Pros:** Faster setup, proven monitoring
**Cons:** Limited customization, no user management, not integrated

### Option 2: CLI-Only with Better Tools
**Pros:** Simpler, no web development
**Cons:** Not user-friendly, no multi-user, limited scalability

### Option 3: Build Custom Admin Platform (Recommended)
**Pros:** Full control, tailored to needs, professional, scalable
**Cons:** Takes time to build, requires maintenance

---

## Recommendation

**Build the Admin Control Center - Here's Why:**

1. **You're building a serious trading system** - It deserves a professional interface
2. **Configuration management is painful** - Web UI solves this
3. **Multi-user support is valuable** - Share with team/family
4. **Monitoring is critical** - Real-time visibility into bot performance
5. **Scalability** - Foundation for future features (scanner UI, backtest runner, etc.)
6. **Industry standard** - All professional trading platforms have admin interfaces

**Suggested Approach:**

**Phase A: Build Core Admin Platform (3-4 weeks)**
- Authentication & user management
- Bot monitoring dashboard
- Email configuration UI
- Basic bot control

**Phase B: Continue Feature Development (Parallel)**
- Golden Cross scanner
- Scale-out strategy
- Trailing stops
- Advanced analytics

**Phase C: Advanced Admin Features (Future)**
- Scanner results viewer
- Backtest runner UI
- Strategy comparison
- API access

---

## Next Steps

### Immediate (Today):
1. Test email notification system
2. Decide on admin platform approach
3. If YES: Start Phase A (authentication)

### This Week:
1. Set up Next.js + FastAPI project structure
2. Implement authentication system
3. Create basic dashboard

### Next 2-3 Weeks:
1. Build email configuration UI
2. Add bot monitoring
3. Implement bot control

---

## Questions for Discussion

1. **Do you want multi-user support?** Or just single admin user?
2. **Mobile app in future?** Or web-only?
3. **Public access?** Or private/internal only?
4. **SaaS potential?** Could you offer this to others?
5. **Timeline priority?** Admin platform first, or continue with scanner?

---

## My Strong Recommendation

**YES - Build the Admin Control Center**

**Why now?**
- Email config UI would be immediately useful
- Bot monitoring is critical as we add more features
- Foundation for all future development
- Professional appearance and usability

**Start with:**
1. Authentication (login/logout)
2. Email configuration UI
3. Bot status dashboard
4. Then continue with scanner and other features

**This transforms QuantShift from a CLI tool into a professional trading platform.**
