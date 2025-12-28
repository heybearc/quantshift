-- Fix existing admin accounts to bypass new security requirements
UPDATE users 
SET 
  email_verified = true,
  requires_approval = false,
  is_active = true,
  email_verification_token = NULL,
  email_verification_expiry = NULL,
  failed_login_attempts = 0,
  account_locked_until = NULL
WHERE role = 'ADMIN';
