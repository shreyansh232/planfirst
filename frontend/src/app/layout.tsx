import type { Metadata } from "next";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider } from "@/components/ui/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Planfirst",
  description: "Plan better trips, faster.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <TooltipProvider>
          <SidebarProvider defaultOpen={false}>
            {children}
          </SidebarProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
