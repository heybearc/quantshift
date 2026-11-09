import { NextRequest, NextResponse } from 'next/server';
import { 
  getRefreshToken, 
  verifyRefreshToken,
  verifyToken,
  createAccessToken, 
  createRefreshToken,
  setAuthCookies,
  storeRefreshToken,
  revokeRefreshToken 
} from '@/lib/auth';

async function readRefreshToken(request: NextRequest): Promise<string | undefined> {
  const fromCookie = await getRefreshToken();
  if (fromCookie) return fromCookie;

  const authorization = request.headers.get('authorization');
  if (authorization) {
    const [scheme, token] = authorization.split(/\s+/, 2);
    if (scheme?.toLowerCase() === 'bearer' && token && verifyToken(token)?.type === 'refresh') {
      return token;
    }
  }

  try {
    const body = await request.json();
    if (typeof body?.refresh_token === 'string' && body.refresh_token) {
      return body.refresh_token;
    }
  } catch {
    return undefined;
  }
  return undefined;
}

export async function POST(request: NextRequest) {
  try {
    const oldRefreshToken = await readRefreshToken(request);

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

    return NextResponse.json({
      access_token: accessToken,
      refresh_token: newRefreshToken,
      token_type: 'bearer',
    });
  } catch (error) {
    console.error('Token refresh error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
