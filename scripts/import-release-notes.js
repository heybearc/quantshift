#!/usr/bin/env node
/**
 * Import release notes from markdown files to database
 * Usage: node scripts/import-release-notes.js
 */

const fs = require('fs');
const path = require('path');
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

const releaseNotes = [
  {
    version: '1.3.0',
    file: 'v1.3.0.md',
    title: 'Environment Indicator & Infrastructure Improvements',
    date: new Date('2026-01-26')
  },
  {
    version: '1.3.1',
    file: 'v1.3.1.md',
    title: 'Bug Fixes & Performance Improvements',
    date: new Date('2026-01-28')
  },
  {
    version: '1.3.2',
    file: 'v1.3.2.md',
    title: 'Dashboard Enhancements',
    date: new Date('2026-02-01')
  },
  {
    version: '1.4.0',
    file: 'v1.4.0.md',
    title: 'Enhanced Dashboard Analytics',
    date: new Date('2026-02-18')
  },
  {
    version: '1.5.0',
    file: 'v1.5.0.md',
    title: 'AI/ML Trading Platform',
    date: new Date('2026-02-21')
  }
];

async function importReleaseNotes() {
  console.log('Starting release notes import...\n');

  for (const note of releaseNotes) {
    const filePath = path.join(__dirname, '..', 'release-notes', note.file);
    
    if (!fs.existsSync(filePath)) {
      console.log(`⚠️  Skipping ${note.version} - file not found: ${note.file}`);
      continue;
    }

    const content = fs.readFileSync(filePath, 'utf-8');

    try {
      // Check if already exists
      const existing = await prisma.releaseNotes.findUnique({
        where: { version: note.version }
      });

      if (existing) {
        console.log(`✓ ${note.version} already exists - updating...`);
        await prisma.releaseNotes.update({
          where: { version: note.version },
          data: {
            title: note.title,
            content: content,
            createdAt: note.date
          }
        });
      } else {
        console.log(`✓ Importing ${note.version}...`);
        await prisma.releaseNotes.create({
          data: {
            version: note.version,
            title: note.title,
            content: content,
            createdAt: note.date
          }
        });
      }
    } catch (error) {
      console.error(`✗ Error importing ${note.version}:`, error.message);
    }
  }

  console.log('\n✅ Release notes import complete!');
  await prisma.$disconnect();
}

importReleaseNotes().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
