import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { BrokerError } from "@/lib/broker-gateway";
import { prisma } from "@/lib/prisma";
import { ensureBrokerTables, submitBrokerRequest } from "@/lib/broker-store";

export async function GET(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  await ensureBrokerTables();
  const queue = request.nextUrl.searchParams.get("scope") === "queue";
  const staff = user.role === "ADMIN" || user.role === "SUPER_ADMIN";
  if (queue && !staff) return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
  const requests = queue
    ? await prisma.brokerRequest.findMany({
        where: { status: "submitted" },
        orderBy: { createdAt: "desc" },
        include: { user: { select: { email: true } } },
      })
    : await prisma.brokerRequest.findMany({
        where: { userId: user.id },
        orderBy: { createdAt: "desc" },
      });
  return NextResponse.json({ requests });
}

export async function POST(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  if (body.apiKey || body.apiSecret || body.secret || body.password) {
    return NextResponse.json({ error: "A request does not take API keys." }, { status: 400 });
  }
  try {
    const saved = await submitBrokerRequest(user.id, body);
    return NextResponse.json({ request: saved });
  } catch (error) {
    const status = error instanceof BrokerError ? error.status : 500;
    const message = error instanceof Error ? error.message : "The broker could not be submitted.";
    return NextResponse.json({ error: message }, { status });
  }
}
