import { prisma } from '@/lib/prisma';

export async function registrationDenialMessage(email: string, username: string): Promise<string | null> {
  const normalizedEmail = email.toLowerCase();
  const normalizedUsername = username.toLowerCase();
  const denied = await prisma.registrationDenial.findFirst({
    where: {
      OR: [
        { email: normalizedEmail },
        { username: normalizedUsername },
      ],
    },
  });
  if (!denied) return null;
  if (denied.email === normalizedEmail) {
    return 'This email address was previously denied and cannot be used to register.';
  }
  return 'This username was previously denied and cannot be used to register.';
}
