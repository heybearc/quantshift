import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';

interface EndpointStatus {
  endpoint: string;
  method: string;
  status: 'operational' | 'degraded' | 'down';
  responseTime: number;
  lastChecked: string;
}

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

    // Define critical API endpoints to monitor
    const endpoints = [
      { path: '/api/auth/me', method: 'GET', category: 'Authentication' },
      { path: '/api/users', method: 'GET', category: 'User Management' },
      { path: '/api/admin/sessions', method: 'GET', category: 'Admin' },
      { path: '/api/admin/audit-logs', method: 'GET', category: 'Admin' },
      { path: '/api/admin/settings/email', method: 'GET', category: 'Settings' },
      { path: '/api/release-notes/latest', method: 'GET', category: 'Content' },
    ];

    const results: EndpointStatus[] = [];
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001';

    // Check each endpoint
    for (const endpoint of endpoints) {
      const start = Date.now();
      let status: 'operational' | 'degraded' | 'down' = 'operational';
      let responseTime = 0;

      try {
        const response = await fetch(`${baseUrl}${endpoint.path}`, {
          method: endpoint.method,
          headers: {
            'Cookie': `access_token=${token}`,
          },
          signal: AbortSignal.timeout(5000), // 5 second timeout
        });

        responseTime = Date.now() - start;

        // Determine status based on response
        if (response.status >= 500) {
          status = 'down';
        } else if (response.status === 401 || response.status === 403) {
          // Auth endpoints might return 401/403, which is expected behavior
          status = 'operational';
        } else if (responseTime > 2000) {
          status = 'degraded';
        } else if (response.status >= 400) {
          status = 'degraded';
        }
      } catch (error) {
        status = 'down';
        responseTime = Date.now() - start;
      }

      results.push({
        endpoint: endpoint.path,
        method: endpoint.method,
        status,
        responseTime,
        lastChecked: new Date().toISOString(),
      });
    }

    // Calculate overall statistics
    const operational = results.filter(r => r.status === 'operational').length;
    const degraded = results.filter(r => r.status === 'degraded').length;
    const down = results.filter(r => r.status === 'down').length;
    const avgResponseTime = results.reduce((sum, r) => sum + r.responseTime, 0) / results.length;

    const overallStatus = 
      down > 0 ? 'critical' :
      degraded > 0 ? 'warning' :
      'healthy';

    return NextResponse.json({
      success: true,
      data: {
        overall: {
          status: overallStatus,
          operational,
          degraded,
          down,
          total: results.length,
          avgResponseTime: Math.round(avgResponseTime),
        },
        endpoints: results,
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error('Error checking API status:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to check API status' },
      { status: 500 }
    );
  }
}
