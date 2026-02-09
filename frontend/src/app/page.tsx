"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { UserMenu } from "@/components/layout/UserMenu";
import { useProfile } from "@/lib/useProfile";

export default function Home() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const { user, loading, signOut } = useProfile();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    const encoded = encodeURIComponent(prompt.trim());
    router.push(`/trip?prompt=${encoded}`);
  };

  const handleAutoStart = () => {
    if (!prompt.trim()) return;
    const encoded = encodeURIComponent(prompt.trim());
    router.push(`/trip?prompt=${encoded}`);
  };

  return (
    <div className="min-h-screen bg-white text-black">
      <header className="max-w-6xl mx-auto flex items-center justify-between px-6 py-6">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Plandrift
        </Link>
        <nav className="flex items-center gap-3">
          <UserMenu user={user} loading={loading} onSignOut={signOut} />
        </nav>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-20">
        <div className="flex flex-col items-center text-center gap-6">
          <p className="text-sm uppercase tracking-[0.35em] text-slate-500">
            Your AI travel planner
          </p>
          <p className="text-lg text-slate-600 max-w-2xl">
            Start with a single prompt. We handle the clarifying questions,
            feasibility checks, and the full itinerary.
          </p>

            <form
              onSubmit={handleSubmit}
              className="w-full max-w-2xl rounded-3xl border border-black/10 bg-white shadow-sm p-4 sm:p-6"
            >
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleAutoStart();
                  }
                }}
                placeholder="Plan a trip to Japan for 4 people for a week with a $4k budget..."
                className="w-full h-28 resize-none text-base text-black placeholder:text-slate-400 focus:outline-none"
              />
            <div className="flex justify-end">
              <Button
                type="submit"
                className="rounded-full bg-black text-white hover:bg-black/90 px-6"
              >
                Plan →
              </Button>
            </div>
          </form>

          <div className="flex items-center gap-6 text-sm text-slate-500">
            <span>White-glove planning</span>
            <span>Budget-aware</span>
            <span>Instant iterations</span>
          </div>
        </div>
      </main>
    </div>
  );
}
