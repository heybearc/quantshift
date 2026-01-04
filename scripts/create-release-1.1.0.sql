-- Create release note for version 1.1.0
INSERT INTO "ReleaseNote" (
  id,
  version,
  title,
  description,
  type,
  "releaseDate",
  "isPublished",
  "createdBy",
  changes,
  "createdAt",
  "updatedAt"
) VALUES (
  gen_random_uuid(),
  '1.1.0',
  'Admin Platform - Weeks 1-4 Complete',
  'Comprehensive admin platform with user management, security monitoring, system health tracking, and configuration tools.',
  'minor',
  '2026-01-03T00:00:00.000Z',
  true,
  'System',
  '[
    {
      "type": "added",
      "items": [
        "User Management with CRUD operations and role-based access control",
        "Session Management with real-time monitoring and termination capabilities",
        "Audit Logs with filtering, search, and export functionality",
        "Health Monitor dashboard with system metrics and auto-refresh",
        "API Status monitoring with response time tracking",
        "General Settings for platform configuration and maintenance mode",
        "Email Configuration with Gmail and SMTP support",
        "Help Documentation system with searchable guides",
        "Version management workflow and automated release banners"
      ]
    },
    {
      "type": "changed",
      "items": [
        "Enhanced authentication with credentials on all API calls",
        "Improved UI consistency across all admin pages",
        "Updated navigation with Help link"
      ]
    },
    {
      "type": "fixed",
      "items": [
        "Authentication issues in Release Notes management",
        "Email configuration input text visibility",
        "Session and audit log API authentication"
      ]
    }
  ]'::jsonb,
  NOW(),
  NOW()
);
