import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { sendAccountRejectedEmail } from '@/lib/email';

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
    const { reason } = await request.json();

    // Get user
    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    // Update user status
    const updatedUser = await prisma.user.update({
      where: { id: userId },
      data: {
        accountStatus: 'INACTIVE',
        isActive: false,
      },
    });

    // Send rejection email
    await sendAccountRejectedEmail(
      updatedUser.email,
      updatedUser.fullName || updatedUser.username || updatedUser.email,
      reason
    );

    // Create audit log
    await prisma.auditLog.create({
      data: {
        userId: payload.sub,
        action: 'USER_REJECTED',
        resourceType: 'USER',
        resourceId: userId,
        changes: reason ? { reason } : {},
        ipAddress: request.headers.get('x-forwarded-for') || 'unknown',
      },
    });

    return NextResponse.json({
      success: true,
      message: `User ${updatedUser.email} has been rejected`,
      user: {
        id: updatedUser.id,
        email: updatedUser.email,
        accountStatus: updatedUser.accountStatus,
      },
    });
  } catch (error) {
    console.error('Error rejecting user:', error);
    return NextResponse.json(
      { error: 'Failed to reject user' },
      { status: 500 }
    );
  }
}
