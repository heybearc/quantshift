import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { writeFile, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

const ENV_FILE_PATH = path.join(process.cwd(), '.env');

interface EmailSettings {
  smtpHost: string;
  smtpPort: string;
  smtpUser: string;
  smtpPass: string;
  appUrl: string;
}

// GET - Retrieve current email settings (without password)
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

    const settings: EmailSettings = {
      smtpHost: process.env.SMTP_HOST || '',
      smtpPort: process.env.SMTP_PORT || '587',
      smtpUser: process.env.SMTP_USER || '',
      smtpPass: process.env.SMTP_PASS ? '••••••••' : '', // Mask password
      appUrl: process.env.NEXT_PUBLIC_APP_URL || '',
    };

    return NextResponse.json({ settings });
  } catch (error) {
    console.error('Error fetching email settings:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST - Update email settings
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
    const { smtpHost, smtpPort, smtpUser, smtpPass, appUrl } = body;

    // Validate required fields
    if (!smtpHost || !smtpPort || !smtpUser || !appUrl) {
      return NextResponse.json(
        { error: 'All fields except password are required' },
        { status: 400 }
      );
    }

    // Read current .env file
    let envContent = '';
    if (existsSync(ENV_FILE_PATH)) {
      envContent = await readFile(ENV_FILE_PATH, 'utf-8');
    }

    // Parse existing env variables
    const envLines = envContent.split('\n');
    const envVars = new Map<string, string>();
    
    for (const line of envLines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key) {
          envVars.set(key.trim(), valueParts.join('=').trim());
        }
      }
    }

    // Update email settings
    envVars.set('SMTP_HOST', smtpHost);
    envVars.set('SMTP_PORT', smtpPort);
    envVars.set('SMTP_USER', smtpUser);
    
    // Only update password if provided and not masked
    if (smtpPass && smtpPass !== '••••••••') {
      envVars.set('SMTP_PASS', smtpPass);
    }
    
    envVars.set('NEXT_PUBLIC_APP_URL', appUrl);

    // Rebuild .env file
    const newEnvContent = Array.from(envVars.entries())
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');

    // Write back to .env file
    await writeFile(ENV_FILE_PATH, newEnvContent + '\n', 'utf-8');

    // Note: Process env updates require server restart to take full effect
    // These updates only affect the current process instance

    return NextResponse.json({ 
      success: true,
      message: 'Email settings updated successfully. Changes will take effect on next server restart.' 
    });
  } catch (error) {
    console.error('Error updating email settings:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
