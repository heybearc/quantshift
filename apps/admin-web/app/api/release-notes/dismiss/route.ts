import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get('token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload) {
      return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
    }

    const { releaseId } = await request.json();

    // Get the release version
    const release = await prisma.releaseNote.findUnique({
      where: { id: releaseId },
      select: { version: true },
    });

    if (!release) {
      return NextResponse.json({ error: 'Release not found' }, { status: 404 });
    }

    // Update user's last seen version
    await prisma.user.update({
      where: { id: payload.sub },
      data: {
        lastSeenReleaseVersion: release.version,
      },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error dismissing release banner:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to dismiss banner' },
      { status: 500 }
    );
  }
}
