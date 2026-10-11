import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyToken } from '@/lib/auth';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const user = await prisma.user.findUnique({
      where: { id: params.id },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    if (params.id === payload.sub) {
      return NextResponse.json({ error: 'Cannot reject your own account' }, { status: 400 });
    }

    const awaitingDecision = user.accountStatus === 'PENDING_APPROVAL' || user.requiresApproval;
    if (!awaitingDecision) {
      return NextResponse.json(
        { error: 'User is not waiting for approval' },
        { status: 400 }
      );
    }

    await prisma.user.update({
      where: { id: params.id },
      data: {
        accountStatus: 'INACTIVE',
        requiresApproval: false,
        isActive: false,
      },
    });

    await prisma.auditLog.create({
      data: {
        userId: payload.sub,
        action: 'USER_REJECTED',
        resourceType: 'USER',
        resourceId: params.id,
        changes: {
          rejectedUser: user.email,
          rejectedBy: payload.email,
        },
      },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error rejecting user:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
