import { NextRequest, NextResponse } from 'next/server';
import { getRefreshToken, clearAuthCookies, revokeRefreshToken } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const refreshToken = await getRefreshToken();
    
    if (refreshToken) {
      await revokeRefreshToken(refreshToken);
    }

    await clearAuthCookies();

    return NextResponse.json({ message: 'Logged out successfully' });
  } catch (error) {
    console.error('Logout error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
