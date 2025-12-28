import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyToken } from '@/lib/auth';
import { sendAccountApprovedEmail } from '@/lib/email';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Verify admin authentication
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    // Get user to approve
    const user = await prisma.user.findUnique({
      where: { id: params.id },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    if (!user.requiresApproval) {
      return NextResponse.json(
        { error: 'User does not require approval' },
        { status: 400 }
      );
    }

    if (!user.emailVerified) {
      return NextResponse.json(
        { error: 'User must verify their email before approval' },
        { status: 400 }
      );
    }

    // Approve user
    const updatedUser = await prisma.user.update({
      where: { id: params.id },
      data: {
        requiresApproval: false,
        isActive: true,
        approvedBy: payload.sub,
        approvedAt: new Date(),
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
        approvedBy: true,
        approvedAt: true,
        createdAt: true,
      },
    });

    // Send approval email
    await sendAccountApprovedEmail(user.email, user.fullName || 'User');

    // Log approval in audit log
    await prisma.auditLog.create({
      data: {
        userId: payload.sub,
        action: 'USER_APPROVED',
        resourceType: 'USER',
        resourceId: params.id,
        changes: {
          approvedUser: user.email,
          approvedBy: payload.email,
        },
      },
    });

    return NextResponse.json({ user: updatedUser });
  } catch (error) {
    console.error('Error approving user:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
