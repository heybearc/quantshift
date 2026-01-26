import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { getLatestReleaseNote } from '@/lib/release-notes';

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

    // Get the latest release from markdown files
    const latestRelease = getLatestReleaseNote();

    if (!latestRelease) {
      return NextResponse.json({ success: true, data: null, showBanner: false });
    }

    // Format to match expected structure
    const formattedRelease = {
      version: latestRelease.version,
      title: `Release v${latestRelease.version}`,
      releaseDate: latestRelease.date,
      isPublished: true,
      type: latestRelease.type,
    };

    return NextResponse.json({
      success: true,
      data: formattedRelease,
      showBanner: true,
    });
  } catch (error) {
    console.error('Error fetching latest release:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch latest release' },
      { status: 500 }
    );
  }
}
