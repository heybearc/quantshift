import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { sendAccountApprovedEmail } from '@/lib/email';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const userId = params.id;

    // Get user
    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    if (user.accountStatus === 'ACTIVE') {
      return NextResponse.json(
        { error: 'User is already approved' },
        { status: 400 }
      );
    }

    // Update user status
    const updatedUser = await prisma.user.update({
      where: { id: userId },
      data: {
        accountStatus: 'ACTIVE',
        isActive: true,
      },
    });

    // Send approval email
    await sendAccountApprovedEmail(
      updatedUser.email,
      updatedUser.fullName || updatedUser.username || updatedUser.email
    );

    // Create audit log
    await prisma.auditLog.create({
      data: {
        userId: payload.sub,
        action: 'USER_APPROVED',
        resourceType: 'USER',
        resourceId: userId,
        changes: {
          approvedUser: updatedUser.email,
          approvedBy: payload.sub,
        },
        ipAddress: request.headers.get('x-forwarded-for') || 'unknown',
      },
    });

    return NextResponse.json({
      success: true,
      message: `User ${updatedUser.email} has been approved`,
      user: {
        id: updatedUser.id,
        email: updatedUser.email,
        accountStatus: updatedUser.accountStatus,
      },
    });
  } catch (error) {
    console.error('Error approving user:', error);
    return NextResponse.json(
      { error: 'Failed to approve user' },
      { status: 500 }
    );
  }
}
