"use client";

import { useEffect, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { setTokens } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

export function AuthCallbackClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const error = useMemo(() => {
    const err = searchParams.get("error");
    const message = searchParams.get("message");
    if (!err) return null;
    return message || "Authentication failed. Please try again.";
  }, [searchParams]);

  useEffect(() => {
    if (error) return;

    if (typeof window === "undefined") return;
    const hash = window.location.hash.replace(/^#/, "");
    const params = new URLSearchParams(hash);
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (!accessToken || !refreshToken) {
      return;
    }

    setTokens(accessToken, refreshToken);
    router.replace("/");
  }, [error, router]);

  // Error state - show centered error message
  if (error) {
    return (
      <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#FAFAF8] px-6">
        <div className="text-center space-y-4 max-w-sm">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto">
            <span className="text-red-600 text-xl">!</span>
          </div>
          <h1 className="text-xl font-semibold text-slate-900">Sign in failed</h1>
          <p className="text-sm text-slate-600">{error}</p>
          <Link href="/login">
            <Button className="mt-4 bg-slate-900 text-white hover:bg-slate-800">
              Try again
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // Loading state - minimal centered spinner
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#FAFAF8]">
      <Loader2 className="w-8 h-8 text-slate-400 animate-spin" />
    </div>
  );
}
