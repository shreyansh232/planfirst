"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import type { AuthUser } from "@/lib/api";
import Link from "next/link";

type UserMenuProps = {
  user: AuthUser | null;
  loading?: boolean;
  onSignOut: () => void;
};

function getInitials(name?: string | null, email?: string | null): string {
  const source = name || email || "";
  if (!source) return "U";
  const parts = source.split(" ").filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

export function UserMenu({ user, loading, onSignOut }: UserMenuProps) {
  const [open, setOpen] = useState(false);
  const [imageError, setImageError] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (!wrapperRef.current) return;
      if (!wrapperRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (!user) {
    return (
      <Link href="/login">
        <Button
          className="text-sm font-medium bg-primary text-primary-foreground px-5 py-2 rounded-full hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-100"
          disabled={loading}
        >
          Sign in
        </Button>
      </Link>
    );
  }

  const initials = getInitials(user.name, user.email);
  const showImage = !!user.picture_url && !imageError;

  return (
    <div className="relative flex justify-center" ref={wrapperRef}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="size-10 rounded-full border border-black/10 overflow-hidden bg-white flex items-center justify-center text-xs font-semibold text-black shrink-0 shadow-sm hover:shadow-md transition-all cursor-pointer"
      >
        {showImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.picture_url ?? ""}
            alt={user.name || user.email}
            className="h-full w-full object-cover"
            referrerPolicy="no-referrer"
            onError={() => setImageError(true)}
          />
        ) : (
          initials
        )}
      </button>
      {open && (
        <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-24 rounded-xl border border-border/50 bg-white shadow-lg overflow-hidden">
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              onSignOut();
            }}
            className="w-full px-2 py-2.5 text-left text-sm text-foreground hover:bg-muted transition-colors flex items-center gap-2 cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
