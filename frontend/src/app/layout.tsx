import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import AuthModal from "@/components/auth/AuthModal";
import AdModal from "@/components/AdModal";
import PaymentModal from "@/components/PaymentModal";
import PwaRegister from "@/components/PwaRegister";
import ErrorBoundary from "@/components/ErrorBoundary";
import NotificationBanner from "@/components/NotificationBanner";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "GoTot - Universal Video Downloader | Download Videos Free",
  description:
    "Download videos from YouTube, TikTok, Instagram, Twitter, Facebook, and more. Fast, secure, and free. No registration required.",
  keywords: [
    "video downloader", "youtube downloader", "tiktok downloader",
    "instagram downloader", "twitter downloader", "free downloader",
    "online video downloader", "download videos free",
  ],
  openGraph: {
    title: "GoTot - Universal Video Downloader",
    description: "Download videos from any platform. Fast, secure, and free.",
    type: "website",
    siteName: "GoTot",
    locale: "en_US",
    url: "https://gotot.app",
  },
  twitter: {
    card: "summary_large_image",
    title: "GoTot - Universal Video Downloader",
    description: "Download videos from any platform. Fast, secure, and free.",
  },
  robots: "index, follow",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    title: "GoTot",
    statusBarStyle: "black-translucent",
  },
  icons: {
    icon: "/favicon.svg",
    apple: "/icons/icon-192x192.svg",
  },
  other: {
    "mobile-web-app-capable": "yes",
    "apple-mobile-web-app-capable": "yes",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "GoTot",
  applicationCategory: "Multimedia",
  operatingSystem: "Web",
  description: "Download videos from YouTube, TikTok, Instagram, Twitter, Facebook, Reddit, Vimeo, Twitch, Dailymotion, LinkedIn, and Pinterest. Free, fast, and secure.",
  url: "https://gotot.app",
  offers: [
    { "@type": "Offer", price: "0", priceCurrency: "USD", description: "Free unlimited downloads" },
    { "@type": "Offer", price: "4.99", priceCurrency: "USD", description: "Pro plan - Priority processing" },
    { "@type": "Offer", price: "9.99", priceCurrency: "USD", description: "Unlimited plan - Everything included" },
  ],
  aggregateRating: {
    "@type": "AggregateRating",
    ratingValue: "4.8",
    ratingCount: "15234",
    bestRating: "5",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                if (localStorage.getItem('darkMode') === 'true' || (!localStorage.getItem('darkMode') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                }
              } catch(e) {}
            `,
          }}
        />
      </head>
      <body className="min-h-screen flex flex-col bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">
        <Toaster position="top-center" toastOptions={{ duration: 4000 }} />
        <Header />
        <NotificationBanner />
        <ErrorBoundary>
          <main className="flex-1">{children}</main>
        </ErrorBoundary>
        <Footer />
        <AuthModal />
        <AdModal />
        <PaymentModal />
        <PwaRegister />
      </body>
    </html>
  );
}
