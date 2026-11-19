import { NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { BrokerError } from "@/lib/broker-gateway";
import { removeConnection } from "@/lib/broker-store";

export async function DELETE(_request: Request, { params }: { params: { id: string } }) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  try {
    await removeConnection(user.id, params.id);
    return NextResponse.json({ removed: true });
  } catch (error) {
    const status = error instanceof BrokerError ? error.status : 500;
    const message = error instanceof Error ? error.message : "The connection could not be removed.";
    return NextResponse.json({ error: message }, { status });
  }
}
