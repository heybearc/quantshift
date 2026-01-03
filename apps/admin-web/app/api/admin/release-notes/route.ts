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
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    // Get all release notes (including drafts)
    const releases = await prisma.releaseNote.findMany({
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

    const body = await request.json();

    // Create new release note
    const release = await prisma.releaseNote.create({
      data: {
        version: body.version,
        title: body.title,
        description: body.description,
        type: body.type || 'patch',
        changes: body.changes,
        releaseDate: new Date(body.releaseDate),
        isPublished: false,
        createdBy: payload.sub,
      },
    });

    return NextResponse.json({ success: true, data: release });
  } catch (error) {
    console.error('Error creating release note:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create release note' },
      { status: 500 }
    );
  }
}
