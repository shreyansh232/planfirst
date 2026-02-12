"use client";

import Link from "next/link";
import { UserMenu } from "./UserMenu";
import { useProfile } from "@/lib/useProfile";

interface HeaderProps {
  showUserMenu?: boolean;
  children?: React.ReactNode;
}

export function Header({ showUserMenu = true, children }: HeaderProps) {
  const { user, loading, signOut } = useProfile();

  return (
    <header className="relative z-20 max-w-6xl mx-auto flex items-center justify-between px-6 py-6 w-full">
      <Link href="/" className="font-display text-xl tracking-tight text-foreground">
        Plandrift
      </Link>
      <nav className="flex items-center gap-6">
        {showUserMenu && (
          <UserMenu user={user} loading={loading} onSignOut={signOut} />
        )}
        {children}
      </nav>
    </header>
  );
}
