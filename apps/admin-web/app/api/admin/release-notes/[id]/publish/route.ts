import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const token = request.cookies.get('token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const { id } = await params;
    const { isPublished } = await request.json();

    // Update publish status
    const release = await prisma.releaseNote.update({
      where: { id },
      data: { isPublished },
    });

    return NextResponse.json({ success: true, data: release });
  } catch (error) {
    console.error('Error updating publish status:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to update publish status' },
      { status: 500 }
    );
  }
}
