import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function PUT(
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
    const body = await request.json();

    // Update release note
    const release = await prisma.releaseNote.update({
      where: { id },
      data: {
        version: body.version,
        title: body.title,
        description: body.description,
        changes: body.changes,
        releaseDate: new Date(body.releaseDate),
        type: body.type,
      },
    });

    return NextResponse.json({ success: true, data: release });
  } catch (error) {
    console.error('Error updating release note:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to update release note' },
      { status: 500 }
    );
  }
}

export async function DELETE(
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

    // Delete release note
    await prisma.releaseNote.delete({
      where: { id },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting release note:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to delete release note' },
      { status: 500 }
    );
  }
}
