import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { describeBot } from "@/lib/user-desk";

export async function POST(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  if (body.apiKey || body.secret || body.apiSecret || body.password) {
    return NextResponse.json(
      { error: "Credentials stay off this form. A paper login is added with each broker adapter." },
      { status: 400 }
    );
  }
  const bot = describeBot(String(body.name || body.venue || ""));
  if (!bot.venue) return NextResponse.json({ error: "Name the broker." }, { status: 400 });

  await prisma.userDesk.upsert({
    where: { userId: user.id },
    create: { userId: user.id, mode: "personal" },
    update: { mode: "personal" },
  });
  const saved = await prisma.personalBot.upsert({
    where: { userId_venue: { userId: user.id, venue: bot.venue } },
    create: { userId: user.id, ...bot },
    update: {
      displayName: bot.displayName,
      adapter: bot.adapter,
      tradingMode: "paper",
      paperAvailable: true,
      status: bot.status,
    },
  });
  return NextResponse.json({ bot: saved, mode: "personal" });
}
