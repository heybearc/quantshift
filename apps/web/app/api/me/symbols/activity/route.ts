import { NextRequest } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { readActivity } from "@/lib/symbol-research";
import { normalizeSymbol } from "@/lib/user-desk";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  const symbol = normalizeSymbol(request.nextUrl.searchParams.get("symbol") || "");
  if (!symbol) return Response.json({ error: "Enter a symbol such as NVDA or BTC-USD." }, { status: 400 });
  try {
    return Response.json({ symbol, closes: await readActivity(symbol) });
  } catch {
    return Response.json({ symbol, closes: [] });
  }
}
