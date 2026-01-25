import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const releaseNotes = await prisma.releaseNote.findMany({
      where: {
        isPublished: true,
      },
      orderBy: {
        releaseDate: "desc",
      },
      take: 10,
    });

    return NextResponse.json(releaseNotes);
  } catch (error) {
    console.error("Error fetching release notes:", error);
    return NextResponse.json(
      { error: "Failed to fetch release notes" },
      { status: 500 }
    );
  }
}
