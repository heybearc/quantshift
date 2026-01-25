import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { 
  verifyPassword, 
  createAccessToken, 
  createRefreshToken, 
  setAuthCookies,
  storeRefreshToken 
} from '@/lib/auth';
import { rateLimiter, RATE_LIMITS, getClientIp } from '@/lib/rate-limiter';

export async function POST(request: NextRequest) {
  try {
    const clientIp = getClientIp(request);
    const { email, password } = await request.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Username/email and password are required' },
        { status: 400 }
      );
    }

    // Rate limiting - IP based
    const ipLimit = await rateLimiter.checkLimit(
      `login:ip:${clientIp}`,
      RATE_LIMITS.LOGIN.PER_IP.maxAttempts,
      RATE_LIMITS.LOGIN.PER_IP.windowMs
    );

    if (!ipLimit.allowed) {
      const resetIn = Math.ceil((ipLimit.resetAt - Date.now()) / 1000 / 60);
      return NextResponse.json(
        { error: `Too many login attempts. Please try again in ${resetIn} minutes.` },
        { status: 429 }
      );
    }

    // Find user by email OR username
    const user = await prisma.user.findFirst({
      where: {
        OR: [
          { email: email.toLowerCase() },
          { username: email.toLowerCase() }, // Allow username in email field
        ],
      },
    });

    if (!user) {
      return NextResponse.json(
        { error: 'Invalid username/email or password' },
        { status: 401 }
      );
    }

    // Rate limiting - Email based
    const emailLimit = await rateLimiter.checkLimit(
      `login:email:${user.email}`,
      RATE_LIMITS.LOGIN.PER_EMAIL.maxAttempts,
      RATE_LIMITS.LOGIN.PER_EMAIL.windowMs
    );

    if (!emailLimit.allowed) {
      const resetIn = Math.ceil((emailLimit.resetAt - Date.now()) / 1000 / 60);
      return NextResponse.json(
        { error: `Too many login attempts for this account. Please try again in ${resetIn} minutes.` },
        { status: 429 }
      );
    }

    // Check if account is locked
    if (user.accountLockedUntil && user.accountLockedUntil > new Date()) {
      const lockMinutes = Math.ceil((user.accountLockedUntil.getTime() - Date.now()) / 1000 / 60);
      return NextResponse.json(
        { error: `Account is temporarily locked due to multiple failed login attempts. Please try again in ${lockMinutes} minutes.` },
        { status: 423 }
      );
    }

    // Check if email is verified
    if (!user.emailVerified) {
      return NextResponse.json(
        { error: 'Please verify your email address before logging in. Check your inbox for the verification link.' },
        { status: 403 }
      );
    }

    // Check if account requires approval
    if (user.requiresApproval) {
      return NextResponse.json(
        { error: 'Your account is pending administrator approval. You will receive an email once approved.' },
        { status: 403 }
      );
    }

    if (!user.isActive) {
      return NextResponse.json(
        { error: 'Account is inactive. Please contact support.' },
        { status: 401 }
      );
    }

    // Verify password
    const isValid = await verifyPassword(password, user.passwordHash);
    if (!isValid) {
      // Increment failed login attempts
      const newFailedAttempts = user.failedLoginAttempts + 1;
      const updateData: any = {
        failedLoginAttempts: newFailedAttempts,
      };

      // Lock account after 5 failed attempts
      if (newFailedAttempts >= 5) {
        updateData.accountLockedUntil = new Date(Date.now() + 30 * 60 * 1000); // 30 minutes
      }

      await prisma.user.update({
        where: { id: user.id },
        data: updateData,
      });

      // Log failed login attempt
      await prisma.auditLog.create({
        data: {
          userId: user.id,
          action: 'LOGIN_FAILED',
          resourceType: 'USER',
          resourceId: user.id,
          ipAddress: clientIp,
          changes: {
            failedAttempts: newFailedAttempts,
            locked: newFailedAttempts >= 5,
          },
        },
      });

      if (newFailedAttempts >= 5) {
        return NextResponse.json(
          { error: 'Account locked due to multiple failed login attempts. Please try again in 30 minutes.' },
          { status: 423 }
        );
      }

      return NextResponse.json(
        { error: 'Invalid username/email or password' },
        { status: 401 }
      );
    }

    // Reset failed login attempts and update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { 
        lastLogin: new Date(),
        failedLoginAttempts: 0,
        accountLockedUntil: null,
      },
    });

    // Reset rate limits on successful login
    await rateLimiter.reset(`login:ip:${clientIp}`);
    await rateLimiter.reset(`login:email:${user.email}`);

    // Log successful login
    await prisma.auditLog.create({
      data: {
        userId: user.id,
        action: 'LOGIN_SUCCESS',
        resourceType: 'USER',
        resourceId: user.id,
        ipAddress: clientIp,
      },
    });

    // Create tokens
    const accessToken = createAccessToken(user.id, user.email, user.role);
    const refreshToken = createRefreshToken(user.id);

    // Store refresh token
    await storeRefreshToken(user.id, refreshToken);

    // Set cookies
    await setAuthCookies(accessToken, refreshToken);

    // Return user data
    return NextResponse.json({
      user: {
        id: user.id,
        email: user.email,
        full_name: user.fullName,
        role: user.role,
        is_active: user.isActive,
        created_at: user.createdAt.toISOString(),
        last_login: user.lastLogin?.toISOString() || null,
      },
      token_type: 'bearer',
    });
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
