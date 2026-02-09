"use client";

import Link from "next/link";
import { getGoogleLoginUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const handleGoogleSignIn = () => {
    window.location.href = getGoogleLoginUrl();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-6">
      <Card className="w-full max-w-md border-black/10 shadow-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-black">Welcome back</CardTitle>
          <CardDescription className="text-slate-600">
            Sign in with Google to continue
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            type="button"
            className="w-full bg-black text-white hover:bg-black/90"
            onClick={handleGoogleSignIn}
          >
            <span className="flex items-center gap-2">
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                className="h-4 w-4"
              >
                <path
                  d="M12 10.2v3.9h5.5c-.2 1.4-1.7 4.1-5.5 4.1-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.8 1.5l2.6-2.5C17.5 3.6 15 2.5 12 2.5 6.9 2.5 2.8 6.6 2.8 11.7S6.9 20.9 12 20.9c6.9 0 8.6-4.8 8.6-7.2 0-.5-.1-.9-.2-1.3H12z"
                  fill="currentColor"
                />
              </svg>
              Continue with Google
            </span>
          </Button>
        </CardContent>
        <CardFooter className="flex flex-col space-y-2">
          <p className="text-xs text-slate-500 text-center">
            We only support Google sign-in for now.
          </p>
          <Link href="/" className="text-sm text-black underline-offset-4 hover:underline">
            Back to home
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
