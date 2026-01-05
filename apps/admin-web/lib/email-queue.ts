import { prisma } from './prisma';
import { sendEmail } from './email';

export interface QueueEmailOptions {
  to: string;
  subject: string;
  htmlBody: string;
  textBody?: string;
}

export async function queueEmail(options: QueueEmailOptions) {
  return await prisma.emailQueue.create({
    data: {
      to: options.to,
      subject: options.subject,
      htmlBody: options.htmlBody,
      textBody: options.textBody,
      status: 'PENDING',
    },
  });
}

export async function processEmailQueue() {
  const pendingEmails = await prisma.emailQueue.findMany({
    where: {
      status: 'PENDING',
      attempts: {
        lt: prisma.emailQueue.fields.maxAttempts,
      },
    },
    orderBy: {
      createdAt: 'asc',
    },
    take: 10,
  });

  for (const email of pendingEmails) {
    try {
      await prisma.emailQueue.update({
        where: { id: email.id },
        data: { status: 'SENDING' },
      });

      await sendEmail({
        to: email.to,
        subject: email.subject,
        html: email.htmlBody,
        text: email.textBody,
      });

      await prisma.emailQueue.update({
        where: { id: email.id },
        data: {
          status: 'SENT',
          sentAt: new Date(),
        },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      await prisma.emailQueue.update({
        where: { id: email.id },
        data: {
          status: email.attempts + 1 >= email.maxAttempts ? 'FAILED' : 'PENDING',
          attempts: email.attempts + 1,
          lastError: errorMessage,
        },
      });
    }
  }

  return pendingEmails.length;
}

export async function getQueueStats() {
  const [pending, sending, sent, failed] = await Promise.all([
    prisma.emailQueue.count({ where: { status: 'PENDING' } }),
    prisma.emailQueue.count({ where: { status: 'SENDING' } }),
    prisma.emailQueue.count({ where: { status: 'SENT' } }),
    prisma.emailQueue.count({ where: { status: 'FAILED' } }),
  ]);

  return { pending, sending, sent, failed };
}

export async function retryFailedEmail(emailId: string) {
  const email = await prisma.emailQueue.findUnique({
    where: { id: emailId },
  });

  if (!email || email.status !== 'FAILED') {
    throw new Error('Email not found or not in failed status');
  }

  return await prisma.emailQueue.update({
    where: { id: emailId },
    data: {
      status: 'PENDING',
      attempts: 0,
      lastError: null,
    },
  });
}

export async function cancelQueuedEmail(emailId: string) {
  return await prisma.emailQueue.update({
    where: { id: emailId },
    data: { status: 'CANCELLED' },
  });
}
