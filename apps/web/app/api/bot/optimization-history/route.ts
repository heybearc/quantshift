import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';

export async function GET() {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // No optimization runs are stored yet. The page shows its empty state.
    return NextResponse.json([]);
  } catch (error) {
    console.error('Error fetching optimization history:', error);
    return NextResponse.json(
      { error: 'Failed to fetch optimization history' },
      { status: 500 }
    );
  }
}
