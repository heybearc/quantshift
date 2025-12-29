import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import bcrypt from 'bcryptjs';
import { verifyToken } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const users = await prisma.user.findMany({
      select: {
        id: true,
        email: true,
        username: true,
        fullName: true,
        phoneNumber: true,
        timeZone: true,
        role: true,
        isActive: true,
        accountStatus: true,
        emailVerified: true,
        phoneVerified: true,
        mfaEnabled: true,
        requiresApproval: true,
        approvedBy: true,
        approvedAt: true,
        kycStatus: true,
        alpacaAccountId: true,
        riskTolerance: true,
        canPlaceOrders: true,
        subscriptionTier: true,
        createdAt: true,
        lastLogin: true,
        lastLoginIp: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    return NextResponse.json({ users });
  } catch (error) {
    console.error('Error fetching users:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const body = await request.json();
    const { 
      email, 
      username, 
      fullName, 
      password, 
      role,
      phoneNumber,
      timeZone,
      accountStatus,
      emailVerified,
      requiresApproval,
      kycStatus,
      riskTolerance,
      canPlaceOrders,
      subscriptionTier
    } = body;

    if (!email || !username || !fullName || !password) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [
          { email },
          { username }
        ]
      }
    });

    if (existingUser) {
      return NextResponse.json({ error: 'User with this email or username already exists' }, { status: 409 });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const user = await prisma.user.create({
      data: {
        email,
        username,
        fullName,
        passwordHash: hashedPassword,
        role: role || 'VIEWER',
        phoneNumber: phoneNumber || null,
        timeZone: timeZone || 'America/New_York',
        isActive: true,
        accountStatus: accountStatus || 'ACTIVE',
        emailVerified: emailVerified !== undefined ? emailVerified : true,
        requiresApproval: requiresApproval !== undefined ? requiresApproval : false,
        kycStatus: kycStatus || 'NOT_STARTED',
        riskTolerance: riskTolerance || null,
        canPlaceOrders: canPlaceOrders || false,
        subscriptionTier: subscriptionTier || 'FREE',
      },
      select: {
        id: true,
        email: true,
        username: true,
        fullName: true,
        phoneNumber: true,
        timeZone: true,
        role: true,
        isActive: true,
        accountStatus: true,
        emailVerified: true,
        phoneVerified: true,
        mfaEnabled: true,
        requiresApproval: true,
        approvedBy: true,
        approvedAt: true,
        kycStatus: true,
        alpacaAccountId: true,
        riskTolerance: true,
        canPlaceOrders: true,
        subscriptionTier: true,
        createdAt: true,
        lastLogin: true,
        lastLoginIp: true,
      },
    });

    return NextResponse.json({ user }, { status: 201 });
  } catch (error) {
    console.error('Error creating user:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
