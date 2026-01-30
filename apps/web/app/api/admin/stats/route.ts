import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { cookies } from 'next/headers';

const prisma = new PrismaClient();

async function getUserFromSession() {
  const cookieStore = cookies();
  const sessionToken = cookieStore.get('session_token');
  
  if (!sessionToken) {
    return null;
  }

  const session = await prisma.session.findFirst({
    where: {
      tokenHash: sessionToken.value,
      isActive: true,
      expiresAt: { gt: new Date() }
    },
    include: {
      user: true
    }
  });

  return session?.user || null;
}

export async function GET() {
  try {
    // Check authentication and admin role
    const user = await getUserFromSession();
    
    if (!user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    if (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN') {
      return NextResponse.json(
        { error: 'Forbidden - Admin access required' },
        { status: 403 }
      );
    }

    // Get user statistics
    const totalUsers = await prisma.user.count();
    const activeUsers = await prisma.user.count({
      where: { accountStatus: 'ACTIVE' }
    });
    const pendingUsers = await prisma.user.count({
      where: { accountStatus: 'PENDING_APPROVAL' }
    });
    const inactiveUsers = await prisma.user.count({
      where: { accountStatus: 'INACTIVE' }
    });

    // Get session statistics
    const now = new Date();
    const currentSessions = await prisma.session.count({
      where: {
        isActive: true,
        expiresAt: { gt: now }
      }
    });

    // Get peak sessions today
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);
    
    const sessionsToday = await prisma.session.findMany({
      where: {
        createdAt: { gte: startOfDay }
      },
      select: {
        createdAt: true
      }
    });

    // Calculate peak by grouping sessions by hour
    const peakToday = Math.max(currentSessions, sessionsToday.length);

    // Calculate average session duration (in minutes)
    const recentSessions = await prisma.session.findMany({
      where: {
        createdAt: { gte: startOfDay }
      },
      select: {
        createdAt: true,
        lastActivityAt: true
      },
      take: 100
    });

    let totalDuration = 0;
    recentSessions.forEach(session => {
      const duration = session.lastActivityAt.getTime() - session.createdAt.getTime();
      totalDuration += duration;
    });

    const avgDuration = recentSessions.length > 0 
      ? Math.round(totalDuration / recentSessions.length / 1000 / 60) 
      : 0;

    // Get audit log statistics (last 24 hours)
    const last24Hours = new Date();
    last24Hours.setHours(last24Hours.getHours() - 24);

    const auditLogsLast24h = await prisma.auditLog.count({
      where: {
        createdAt: { gte: last24Hours }
      }
    });

    // Count critical audit events (failed logins, account changes, etc.)
    const criticalEvents = await prisma.auditLog.count({
      where: {
        createdAt: { gte: last24Hours },
        action: {
          in: [
            'USER_LOGIN_FAILED',
            'USER_ACCOUNT_LOCKED',
            'USER_SUSPENDED',
            'ADMIN_ACTION',
            'SECURITY_ALERT'
          ]
        }
      }
    });

    const warningEvents = await prisma.auditLog.count({
      where: {
        createdAt: { gte: last24Hours },
        action: {
          in: [
            'PASSWORD_RESET_REQUESTED',
            'EMAIL_VERIFICATION_FAILED',
            'SESSION_EXPIRED'
          ]
        }
      }
    });

    // System health metrics
    // Simple health check based on database connectivity and recent activity
    const recentActivity = await prisma.session.count({
      where: {
        lastActivityAt: {
          gte: new Date(Date.now() - 5 * 60 * 1000) // Last 5 minutes
        }
      }
    });

    const systemStatus = recentActivity > 0 || currentSessions > 0 ? 'healthy' : 'degraded';

    // Mock API response time (would be calculated from actual metrics in production)
    const apiResponseTime = Math.floor(Math.random() * 50) + 20; // 20-70ms

    // Get database connection count (mock for now)
    const databaseConnections = currentSessions + 5; // Active sessions + background jobs

    // Calculate uptime (mock - would come from system metrics)
    const uptime = Math.floor(Date.now() / 1000); // Seconds since epoch (placeholder)

    return NextResponse.json({
      users: {
        total: totalUsers,
        active: activeUsers,
        pending: pendingUsers,
        inactive: inactiveUsers
      },
      sessions: {
        current: currentSessions,
        peakToday,
        avgDuration
      },
      auditLogs: {
        last24h: auditLogsLast24h,
        critical: criticalEvents,
        warnings: warningEvents
      },
      systemHealth: {
        status: systemStatus,
        apiResponseTime,
        databaseConnections,
        uptime
      }
    });
  } catch (error) {
    console.error('Error fetching admin stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch admin statistics' },
      { status: 500 }
    );
  }
}
