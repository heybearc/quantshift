import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const config = await prisma.botConfig.findUnique({
      where: { name: 'equity-bot' },
    });

    if (!config) {
      return NextResponse.json(
        { error: 'Bot configuration not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      name: config.name,
      strategy: config.strategy,
      symbols: config.symbols,
      enabled: config.enabled,
      paperTrading: config.paperTrading,
      riskPerTrade: config.riskPerTrade,
      maxPositionSize: config.maxPositionSize,
      maxPortfolioHeat: config.maxPortfolioHeat,
      simulatedCapital: config.simulatedCapital,
    });
  } catch (error) {
    console.error('Get bot config error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user || user.role !== 'ADMIN') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const data = await request.json();

    const config = await prisma.botConfig.update({
      where: { name: 'equity-bot' },
      data: {
        strategy: data.strategy,
        symbols: data.symbols,
        enabled: data.enabled,
        paperTrading: data.paperTrading,
        riskPerTrade: data.riskPerTrade,
        maxPositionSize: data.maxPositionSize,
        maxPortfolioHeat: data.maxPortfolioHeat,
        simulatedCapital: data.simulatedCapital,
      },
    });

    return NextResponse.json({
      message: 'Configuration updated successfully',
      config,
    });
  } catch (error) {
    console.error('Update bot config error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
