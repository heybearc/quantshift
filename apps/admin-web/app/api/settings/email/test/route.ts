import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import nodemailer from 'nodemailer';

// POST - Test email configuration
export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const body = await request.json();
    const { smtpHost, smtpPort, smtpUser, smtpPass, testEmail } = body;

    // Validate required fields
    if (!smtpHost || !smtpPort || !smtpUser || !smtpPass || !testEmail) {
      return NextResponse.json(
        { error: 'All fields are required for testing' },
        { status: 400 }
      );
    }

    // Use provided password or fall back to env if masked
    const password = smtpPass === '••••••••' ? process.env.SMTP_PASS : smtpPass;

    if (!password) {
      return NextResponse.json(
        { error: 'SMTP password is required for testing' },
        { status: 400 }
      );
    }

    // Create transporter with provided settings
    const transporter = nodemailer.createTransport({
      host: smtpHost,
      port: parseInt(smtpPort),
      secure: parseInt(smtpPort) === 465,
      auth: {
        user: smtpUser,
        pass: password,
      },
    });

    // Verify connection
    await transporter.verify();

    // Send test email
    await transporter.sendMail({
      from: `"QuantShift Admin" <${smtpUser}>`,
      to: testEmail,
      subject: 'QuantShift Email Configuration Test',
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }
            .success-badge { background: #10b981; color: white; padding: 10px 20px; border-radius: 20px; display: inline-block; margin: 20px 0; }
            .footer { text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>✅ Email Configuration Test</h1>
            </div>
            <div class="content">
              <div class="success-badge">Configuration Successful!</div>
              <p>Your QuantShift email configuration is working correctly.</p>
              <p><strong>SMTP Settings:</strong></p>
              <ul>
                <li>Host: ${smtpHost}</li>
                <li>Port: ${smtpPort}</li>
                <li>User: ${smtpUser}</li>
              </ul>
              <p>You will now receive:</p>
              <ul>
                <li>Email verification requests</li>
                <li>Account approval notifications</li>
                <li>Security alerts</li>
                <li>Password reset emails</li>
              </ul>
              <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                If you did not request this test, please contact your system administrator.
              </p>
            </div>
            <div class="footer">
              <p>Powered by QuantShift Trading Platform</p>
            </div>
          </div>
        </body>
        </html>
      `,
    });

    return NextResponse.json({ 
      success: true,
      message: `Test email sent successfully to ${testEmail}` 
    });
  } catch (error: any) {
    console.error('Error testing email configuration:', error);
    
    let errorMessage = 'Failed to send test email';
    if (error.code === 'EAUTH') {
      errorMessage = 'Authentication failed. Please check your SMTP username and password.';
    } else if (error.code === 'ECONNECTION') {
      errorMessage = 'Connection failed. Please check your SMTP host and port.';
    } else if (error.message) {
      errorMessage = error.message;
    }

    return NextResponse.json(
      { error: errorMessage },
      { status: 400 }
    );
  }
}
