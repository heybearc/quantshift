import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { sendTestEmail } from '@/lib/email';

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

    const { testEmail } = await request.json();

    if (!testEmail) {
      return NextResponse.json(
        { success: false, error: 'Test email address is required' },
        { status: 400 }
      );
    }

    // Send test email using the centralized email service
    const result = await sendTestEmail(testEmail);

    if (result.success) {
      return NextResponse.json({ 
        success: true, 
        message: `Test email sent successfully to ${testEmail}` 
      });
    } else {
      return NextResponse.json(
        { 
          success: false, 
          error: result.error instanceof Error ? result.error.message : 'Failed to send test email' 
        },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Error sending test email:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to send test email' 
      },
      { status: 500 }
    );
  }
}
