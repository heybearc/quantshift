'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { X } from 'lucide-react';

interface VersionBannerProps {
  version: string;
  date: string;
  title: string;
}

export default function VersionBanner({ version, date, title }: VersionBannerProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if user has seen this version
    const lastSeenVersion = localStorage.getItem('lastSeenVersion');
    
    if (!lastSeenVersion || lastSeenVersion !== version) {
      setIsVisible(true);
    }
  }, [version]);

  const handleDismiss = () => {
    localStorage.setItem('lastSeenVersion', version);
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-r-lg shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              New Release
            </span>
            <span className="text-sm font-semibold text-blue-900">
              v{version}
            </span>
            <span className="text-xs text-blue-600">
              {new Date(date).toLocaleDateString()}
            </span>
          </div>
          <h3 className="text-sm font-medium text-blue-900 mb-2">
            {title}
          </h3>
          <Link
            href="/release-notes"
            className="text-sm text-blue-700 hover:text-blue-800 font-medium underline"
          >
            View release notes →
          </Link>
        </div>
        <button
          onClick={handleDismiss}
          className="ml-4 text-blue-400 hover:text-blue-600 transition-colors"
          aria-label="Dismiss banner"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
