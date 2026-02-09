"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { setTokens } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  const queryError = useMemo(() => {
    const err = searchParams.get("error");
    const message = searchParams.get("message");
    if (!err) return null;
    return message || "Authentication failed. Please try again.";
  }, [searchParams]);

  useEffect(() => {
    if (queryError) {
      setError(queryError);
      return;
    }

    if (typeof window === "undefined") return;
    const hash = window.location.hash.replace(/^#/, "");
    const params = new URLSearchParams(hash);
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (!accessToken || !refreshToken) {
      setError("Missing tokens from Google sign-in. Please try again.");
      return;
    }

    setTokens(accessToken, refreshToken);
    router.replace("/");
  }, [queryError, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-6">
      <Card className="w-full max-w-md border-black/10 shadow-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-black">
            Finishing sign-in
          </CardTitle>
          <CardDescription className="text-slate-600">
            We&apos;re wrapping things up.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error ? (
            <>
              <p className="text-sm text-red-600">{error}</p>
              <Link href="/login">
                <Button className="w-full bg-black text-white hover:bg-black/90">
                  Try again
                </Button>
              </Link>
            </>
          ) : (
            <p className="text-sm text-slate-600">
              Redirecting to home...
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
