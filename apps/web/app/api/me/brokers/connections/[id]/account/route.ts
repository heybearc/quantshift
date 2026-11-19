import { NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { BrokerError } from "@/lib/broker-gateway";
import { refreshConnection } from "@/lib/broker-store";

export async function GET(_request: Request, { params }: { params: { id: string } }) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  try {
    return NextResponse.json({ connection: await refreshConnection(user.id, params.id) });
  } catch (error) {
    const status = error instanceof BrokerError ? error.status : 500;
    const message = error instanceof Error ? error.message : "The balance could not be read.";
    return NextResponse.json({ error: message }, { status });
  }
}
