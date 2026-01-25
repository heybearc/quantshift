import { prisma } from './prisma';
import { queueEmail } from './email-queue';

interface HealthCheckResult {
  service: string;
  status: 'healthy' | 'degraded' | 'down';
  responseTime?: number;
  error?: string;
}

export async function checkHealthAndAlert(results: HealthCheckResult[]) {
  const failedServices = results.filter(r => r.status === 'down' || r.status === 'degraded');
  
  if (failedServices.length === 0) {
    return;
  }

  // Get admin users to notify
  const admins = await prisma.user.findMany({
    where: {
      role: 'ADMIN',
      isActive: true,
      emailVerified: true,
    },
    select: {
      email: true,
      fullName: true,
    },
  });

  const alertHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }
        .content { background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }
        .service { background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #ef4444; border-radius: 5px; }
        .service-name { font-weight: bold; color: #1f2937; margin-bottom: 5px; }
        .service-status { color: #ef4444; font-size: 14px; }
        .service-error { color: #6b7280; font-size: 12px; margin-top: 5px; }
        .footer { text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1 style="margin: 0;">⚠️ Health Alert</h1>
          <p style="margin: 10px 0 0 0; opacity: 0.9;">QuantShift Platform Health Issue Detected</p>
        </div>
        <div class="content">
          <p>The following services are experiencing issues:</p>
          ${failedServices.map(service => `
            <div class="service">
              <div class="service-name">${service.service}</div>
              <div class="service-status">Status: ${service.status.toUpperCase()}</div>
              ${service.error ? `<div class="service-error">Error: ${service.error}</div>` : ''}
              ${service.responseTime ? `<div class="service-error">Response Time: ${service.responseTime}ms</div>` : ''}
            </div>
          `).join('')}
          <p style="margin-top: 20px;">
            <strong>Time:</strong> ${new Date().toLocaleString()}<br>
            <strong>Affected Services:</strong> ${failedServices.length}
          </p>
          <p style="margin-top: 20px; padding: 15px; background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 5px;">
            <strong>Action Required:</strong> Please investigate these issues immediately to ensure platform stability.
          </p>
        </div>
        <div class="footer">
          <p>This is an automated alert from QuantShift Platform Health Monitoring</p>
        </div>
      </div>
    </body>
    </html>
  `;

  const alertText = `
QUANTSHIFT HEALTH ALERT

The following services are experiencing issues:

${failedServices.map(s => `
- ${s.service}: ${s.status.toUpperCase()}
  ${s.error ? `Error: ${s.error}` : ''}
  ${s.responseTime ? `Response Time: ${s.responseTime}ms` : ''}
`).join('\n')}

Time: ${new Date().toLocaleString()}
Affected Services: ${failedServices.length}

Action Required: Please investigate these issues immediately.
  `;

  // Queue emails to all admins
  for (const admin of admins) {
    await queueEmail({
      to: admin.email,
      subject: `⚠️ QuantShift Health Alert - ${failedServices.length} Service(s) Down`,
      htmlBody: alertHtml,
      textBody: alertText,
    });
  }

  // Log the alert
  await prisma.auditLog.create({
    data: {
      userId: 'system',
      action: 'HEALTH_ALERT_SENT',
      resourceType: 'SYSTEM',
      resourceId: 'health-monitor',
      changes: {
        failedServices: failedServices.map(s => s.service),
        adminCount: admins.length,
      },
      ipAddress: 'system',
    },
  });
}

export async function shouldSendAlert(service: string): Promise<boolean> {
  // Check if we've sent an alert for this service in the last hour
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
  
  const recentAlert = await prisma.auditLog.findFirst({
    where: {
      action: 'HEALTH_ALERT_SENT',
      resourceType: 'SYSTEM',
      createdAt: {
        gte: oneHourAgo,
      },
    },
  });

  return !recentAlert;
}
