#!/usr/bin/env node
/**
 * Import release notes to database with proper schema
 * Usage: node scripts/import-release-notes-v2.js
 */

const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

const releaseNotes = [
  {
    version: '1.3.0',
    title: 'Environment Indicator & Infrastructure Improvements',
    description: 'New environment indicator showing LIVE/STANDBY status, enhanced deployment system, and improved testing coverage.',
    releaseDate: new Date('2026-01-29'),
    type: 'minor',
    changes: {
      features: [
        'Environment indicator with colored dot (Green=LIVE, Blue=STANDBY)',
        'Hover tooltip showing server details (name, status, container, IP)',
        'Enhanced deployment system for zero-downtime updates'
      ],
      improvements: [
        'Page title consistency across application',
        'Enhanced test coverage for reliability',
        'Better deployment infrastructure'
      ],
      bugFixes: [
        'Fixed page titles for better clarity',
        'Improved navigation consistency'
      ]
    }
  },
  {
    version: '1.3.1',
    title: 'Bug Fixes & Performance Improvements',
    description: 'Minor bug fixes and performance enhancements for improved stability.',
    releaseDate: new Date('2026-01-28'),
    type: 'patch',
    changes: {
      bugFixes: [
        'Fixed environment indicator display issues',
        'Improved session handling'
      ],
      improvements: [
        'Performance optimizations',
        'Enhanced error handling'
      ]
    }
  },
  {
    version: '1.3.2',
    title: 'Dashboard Enhancements',
    description: 'Improved dashboard layout and user experience enhancements.',
    releaseDate: new Date('2026-02-01'),
    type: 'patch',
    changes: {
      improvements: [
        'Enhanced dashboard layout',
        'Improved data visualization',
        'Better responsive design'
      ],
      bugFixes: [
        'Fixed dashboard loading issues',
        'Improved chart rendering'
      ]
    }
  },
  {
    version: '1.4.0',
    title: 'Enhanced Dashboard Analytics',
    description: 'Major dashboard improvements with advanced analytics, real-time updates, and enhanced bot monitoring.',
    releaseDate: new Date('2026-02-18'),
    type: 'minor',
    changes: {
      features: [
        'Advanced analytics dashboard with real-time metrics',
        'Enhanced bot status monitoring',
        'Improved performance charts',
        'Real-time position tracking',
        'Advanced trade history filtering'
      ],
      improvements: [
        'Faster dashboard loading',
        'Better data refresh rates',
        'Enhanced mobile responsiveness',
        'Improved chart interactions'
      ],
      bugFixes: [
        'Fixed data synchronization issues',
        'Improved error handling',
        'Better session management'
      ]
    }
  },
  {
    version: '1.5.0',
    title: 'AI/ML Trading Platform',
    description: 'Revolutionary AI-powered trading with ML market regime analysis, sentiment analysis, and deep reinforcement learning for position sizing.',
    releaseDate: new Date('2026-02-21'),
    type: 'minor',
    changes: {
      features: [
        'ML-powered market regime analysis (91.7% accuracy)',
        'Real-time regime detection (Bull, Bear, Choppy, Range, Crisis)',
        'FinBERT sentiment analysis for trade filtering',
        'Deep RL agent for intelligent position sizing',
        'ML Regime Analysis dashboard with dark theme',
        'Automated weekly model retraining',
        'Daily online learning for RL agent'
      ],
      improvements: [
        'Strategy allocation based on market regime',
        'Sentiment-aware trade filtering',
        'AI-optimized position sizing',
        'Enhanced risk management through ML insights'
      ],
      technical: [
        'RandomForest classifier integration',
        'PPO reinforcement learning implementation',
        'Custom trading environment for AI training',
        'Automated ML pipeline'
      ]
    }
  }
];

async function importReleaseNotes() {
  console.log('Starting release notes import...\n');

  for (const note of releaseNotes) {
    try {
      const existing = await prisma.releaseNotes.findUnique({
        where: { version: note.version }
      });

      if (existing) {
        console.log(`✓ Updating ${note.version}...`);
        await prisma.releaseNotes.update({
          where: { version: note.version },
          data: {
            title: note.title,
            description: note.description,
            changes: note.changes,
            releaseDate: note.releaseDate,
            type: note.type,
            isPublished: true,
            updatedAt: new Date()
          }
        });
      } else {
        console.log(`✓ Creating ${note.version}...`);
        await prisma.releaseNotes.create({
          data: {
            version: note.version,
            title: note.title,
            description: note.description,
            changes: note.changes,
            releaseDate: note.releaseDate,
            type: note.type,
            isPublished: true
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
