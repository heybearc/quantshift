# QuantShift Development Roadmap

**Last Updated:** 2026-01-25  
**Status:** Active Development  
**Current Focus:** Infrastructure standardization and blue-green deployment preparation

---

## Overview

QuantShift is a quantum trading intelligence platform combining algorithmic trading bots with a Next.js admin dashboard. This roadmap tracks all development priorities, infrastructure improvements, and feature enhancements.

**Key Principles:**
- Container-first development (D-QS-001)
- Single container deployment (D-QS-002) - **Migrating to blue-green**
- Agentic AI-driven development with Windsurf/Claude
- Industry-standard practices and patterns

---

## Current State (2026-01-25)

### ✅ What's Working

**Infrastructure:**
- LXC container: qs-dashboard (10.92.3.29)
- PostgreSQL database
- Redis state management
- PM2 process management (quantshift-admin)
- Container-first development workflow

**Application:**
- Next.js 14 admin platform (root `/app/` directory)
- Route groups: `(auth)`, `(protected)`
- Authentication system (username or email login)
- User management (CRUD operations)
- Session management
- Audit logs
- Settings page (email/SMTP configuration)
- Help documentation system
- Database-driven release notes (Prisma)
- Version banner system

**Trading Bots:**
- Python trading bots in `apps/bots/`
- MA Crossover strategy (5/20)
- Alpaca paper trading integration
- Risk management (1% per trade, ATR-based stops)
- Redis state tracking

**Development:**
- Cloudy-Work submodule integrated
- Shared workflows and context
- Container-first development model
- Git-tracked configuration

### 🔄 In Progress

**Repository Cleanup:**
- ✅ Archived zombie apps (apps/admin-web, apps/dashboard)
- ✅ Archived outdated documentation
- ✅ Quarantined uncertain documentation for review
- ⏳ Consolidating roadmaps and planning documents

**Infrastructure Planning:**
- ⏳ Release notes standardization (markdown files)
- ⏳ Blue-green deployment preparation
- ⏳ /bump workflow compatibility analysis

---

## Strategic Initiatives

### 1. Infrastructure Standardization (Q1 2026)

**Priority:** 🔴 Critical

**Goal:** Standardize QuantShift infrastructure to match TheoShift and LDC Tools patterns

#### 1.1 Release Notes Standardization
**Status:** Planning  
**Timeline:** Week of Jan 27, 2026

**Tasks:**
- [ ] Migrate from database-driven to markdown file-based release notes
- [ ] Create `/release-notes/` directory structure
- [ ] Convert existing database releases to markdown files
- [ ] Create `lib/release-notes.ts` parsing functions
- [ ] Update version banner to parse markdown files
- [ ] Create release notes page using markdown files
- [ ] Remove database dependency (optional - keep for history)

**Why:** 
- Industry standard for SaaS applications
- Atomic deployment with code (no timing issues)
- Version controlled with code
- Blue-green deployment compatible

**Reference:** `RELEASE-NOTES-STANDARDIZATION-REVISED.md`

#### 1.2 Blue-Green Deployment Migration
**Status:** Planning  
**Timeline:** Q1 2026 (after release notes standardization)

**Tasks:**
- [ ] Provision second LXC container (qs-standby or similar)
- [ ] Configure HAProxy routing for QuantShift
- [ ] Set up shared PostgreSQL database
- [ ] Test blue-green deployment workflow
- [ ] Update deployment scripts for blue-green
- [ ] Document rollback procedures
- [ ] Test MCP server integration

**Why:**
- Zero-downtime deployments
- Safe testing on STANDBY before traffic switch
- Matches TheoShift and LDC Tools deployment model
- Enables use of generic /bump workflow

**Reference:** `BUMP-WORKFLOW-COMPATIBILITY-ANALYSIS.md`

#### 1.3 Generic /bump Workflow Integration
**Status:** Planning  
**Timeline:** After blue-green deployment

**Tasks:**
- [ ] Test generic /bump workflow with QuantShift
- [ ] Verify MCP server compatibility
- [ ] Update deployment scripts
- [ ] Test release workflow end-to-end
- [ ] Document QuantShift-specific steps (if any)

**Why:**
- Consistent release process across all apps
- Automated deployment via MCP server
- Help documentation analysis built-in
- Test enforcement before release

**Reference:** `.cloudy-work/.windsurf/workflows/bump.md`

---

### 2. Admin Platform Enhancements (Q1-Q2 2026)

**Priority:** 🟡 High

**Goal:** Complete admin platform with trading integration and monitoring

#### 2.1 Enhanced Dashboard & Monitoring
**Status:** Planned  
**Timeline:** Weeks 3-4, Jan 2026

**Tasks:**
- [ ] Statistics cards (users, trades, positions, sessions)
- [ ] Health monitor dashboard
- [ ] API status monitoring
- [ ] System operations page
- [ ] Real-time metrics display

#### 2.2 Trading Pages Integration
**Status:** Planned  
**Timeline:** Feb 2026

**Tasks:**
- [ ] Connect to admin-api backend (or create if needed)
- [ ] Build functional Trades page
- [ ] Build functional Positions page
- [ ] Build functional Performance page
- [ ] Bot monitoring dashboard
- [ ] Real-time bot status display

#### 2.3 Advanced Admin Features
**Status:** Future  
**Timeline:** Q2 2026

**Tasks:**
- [ ] Email templates management
- [ ] Import/export system
- [ ] Analytics dashboard
- [ ] User activity tracking
- [ ] System health alerts

**Reference:** `_quarantine/review-2026-01-25/ADMIN_PLATFORM_PROPOSAL.md` (archived)

---

### 3. Trading Bot Enhancements (Q1-Q2 2026)

**Priority:** 🟢 Medium

**Goal:** Enhance trading bot capabilities and performance

#### 3.1 Paper Trading Validation
**Status:** Ongoing  
**Timeline:** 30 days (started Dec 26, 2025)

**Tasks:**
- [x] Deploy bot to paper trading
- [ ] Monitor daily performance
- [ ] Track trades and compare to backtest
- [ ] Calculate performance metrics
- [ ] Prepare go/no-go decision for live trading

**Success Criteria:**
- Minimum 10 trades in 30 days
- Win rate ≥ 45%
- Max drawdown < 20%
- No critical bugs

#### 3.2 Advanced Risk Management
**Status:** Planned  
**Timeline:** After paper trading validation

**Tasks:**
- [ ] Portfolio heat tracking (max 10% total risk)
- [ ] Kelly Criterion position sizing
- [ ] Dynamic stop losses (ATR-based trailing)
- [ ] Maximum drawdown circuit breakers
- [ ] Daily loss limits
- [ ] Position correlation monitoring

#### 3.3 Multi-Strategy Framework
**Status:** Future  
**Timeline:** Q2 2026

**Strategies to Add:**
- [ ] RSI Mean Reversion
- [ ] Breakout Trading
- [ ] Bollinger Band Strategy
- [ ] Volume Profile Strategy

**Tasks:**
- [ ] Create strategy interface/base class
- [ ] Implement each strategy
- [ ] Backtest each strategy independently
- [ ] Add strategy allocation system
- [ ] Monitor strategy correlation

**Reference:** `_quarantine/review-2026-01-25/BOT_ENHANCEMENT_ROADMAP.md` (archived)

#### 3.4 Real-Time Data Streaming
**Status:** Future  
**Timeline:** Q2 2026

**Tasks:**
- [ ] Implement Alpaca WebSocket client
- [ ] Add real-time quote processing
- [ ] Update strategy to use streaming data
- [ ] Add sub-second latency monitoring
- [ ] Implement event-driven architecture

#### 3.5 Crypto Bot Development
**Status:** Future  
**Timeline:** Q2-Q3 2026

**Tasks:**
- [ ] Set up Coinbase Advanced Trade API
- [ ] Adapt strategy for crypto markets (24/7, higher volatility)
- [ ] Implement crypto-specific risk parameters
- [ ] Add funding rate monitoring
- [ ] Test with paper trading
- [ ] Deploy to production

---

### 4. Documentation & Knowledge Management (Ongoing)

**Priority:** 🟢 Medium

**Goal:** Maintain clear, up-to-date documentation

#### 4.1 Documentation Cleanup
**Status:** In Progress  
**Timeline:** Jan 2026

**Tasks:**
- [x] Archive zombie app directories
- [x] Archive outdated documentation
- [x] Quarantine uncertain documentation
- [x] Create archive and quarantine READMEs
- [ ] Review quarantined documentation (by Feb 1, 2026)
- [ ] Consolidate roadmaps into single source of truth
- [ ] Update DECISIONS.md with new decisions

#### 4.2 Help Documentation
**Status:** Ongoing  
**Timeline:** With each feature release

**Tasks:**
- [ ] Create help pages for new features
- [ ] Update help index
- [ ] Add screenshots and examples
- [ ] Keep help docs in sync with features

---

## Known Issues

**None currently blocking development.**

**Resolved:**
- ✅ Zombie app directories (archived 2026-01-25)
- ✅ Deployment scripts pointing to old structure (fixed 2026-01-25)
- ✅ Container had 710MB zombie directory (cleaned 2026-01-25)

---

## Decisions Log

See `DECISIONS.md` for repo-local decisions.  
See `.cloudy-work/_cloudy-ops/context/DECISIONS.md` for shared decisions.

**Recent Decisions:**
- **D-QS-003:** Standardize on markdown file-based release notes (2026-01-25)
- **D-QS-004:** Migrate to blue-green deployment (planned Q1 2026)

---

## Success Metrics

### Performance Targets (Trading Bots):
- **Sharpe Ratio:** > 2.0 (industry: 1.5-2.0)
- **Max Drawdown:** < 15% (industry: 15-20%)
- **Win Rate:** > 55% (industry: 50-55%)
- **Profit Factor:** > 2.0 (industry: 1.5-2.0)
- **Annual Return:** > 30% (industry: 15-25%)

### Operational Targets:
- **Uptime:** > 99.9%
- **Latency:** < 100ms (order execution)
- **Slippage:** < 0.1%
- **Deployment Time:** < 5 minutes (with blue-green)

### Development Targets:
- **Release Frequency:** Weekly (after blue-green)
- **Test Coverage:** > 80%
- **Documentation:** Up-to-date with features
- **Code Review:** All changes reviewed

---

## Timeline Summary

| Initiative | Priority | Timeline | Status |
|-----------|----------|----------|--------|
| Release notes standardization | 🔴 Critical | Week of Jan 27 | Planning |
| Blue-green deployment | 🔴 Critical | Q1 2026 | Planning |
| /bump workflow integration | 🔴 Critical | After blue-green | Planning |
| Enhanced dashboard | 🟡 High | Weeks 3-4 Jan | Planned |
| Trading pages integration | 🟡 High | Feb 2026 | Planned |
| Paper trading validation | 🟡 High | 30 days | In Progress |
| Advanced risk management | 🟢 Medium | After paper trading | Planned |
| Multi-strategy framework | 🟢 Medium | Q2 2026 | Future |
| Real-time data streaming | 🟢 Medium | Q2 2026 | Future |
| Crypto bot development | 🟢 Medium | Q2-Q3 2026 | Future |

---

## Next Immediate Steps

### This Week (Jan 25-31, 2026):
1. ✅ Consolidate roadmaps and planning documents
2. [ ] Review quarantined documentation
3. [ ] Plan release notes standardization implementation
4. [ ] Update DECISIONS.md with new decisions
5. [ ] Archive old roadmap documents

### Next Week (Feb 1-7, 2026):
1. [ ] Implement markdown file-based release notes
2. [ ] Test release notes parsing and display
3. [ ] Update version banner component
4. [ ] Plan blue-green deployment infrastructure

### Next Month (Feb 2026):
1. [ ] Complete release notes migration
2. [ ] Provision second LXC container
3. [ ] Configure HAProxy for QuantShift
4. [ ] Test blue-green deployment workflow
5. [ ] Build trading pages integration

---

## References

**Analysis Documents:**
- `RELEASE-NOTES-STANDARDIZATION-REVISED.md` - Release notes approach
- `BUMP-WORKFLOW-COMPATIBILITY-ANALYSIS.md` - /bump workflow analysis
- `QUANTSHIFT-RELEASE-SYSTEM.md` - Current release system documentation
- `CLEANUP-COMPLETE-2026-01-25.md` - Repository cleanup summary

**Archived Roadmaps:**
- `_quarantine/review-2026-01-25/IMPLEMENTATION_ROADMAP.md` - Original implementation roadmap
- `_quarantine/review-2026-01-25/BOT_ENHANCEMENT_ROADMAP.md` - Bot enhancement plans
- `_quarantine/review-2026-01-25/ROADMAP_MANAGEMENT.md` - Roadmap management practices

**Configuration:**
- `DECISIONS.md` - Repo-local decisions
- `TASK-STATE.md` - Current task tracking
- `.cloudy-work/_cloudy-ops/context/` - Shared context and decisions

---

**Status:** Active  
**Owner:** Cory Allen  
**Next Review:** Weekly (every Friday)
