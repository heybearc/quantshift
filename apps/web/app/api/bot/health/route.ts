import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET() {
  try {
    const user = await getCurrentUser();
    
    if (!user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get bot status from database
    const botStatuses = await prisma.$queryRaw<any[]>`
      SELECT 
        bot_name,
        status,
        last_heartbeat,
        account_equity,
        account_cash,
        buying_power,
        portfolio_value,
        unrealized_pl,
        realized_pl,
        error_message,
        created_at,
        updated_at
      FROM bot_status
      ORDER BY bot_name
    `;

    // Calculate uptime and errors for each bot
    const bots = await Promise.all(botStatuses.map(async (bot) => {
      const now = new Date();
      const lastHeartbeat = bot.last_heartbeat ? new Date(bot.last_heartbeat) : null;
      const createdAt = new Date(bot.created_at);
      
      // Calculate uptime in seconds
      const uptime = lastHeartbeat 
        ? Math.floor((now.getTime() - createdAt.getTime()) / 1000)
        : 0;

      // Get error count in last 24 hours from logs (if available)
      // For now, we'll use a simple check based on error_message
      const errors24h = bot.error_message ? 1 : 0;

      // Get active strategies count
      const activeStrategies = await prisma.$queryRaw<any[]>`
        SELECT COUNT(DISTINCT strategy) as count
        FROM trades
        WHERE bot_name = ${bot.bot_name}
        AND created_at > NOW() - INTERVAL '7 days'
      `;

      const strategyCount = activeStrategies[0]?.count || 7; // Default to 7 strategies

      // Get current regime (from Redis or database)
      const currentRegime = 'BULL'; // TODO: Fetch from Redis or regime_history table

      // Calculate portfolio heat (risk as % of portfolio)
      const portfolioHeat = bot.portfolio_value > 0
        ? Math.abs(bot.unrealized_pl) / bot.portfolio_value
        : 0;

      return {
        botName: bot.bot_name,
        lastHeartbeat: bot.last_heartbeat,
        uptime,
        errors24h,
        currentRegime,
        activeStrategies: strategyCount,
        portfolioHeat,
        status: bot.status,
        accountEquity: bot.account_equity,
        portfolioValue: bot.portfolio_value,
        unrealizedPl: bot.unrealized_pl,
        realizedPl: bot.realized_pl,
      };
    }));

    return NextResponse.json({
      bots,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Bot health API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch bot health' },
      { status: 500 }
    );
  }
}
