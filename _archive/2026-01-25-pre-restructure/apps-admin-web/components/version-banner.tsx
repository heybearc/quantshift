'use client';

import { useState, useEffect } from 'react';
import { X, Sparkles } from 'lucide-react';
import Link from 'next/link';

interface LatestRelease {
  version: string;
  title: string;
  description: string;
  releaseDate: string;
}

export function VersionBanner() {
  const [latestRelease, setLatestRelease] = useState<LatestRelease | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check if banner was already dismissed for this version
    const dismissedVersion = localStorage.getItem('dismissedReleaseVersion');
    
    // Fetch latest release note
    const fetchLatestRelease = async () => {
      try {
        const response = await fetch('/api/release-notes/latest', {
          credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success && data.data) {
          const release = data.data;
          // Only show if this version hasn't been dismissed
          if (dismissedVersion !== release.version) {
            setLatestRelease({
              version: release.version,
              title: release.title,
              description: release.description,
              releaseDate: release.releaseDate,
            });
          } else {
            setDismissed(true);
          }
        }
      } catch (error) {
        console.error('Error fetching latest release:', error);
      }
    };

    fetchLatestRelease();
  }, []);

  const handleDismiss = () => {
    if (latestRelease) {
      localStorage.setItem('dismissedReleaseVersion', latestRelease.version);
      setDismissed(true);
    }
  };

  if (!latestRelease || dismissed) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            <Sparkles className="h-5 w-5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold">New Release: v{latestRelease.version}</span>
                <span className="hidden sm:inline">•</span>
                <span className="text-blue-100">{latestRelease.title}</span>
              </div>
              <p className="text-sm text-blue-100 mt-1 line-clamp-1">
                {latestRelease.description}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 ml-4">
            <Link
              href="/release-notes"
              className="text-sm font-medium hover:text-blue-100 transition-colors whitespace-nowrap"
            >
              View Details →
            </Link>
            <button
              onClick={handleDismiss}
              className="p-1 hover:bg-white/10 rounded transition-colors"
              aria-label="Dismiss banner"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
