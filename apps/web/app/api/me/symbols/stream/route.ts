import { NextRequest } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { readQuote } from "@/lib/symbol-quote";
import { normalizeSymbol } from "@/lib/user-desk";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const TICK_MS = 2000;

export async function GET(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  const symbol = normalizeSymbol(request.nextUrl.searchParams.get("symbol") || "");
  if (!symbol) return Response.json({ error: "Enter a symbol such as NVDA or BTC-USD." }, { status: 400 });

  const encoder = new TextEncoder();
  let timer: ReturnType<typeof setInterval> | undefined;
  let closed = false;
  let busy = false;

  const stream = new ReadableStream({
    start(controller) {
      const send = (payload: unknown) => {
        if (closed) return;
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
      };
      const tick = async () => {
        if (closed || busy) return;
        busy = true;
        try {
          send(await readQuote(symbol));
        } catch (error) {
          const message = error instanceof Error ? error.message : "The quote paused.";
          send({ symbol, error: message });
        } finally {
          busy = false;
        }
      };
      const stop = () => {
        if (closed) return;
        closed = true;
        if (timer) clearInterval(timer);
        try {
          controller.close();
        } catch {
          /* already closed */
        }
      };
      request.signal.addEventListener("abort", stop);
      void tick();
      timer = setInterval(() => {
        void tick();
      }, TICK_MS);
    },
    cancel() {
      closed = true;
      if (timer) clearInterval(timer);
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
