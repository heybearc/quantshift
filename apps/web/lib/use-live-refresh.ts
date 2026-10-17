"use client";

import { useEffect, useRef } from "react";

/** Keep a signed-in page current. Repeats on a timer and again when the tab is visible. */
export function useLiveRefresh(refresh: () => void, enabled: boolean, intervalMs = 30000) {
  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;

  useEffect(() => {
    if (!enabled) return;
    const run = () => refreshRef.current();
    const interval = setInterval(run, intervalMs);
    const onVisible = () => {
      if (document.visibilityState === "visible") run();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [enabled, intervalMs]);
}
