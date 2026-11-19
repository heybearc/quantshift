import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { BrokerError } from "@/lib/broker-gateway";
import { connectBroker, listConnections } from "@/lib/broker-store";

export async function GET() {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  try {
    return NextResponse.json(await listConnections(user.id));
  } catch (error) {
    const message = error instanceof Error ? error.message : "Connections could not be loaded.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  try {
    const connection = await connectBroker(user.id, body);
    return NextResponse.json({ connection });
  } catch (error) {
    const status = error instanceof BrokerError ? error.status : 500;
    const message = error instanceof Error ? error.message : "The connection could not be saved.";
    return NextResponse.json({ error: message }, { status });
  }
}
