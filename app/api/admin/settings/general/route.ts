import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('access_token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    // Fetch general settings from database
    const settings = await prisma.platformSettings.findMany({
      where: {
        category: 'general'
      }
    });

    // Convert to key-value object
    const settingsObj: Record<string, string> = {};
    settings.forEach(setting => {
      settingsObj[setting.key] = setting.value;
    });

    // Provide defaults if not set
    const generalSettings = {
      platformName: settingsObj.platformName || 'QuantShift Trading Platform',
      platformDescription: settingsObj.platformDescription || 'Advanced Algorithmic Trading Platform',
      maintenanceMode: settingsObj.maintenanceMode === 'true',
      maintenanceMessage: settingsObj.maintenanceMessage || 'System is currently under maintenance. Please check back soon.',
      allowRegistration: settingsObj.allowRegistration !== 'false', // Default true
      requireEmailVerification: settingsObj.requireEmailVerification === 'true',
      sessionTimeout: parseInt(settingsObj.sessionTimeout || '86400'), // 24 hours default
      maxLoginAttempts: parseInt(settingsObj.maxLoginAttempts || '5'),
    };

    return NextResponse.json({ success: true, data: generalSettings });
  } catch (error) {
    console.error('Error fetching general settings:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch general settings' },
      { status: 500 }
    );
  }
}

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

    const body = await request.json();

    // Save each setting to database
    const settingsToSave = [
      { key: 'platformName', value: body.platformName },
      { key: 'platformDescription', value: body.platformDescription },
      { key: 'maintenanceMode', value: String(body.maintenanceMode) },
      { key: 'maintenanceMessage', value: body.maintenanceMessage },
      { key: 'allowRegistration', value: String(body.allowRegistration) },
      { key: 'requireEmailVerification', value: String(body.requireEmailVerification) },
      { key: 'sessionTimeout', value: String(body.sessionTimeout) },
      { key: 'maxLoginAttempts', value: String(body.maxLoginAttempts) },
    ];

    // Upsert each setting
    for (const setting of settingsToSave) {
      await prisma.platformSettings.upsert({
        where: {
          key: setting.key,
        },
        update: {
          value: setting.value,
          category: 'general',
        },
        create: {
          key: setting.key,
          value: setting.value,
          category: 'general',
        },
      });
    }

    // Create audit log
    await prisma.auditLog.create({
      data: {
        userId: payload.sub,
        action: 'UPDATE_GENERAL_SETTINGS',
        resourceType: 'platform_settings',
        changes: body,
        ipAddress: request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown',
      },
    });

    return NextResponse.json({ success: true, message: 'General settings updated successfully' });
  } catch (error) {
    console.error('Error updating general settings:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to update general settings' },
      { status: 500 }
    );
  }
}
