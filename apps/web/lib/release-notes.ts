import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

export interface ReleaseNote {
  version: string;
  date: string;
  type: 'major' | 'minor' | 'patch';
  content: string;
  slug: string;
}

export interface ReleaseNoteFrontmatter {
  version: string;
  date: string;
  type: 'major' | 'minor' | 'patch';
}

/**
 * Get all release notes from the release-notes directory
 */
export function getAllReleaseNotes(): ReleaseNote[] {
  // In monorepo structure, release-notes is at repo root, not in apps/web
  const releaseNotesDirectory = path.join(process.cwd(), '..', '..', 'release-notes');
  
  // Check if directory exists
  if (!fs.existsSync(releaseNotesDirectory)) {
    return [];
  }

  const fileNames = fs.readdirSync(releaseNotesDirectory);
  
  const releaseNotes = fileNames
    .filter((fileName: string) => fileName.endsWith('.md') && fileName !== 'README.md')
    .map((fileName: string) => {
      try {
        const slug = fileName.replace(/\.md$/, '');
        const fullPath = path.join(releaseNotesDirectory, fileName);
        const fileContents = fs.readFileSync(fullPath, 'utf8');
        
        const { data, content } = matter(fileContents);
        const frontmatter = data as ReleaseNoteFrontmatter;
        
        return {
          version: frontmatter.version || '0.0.0',
          date: frontmatter.date || new Date().toISOString(),
          type: frontmatter.type || 'patch',
          content,
          slug,
        };
      } catch (error) {
        console.error(`Error reading release note ${fileName}:`, error);
        return null;
      }
    })
    .filter((note): note is ReleaseNote => note !== null)
    .sort((a: ReleaseNote, b: ReleaseNote) => {
      // Sort by version number (descending)
      const versionA = a.version.split('.').map(Number);
      const versionB = b.version.split('.').map(Number);
      
      for (let i = 0; i < 3; i++) {
        const partA = versionA[i] || 0;
        const partB = versionB[i] || 0;
        
        if (partA !== partB) {
          return partB - partA;
        }
      }
      return 0;
    });

  return releaseNotes;
}

/**
 * Get the latest release note
 */
export function getLatestReleaseNote(): ReleaseNote | null {
  const releaseNotes = getAllReleaseNotes();
  return releaseNotes.length > 0 ? releaseNotes[0] : null;
}

/**
 * Get a specific release note by version
 */
export function getReleaseNoteByVersion(version: string): ReleaseNote | null {
  const releaseNotes = getAllReleaseNotes();
  return releaseNotes.find(note => note.version === version) || null;
}

/**
 * Compare two version strings
 * Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal
 */
export function compareVersions(v1: string, v2: string): number {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);
  
  for (let i = 0; i < 3; i++) {
    if (parts1[i] > parts2[i]) return 1;
    if (parts1[i] < parts2[i]) return -1;
  }
  return 0;
}

/**
 * Check if a new version is available compared to last seen version
 */
export function hasNewVersion(lastSeenVersion: string | null): boolean {
  if (!lastSeenVersion) return true;
  
  const latest = getLatestReleaseNote();
  if (!latest) return false;
  
  return compareVersions(latest.version, lastSeenVersion) > 0;
}
