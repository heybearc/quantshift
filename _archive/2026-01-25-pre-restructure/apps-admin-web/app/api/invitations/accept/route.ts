import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const { token, fullName, username, password } = await request.json();

    if (!token || !fullName || !username || !password) {
      return NextResponse.json(
        { success: false, error: 'All fields are required' },
        { status: 400 }
      );
    }

    // Validate invitation
    const invitation = await prisma.userInvitation.findUnique({
      where: { invitationToken: token },
    });

    if (!invitation) {
      return NextResponse.json(
        { success: false, error: 'Invalid invitation token' },
        { status: 400 }
      );
    }

    if (invitation.status !== 'PENDING') {
      return NextResponse.json(
        { success: false, error: 'This invitation is no longer valid' },
        { status: 400 }
      );
    }

    if (invitation.expiresAt < new Date()) {
      await prisma.userInvitation.update({
        where: { id: invitation.id },
        data: { status: 'EXPIRED' },
      });

      return NextResponse.json(
        { success: false, error: 'This invitation has expired' },
        { status: 400 }
      );
    }

    // Check if user already exists
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [
          { email: invitation.email },
          { username: username },
        ],
      },
    });

    if (existingUser) {
      return NextResponse.json(
        { success: false, error: 'User with this email or username already exists' },
        { status: 400 }
      );
    }

    // Hash password
    const passwordHash = await bcrypt.hash(password, 10);

    // Generate email verification token
    const emailVerificationToken = crypto.randomBytes(32).toString('hex');
    const emailVerificationExpiry = new Date();
    emailVerificationExpiry.setHours(emailVerificationExpiry.getHours() + 24);

    // Create user account
    const user = await prisma.user.create({
      data: {
        email: invitation.email,
        username,
        fullName,
        passwordHash,
        role: 'VIEWER',
        accountStatus: 'PENDING_APPROVAL',
        isActive: false,
        emailVerified: false,
        emailVerificationToken,
        emailVerificationExpiry,
      },
    });

    // Mark invitation as accepted
    await prisma.userInvitation.update({
      where: { id: invitation.id },
      data: {
        status: 'ACCEPTED',
        acceptedAt: new Date(),
      },
    });

    // TODO: Send email verification email
    // await sendVerificationEmail(user.email, user.fullName || user.username, emailVerificationToken);

    return NextResponse.json({
      success: true,
      message: 'Account created successfully. Please check your email to verify your account.',
      user: {
        id: user.id,
        email: user.email,
        username: user.username,
      },
    });
  } catch (error) {
    console.error('Error accepting invitation:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create account' },
      { status: 500 }
    );
  }
}
