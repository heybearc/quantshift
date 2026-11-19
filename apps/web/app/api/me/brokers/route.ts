import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { catalogBroker } from "@/lib/broker-catalog";
import { BrokerError } from "@/lib/broker-gateway";
import { submitBrokerRequest } from "@/lib/broker-store";
import { describeBot, venueSlug } from "@/lib/user-desk";

export async function POST(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  if (body.apiKey || body.secret || body.apiSecret || body.password) {
    return NextResponse.json(
      { error: "Store the key on the broker connection. This step only adds a paper slot or a review request." },
      { status: 400 }
    );
  }
  const named = String(body.name || body.venue || "");
  const known = catalogBroker(named) || catalogBroker(venueSlug(named));
  if (!known) {
    try {
      const submitted = await submitBrokerRequest(user.id, {
        name: named,
        website: body.website,
        docsUrl: body.docsUrl,
        notes: body.notes || "Submitted from the broker desk.",
      });
      return NextResponse.json({ request: submitted, mode: "personal" });
    } catch (error) {
      const status = error instanceof BrokerError ? error.status : 400;
      const message = error instanceof Error ? error.message : "The broker could not be submitted.";
      return NextResponse.json({ error: message }, { status });
    }
  }
  const bot = describeBot(known.id);
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
