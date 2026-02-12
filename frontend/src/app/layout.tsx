import type { Metadata } from "next";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider } from "@/components/ui/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Planfirst",
  description: "Plan better trips, faster.",
  openGraph: {
    title: "Planfirst",
    description: "Plan better trips, faster.",
    type: "website",
    siteName: "Planfirst",
    url: "https://planfirst.vercel.app",
    images: [
      {
        url: "https://planfirst.vercel.app/og.png",
        width: 1200,
        height: 630,
        alt: "Planfirst - AI That Plans Before You Do",
        type: "image/png",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: "@planfirst",
    title: "Planfirst",
    description: "Plan better trips, faster.",
    images: ["https://planfirst.vercel.app/og.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
  metadataBase: new URL("https://planfirst.vercel.app"),
  alternates: {
    canonical: "/",
  },
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
