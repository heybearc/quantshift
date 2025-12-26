import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🚀 Initializing QuantShift database...\n');

  // Check if admin user already exists
  const existingAdmin = await prisma.user.findUnique({
    where: { email: 'corya1992@gmail.com' },
  });

  if (existingAdmin) {
    console.log('⚠️  Admin user already exists');
    console.log(`   Email: ${existingAdmin.email}`);
    console.log(`   Role: ${existingAdmin.role}`);
    return;
  }

  // Create admin user
  const passwordHash = await bcrypt.hash('admin123', 12);

  const admin = await prisma.user.create({
    data: {
      email: 'corya1992@gmail.com',
      passwordHash,
      fullName: 'Cory Anderson',
      role: 'ADMIN',
      isActive: true,
    },
  });

  console.log('✅ Admin user created successfully!\n');
  console.log('📧 Email:', admin.email);
  console.log('🔑 Password: admin123');
  console.log('👤 Role:', admin.role);
  console.log('🆔 ID:', admin.id);
  console.log('\n⚠️  IMPORTANT: Change the password after first login!\n');
}

main()
  .catch((e) => {
    console.error('❌ Error:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
