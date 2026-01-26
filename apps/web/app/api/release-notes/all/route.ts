import { NextResponse } from 'next/server';
import { getAllReleaseNotes } from '@/lib/release-notes';

export async function GET() {
  try {
    const releaseNotes = getAllReleaseNotes();
    return NextResponse.json(releaseNotes);
  } catch (error) {
    console.error('Error fetching release notes:', error);
    return NextResponse.json({ error: 'Failed to fetch release notes' }, { status: 500 });
  }
}
