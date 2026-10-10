import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

const DEFAULTS = {
  emailNotifications: true,
  tradeAlerts: true,
  performanceReports: true,
  systemAlerts: true,
};

function asPreferences(value: unknown) {
  const stored = value && typeof value === 'object' ? value as Record<string, unknown> : {};
  return {
    emailNotifications: typeof stored.emailNotifications === 'boolean' ? stored.emailNotifications : DEFAULTS.emailNotifications,
    tradeAlerts: typeof stored.tradeAlerts === 'boolean' ? stored.tradeAlerts : DEFAULTS.tradeAlerts,
    performanceReports: typeof stored.performanceReports === 'boolean' ? stored.performanceReports : DEFAULTS.performanceReports,
    systemAlerts: typeof stored.systemAlerts === 'boolean' ? stored.systemAlerts : DEFAULTS.systemAlerts,
  };
}

export async function GET() {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const record = await prisma.user.findUnique({
      where: { id: user.id },
      select: { emailNotifications: true, notificationPreferences: true },
    });

    const preferences = asPreferences(record?.notificationPreferences);
    if (typeof record?.emailNotifications === 'boolean') {
      preferences.emailNotifications = record.emailNotifications;
    }

    return NextResponse.json(preferences);
  } catch (error) {
    console.error('Error loading notification settings:', error);
    return NextResponse.json({ error: 'Failed to load notification settings' }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const preferences = asPreferences(body);

    await prisma.user.update({
      where: { id: user.id },
      data: {
        emailNotifications: preferences.emailNotifications,
        notificationPreferences: preferences,
      },
    });

    return NextResponse.json(preferences);
  } catch (error) {
    console.error('Error saving notification settings:', error);
    return NextResponse.json({ error: 'Failed to save notification settings' }, { status: 500 });
  }
}
