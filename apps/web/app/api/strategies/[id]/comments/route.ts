import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { cleanText } from "@/lib/user-desk";

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const { id } = params;
  const idea = await prisma.strategyIdea.findUnique({ where: { id } });
  if (!idea) return NextResponse.json({ error: "That suggestion is gone." }, { status: 404 });
  const body = await request.json().catch(() => ({}));
  const text = cleanText(body.body, 1000);
  if (!text) return NextResponse.json({ error: "Write a comment." }, { status: 400 });
  const comment = await prisma.strategyComment.create({
    data: { ideaId: id, authorId: user.id, body: text },
  });
  return NextResponse.json({ id: comment.id });
}
