import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

/**
 * Industry-standard session management utilities
 */

/**
 * Clean up expired sessions
 * Should be run periodically (e.g., daily via cron job)
 */
export async function cleanupExpiredSessions() {
  const result = await prisma.session.deleteMany({
    where: {
      expiresAt: {
        lt: new Date()
      }
    }
  });
  
  console.log(`[Session Cleanup] Removed ${result.count} expired sessions`);
  return result.count;
}

/**
 * Clean up inactive sessions (no activity for 30+ days)
 */
export async function cleanupInactiveSessions() {
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
  
  const result = await prisma.session.deleteMany({
    where: {
      lastActivityAt: {
        lt: thirtyDaysAgo
      }
    }
  });
  
  console.log(`[Session Cleanup] Removed ${result.count} inactive sessions (30+ days)`);
  return result.count;
}

/**
 * Enforce max concurrent sessions per user
 * Keeps only the N most recent sessions, removes older ones
 */
export async function enforceMaxSessionsPerUser(userId: string, maxSessions: number = 3) {
  // Get all active sessions for user, ordered by most recent first
  const sessions = await prisma.session.findMany({
    where: {
      userId,
      expiresAt: {
        gt: new Date()
      }
    },
    orderBy: {
      lastActivityAt: 'desc'
    }
  });

  // If user has more than max allowed, delete the oldest ones
  if (sessions.length > maxSessions) {
    const sessionsToDelete = sessions.slice(maxSessions);
    const sessionIds = sessionsToDelete.map(s => s.id);
    
    const result = await prisma.session.deleteMany({
      where: {
        id: {
          in: sessionIds
        }
      }
    });
    
    console.log(`[Session Cleanup] Removed ${result.count} excess sessions for user ${userId}`);
    return result.count;
  }
  
  return 0;
}

/**
 * Clean up all sessions for a specific user
 * Useful for logout all devices or security incidents
 */
export async function revokeAllUserSessions(userId: string) {
  const result = await prisma.session.deleteMany({
    where: { userId }
  });
  
  console.log(`[Session Cleanup] Revoked all ${result.count} sessions for user ${userId}`);
  return result.count;
}

/**
 * Get session statistics
 */
export async function getSessionStats() {
  const total = await prisma.session.count();
  
  const active = await prisma.session.count({
    where: {
      expiresAt: {
        gt: new Date()
      }
    }
  });
  
  const expired = total - active;
  
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
  const inactive = await prisma.session.count({
    where: {
      lastActivityAt: {
        lt: thirtyDaysAgo
      }
    }
  });
  
  return {
    total,
    active,
    expired,
    inactive
  };
}
