import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { BrokerError } from "@/lib/broker-gateway";
import { placeConnectionOrder } from "@/lib/broker-store";

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  try {
    return NextResponse.json({ order: await placeConnectionOrder(user.id, params.id, body) });
  } catch (error) {
    const status = error instanceof BrokerError ? error.status : 500;
    const message = error instanceof Error ? error.message : "The order could not be sent.";
    return NextResponse.json({ error: message }, { status });
  }
}
