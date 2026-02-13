"use client";

import { useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const PING_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes (Render sleeps after 15)

/**
 * Pings the backend /health endpoint at regular intervals to prevent
 * Render's free-tier from putting the service to sleep after 15 min.
 *
 * Mount this once in the root layout or a top-level provider.
 */
export function BackendKeepAlive() {
  useEffect(() => {
    let mounted = true;

    const ping = async () => {
      if (!mounted) return;
      try {
        await fetch(`${API_BASE}/health`, { method: "GET", cache: "no-store" });
      } catch {
        // Silently ignore — the backend may be cold-starting
      }
    };

    // Ping immediately on mount, then every 10 minutes
    ping();
    const interval = setInterval(ping, PING_INTERVAL_MS);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return null; // Renders nothing
}
