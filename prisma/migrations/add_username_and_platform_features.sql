-- Add username field to users table
ALTER TABLE users ADD COLUMN username VARCHAR(255) UNIQUE;

-- Create platform_settings table
CREATE TABLE platform_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    updated_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create release_notes table
CREATE TABLE release_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    changes JSONB NOT NULL,
    release_date TIMESTAMP NOT NULL,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    is_dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    created_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_release_notes_version ON release_notes(version);
CREATE INDEX idx_release_notes_release_date ON release_notes(release_date);

-- Insert default QuantAdmin user
INSERT INTO users (id, username, email, password_hash, full_name, role, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'quantadmin',
    'admin@quantshift.local',
    '$2a$10$YourHashedPasswordHere', -- Will be replaced by seed script
    'QuantShift Administrator',
    'ADMIN',
    TRUE,
    NOW(),
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Update existing user to Cory Allen
UPDATE users 
SET full_name = 'Cory Allen', username = 'coryallen'
WHERE email = 'corya1992@gmail.com';

-- Insert default platform settings
INSERT INTO platform_settings (key, value, description, category, created_at, updated_at) VALUES
('smtp_host', '', 'SMTP server hostname', 'EMAIL', NOW(), NOW()),
('smtp_port', '587', 'SMTP server port', 'EMAIL', NOW(), NOW()),
('smtp_username', '', 'SMTP username', 'EMAIL', NOW(), NOW()),
('smtp_password', '', 'SMTP password (encrypted)', 'EMAIL', NOW(), NOW()),
('smtp_from_email', '', 'From email address', 'EMAIL', NOW(), NOW()),
('smtp_from_name', 'QuantShift Platform', 'From name', 'EMAIL', NOW(), NOW()),
('platform_name', 'QuantShift', 'Platform name', 'GENERAL', NOW(), NOW()),
('platform_version', '1.0.0', 'Current platform version', 'GENERAL', NOW(), NOW()),
('enable_notifications', 'true', 'Enable email notifications', 'NOTIFICATIONS', NOW(), NOW()),
('enable_trade_alerts', 'true', 'Enable trade alert emails', 'NOTIFICATIONS', NOW(), NOW())
ON CONFLICT (key) DO NOTHING;

-- Insert initial release note
INSERT INTO release_notes (version, title, description, changes, release_date, is_published, created_at, updated_at) VALUES
(
    '1.0.0',
    'QuantShift Platform Launch',
    'Initial release of the QuantShift quantum trading intelligence platform',
    '[
        {"type": "feature", "description": "User authentication and authorization system"},
        {"type": "feature", "description": "Trading bot configuration and monitoring"},
        {"type": "feature", "description": "Real-time trade and position tracking"},
        {"type": "feature", "description": "Performance analytics dashboard"},
        {"type": "feature", "description": "Email notification system"},
        {"type": "feature", "description": "Admin control center"},
        {"type": "feature", "description": "Release notes and version tracking"}
    ]'::jsonb,
    NOW(),
    TRUE,
    NOW(),
    NOW()
) ON CONFLICT (version) DO NOTHING;
