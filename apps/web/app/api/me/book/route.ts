import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { BROKERS, PERSONAL_VENUES, describeBot } from "@/lib/user-desk";

export async function GET() {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const desk = await prisma.userDesk.findUnique({
    where: { userId: user.id },
    include: { bots: { orderBy: { venue: "asc" } } },
  });
  const trials = await prisma.strategyTrial.findMany({
    where: { userId: user.id },
    include: { idea: { select: { title: true, status: true } } },
  });
  return NextResponse.json({
    mode: desk?.mode || "house",
    bots: desk?.bots || [],
    brokers: BROKERS,
    trials: trials.filter((trial) => trial.idea.status === "published"),
  });
}

export async function PUT(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await request.json().catch(() => ({}));
  if (body.apiKey || body.secret || body.apiSecret) {
    return NextResponse.json(
      { error: "Broker keys stay off this desk. A personal bot starts only after a later paper connection." },
      { status: 400 }
    );
  }
  const mode = body.mode === "personal" ? "personal" : body.mode === "house" ? "house" : "";
  if (!mode) return NextResponse.json({ error: "Choose house or personal." }, { status: 400 });

  const desk = await prisma.userDesk.upsert({
    where: { userId: user.id },
    create: { userId: user.id, mode },
    update: { mode },
    include: { bots: true },
  });

  if (mode === "personal") {
    for (const venue of PERSONAL_VENUES) {
      const bot = describeBot(venue);
      await prisma.personalBot.upsert({
        where: { userId_venue: { userId: user.id, venue: bot.venue } },
        create: { userId: user.id, ...bot },
        update: { displayName: bot.displayName, adapter: bot.adapter, tradingMode: "paper", paperAvailable: true },
      });
    }
  }

  const bots = await prisma.personalBot.findMany({
    where: { userId: desk.userId },
    orderBy: { venue: "asc" },
  });
  return NextResponse.json({ mode, bots });
}
