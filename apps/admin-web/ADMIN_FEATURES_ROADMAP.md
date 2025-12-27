# QuantShift Admin Features Roadmap
## Integrated from Theoshift & LDC Tools Analysis

**Created:** December 27, 2025  
**Status:** Ready for Implementation  
**Source:** Analysis of Theoshift and LDC Tools admin functionality

---

## 🎯 Overview

This roadmap integrates proven admin patterns from Theoshift (Next.js Pages Router) and LDC Tools (Next.js + FastAPI) into the QuantShift admin platform.

---

## 📊 Phase 2: Admin Control Center (Week 2 - Current)

### **2.1 Settings Page** ⭐ CRITICAL
**Source:** Theoshift `/admin/email-config/index.tsx`

**Features:**
- **Email Configuration:**
  - Gmail App Password authentication (recommended)
  - Custom SMTP configuration
  - Auto-remove spaces from app password
  - Test email functionality
  - Configuration validation
  
- **Email Settings:**
  - From Email (required)
  - From Name (required)
  - Reply-To Email (optional)
  
- **Platform Settings:**
  - Platform name
  - Platform version
  - Notification preferences
  - General configuration

**Implementation:**
```typescript
// Two authentication methods
authType: 'gmail' | 'smtp'

// Gmail config
gmailEmail: string
gmailAppPassword: string (auto-remove spaces)

// SMTP config
smtpServer: string
smtpPort: '587' | '465' | '25'
smtpUser: string
smtpPassword: string
smtpSecure: boolean

// Common settings
fromEmail: string (required)
fromName: string (required)
replyToEmail: string (optional)
```

**API Endpoints:**
- `GET /api/admin/settings` - Load all settings
- `POST /api/admin/settings` - Save settings
- `POST /api/admin/settings/test-email` - Send test email

**UI Components:**
- Tab-based interface (Email, General, Notifications)
- Real-time validation
- Success/error status messages
- Test email button
- Save button (disabled until valid)

**Priority:** 🔴 CRITICAL - Needed for email notifications

---

### **2.2 Release Notes System** ⭐ CRITICAL
**Source:** Theoshift `/pages/release-notes.tsx`

**Features:**
- **Markdown-Based System:**
  - Store releases in database (not files)
  - Markdown content rendering
  - Version sorting (descending)
  - Type badges (major/minor/patch)
  
- **Banner Notification:**
  - Show on login if new version
  - Dismiss functionality
  - Track user's last seen version
  - Persistent until dismissed

- **Admin Interface:**
  - Create new release notes
  - Edit existing releases
  - Publish/unpublish releases
  - Preview markdown

**Database Schema:**
```typescript
ReleaseNote {
  id: string
  version: string (unique)
  title: string
  description: string
  changes: Json // Array of change objects
  releaseDate: DateTime
  isPublished: boolean
  isDismissed: boolean
  createdBy: string
  type: 'major' | 'minor' | 'patch'
}
```

**Banner Logic:**
```typescript
// Show banner if:
1. New release exists (isPublished = true)
2. User hasn't seen this version (lastSeenReleaseVersion < latest)
3. User hasn't dismissed it (isDismissed = false)
```

**API Endpoints:**
- `GET /api/release-notes` - Get all published releases
- `GET /api/release-notes/latest` - Get latest release
- `POST /api/admin/release-notes` - Create release (admin only)
- `PUT /api/admin/release-notes/:id` - Update release (admin only)
- `POST /api/release-notes/dismiss` - Dismiss banner for user

**UI Components:**
- Release notes page with version list
- Banner component (dismissible)
- Admin editor with markdown preview
- Version badge with color coding

**Priority:** 🔴 CRITICAL - Needed for version tracking

---

### **2.3 Navigation Restructure** ⭐ CRITICAL
**Source:** Theoshift admin dashboard organization

**Structure:**
```
┌─────────────────────────────────────┐
│  ADMIN CONTROL CENTER               │
├─────────────────────────────────────┤
│  👥 Users                           │
│  ⚙️  Settings                       │
│  📋 Release Notes (Admin)           │
│  📊 Audit Logs                      │
│  💚 Health Monitor                  │
│  📡 API Status                      │
│  ⚡ System Operations               │
│  🔐 Sessions                        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  TRADING PLATFORM                   │
├─────────────────────────────────────┤
│  📈 Dashboard                       │
│  💰 Trades                          │
│  📊 Positions                       │
│  📉 Performance                     │
│  🤖 Bot Configuration               │
│  📧 Email Notifications             │
└─────────────────────────────────────┘
```

**Implementation:**
- Separate sidebar sections
- Visual divider between sections
- Color coding (Admin: blue, Platform: green)
- Icons for each module
- Active state highlighting

**Priority:** 🔴 CRITICAL - Needed for clarity

---

## 📊 Phase 3: Enhanced Admin Dashboard (Week 3)

### **3.1 Statistics Cards** ⭐ HIGH
**Source:** Theoshift `/admin/index.tsx`

**Metrics:**
- Total Users
- Total Events (or Trades for QuantShift)
- Active Sessions (clickable)
- Total Positions
- Bot Status
- System Health

**Implementation:**
```typescript
<div className="grid grid-cols-1 md:grid-cols-4 gap-6">
  <StatCard
    icon="👥"
    value={stats.totalUsers}
    label="Total Users"
    color="blue"
  />
  <StatCard
    icon="💰"
    value={stats.totalTrades}
    label="Total Trades"
    color="green"
  />
  <Link href="/admin/sessions">
    <StatCard
      icon="🔐"
      value={stats.activeSessions}
      label="Active Sessions"
      color="orange"
      clickable
    />
  </Link>
</div>
```

**Priority:** 🟡 HIGH - Improves dashboard

---

### **3.2 Session Management** ⭐ HIGH
**Source:** Theoshift `/admin/sessions.tsx`

**Features:**
- Active session list
- User activity tracking
- Session termination
- Last activity timestamps
- IP address tracking
- User agent display

**Data Tracked:**
```typescript
UserActivity {
  id: string
  userId: string
  sessionId: string
  isActive: boolean
  lastActivityAt: DateTime
  ipAddress: string
  userAgent: string
  createdAt: DateTime
}
```

**API Endpoints:**
- `GET /api/admin/sessions` - List all sessions
- `DELETE /api/admin/sessions/:id` - Terminate session

**Priority:** 🟡 HIGH - Security feature

---

### **3.3 Audit Logs Viewer** ⭐ HIGH
**Source:** Theoshift `/admin/audit-logs/`

**Features:**
- System activity log
- User action tracking
- Filterable by user/action/date
- Searchable
- Exportable

**Log Structure:**
```typescript
AuditLog {
  id: string
  userId: string
  action: string
  resourceType: string
  resourceId: string
  changes: Json
  ipAddress: string
  createdAt: DateTime
}
```

**Actions Logged:**
- User login/logout
- Settings changes
- User creation/deletion
- Configuration updates
- System operations
- Data modifications

**Priority:** 🟡 HIGH - Compliance requirement

---

## 📊 Phase 4: System Operations (Week 4)

### **4.1 Health Monitor** ⭐ MEDIUM
**Source:** Theoshift `/admin/health/`

**Metrics:**
- Database connection status
- API response times
- Memory usage
- CPU usage
- Disk space
- Service status
- Bot health

**Implementation:**
```typescript
HealthMetrics {
  database: { status: 'healthy' | 'degraded' | 'down', latency: number }
  api: { status: 'healthy' | 'degraded' | 'down', avgResponseTime: number }
  memory: { used: number, total: number, percentage: number }
  cpu: { usage: number }
  disk: { used: number, total: number, percentage: number }
  bot: { status: 'running' | 'stopped' | 'error', lastHeartbeat: DateTime }
}
```

**API Endpoints:**
- `GET /api/admin/health` - Get current health metrics
- `GET /api/admin/health/history` - Get historical data

**Priority:** 🟢 MEDIUM - Operations tool

---

### **4.2 API Status Dashboard** ⭐ MEDIUM
**Source:** Theoshift `/admin/api-status/`

**Features:**
- Endpoint health monitoring
- Response time tracking
- Error rate monitoring
- Uptime statistics
- Service dependencies

**Monitored Endpoints:**
- `/api/auth/*`
- `/api/bot/*`
- `/api/users/*`
- `/api/admin/*`
- External APIs (Alpaca, etc.)

**Priority:** 🟢 MEDIUM - Monitoring tool

---

### **4.3 System Operations** ⭐ MEDIUM
**Source:** Theoshift `/admin/system-ops/`

**Operations:**
- Database backup
- Database restore
- Cache clearing
- Log rotation
- Index rebuilding
- Data cleanup

**Safety Features:**
- Confirmation dialogs
- Backup before destructive operations
- Operation logging
- Rollback capability

**Priority:** 🟢 MEDIUM - Maintenance tool

---

## 📊 Phase 5: Advanced Features (Future)

### **5.1 Email Templates** ⭐ LOW
**Source:** Theoshift email config (placeholder)

**Features:**
- Template editor
- Variable substitution
- Preview functionality
- Template versioning
- Multiple templates

**Templates:**
- Welcome email
- Trade alert
- Daily summary
- Weekly report
- Error notification
- Password reset

**Priority:** 🔵 LOW - Enhancement

---

### **5.2 Import/Export System** ⭐ LOW
**Source:** LDC Tools `/admin`

**Features:**
- CSV import with preview
- Excel export (multiple sheets)
- Data validation
- Bulk operations
- Error handling

**Use Cases:**
- User bulk import
- Trade data export
- Configuration backup
- Data migration

**Priority:** 🔵 LOW - Utility feature

---

### **5.3 User Activity Analytics** ⭐ LOW

**Features:**
- Usage statistics
- Feature adoption tracking
- Performance insights
- User behavior analysis
- Engagement metrics

**Priority:** 🔵 LOW - Analytics feature

---

## 🗂️ Database Models Required

### **Already Created:**
- ✅ `User` - User accounts with username support
- ✅ `Session` - User sessions
- ✅ `PlatformSettings` - Key-value configuration
- ✅ `ReleaseNote` - Version tracking
- ✅ `AuditLog` - System activity (in schema)

### **Need to Create:**
- ⏳ `UserActivity` - Session tracking
- ⏳ `SystemHealth` - Health metrics
- ⏳ `ApiEndpoint` - API monitoring
- ⏳ `EmailTemplate` - Email templates

---

## 🎨 UI Component Library Needed

### **Reusable Components:**
1. **StatCard** - Dashboard statistics
2. **ModuleCard** - Admin module grid items
3. **StatusBadge** - Status indicators
4. **LoadingSpinner** - Loading states
5. **SuccessMessage** - Success feedback
6. **ErrorMessage** - Error feedback
7. **ConfirmDialog** - Confirmation modals
8. **DataTable** - Sortable/filterable tables
9. **MarkdownEditor** - Markdown input
10. **MarkdownRenderer** - Markdown display
11. **Banner** - Notification banner
12. **TabPanel** - Tab-based interface

---

## 📋 Implementation Checklist

### **Week 2 (Current):**
- [ ] Build Settings page with email configuration
- [ ] Implement release notes system with banner
- [ ] Restructure navigation (Admin vs Platform)
- [ ] Create reusable UI components
- [ ] Add UserActivity model for sessions

### **Week 3:**
- [ ] Enhance admin dashboard with statistics
- [ ] Build session management page
- [ ] Build audit logs viewer
- [ ] Add filtering and search
- [ ] Create admin layout component

### **Week 4:**
- [ ] Build health monitor dashboard
- [ ] Build API status dashboard
- [ ] Build system operations page
- [ ] Add confirmation dialogs
- [ ] Implement backup/restore

### **Future:**
- [ ] Build email template editor
- [ ] Implement import/export system
- [ ] Add user activity analytics
- [ ] Create reporting system
- [ ] Add advanced monitoring

---

## 🔧 Technical Patterns to Use

### **1. Authentication Guard:**
```typescript
export const getServerSideProps: GetServerSideProps = async (context) => {
  const session = await getServerSession(context.req, context.res, authOptions)
  if (!session || session.user?.role !== 'ADMIN') {
    return { redirect: { destination: '/login', permanent: false } }
  }
  return { props: {} }
}
```

### **2. API Route Pattern:**
```typescript
export async function GET(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  
  const payload = await verifyToken(token)
  if (!payload || payload.role !== 'ADMIN') {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }
  
  const data = await fetchData()
  return NextResponse.json({ success: true, data })
}
```

### **3. State Management:**
```typescript
const [data, setData] = useState(initialData)
const [loading, setLoading] = useState(true)
const [saving, setSaving] = useState(false)
const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')

useEffect(() => {
  loadData()
}, [])
```

### **4. Error Handling:**
```typescript
try {
  const response = await fetch('/api/endpoint')
  const data = await response.json()
  if (data.success) {
    setStatus('success')
    setTimeout(() => setStatus('idle'), 3000)
  } else {
    throw new Error(data.error)
  }
} catch (error) {
  console.error('Operation failed:', error)
  setStatus('error')
  setTimeout(() => setStatus('idle'), 3000)
}
```

---

## 📊 Success Metrics

### **Week 2 Goals:**
- ✅ Settings page functional with email config
- ✅ Release notes system with banner working
- ✅ Navigation clearly separated
- ✅ Test email functionality working

### **Week 3 Goals:**
- ✅ Admin dashboard shows real statistics
- ✅ Session management operational
- ✅ Audit logs viewable and searchable

### **Week 4 Goals:**
- ✅ Health monitor showing real metrics
- ✅ API status dashboard operational
- ✅ System operations safe and functional

---

## 🎯 Next Actions

1. **Review this roadmap** with user
2. **Prioritize features** based on immediate needs
3. **Start with Settings page** (Week 2 Priority 1)
4. **Build Release Notes system** (Week 2 Priority 2)
5. **Restructure Navigation** (Week 2 Priority 3)
6. **Create UI component library** (Ongoing)
7. **Build admin dashboard** (Week 3)
8. **Implement monitoring** (Week 4)

---

**Status:** Ready for Implementation  
**Next Step:** User approval and prioritization
