import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { normalizeSymbol } from "@/lib/user-desk";

export async function GET() {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const symbols = await prisma.symbolPreference.findMany({
    where: { userId: user.id },
  });
  symbols.sort((a, b) => {
    if (a.intent !== b.intent) return a.intent === "trade" ? -1 : 1;
    return a.symbol.localeCompare(b.symbol);
  });
  return NextResponse.json({ symbols });
}

export async function POST(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  const symbol = normalizeSymbol(String(body.symbol || ""));
  const intent = body.intent === "trade" ? "trade" : "research";
  if (!symbol) return NextResponse.json({ error: "Enter a symbol such as NVDA or BTC-USD." }, { status: 400 });

  const saved = await prisma.symbolPreference.upsert({
    where: { userId_symbol: { userId: user.id, symbol } },
    create: { userId: user.id, symbol, intent },
    update: { intent },
  });
  return NextResponse.json({ symbol: saved });
}

export async function DELETE(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const symbol = normalizeSymbol(String(new URL(request.url).searchParams.get("symbol") || ""));
  if (!symbol) return NextResponse.json({ error: "Missing symbol." }, { status: 400 });
  await prisma.symbolPreference.deleteMany({ where: { userId: user.id, symbol } });
  return NextResponse.json({ ok: true });
}
