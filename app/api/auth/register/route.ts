import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import bcrypt from 'bcryptjs';
import { randomBytes } from 'crypto';
import { validatePassword } from '@/lib/password-validator';
import { rateLimiter, RATE_LIMITS, getClientIp } from '@/lib/rate-limiter';
import { sendVerificationEmail } from '@/lib/email';

export async function POST(request: NextRequest) {
  try {
    const clientIp = getClientIp(request);
    const body = await request.json();
    const { email, username, fullName, password } = body;

    // Validate input
    if (!email || !username || !fullName || !password) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Rate limiting - IP based
    const ipLimit = await rateLimiter.checkLimit(
      `register:ip:${clientIp}`,
      RATE_LIMITS.REGISTRATION.PER_IP.maxAttempts,
      RATE_LIMITS.REGISTRATION.PER_IP.windowMs
    );

    if (!ipLimit.allowed) {
      const resetIn = Math.ceil((ipLimit.resetAt - Date.now()) / 1000 / 60);
      return NextResponse.json(
        { 
          error: `Too many registration attempts. Please try again in ${resetIn} minutes.`,
          resetAt: ipLimit.resetAt
        },
        { status: 429 }
      );
    }

    // Rate limiting - Email based
    const emailLimit = await rateLimiter.checkLimit(
      `register:email:${email.toLowerCase()}`,
      RATE_LIMITS.REGISTRATION.PER_EMAIL.maxAttempts,
      RATE_LIMITS.REGISTRATION.PER_EMAIL.windowMs
    );

    if (!emailLimit.allowed) {
      const resetIn = Math.ceil((emailLimit.resetAt - Date.now()) / 1000 / 60 / 60);
      return NextResponse.json(
        { 
          error: `Too many registration attempts for this email. Please try again in ${resetIn} hours.`,
          resetAt: emailLimit.resetAt
        },
        { status: 429 }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      );
    }

    // Block disposable email domains
    const disposableDomains = [
      'tempmail.com', 'throwaway.email', '10minutemail.com', 
      'guerrillamail.com', 'mailinator.com', 'trashmail.com'
    ];
    const emailDomain = email.split('@')[1].toLowerCase();
    if (disposableDomains.includes(emailDomain)) {
      return NextResponse.json(
        { error: 'Disposable email addresses are not allowed' },
        { status: 400 }
      );
    }

    // Validate username format
    const usernameRegex = /^[a-zA-Z0-9_-]{3,20}$/;
    if (!usernameRegex.test(username)) {
      return NextResponse.json(
        { error: 'Username must be 3-20 characters and contain only letters, numbers, underscores, or hyphens' },
        { status: 400 }
      );
    }

    // Validate password strength
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
      return NextResponse.json(
        { 
          error: 'Password does not meet security requirements',
          details: passwordValidation.errors
        },
        { status: 400 }
      );
    }

    // Check if user already exists (email or username)
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [
          { email: email.toLowerCase() },
          { username: username.toLowerCase() }
        ],
      },
    });

    if (existingUser) {
      if (existingUser.email.toLowerCase() === email.toLowerCase()) {
        return NextResponse.json(
          { error: 'An account with this email already exists' },
          { status: 409 }
        );
      } else {
        return NextResponse.json(
          { error: 'This username is already taken' },
          { status: 409 }
        );
      }
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 12);

    // Generate email verification token
    const verificationToken = randomBytes(32).toString('hex');
    const verificationExpiry = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours

    // Create user with email verification required and admin approval required
    const user = await prisma.user.create({
      data: {
        email: email.toLowerCase(),
        username: username.toLowerCase(),
        fullName,
        passwordHash: hashedPassword,
        role: 'VIEWER',
        isActive: false, // Inactive until approved
        emailVerified: false,
        emailVerificationToken: verificationToken,
        emailVerificationExpiry: verificationExpiry,
        requiresApproval: true,
      },
      select: {
        id: true,
        email: true,
        username: true,
        fullName: true,
        role: true,
        isActive: true,
        emailVerified: true,
        requiresApproval: true,
        createdAt: true,
      },
    });

    // Send verification email
    const emailResult = await sendVerificationEmail(email, fullName, verificationToken);
    
    if (!emailResult.success) {
      console.error('Failed to send verification email:', emailResult.error);
      // Don't fail registration, but log the error
    }

    // Log registration in audit log
    await prisma.auditLog.create({
      data: {
        userId: user.id,
        action: 'USER_REGISTERED',
        resourceType: 'USER',
        resourceId: user.id,
        ipAddress: clientIp,
        changes: {
          email: user.email,
          username: user.username,
          fullName: user.fullName,
        },
      },
    });

    return NextResponse.json({ 
      user,
      message: 'Registration successful! Please check your email to verify your account. An administrator will review your account before granting access.',
      emailSent: emailResult.success
    }, { status: 201 });
  } catch (error) {
    console.error('Error creating user:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
