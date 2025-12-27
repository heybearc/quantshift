# Changelog

All notable changes to the QuantShift Trading Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Enhanced admin dashboard with statistics cards
- Health monitor dashboard
- API status monitoring
- System operations page

---

## [0.2.0] - 2025-12-27 - **Week 2 Complete**

### Added - Admin Platform Core Features
- **Settings Page**: Email/SMTP configuration with Gmail App Password and Custom SMTP support
- **Release Notes System**: Database-stored releases with banner notifications on login
- **Session Management**: Real-time session monitoring with termination capability
- **Audit Logs Viewer**: Comprehensive audit log display with search and filtering
- **Navigation Restructure**: Clear separation between Trading Platform (green) and Admin Control Center (blue)
- Username-based authentication (login with username OR email)
- Default admin accounts (quantadmin, coryallen)
- User CRUD operations via API
- Platform settings infrastructure (database model)
- Release notes system infrastructure (database model)
- Audit log model in Prisma schema
- Database migration for username field and new tables
- Seed script for default users and platform settings
- nodemailer dependency for email functionality

### Changed
- Navigation now has two distinct sections with visual dividers and color coding
- Login form now accepts username or email
- User model includes username field (unique, optional)
- User model includes lastSeenReleaseVersion for banner tracking
- Authentication API supports both username and email lookup

### Fixed
- User authentication flow to support multiple login methods
- Prisma schema field naming (passwordHash vs password)

### API Endpoints Added
- `GET/POST /api/admin/settings/email` - Email configuration management
- `POST /api/admin/settings/email/test` - Test email functionality
- `GET /api/release-notes` - Public release notes
- `GET /api/release-notes/latest` - Check for new releases
- `POST /api/release-notes/dismiss` - Dismiss banner notification
- `GET/POST /api/admin/release-notes` - Admin release management
- `PUT/DELETE /api/admin/release-notes/:id` - Update/delete releases
- `POST /api/admin/release-notes/:id/publish` - Toggle publish status
- `GET /api/admin/sessions` - View all user sessions
- `DELETE /api/admin/sessions/:id` - Terminate session
- `GET /api/admin/audit-logs` - View audit logs (last 500)

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
