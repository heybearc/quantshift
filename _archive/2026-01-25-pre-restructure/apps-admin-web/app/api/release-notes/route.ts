import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    await verifyToken(token);

    // Get all published release notes, sorted by version descending
    const releases = await prisma.releaseNote.findMany({
      where: {
        isPublished: true,
      },
      orderBy: {
        releaseDate: 'desc',
      },
    });

    return NextResponse.json({ success: true, data: releases });
  } catch (error) {
    console.error('Error fetching release notes:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch release notes' },
      { status: 500 }
    );
  }
}
