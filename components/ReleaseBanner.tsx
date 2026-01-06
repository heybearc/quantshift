'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { X } from 'lucide-react';

interface ReleaseNote {
  id: string;
  version: string;
  title: string;
  description: string;
}

export default function ReleaseBanner() {
  const [release, setRelease] = useState<ReleaseNote | null>(null);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    async function fetchLatestRelease() {
      try {
        const response = await fetch('/api/release-notes/latest', {
          credentials: 'include',
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success && data.showBanner && data.data) {
            setRelease(data.data);
            setShowBanner(true);
          }
        }
      } catch (error) {
        console.error('Error fetching latest release:', error);
      }
    }

    fetchLatestRelease();
  }, []);

  const handleDismiss = async () => {
    if (!release) return;

    try {
      await fetch('/api/release-notes/dismiss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ releaseId: release.id }),
        credentials: 'include',
      });
      setShowBanner(false);
    } catch (error) {
      console.error('Error dismissing banner:', error);
    }
  };

  if (!showBanner || !release) return null;

  return (
    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 flex-1">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                <span className="text-xl">🎉</span>
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold">
                New Release: {release.title}
              </p>
              <p className="text-sm text-blue-100 truncate">
                {release.description}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3 ml-4">
            <Link
              href="/release-notes"
              className="bg-white/10 hover:bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 border border-white/20 whitespace-nowrap"
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
