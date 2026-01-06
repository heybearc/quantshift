import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload) {
      return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
    }

    // Get the latest published release
    const latestRelease = await prisma.releaseNote.findFirst({
      where: {
        isPublished: true,
      },
      orderBy: {
        releaseDate: 'desc',
      },
    });

    if (!latestRelease) {
      return NextResponse.json({ success: true, data: null, showBanner: false });
    }

    // Get the user's last seen version
    const user = await prisma.user.findUnique({
      where: { id: payload.sub },
      select: { lastSeenReleaseVersion: true },
    });

    // Show banner if user hasn't seen this version
    const showBanner = !user?.lastSeenReleaseVersion || 
                       user.lastSeenReleaseVersion !== latestRelease.version;

    return NextResponse.json({
      success: true,
      data: latestRelease,
      showBanner,
    });
  } catch (error) {
    console.error('Error fetching latest release:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch latest release' },
      { status: 500 }
    );
  }
}
