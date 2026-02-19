"use client";

import { Suspense } from "react";
import { ChatHistorySidebar } from "@/components/layout/ChatHistorySidebar";
import { Header } from "@/components/layout/Header";
import { SidebarInset } from "@/components/ui/sidebar";
import { useProfile } from "@/lib/useProfile";

interface HomeLayoutProps {
  children: React.ReactNode;
}

export function HomeLayout({ children }: HomeLayoutProps) {
  const { user, loading, signOut } = useProfile();

  return (
    <div className="min-h-svh w-full flex bg-background">
      <Suspense fallback={<div className="w-16 bg-[#FAFAF8]" />}>
        <ChatHistorySidebar user={user} loading={loading} onSignOut={signOut} />
      </Suspense>
      <SidebarInset className="flex-1 flex flex-col">
        <Header user={user} loading={loading} onSignOut={signOut} />
        {children}
      </SidebarInset>
    </div>
  );
}
