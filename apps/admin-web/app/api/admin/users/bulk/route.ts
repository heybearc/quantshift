import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { sendAccountApprovedEmail, sendAccountRejectedEmail } from '@/lib/email';

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

    const { action, userIds, reason } = await request.json();

    if (!action || !userIds || !Array.isArray(userIds) || userIds.length === 0) {
      return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
    }

    if (action === 'approve') {
      const users = await prisma.user.findMany({
        where: {
          id: { in: userIds },
          accountStatus: 'PENDING_APPROVAL',
        },
      });

      const results = await Promise.allSettled(
        users.map(async (user) => {
          await prisma.user.update({
            where: { id: user.id },
            data: {
              accountStatus: 'ACTIVE',
              isActive: true,
            },
          });

          await prisma.auditLog.create({
            data: {
              userId: payload.sub,
              action: 'USER_BULK_APPROVED',
              resourceType: 'USER',
              resourceId: user.id,
              changes: {
                approvedUser: user.email,
                approvedBy: payload.sub,
              },
              ipAddress: request.headers.get('x-forwarded-for') || 'unknown',
            },
          });

          try {
            await sendAccountApprovedEmail(user.email, user.fullName || user.email);
          } catch (emailError) {
            console.error(`Failed to send approval email to ${user.email}:`, emailError);
          }

          return user;
        })
      );

      const successful = results.filter((r) => r.status === 'fulfilled').length;
      const failed = results.filter((r) => r.status === 'rejected').length;

      return NextResponse.json({
        success: true,
        message: `Approved ${successful} users${failed > 0 ? `, ${failed} failed` : ''}`,
        successful,
        failed,
      });
    } else if (action === 'reject') {
      const users = await prisma.user.findMany({
        where: {
          id: { in: userIds },
          accountStatus: 'PENDING_APPROVAL',
        },
      });

      const results = await Promise.allSettled(
        users.map(async (user) => {
          await prisma.user.update({
            where: { id: user.id },
            data: {
              accountStatus: 'INACTIVE',
              isActive: false,
            },
          });

          await prisma.auditLog.create({
            data: {
              userId: payload.sub,
              action: 'USER_BULK_REJECTED',
              resourceType: 'USER',
              resourceId: user.id,
              changes: reason ? { reason } : {},
              ipAddress: request.headers.get('x-forwarded-for') || 'unknown',
            },
          });

          try {
            await sendAccountRejectedEmail(user.email, user.fullName || user.email, reason);
          } catch (emailError) {
            console.error(`Failed to send rejection email to ${user.email}:`, emailError);
          }

          return user;
        })
      );

      const successful = results.filter((r) => r.status === 'fulfilled').length;
      const failed = results.filter((r) => r.status === 'rejected').length;

      return NextResponse.json({
        success: true,
        message: `Rejected ${successful} users${failed > 0 ? `, ${failed} failed` : ''}`,
        successful,
        failed,
      });
    } else {
      return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
    }
  } catch (error) {
    console.error('Error in bulk user operation:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
