# Phase 6: Admin Platform Development

**Status:** In Progress  
**Started:** December 26, 2025  
**Duration:** 3-4 weeks  
**Goal:** Build professional web-based admin interface for QuantShift

---

## Overview

Transform QuantShift from CLI-only to a professional web platform with:
- User authentication and management
- Email configuration UI
- Real-time bot monitoring
- Configuration management
- Bot control panel

---

## Technology Stack

### Frontend:
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Recharts** - Charts and graphs
- **React Query** - Data fetching
- **Zustand** - State management

### Backend:
- **FastAPI** - Python API framework
- **PostgreSQL** - Database (existing)
- **Redis** - Session storage (existing)
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **JWT** - Authentication tokens
- **Pydantic** - Data validation

### Infrastructure:
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **Hot-Standby** - Same as bot infrastructure

---

## Phase 6.1: Project Setup & Authentication (Week 1-2)

### Tasks:

#### 1. Project Structure Setup
- [x] Create Next.js app in `apps/admin-web/`
- [ ] Create FastAPI app in `apps/admin-api/`
- [ ] Set up shared types/interfaces
- [ ] Configure Docker containers
- [ ] Set up development environment

#### 2. Database Schema
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit log table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    changes JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. Authentication System
**Backend (FastAPI):**
- [ ] User model and CRUD operations
- [ ] Password hashing (bcrypt)
- [ ] JWT token generation/validation
- [ ] Login endpoint
- [ ] Logout endpoint
- [ ] Token refresh endpoint
- [ ] Password reset flow
- [ ] Rate limiting

**Frontend (Next.js):**
- [ ] Login page UI
- [ ] Auth context/provider
- [ ] Protected route wrapper
- [ ] Token storage (httpOnly cookies)
- [ ] Auto token refresh
- [ ] Logout functionality

#### 4. User Management
- [ ] List users (admin only)
- [ ] Create user (admin only)
- [ ] Update user (admin only)
- [ ] Delete user (admin only)
- [ ] User invitation system
- [ ] Role-based access control

**Deliverables:**
- Working authentication system
- Login/logout functionality
- User management UI
- Protected routes
- JWT token handling

**Time:** 7-10 days

---

## Phase 6.2: Email Configuration UI (Week 3)

### Tasks:

#### 1. Email Settings API
**Backend:**
- [ ] Get email configuration endpoint
- [ ] Update email configuration endpoint
- [ ] Test email endpoint
- [ ] Get recipients endpoint
- [ ] Add/remove recipient endpoints
- [ ] Update notification preferences

#### 2. Email Configuration Page
**Frontend:**
- [ ] Email settings form
  - SMTP host/port
  - Gmail credentials
  - Test connection button
- [ ] Recipients management
  - List recipients by type
  - Add recipient modal
  - Remove recipient button
  - Bulk operations
- [ ] Notification preferences
  - Toggle switches for each type
  - Schedule settings (daily/weekly)
  - Enable/disable per notification
- [ ] Test email functionality
  - Send test trade alert
  - Send test daily summary
  - Send test error alert

#### 3. Integration with Email Service
- [ ] Connect UI to existing email_service.py
- [ ] Update config/email_config.yaml from UI
- [ ] Restart bot when config changes
- [ ] Validate email addresses
- [ ] Show email sending status

**Deliverables:**
- Email configuration UI
- Recipient management
- Test email functionality
- No more YAML editing needed

**Time:** 5-7 days

---

## Phase 6.3: Bot Monitoring Dashboard (Week 4)

### Tasks:

#### 1. Bot Status API
**Backend:**
- [ ] Get bot status endpoint
- [ ] Get account info endpoint
- [ ] Get positions endpoint
- [ ] Get trade history endpoint
- [ ] Get performance metrics endpoint
- [ ] WebSocket for real-time updates

#### 2. Dashboard UI
**Frontend:**
- [ ] Overview page
  - Bot status indicator (running/stopped)
  - Account balance/equity
  - Today's P&L
  - Open positions count
  - Recent trades
- [ ] Positions page
  - Table of open positions
  - Unrealized P&L
  - Entry price, current price
  - Stop loss, take profit
  - Time in trade
- [ ] Trade history page
  - Filterable trade table
  - Date range picker
  - Symbol filter
  - Win/loss filter
  - Export to CSV
- [ ] Performance page
  - Equity curve chart
  - Daily returns chart
  - Drawdown chart
  - Win/loss distribution
  - Key metrics (Sharpe, win rate, profit factor)

#### 3. Real-Time Updates
- [ ] WebSocket connection
- [ ] Live account balance updates
- [ ] Live position updates
- [ ] Trade execution notifications
- [ ] Bot status changes

**Deliverables:**
- Real-time bot monitoring
- Performance charts
- Trade history
- No more SSH log checking

**Time:** 7-10 days

---

## Phase 6.4: Bot Control & Configuration (Future)

### Tasks:

#### 1. Bot Control Panel
- [ ] Start/stop bot
- [ ] Restart bot
- [ ] View live logs
- [ ] Manual trade execution
- [ ] Force close positions
- [ ] Pause trading

#### 2. Strategy Configuration UI
- [ ] MA periods (5/20)
- [ ] Risk per trade
- [ ] Position sizing
- [ ] Symbol watchlist
- [ ] Filters (enable/disable)
- [ ] Save and apply changes

#### 3. Risk Management Settings
- [ ] Max positions
- [ ] Max portfolio heat
- [ ] Daily loss limit
- [ ] Circuit breakers
- [ ] Position size limits

**Deliverables:**
- Bot control panel
- Strategy configuration UI
- Risk management settings
- No more YAML editing

**Time:** 5-7 days

---

## Project Structure

```
quantshift/
├── apps/
│   ├── admin-web/              # Next.js frontend
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── trades/
│   │   │   │   ├── positions/
│   │   │   │   ├── performance/
│   │   │   │   └── settings/
│   │   │   │       ├── email/
│   │   │   │       ├── strategy/
│   │   │   │       └── users/
│   │   │   └── api/            # API routes (proxy to FastAPI)
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   │
│   ├── admin-api/              # FastAPI backend
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── bot.py
│   │   │   ├── email.py
│   │   │   ├── trades.py
│   │   │   └── config.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   └── bots/
│       └── equity/             # Existing bot
│
├── packages/
│   └── core/                   # Shared code
│
└── docker/
    ├── admin-web.Dockerfile
    └── admin-api.Dockerfile
```

---

## API Endpoints

### Authentication:
```
POST   /api/auth/login          # Login with email/password
POST   /api/auth/logout         # Logout and invalidate token
POST   /api/auth/refresh        # Refresh access token
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
GET    /api/auth/me             # Get current user info
```

### Users:
```
GET    /api/users               # List all users (admin)
POST   /api/users               # Create user (admin)
GET    /api/users/:id           # Get user details
PUT    /api/users/:id           # Update user
DELETE /api/users/:id           # Delete user (admin)
POST   /api/users/invite        # Send invitation (admin)
```

### Bot:
```
GET    /api/bot/status          # Get bot status
POST   /api/bot/start           # Start bot
POST   /api/bot/stop            # Stop bot
POST   /api/bot/restart         # Restart bot
GET    /api/bot/logs            # Get bot logs
WS     /api/bot/ws              # WebSocket for real-time updates
```

### Email:
```
GET    /api/email/config        # Get email configuration
PUT    /api/email/config        # Update email configuration
POST   /api/email/test          # Send test email
GET    /api/email/recipients    # Get recipients
POST   /api/email/recipients    # Add recipient
DELETE /api/email/recipients/:id # Remove recipient
```

### Trading:
```
GET    /api/trades              # Get trade history
GET    /api/trades/:id          # Get trade details
GET    /api/positions           # Get open positions
GET    /api/account             # Get account info
GET    /api/performance         # Get performance metrics
```

---

## Development Workflow

### Local Development:
```bash
# Terminal 1: Start FastAPI backend
cd apps/admin-api
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Start Next.js frontend
cd apps/admin-web
npm run dev

# Terminal 3: Start trading bot
cd apps/bots/equity
python run_bot_v2.py
```

### Production Deployment:
```bash
# Build and deploy to containers
docker-compose up -d

# Access:
# - Admin UI: https://admin.quantshift.local
# - API: https://api.quantshift.local
# - Bot: Running in background
```

---

## Security Considerations

### Authentication:
- JWT tokens with 15-minute expiration
- Refresh tokens with 7-day expiration
- HttpOnly cookies for token storage
- CSRF protection
- Rate limiting on auth endpoints
- Account lockout after 5 failed attempts

### Authorization:
- Role-based access control (RBAC)
- Admin vs Viewer roles
- API endpoint protection
- Resource-level permissions

### Data Protection:
- HTTPS only (TLS 1.3)
- Password hashing with bcrypt (cost 12)
- Encrypted credentials in database
- API key rotation
- Audit logging for all actions

---

## Testing Strategy

### Backend Tests:
- Unit tests for all endpoints
- Integration tests for auth flow
- Database migration tests
- API contract tests

### Frontend Tests:
- Component tests (Jest + React Testing Library)
- E2E tests (Playwright)
- Accessibility tests
- Performance tests

### Security Tests:
- Authentication bypass attempts
- SQL injection tests
- XSS vulnerability tests
- CSRF protection tests

---

## Success Criteria

### Phase 6.1 (Authentication):
- ✓ User can login/logout
- ✓ JWT tokens work correctly
- ✓ Protected routes enforce authentication
- ✓ Admin can manage users
- ✓ Password reset flow works

### Phase 6.2 (Email UI):
- ✓ Can configure email settings via UI
- ✓ Can add/remove recipients
- ✓ Test email functionality works
- ✓ No more YAML editing needed
- ✓ Changes apply without restart

### Phase 6.3 (Dashboard):
- ✓ Real-time bot status visible
- ✓ Account balance updates live
- ✓ Trade history displays correctly
- ✓ Performance charts render
- ✓ No more SSH log checking

---

## Timeline

**Week 1-2:** Authentication & User Management  
**Week 3:** Email Configuration UI  
**Week 4:** Bot Monitoring Dashboard  
**Week 5+:** Bot Control & Advanced Features

**Total:** 3-4 weeks for core admin platform

---

## Next Steps

**Starting NOW:**
1. Create Next.js project structure
2. Create FastAPI project structure
3. Set up database schema
4. Implement authentication backend
5. Build login page UI

**First Milestone:** Working login/logout by end of Week 1
