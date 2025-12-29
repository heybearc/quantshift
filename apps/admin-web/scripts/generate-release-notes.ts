import { PrismaClient } from '@prisma/client';
import { execSync } from 'child_process';

const prisma = new PrismaClient();

async function generateReleaseNotes() {
  try {
    const packageJson = require('../package.json');
    const version = packageJson.version;

    const existing = await prisma.releaseNote.findUnique({
      where: { version },
    });

    if (existing) {
      console.log(`Release note for v${version} already exists`);
      return;
    }

    let commits: string;
    try {
      const lastTag = execSync('git describe --tags --abbrev=0 2>/dev/null || echo "HEAD~10"', {
        encoding: 'utf-8',
      }).trim();
      commits = execSync(`git log ${lastTag}..HEAD --pretty=format:"%s" --no-merges`, {
        encoding: 'utf-8',
      });
    } catch (error) {
      commits = execSync('git log HEAD~10..HEAD --pretty=format:"%s" --no-merges', {
        encoding: 'utf-8',
      });
    }

    if (!commits) {
      console.log('No new commits found');
      return;
    }

    const features: any[] = [];
    const fixes: any[] = [];
    const improvements: any[] = [];
    const other: any[] = [];

    commits.split('\n').forEach((commit) => {
      const trimmed = commit.trim();
      if (!trimmed) return;

      if (trimmed.match(/^(feat|feature):/i)) {
        features.push({ type: 'feature', description: trimmed.replace(/^(feat|feature):\s*/i, '') });
      } else if (trimmed.match(/^fix:/i)) {
        fixes.push({ type: 'fix', description: trimmed.replace(/^fix:\s*/i, '') });
      } else if (trimmed.match(/^(improve|enhancement|refactor):/i)) {
        improvements.push({ type: 'improvement', description: trimmed.replace(/^(improve|enhancement|refactor):\s*/i, '') });
      } else {
        other.push({ type: 'other', description: trimmed });
      }
    });

    const changes = [...features, ...improvements, ...fixes, ...other];
    
    let content = `# QuantShift v${version}\n\n`;
    let description = '';
    
    if (features.length > 0) {
      content += '## ✨ New Features\n\n';
      features.forEach((f) => {
        content += `- ${f.description}\n`;
      });
      content += '\n';
      description = features[0].description;
    }

    if (improvements.length > 0) {
      content += '## 🚀 Improvements\n\n';
      improvements.forEach((i) => {
        content += `- ${i.description}\n`;
      });
      content += '\n';
      if (!description) description = improvements[0].description;
    }

    if (fixes.length > 0) {
      content += '## 🐛 Bug Fixes\n\n';
      fixes.forEach((f) => {
        content += `- ${f.description}\n`;
      });
      content += '\n';
      if (!description) description = fixes[0].description;
    }

    if (other.length > 0) {
      content += '## 📝 Other Changes\n\n';
      other.forEach((o) => {
        content += `- ${o.description}\n`;
      });
      if (!description) description = other[0].description;
    }

    if (!description) {
      description = `Release v${version}`;
    }

    await prisma.releaseNote.create({
      data: {
        version,
        title: `QuantShift v${version}`,
        description: description.substring(0, 200),
        type: 'minor',
        changes: changes,
        releaseDate: new Date(),
        isPublished: true,
      },
    });

    console.log(`✅ Created release note for v${version}`);
  } catch (error) {
    console.error('Error generating release notes:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

generateReleaseNotes();
