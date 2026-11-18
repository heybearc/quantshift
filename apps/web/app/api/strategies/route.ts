import { NextRequest, NextResponse } from "next/server";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { cleanText } from "@/lib/user-desk";

export async function GET() {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const ideas = await prisma.strategyIdea.findMany({
    orderBy: { createdAt: "desc" },
    take: 50,
    include: {
      author: { select: { fullName: true, email: true } },
      comments: {
        orderBy: { createdAt: "asc" },
        include: { author: { select: { fullName: true, email: true } } },
      },
    },
  });
  return NextResponse.json({
    ideas: ideas.map((idea) => ({
      id: idea.id,
      title: idea.title,
      body: idea.body,
      source: idea.source,
      status: idea.status === "published" ? "published" : "suggestion",
      authorId: idea.authorId,
      createdAt: idea.createdAt,
      author: idea.author.fullName || idea.author.email,
      comments: idea.comments.map((comment) => ({
        id: comment.id,
        body: comment.body,
        createdAt: comment.createdAt,
        author: comment.author.fullName || comment.author.email,
      })),
    })),
  });
}

export async function POST(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const body = await request.json().catch(() => ({}));
  const title = cleanText(body.title, 120);
  const text = cleanText(body.body, 2000);
  const source = body.source === "engine" ? "engine" : "human";
  if (!title || !text) {
    return NextResponse.json({ error: "A suggestion needs a title and the pattern you saw." }, { status: 400 });
  }
  const idea = await prisma.strategyIdea.create({
    data: { authorId: user.id, title, body: text, source, status: "suggestion" },
  });
  return NextResponse.json({ id: idea.id, status: "suggestion" });
}
