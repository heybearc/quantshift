import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding database...');

  // Hash passwords
  const quantAdminPassword = await bcrypt.hash('QuantAdmin2024!', 10);
  const coryPassword = await bcrypt.hash('admin123', 10);

  // Create QuantAdmin default admin user
  const quantAdmin = await prisma.user.upsert({
    where: { email: 'admin@quantshift.local' },
    update: {
      username: 'quantadmin',
      passwordHash: quantAdminPassword,
      fullName: 'QuantShift Administrator',
      role: 'ADMIN',
      isActive: true,
    },
    create: {
      username: 'quantadmin',
      email: 'admin@quantshift.local',
      passwordHash: quantAdminPassword,
      fullName: 'QuantShift Administrator',
      role: 'ADMIN',
      isActive: true,
    },
  });

  console.log('✅ Created QuantAdmin user:', quantAdmin.username);

  // Update/Create Cory Allen user
  const coryUser = await prisma.user.upsert({
    where: { email: 'corya1992@gmail.com' },
    update: {
      username: 'coryallen',
      fullName: 'Cory Allen',
      passwordHash: coryPassword,
      role: 'ADMIN',
      isActive: true,
    },
    create: {
      username: 'coryallen',
      email: 'corya1992@gmail.com',
      passwordHash: coryPassword,
      fullName: 'Cory Allen',
      role: 'ADMIN',
      isActive: true,
    },
  });

  console.log('✅ Created/Updated Cory Allen user:', coryUser.username);

  // Create platform settings
  const settings = [
    { key: 'smtp_host', value: '', description: 'SMTP server hostname', category: 'EMAIL' },
    { key: 'smtp_port', value: '587', description: 'SMTP server port', category: 'EMAIL' },
    { key: 'smtp_username', value: '', description: 'SMTP username', category: 'EMAIL' },
    { key: 'smtp_password', value: '', description: 'SMTP password (encrypted)', category: 'EMAIL' },
    { key: 'smtp_from_email', value: '', description: 'From email address', category: 'EMAIL' },
    { key: 'smtp_from_name', value: 'QuantShift Platform', description: 'From name', category: 'EMAIL' },
    { key: 'smtp_use_tls', value: 'true', description: 'Use TLS encryption', category: 'EMAIL' },
    { key: 'platform_name', value: 'QuantShift', description: 'Platform name', category: 'GENERAL' },
    { key: 'platform_version', value: '1.0.0', description: 'Current platform version', category: 'GENERAL' },
    { key: 'enable_notifications', value: 'true', description: 'Enable email notifications', category: 'NOTIFICATIONS' },
    { key: 'enable_trade_alerts', value: 'true', description: 'Enable trade alert emails', category: 'NOTIFICATIONS' },
    { key: 'enable_daily_summary', value: 'true', description: 'Enable daily summary emails', category: 'NOTIFICATIONS' },
  ];

  for (const setting of settings) {
    await prisma.platformSettings.upsert({
      where: { key: setting.key },
      update: setting,
      create: setting,
    });
  }

  console.log('✅ Created platform settings');

  // Create initial release note
  const releaseNote = await prisma.releaseNote.upsert({
    where: { version: '1.0.0' },
    update: {
      title: 'QuantShift Platform Launch',
      description: 'Initial release of the QuantShift quantum trading intelligence platform with comprehensive admin controls and real-time trading analytics.',
      changes: [
        { type: 'feature', description: 'Username and email-based authentication system' },
        { type: 'feature', description: 'Trading bot configuration and monitoring' },
        { type: 'feature', description: 'Real-time trade and position tracking' },
        { type: 'feature', description: 'Performance analytics dashboard' },
        { type: 'feature', description: 'Email notification system with SMTP configuration' },
        { type: 'feature', description: 'Admin control center with user management' },
        { type: 'feature', description: 'Release notes and version tracking system' },
        { type: 'feature', description: 'Platform settings management' },
      ],
      releaseDate: new Date(),
      isPublished: true,
    },
    create: {
      version: '1.0.0',
      title: 'QuantShift Platform Launch',
      description: 'Initial release of the QuantShift quantum trading intelligence platform with comprehensive admin controls and real-time trading analytics.',
      changes: [
        { type: 'feature', description: 'Username and email-based authentication system' },
        { type: 'feature', description: 'Trading bot configuration and monitoring' },
        { type: 'feature', description: 'Real-time trade and position tracking' },
        { type: 'feature', description: 'Performance analytics dashboard' },
        { type: 'feature', description: 'Email notification system with SMTP configuration' },
        { type: 'feature', description: 'Admin control center with user management' },
        { type: 'feature', description: 'Release notes and version tracking system' },
        { type: 'feature', description: 'Platform settings management' },
      ],
      releaseDate: new Date(),
      isPublished: true,
    },
  });

  console.log('✅ Created release note:', releaseNote.version);

  console.log('\n🎉 Database seeding completed!');
  console.log('\n📝 Default Admin Credentials:');
  console.log('   Username: quantadmin');
  console.log('   Password: QuantAdmin2024!');
  console.log('\n📝 Cory Allen Credentials:');
  console.log('   Username: coryallen');
  console.log('   Email: corya1992@gmail.com');
  console.log('   Password: admin123');
}

main()
  .catch((e) => {
    console.error('❌ Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
