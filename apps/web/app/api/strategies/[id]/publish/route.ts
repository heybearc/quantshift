import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(_request: NextRequest, { params }: { params: { id: string } }) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const idea = await prisma.strategyIdea.findUnique({ where: { id: params.id } });
  if (!idea || idea.authorId !== user.id) {
    return NextResponse.json({ error: "Only the author can publish this note." }, { status: 403 });
  }
  await prisma.strategyIdea.update({
    where: { id: idea.id },
    data: { status: "published" },
  });
  return NextResponse.json({ status: "published" });
}
