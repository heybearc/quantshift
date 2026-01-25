import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, email, excludeUserId } = body;

    // Check username availability
    const existingUsername = username ? await prisma.user.findFirst({
      where: {
        username,
        ...(excludeUserId ? { id: { not: excludeUserId } } : {}),
      },
    }) : null;

    // Check email availability
    const existingEmail = email ? await prisma.user.findFirst({
      where: {
        email,
        ...(excludeUserId ? { id: { not: excludeUserId } } : {}),
      },
    }) : null;

    // Generate username suggestions if taken
    const suggestions: string[] = [];
    if (existingUsername && username) {
      const baseUsername = username.replace(/\d+$/, ''); // Remove trailing numbers
      
      // Try adding numbers
      for (let i = 1; i <= 5; i++) {
        const suggestion = `${baseUsername}${i}`;
        const exists = await prisma.user.findFirst({
          where: { username: suggestion },
        });
        if (!exists) {
          suggestions.push(suggestion);
          if (suggestions.length >= 3) break;
        }
      }

      // Try adding random numbers if still need more
      if (suggestions.length < 3) {
        for (let i = 0; i < 3; i++) {
          const randomNum = Math.floor(Math.random() * 999) + 1;
          const suggestion = `${baseUsername}${randomNum}`;
          const exists = await prisma.user.findFirst({
            where: { username: suggestion },
          });
          if (!exists && !suggestions.includes(suggestion)) {
            suggestions.push(suggestion);
            if (suggestions.length >= 3) break;
          }
        }
      }
    }

    return NextResponse.json({
      usernameAvailable: !existingUsername,
      emailAvailable: !existingEmail,
      suggestions: suggestions.slice(0, 3),
    });
  } catch (error) {
    console.error('Error checking username/email:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
