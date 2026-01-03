import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import nodemailer from 'nodemailer';

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

    const config = await request.json();

    // Create transporter based on auth type
    let transporter;

    if (config.authType === 'gmail') {
      transporter = nodemailer.createTransport({
        service: 'gmail',
        auth: {
          user: config.gmailEmail,
          pass: config.gmailAppPassword,
        },
      });
    } else {
      transporter = nodemailer.createTransport({
        host: config.smtpServer,
        port: parseInt(config.smtpPort),
        secure: config.smtpSecure,
        auth: {
          user: config.smtpUser,
          pass: config.smtpPassword,
        },
      });
    }

    // Send test email
    const info = await transporter.sendMail({
      from: `"${config.fromName}" <${config.fromEmail}>`,
      to: config.fromEmail,
      replyTo: config.replyToEmail || config.fromEmail,
      subject: 'QuantShift Email Configuration Test',
      text: 'This is a test email from QuantShift Trading Platform. Your email configuration is working correctly!',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #2563eb;">✅ Email Configuration Test</h2>
          <p>This is a test email from <strong>QuantShift Trading Platform</strong>.</p>
          <p>Your email configuration is working correctly!</p>
          <hr style="border: 1px solid #e5e7eb; margin: 20px 0;">
          <p style="color: #6b7280; font-size: 14px;">
            <strong>Configuration Details:</strong><br>
            Provider: ${config.authType === 'gmail' ? 'Gmail' : 'Custom SMTP'}<br>
            From: ${config.fromName} &lt;${config.fromEmail}&gt;<br>
            ${config.replyToEmail ? `Reply-To: ${config.replyToEmail}<br>` : ''}
          </p>
          <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
            Sent from QuantShift Trading Platform
          </p>
        </div>
      `,
    });

    console.log('Test email sent:', info.messageId);

    return NextResponse.json({ 
      success: true, 
      message: 'Test email sent successfully',
      messageId: info.messageId 
    });
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
