"use client";

import { useState, useEffect } from "react";
import { X, Sparkles } from "lucide-react";
import Link from "next/link";

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
      const response = await fetch("/api/release-notes/latest", {
        credentials: "include",
      });
      const data = await response.json();

      if (data.success && data.data) {
        const latestRelease = data.data;
        const dismissedVersion = localStorage.getItem("dismissedReleaseVersion");

        if (dismissedVersion !== latestRelease.version && latestRelease.isPublished) {
          setRelease(latestRelease);
          setVisible(true);
        }
      }
    } catch (error) {
      console.error("Error checking for new release:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    if (release) {
      localStorage.setItem("dismissedReleaseVersion", release.version);
      setVisible(false);
    }
  };

  if (loading || !visible || !release) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 border-b border-blue-500/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3 text-white">
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 flex-shrink-0" />
            <div className="flex items-center gap-2 text-sm">
              <span className="font-semibold">New Release: v{release.version}</span>
              <span className="hidden sm:inline">•</span>
              <span className="hidden sm:inline">{release.title}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/release-notes"
              className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded text-xs font-medium transition-colors"
            >
              View Details
            </Link>
            <button
              onClick={handleDismiss}
              className="p-1 hover:bg-white/10 rounded transition-colors"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
