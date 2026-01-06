export interface PasswordValidationResult {
  isValid: boolean;
  errors: string[];
  strength: 'weak' | 'medium' | 'strong';
}

export function validatePassword(password: string): PasswordValidationResult {
  const errors: string[] = [];
  let strength: 'weak' | 'medium' | 'strong' = 'weak';

  // Minimum length check
  if (password.length < 12) {
    errors.push('Password must be at least 12 characters long');
  }

  // Maximum length check (prevent DoS)
  if (password.length > 128) {
    errors.push('Password must not exceed 128 characters');
  }

  // Uppercase check
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  // Lowercase check
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  // Number check
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  // Special character check
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }

  // Common password patterns
  const commonPatterns = [
    /^password/i,
    /^123456/,
    /^qwerty/i,
    /^admin/i,
    /^letmein/i,
    /^welcome/i,
    /^monkey/i,
    /^dragon/i,
  ];

  for (const pattern of commonPatterns) {
    if (pattern.test(password)) {
      errors.push('Password is too common or predictable');
      break;
    }
  }

  // Sequential characters check
  if (/(.)\1{2,}/.test(password)) {
    errors.push('Password should not contain repeated characters (e.g., "aaa", "111")');
  }

  // Calculate strength
  if (errors.length === 0) {
    let strengthScore = 0;
    
    if (password.length >= 16) strengthScore++;
    if (password.length >= 20) strengthScore++;
    if (/[A-Z].*[A-Z]/.test(password)) strengthScore++; // Multiple uppercase
    if (/[a-z].*[a-z]/.test(password)) strengthScore++; // Multiple lowercase
    if (/[0-9].*[0-9]/.test(password)) strengthScore++; // Multiple numbers
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?].*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) strengthScore++; // Multiple special chars

    if (strengthScore >= 4) {
      strength = 'strong';
    } else if (strengthScore >= 2) {
      strength = 'medium';
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    strength,
  };
}

export function generatePasswordStrengthMessage(strength: 'weak' | 'medium' | 'strong'): string {
  switch (strength) {
    case 'strong':
      return '✅ Strong password';
    case 'medium':
      return '⚠️ Medium strength - consider making it longer';
    case 'weak':
      return '❌ Weak password';
  }
}
