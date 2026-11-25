import { NextRequest } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { readResearch } from "@/lib/symbol-research";
import { normalizeSymbol } from "@/lib/user-desk";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  const symbol = normalizeSymbol(request.nextUrl.searchParams.get("symbol") || "");
  if (!symbol) return Response.json({ error: "Enter a symbol such as NVDA or BTC-USD." }, { status: 400 });
  try {
    return Response.json({ research: await readResearch(symbol) });
  } catch (error) {
    const message = error instanceof Error ? error.message : "The research could not be loaded.";
    return Response.json({ error: message }, { status: 502 });
  }
}
