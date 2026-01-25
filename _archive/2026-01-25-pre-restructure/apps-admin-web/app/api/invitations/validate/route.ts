import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const token = searchParams.get('token');

    if (!token) {
      return NextResponse.json(
        { success: false, valid: false, error: 'Token is required' },
        { status: 400 }
      );
    }

    const invitation = await prisma.userInvitation.findUnique({
      where: { invitationToken: token },
    });

    if (!invitation) {
      return NextResponse.json({
        success: false,
        valid: false,
        error: 'Invalid invitation token',
      });
    }

    // Check if already accepted
    if (invitation.status === 'ACCEPTED') {
      return NextResponse.json({
        success: false,
        valid: false,
        error: 'This invitation has already been used',
      });
    }

    // Check if expired
    if (invitation.expiresAt < new Date()) {
      // Update status to expired
      await prisma.userInvitation.update({
        where: { id: invitation.id },
        data: { status: 'EXPIRED' },
      });

      return NextResponse.json({
        success: false,
        valid: false,
        error: 'This invitation has expired',
      });
    }

    // Check if cancelled
    if (invitation.status === 'CANCELLED') {
      return NextResponse.json({
        success: false,
        valid: false,
        error: 'This invitation has been cancelled',
      });
    }

    return NextResponse.json({
      success: true,
      valid: true,
      invitation: {
        email: invitation.email,
        invitedBy: invitation.invitedByName,
        expiresAt: invitation.expiresAt,
      },
    });
  } catch (error) {
    console.error('Error validating invitation:', error);
    return NextResponse.json(
      { success: false, valid: false, error: 'Failed to validate invitation' },
      { status: 500 }
    );
  }
}
