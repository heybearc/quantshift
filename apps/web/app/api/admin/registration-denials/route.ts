import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const denials = await prisma.registrationDenial.findMany({
      orderBy: { createdAt: 'desc' },
    });

    return NextResponse.json({ success: true, denials });
  } catch (error) {
    console.error('Error fetching registration denials:', error);
    return NextResponse.json({ error: 'Failed to load rejected users' }, { status: 500 });
  }
}
