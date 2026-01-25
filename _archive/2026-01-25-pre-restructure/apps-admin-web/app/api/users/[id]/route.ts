import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyToken } from '@/lib/auth';

export async function PATCH(
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

    const body = await request.json();
    const { 
      isActive,
      fullName,
      username,
      role,
      phoneNumber,
      timeZone,
      accountStatus,
      emailVerified,
      phoneVerified,
      requiresApproval,
      kycStatus,
      alpacaAccountId,
      riskTolerance,
      canPlaceOrders,
      canModifyOrders,
      canCancelOrders,
      maxPositionSize,
      maxOrderSize,
      subscriptionTier,
      mfaEnabled
    } = body;

    const updateData: any = {};
    if (isActive !== undefined) updateData.isActive = isActive;
    if (fullName !== undefined) updateData.fullName = fullName;
    if (username !== undefined) updateData.username = username;
    if (role !== undefined) updateData.role = role;
    if (phoneNumber !== undefined) updateData.phoneNumber = phoneNumber;
    if (timeZone !== undefined) updateData.timeZone = timeZone;
    if (accountStatus !== undefined) updateData.accountStatus = accountStatus;
    if (emailVerified !== undefined) updateData.emailVerified = emailVerified;
    if (phoneVerified !== undefined) updateData.phoneVerified = phoneVerified;
    if (requiresApproval !== undefined) updateData.requiresApproval = requiresApproval;
    if (kycStatus !== undefined) updateData.kycStatus = kycStatus;
    if (alpacaAccountId !== undefined) updateData.alpacaAccountId = alpacaAccountId;
    if (riskTolerance !== undefined) updateData.riskTolerance = riskTolerance;
    if (canPlaceOrders !== undefined) updateData.canPlaceOrders = canPlaceOrders;
    if (canModifyOrders !== undefined) updateData.canModifyOrders = canModifyOrders;
    if (canCancelOrders !== undefined) updateData.canCancelOrders = canCancelOrders;
    if (maxPositionSize !== undefined) updateData.maxPositionSize = maxPositionSize;
    if (maxOrderSize !== undefined) updateData.maxOrderSize = maxOrderSize;
    if (subscriptionTier !== undefined) updateData.subscriptionTier = subscriptionTier;
    if (mfaEnabled !== undefined) updateData.mfaEnabled = mfaEnabled;

    const user = await prisma.user.update({
      where: { id: params.id },
      data: updateData,
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
        canModifyOrders: true,
        canCancelOrders: true,
        maxPositionSize: true,
        maxOrderSize: true,
        subscriptionTier: true,
        createdAt: true,
        lastLogin: true,
        lastLoginIp: true,
      },
    });

    return NextResponse.json({ user });
  } catch (error) {
    console.error('Error updating user:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(
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

    if (params.id === payload.sub) {
      return NextResponse.json({ error: 'Cannot delete your own account' }, { status: 400 });
    }

    await prisma.user.delete({
      where: { id: params.id },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting user:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
