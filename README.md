# QuantShift - Quantum Trading Intelligence Platform

**Production URL:** https://quantshift.io  
**Server:** 10.92.3.29:3001  
**Version:** 1.11.0

## 🏗️ Structure (Standard Next.js 14)
- Operates 24/7 with zero-downtime failover
- Provides real-time monitoring and analytics
- Validates strategies before live deployment

**This is NOT a monitoring-only platform** - it's a complete algorithmic trading system designed to generate consistent returns through systematic strategy execution.

## 🏛️ Architectural Principles

**Broker-Agnostic Design:**
- Strategy logic separated from broker execution
- Reusable strategies across Alpaca, Coinbase, and future brokers
- Clean abstraction layers enable easy backtesting and testing
- Single strategy implementation works for stocks, crypto, and other assets

**Core Philosophy:**
- **Strategies** = Pure logic (no broker dependencies)
- **Executors** = Broker-specific implementation (API calls, order management)
- **Backtesting** = Uses same strategy code as live trading
- **Scalability** = Add new brokers/assets without rewriting strategies

## 🏗️ Architecture

**Monorepo Structure** - Optimized for Agentic AI development (Windsurf + Claude Sonnet) on LXC containers.

### Deployment Model: Hybrid

**Trading Bots: Hot-Standby (Zero Downtime)**
- Primary: LXC 100 (10.92.3.27) - Active trading
- Standby: LXC 101 (10.92.3.28) - Automatic failover
- HA Proxy routes traffic with health checks
- Both containers run identical code

**Dashboard: Single Instance**
- Dashboard: LXC 137 (10.92.3.29) - Next.js UI
- Future: Can add LXC 138 for blue-green deployment

## 📁 Repository Structure

```
quantshift/
├── apps/
│   ├── web/                 # Next.js dashboard (port 3001)
│   │   ├── app/             # Next.js App Router
│   │   ├── components/      # React components
│   │   ├── lib/             # Utilities
│   │   └── prisma/          # Database schema
│   └── bots/
│       ├── equity/          # Alpaca equity trading bot
│       ├── crypto/          # Coinbase crypto trading bot
│       └── core/            # Shared bot utilities
├── packages/
│   └── core/                # Shared libraries (config, database, models)
├── infrastructure/
│   ├── systemd/             # Service files for bots
│   ├── pm2/                 # PM2 config for dashboard
│   ├── deployment/          # Deployment scripts
│   └── docs/                # Setup documentation
├── .github/
│   └── workflows/           # CI/CD pipelines
├── pyproject.toml           # Python workspace
├── package.json             # Node workspace
└── README.md
```

## 🚀 Development Workflow

### On LXC Containers (Agentic AI Development)

```bash
# Clone repo to container
git clone https://github.com/heybearc/quantshift.git /opt/quantshift
cd /opt/quantshift

# Develop with Windsurf/Claude directly on container
# Full monorepo context for AI
# Git history for rollback
```

## 📦 Deployment

### Bot Deployment (Hot-Standby)
```bash
# Deploy to BOTH primary and standby
./infrastructure/deployment/deploy-bots.sh

# Deploys to:
# - LXC 100 (primary)
# - LXC 101 (standby)
# HA Proxy handles automatic failover
```

### Dashboard Deployment (Single Instance)
```bash
# Deploy to dashboard only
./infrastructure/deployment/deploy-dashboard.sh

# Deploys to:
# - LXC 137 (dashboard)
# Brief downtime acceptable
```

## 🔧 Technology Stack

**Bots:**
- Python 3.11+ with type hints
- Alpaca API (equity trading)
- Coinbase Advanced API (crypto trading)
- PostgreSQL (shared state)
- Redis (caching)
- systemd (process management)

**Dashboard (apps/web/):**
- Next.js 14 with App Router
- TypeScript
- Prisma ORM
- PM2 (process management)
- Tailwind CSS
- Real-time updates

**Infrastructure:**
- LXC Containers (not Docker - avoids dev-to-prod issues)
- HA Proxy (load balancing + health checks)
- PostgreSQL (10.92.3.21)
- NPM Proxy Manager (SSL termination)

## 🌐 Domains

- `quantshift.io` - Main dashboard
- `api.quantshift.io` - Bot APIs
- `blue.quantshift.io` - Direct blue container access
- `green.quantshift.io` - Direct green container access

## 🎯 Why Monorepo?

**Optimized for Agentic AI Development:**
- ✅ Windsurf sees entire codebase context
- ✅ Seamless refactoring across packages
- ✅ Single workspace for AI understanding
- ✅ No jumping between repos

**Optimized for LXC Deployment:**
- ✅ Clone once to container
- ✅ All code in one place
- ✅ Git history for entire system
- ✅ Easy rollback across all components

**Optimized for Hot-Standby:**
- ✅ Single git pull updates everything
- ✅ Atomic deployments (all or nothing)
- ✅ Easy to sync primary ↔ standby
- ✅ Consistent versions across components

## 📝 License

MIT
