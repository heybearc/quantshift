interface RateLimitEntry {
  count: number;
  resetAt: number;
}

class RateLimiter {
  private storage: Map<string, RateLimitEntry> = new Map();
  private cleanupInterval: NodeJS.Timeout;

  constructor() {
    // Clean up expired entries every 5 minutes
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 5 * 60 * 1000);
  }

  private cleanup() {
    const now = Date.now();
    for (const [key, entry] of this.storage.entries()) {
      if (entry.resetAt < now) {
        this.storage.delete(key);
      }
    }
  }

  async checkLimit(
    identifier: string,
    maxAttempts: number,
    windowMs: number
  ): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
    const now = Date.now();
    const entry = this.storage.get(identifier);

    if (!entry || entry.resetAt < now) {
      // New window or expired
      const resetAt = now + windowMs;
      this.storage.set(identifier, { count: 1, resetAt });
      return { allowed: true, remaining: maxAttempts - 1, resetAt };
    }

    if (entry.count >= maxAttempts) {
      // Limit exceeded
      return { allowed: false, remaining: 0, resetAt: entry.resetAt };
    }

    // Increment count
    entry.count++;
    this.storage.set(identifier, entry);
    return { allowed: true, remaining: maxAttempts - entry.count, resetAt: entry.resetAt };
  }

  async reset(identifier: string) {
    this.storage.delete(identifier);
  }

  destroy() {
    clearInterval(this.cleanupInterval);
    this.storage.clear();
  }
}

// Singleton instance
export const rateLimiter = new RateLimiter();

// Rate limit configurations
export const RATE_LIMITS = {
  REGISTRATION: {
    PER_IP: { maxAttempts: 3, windowMs: 60 * 60 * 1000 }, // 3 per hour per IP
    PER_EMAIL: { maxAttempts: 5, windowMs: 24 * 60 * 60 * 1000 }, // 5 per day per email
  },
  LOGIN: {
    PER_IP: { maxAttempts: 10, windowMs: 15 * 60 * 1000 }, // 10 per 15 minutes per IP
    PER_EMAIL: { maxAttempts: 5, windowMs: 15 * 60 * 1000 }, // 5 per 15 minutes per email
  },
  PASSWORD_RESET: {
    PER_IP: { maxAttempts: 3, windowMs: 60 * 60 * 1000 }, // 3 per hour per IP
    PER_EMAIL: { maxAttempts: 3, windowMs: 60 * 60 * 1000 }, // 3 per hour per email
  },
  USERNAME_CHECK: {
    PER_IP: { maxAttempts: 30, windowMs: 60 * 1000 }, // 30 per minute per IP
  },
};

// Helper function to get client IP from request
export function getClientIp(request: Request): string {
  const forwarded = request.headers.get('x-forwarded-for');
  const realIp = request.headers.get('x-real-ip');
  
  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }
  
  if (realIp) {
    return realIp;
  }
  
  return 'unknown';
}
