import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  const desk = await prisma.userDesk.findUnique({ where: { userId: user.id } });
  const idea = await prisma.strategyIdea.findUnique({ where: { id: String(body.ideaId || "") } });
  if (!idea || idea.status !== "published") {
    return NextResponse.json({ error: "Publish the note before trying it." }, { status: 400 });
  }
  if (desk?.mode !== "personal" || body.acceptRisk !== true) {
    return NextResponse.json(
      { error: "A community strategy can be tried on your own paper book after you accept the risk." },
      { status: 400 }
    );
  }
  const trial = await prisma.strategyTrial.upsert({
    where: { userId_ideaId: { userId: user.id, ideaId: idea.id } },
    create: { userId: user.id, ideaId: idea.id, acceptedRisk: true },
    update: { acceptedRisk: true },
  });
  return NextResponse.json({ id: trial.id, paper: true });
}
