# Changelog

All notable changes to the QuantShift Trading Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Comprehensive admin functionality analysis from Theoshift and LDC Tools
- Admin features roadmap with phased implementation plan
- Roadmap management best practices document
- Single source of truth structure for all roadmap tracking

### In Progress
- Settings page with email/SMTP configuration
- Release notes system with banner notification
- Navigation restructure (Admin Control Center vs Trading Platform)
- Session management page
- Audit logs viewer

---

## [0.2.0] - 2025-12-27

### Added
- Username-based authentication (login with username OR email)
- Default admin accounts (quantadmin, coryallen)
- User CRUD operations via API
- Platform settings infrastructure (database model)
- Release notes system infrastructure (database model)
- Audit log model in Prisma schema
- Database migration for username field and new tables
- Seed script for default users and platform settings

### Changed
- Login form now accepts username or email
- User model includes username field (unique, optional)
- Authentication API supports both username and email lookup

### Fixed
- User authentication flow to support multiple login methods
- Prisma schema field naming (passwordHash vs password)

---

## [0.1.0] - 2025-12-26

### Added
- Initial admin web application setup
- Next.js 14 with TypeScript
- Prisma ORM with PostgreSQL
- JWT-based authentication
- Basic user management
- Admin dashboard layout
- Login page with modern dark theme
- User management page (placeholder)
- Dashboard page (placeholder)

### Infrastructure
- PostgreSQL database on Container 131 (10.92.3.21)
- Admin web app on Container 132 (10.92.3.22)
- PM2 process management
- Environment-based configuration

---

## [0.0.1] - 2025-12-25

### Added
- Project initialization
- Repository structure
- Basic documentation
- Development environment setup

---

## Version History

- **0.2.0** - Admin platform authentication and infrastructure (Dec 27, 2025)
- **0.1.0** - Initial admin web application (Dec 26, 2025)
- **0.0.1** - Project initialization (Dec 25, 2025)

---

## Upcoming Releases

### [0.3.0] - Planned for Week 2 (Dec 30-Jan 3)
- Settings page with email configuration
- Release notes system with banner
- Navigation restructure
- Session management
- Audit logs viewer

### [0.4.0] - Planned for Week 3 (Jan 6-10)
- Enhanced admin dashboard with statistics
- Health monitor dashboard
- API status monitoring
- System operations page

### [0.5.0] - Planned for Week 4 (Jan 13-17)
- Trading pages integration
- Bot monitoring dashboard
- /bump workflow integration
- Performance analytics

---

## Notes

- All dates are in YYYY-MM-DD format
- Version numbers follow Semantic Versioning (MAJOR.MINOR.PATCH)
- Breaking changes increment MAJOR version
- New features increment MINOR version
- Bug fixes increment PATCH version
