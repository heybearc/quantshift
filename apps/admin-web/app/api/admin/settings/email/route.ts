import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    // Load email configuration from database
    const settings = await prisma.platformSettings.findMany({
      where: {
        key: {
          in: [
            'email_auth_type',
            'email_gmail_email',
            'email_gmail_app_password',
            'email_smtp_server',
            'email_smtp_port',
            'email_smtp_user',
            'email_smtp_password',
            'email_smtp_secure',
            'email_from_email',
            'email_from_name',
            'email_reply_to_email',
          ],
        },
      },
    });

    // Convert settings array to config object
    const config: any = {
      authType: 'gmail',
      gmailEmail: '',
      gmailAppPassword: '',
      smtpServer: 'smtp.gmail.com',
      smtpPort: '587',
      smtpUser: '',
      smtpPassword: '',
      smtpSecure: true,
      fromEmail: '',
      fromName: 'QuantShift Trading Platform',
      replyToEmail: '',
    };

    settings.forEach((setting: { key: string; value: string }) => {
      const key = setting.key.replace('email_', '').replace(/_/g, '');
      let value: string | boolean = setting.value;

      // Convert string values to appropriate types
      if (key === 'smtpsecure') {
        value = value === 'true';
      }

      // Map database keys to config keys
      const keyMap: { [key: string]: string } = {
        authtype: 'authType',
        gmailemail: 'gmailEmail',
        gmailapppassword: 'gmailAppPassword',
        smtpserver: 'smtpServer',
        smtpport: 'smtpPort',
        smtpuser: 'smtpUser',
        smtppassword: 'smtpPassword',
        smtpsecure: 'smtpSecure',
        fromemail: 'fromEmail',
        fromname: 'fromName',
        replytoemail: 'replyToEmail',
      };

      const mappedKey = keyMap[key] || key;
      config[mappedKey] = value;
    });

    return NextResponse.json({ success: true, data: config });
  } catch (error) {
    console.error('Error loading email configuration:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to load email configuration' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get('token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const config = await request.json();

    // Save email configuration to database
    const settingsToSave: Array<{ key: string; value: string }> = [
      { key: 'email_auth_type', value: config.authType },
      { key: 'email_gmail_email', value: config.gmailEmail || '' },
      { key: 'email_gmail_app_password', value: config.gmailAppPassword || '' },
      { key: 'email_smtp_server', value: config.smtpServer || '' },
      { key: 'email_smtp_port', value: config.smtpPort || '' },
      { key: 'email_smtp_user', value: config.smtpUser || '' },
      { key: 'email_smtp_password', value: config.smtpPassword || '' },
      { key: 'email_smtp_secure', value: String(config.smtpSecure) },
      { key: 'email_from_email', value: config.fromEmail || '' },
      { key: 'email_from_name', value: config.fromName || '' },
      { key: 'email_reply_to_email', value: config.replyToEmail || '' },
    ];

    // Upsert each setting
    for (const setting of settingsToSave) {
      await prisma.platformSettings.upsert({
        where: { key: setting.key },
        update: { value: setting.value },
        create: {
          key: setting.key,
          value: setting.value,
        },
      });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error saving email configuration:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to save email configuration' },
      { status: 500 }
    );
  }
}
