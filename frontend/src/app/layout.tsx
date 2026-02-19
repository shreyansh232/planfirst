import type { Metadata } from "next";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Analytics } from '@vercel/analytics/next';
import "./globals.css";

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Planfirst",
  "description": "AI-powered travel planner that creates personalized itineraries in seconds",
  "url": "https://planfirstai.com",
  "applicationCategory": "TravelApplication",
  "operatingSystem": "Web Browser",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "creator": {
    "@type": "Organization",
    "name": "Planfirst",
    "url": "https://planfirstai.com"
  },
  "featureList": [
    "AI-powered trip planning",
    "Personalized itineraries",
    "Budget-aware recommendations",
    "Multi-language support"
  ]
};

export const metadata: Metadata = {
  title: {
    default: "Planfirst - AI-Powered Travel Planner",
    template: "%s | Planfirst",
  },
  description: "Plan your perfect trip in seconds. Describe your dream vacation — flights, hotels, activities, and personalized itineraries tailored to your budget and style.",
  keywords: [
    "AI travel planner",
    "trip planner",
    "travel itinerary",
    "vacation planning",
    "AI travel assistant",
    "budget travel",
    "personalized travel",
  ],
  authors: [{ name: "Planfirst" }],
  creator: "Planfirst",
  publisher: "Planfirst",
  metadataBase: new URL("https://planfirstai.com"),
  openGraph: {
    title: "Planfirst - AI-Powered Travel Planner",
    description: "Plan your perfect trip in seconds. Describe your dream vacation — flights, hotels, activities, and personalized itineraries tailored to your budget and style.",
    url: "https://planfirstai.com",
    siteName: "Planfirst",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "https://planfirstai.com/opengraph-image.jpg",
        width: 1200,
        height: 630,
        alt: "Planfirst - AI-Powered Travel Planner",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Planfirst - AI-Powered Travel Planner",
    description: "Plan your perfect trip in seconds. Describe your dream vacation — flights, hotels, activities, and personalized itineraries.",
    creator: "@planfirst",
    images: ["https://planfirstai.com/twitter-image.jpg"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "https://planfirstai.com",
  },
  verification: {
    google: "W0nYk8Whr-gE4YE0rhcJF4YSTM6CLLXnfUzWFKeh4l4",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="antialiased">
        <TooltipProvider>
          <SidebarProvider defaultOpen={false}>
            {children}
            <Analytics />
          </SidebarProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
