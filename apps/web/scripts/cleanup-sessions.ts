#!/usr/bin/env tsx
/**
 * Session cleanup script
 * Run this periodically via cron job or manually to clean up stale sessions
 * 
 * Usage:
 *   npm run cleanup:sessions
 *   or
 *   tsx scripts/cleanup-sessions.ts
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function cleanupSessions() {
  console.log('🧹 Starting session cleanup...\n');

  try {
    // 1. Clean up expired sessions
    console.log('1️⃣ Cleaning up expired sessions...');
    const expiredResult = await prisma.session.deleteMany({
      where: {
        expiresAt: {
          lt: new Date()
        }
      }
    });
    console.log(`   ✅ Removed ${expiredResult.count} expired sessions\n`);

    // 2. Clean up inactive sessions (no activity for 30+ days)
    console.log('2️⃣ Cleaning up inactive sessions (30+ days)...');
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const inactiveResult = await prisma.session.deleteMany({
      where: {
        lastActivityAt: {
          lt: thirtyDaysAgo
        }
      }
    });
    console.log(`   ✅ Removed ${inactiveResult.count} inactive sessions\n`);

    // 3. Get session statistics
    console.log('3️⃣ Session statistics:');
    const total = await prisma.session.count();
    const active = await prisma.session.count({
      where: {
        expiresAt: {
          gt: new Date()
        }
      }
    });
    
    console.log(`   📊 Total sessions: ${total}`);
    console.log(`   ✅ Active sessions: ${active}`);
    console.log(`   ❌ Expired sessions: ${total - active}\n`);

    // 4. Check for users with excessive sessions
    console.log('4️⃣ Checking for users with excessive sessions...');
    const usersWithManySessions = await prisma.session.groupBy({
      by: ['userId'],
      _count: {
        id: true
      },
      where: {
        expiresAt: {
          gt: new Date()
        }
      },
      having: {
        id: {
          _count: {
            gt: 5
          }
        }
      }
    });

    if (usersWithManySessions.length > 0) {
      console.log(`   ⚠️  Found ${usersWithManySessions.length} users with 5+ active sessions:`);
      for (const user of usersWithManySessions) {
        console.log(`      User ${user.userId}: ${user._count.id} sessions`);
      }
      console.log('   💡 Consider enforcing max concurrent sessions per user\n');
    } else {
      console.log(`   ✅ No users with excessive sessions\n`);
    }

    console.log('✨ Session cleanup complete!');
  } catch (error) {
    console.error('❌ Error during session cleanup:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

cleanupSessions();
