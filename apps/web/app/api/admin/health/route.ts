import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import os from 'os';

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

    // System metrics
    const totalMemory = os.totalmem();
    const freeMemory = os.freemem();
    const usedMemory = totalMemory - freeMemory;
    const memoryUsagePercent = (usedMemory / totalMemory) * 100;

    const cpus = os.cpus();
    const loadAverage = os.loadavg();

    // Database health check
    let dbStatus = 'healthy';
    let dbResponseTime = 0;
    try {
      const start = Date.now();
      await prisma.$queryRaw`SELECT 1`;
      dbResponseTime = Date.now() - start;
      if (dbResponseTime > 1000) dbStatus = 'slow';
    } catch (error) {
      dbStatus = 'error';
    }

    // Count database records
    const [userCount, sessionCount, auditLogCount] = await Promise.all([
      prisma.user.count(),
      prisma.session.count({ where: { isActive: true } }),
      prisma.auditLog.count(),
    ]);

    // Application uptime
    const uptime = process.uptime();

    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      system: {
        platform: os.platform(),
        arch: os.arch(),
        nodeVersion: process.version,
        uptime: uptime,
        hostname: os.hostname(),
      },
      memory: {
        total: totalMemory,
        used: usedMemory,
        free: freeMemory,
        usagePercent: memoryUsagePercent,
      },
      cpu: {
        cores: cpus.length,
        model: cpus[0]?.model || 'Unknown',
        loadAverage: {
          '1min': loadAverage[0],
          '5min': loadAverage[1],
          '15min': loadAverage[2],
        },
      },
      database: {
        status: dbStatus,
        responseTime: dbResponseTime,
        connections: {
          users: userCount,
          activeSessions: sessionCount,
          auditLogs: auditLogCount,
        },
      },
    };

    // Determine overall health status
    if (dbStatus === 'error' || memoryUsagePercent > 90) {
      health.status = 'critical';
    } else if (dbStatus === 'slow' || memoryUsagePercent > 75) {
      health.status = 'warning';
    }

    return NextResponse.json({ success: true, data: health });
  } catch (error) {
    console.error('Error fetching health metrics:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch health metrics' },
      { status: 500 }
    );
  }
}
