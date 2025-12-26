import { NextRequest, NextResponse } from 'next/server';
import { 
  getRefreshToken, 
  verifyRefreshToken, 
  createAccessToken, 
  createRefreshToken,
  setAuthCookies,
  storeRefreshToken,
  revokeRefreshToken 
} from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const oldRefreshToken = await getRefreshToken();

    if (!oldRefreshToken) {
      return NextResponse.json(
        { error: 'No refresh token provided' },
        { status: 401 }
      );
    }

    const user = await verifyRefreshToken(oldRefreshToken);

    if (!user) {
      return NextResponse.json(
        { error: 'Invalid refresh token' },
        { status: 401 }
      );
    }

    // Revoke old refresh token
    await revokeRefreshToken(oldRefreshToken);

    // Create new tokens
    const accessToken = createAccessToken(user.id, user.email, user.role);
    const newRefreshToken = createRefreshToken(user.id);

    // Store new refresh token
    await storeRefreshToken(user.id, newRefreshToken);

    // Set new cookies
    await setAuthCookies(accessToken, newRefreshToken);

    return NextResponse.json({ token_type: 'bearer' });
  } catch (error) {
    console.error('Token refresh error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
