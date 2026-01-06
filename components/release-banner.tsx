'use client';

import { useState, useEffect } from 'react';
import { X, Sparkles } from 'lucide-react';
import Link from 'next/link';

interface ReleaseBannerProps {
  userId: string;
}

export function ReleaseBanner({ userId }: ReleaseBannerProps) {
  const [visible, setVisible] = useState(false);
  const [release, setRelease] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkForNewRelease();
  }, [userId]);

  const checkForNewRelease = async () => {
    try {
      const response = await fetch('/api/release-notes/latest', {
        credentials: 'include'
      });
      const data = await response.json();

      if (data.success && data.data) {
        const latestRelease = data.data;
        // Check if user has dismissed this version
        const dismissedVersion = localStorage.getItem('dismissedReleaseVersion');
        
        if (dismissedVersion !== latestRelease.version && latestRelease.isPublished) {
          setRelease(latestRelease);
          setVisible(true);
        }
      }
    } catch (error) {
      console.error('Error checking for new release:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    if (release) {
      localStorage.setItem('dismissedReleaseVersion', release.version);
      setVisible(false);
    }
  };

  if (loading || !visible || !release) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <div className="flex-shrink-0">
              <Sparkles className="h-6 w-6" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-lg font-semibold">New Release: v{release.version}</h3>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-white/20">
                  {release.type.toUpperCase()}
                </span>
              </div>
              <p className="text-sm text-blue-100">{release.title}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/release-notes"
              className="px-4 py-2 bg-white text-blue-600 rounded-lg font-medium text-sm hover:bg-blue-50 transition-colors"
            >
              View Details
            </Link>
            <button
              onClick={handleDismiss}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              aria-label="Dismiss"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
