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
import CookieConsent from "@/components/CookieConsent";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: {
    default: "GoTot - Universal Video Downloader | Download Videos Free",
    template: "%s | GoTot - Free Video Downloader",
  },
  description:
    "Download videos from TikTok, Instagram, Twitter, Facebook, Reddit, Vimeo, Twitch, Dailymotion, LinkedIn, and Pinterest. Fast, secure, and completely free. No registration required.",
  keywords: [
    "video downloader", "tiktok downloader",
    "instagram downloader", "twitter downloader", "facebook downloader",
    "free video downloader", "online video downloader", "download videos free",
    "reddit downloader", "vimeo downloader", "twitch downloader",
    "dailymotion downloader", "linkedin downloader", "pinterest downloader",
    "mp3 converter", "video to mp3", "4k video downloader",
  ],
  authors: [{ name: "GoTot" }],
  creator: "GoTot",
  publisher: "GoTot",
  metadataBase: new URL("https://gotot.app"),
  openGraph: {
    title: "GoTot - Universal Video Downloader",
    description: "Download videos from 11+ platforms. Fast, secure, and completely free.",
    type: "website",
    siteName: "GoTot",
    locale: "en_US",
    url: "https://gotot.app",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "GoTot - Universal Video Downloader" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "GoTot - Universal Video Downloader",
    description: "Download videos from 11+ platforms. Fast, secure, and completely free.",
    images: ["/og-image.png"],
    creator: "@gotot",
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
  "@graph": [
    {
      "@type": "WebApplication",
      name: "GoTot",
      applicationCategory: "Multimedia",
      operatingSystem: "Web",
      description: "Download videos from TikTok, Instagram, Twitter, Facebook, Reddit, Vimeo, Twitch, Dailymotion, LinkedIn, and Pinterest. Free, fast, and secure.",
      url: "https://gotot.app",
      offers: [
        { "@type": "Offer", price: "0", priceCurrency: "USD", description: "Free unlimited downloads" },
        { "@type": "Offer", price: "4.99", priceCurrency: "USD", description: "Pro plan - Priority processing" },
        { "@type": "Offer", price: "9.99", priceCurrency: "USD", description: "Unlimited plan with all features included" },
      ],
    },
    {
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Home", item: "https://gotot.app" },
        { "@type": "ListItem", position: 2, name: "TikTok Downloader", item: "https://gotot.app/download/tiktok" },
      ],
    },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
        <link rel="canonical" href="https://gotot.app" />
        <link rel="alternate" hrefLang="en" href="https://gotot.app" />
        <link rel="alternate" hrefLang="es" href="https://gotot.app/es" />
        <link rel="alternate" hrefLang="x-default" href="https://gotot.app" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <script
          dangerouslySetInnerHTML={{
            __html: [
              "try {",
              "if (localStorage.getItem('darkMode') === 'true' ||",
              "(!localStorage.getItem('darkMode') &&",
              "window.matchMedia('(prefers-color-scheme: dark)').matches)) {",
              "document.documentElement.classList.add('dark');",
              "}",
              "} catch(e) {}",
            ].join("\n"),
          }}
        />
        {process.env.NEXT_PUBLIC_GA_ID && (
          <>
            <script
              dangerouslySetInnerHTML={{
                __html: [
                  "window.__gaConsent = function() {",
                  "  return localStorage.getItem('gotot_cookie_consent') === 'true';",
                  "};",
                  "window.addEventListener('cookie-consent-changed', function() {",
                  "  if (window.__gaConsent()) {",
                  "    if (!window.__gaLoaded) {",
                  "      window.__gaLoaded = true;",
                  `      var s = document.createElement('script');`,
                  `      s.async = true;`,
                  `      s.src = 'https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}';`,
                  `      document.head.appendChild(s);`,
                  "      s.onload = function() {",
                  "        window.dataLayer = window.dataLayer || [];",
                  "        function gtag(){dataLayer.push(arguments);}",
                  `        gtag('js', new Date());`,
                  `        gtag('config', '${process.env.NEXT_PUBLIC_GA_ID}', {`,
                  "          page_path: window.location.pathname,",
                  "        });",
                  "      };",
                  "    }",
                  "  }",
                  "});",
                  "if (window.__gaConsent()) {",
                  "  window.dispatchEvent(new Event('cookie-consent-changed'));",
                  "}",
                ].join("\n"),
              }}
            />
          </>
        )}
      </head>
      <body className="min-h-screen flex flex-col bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
        >
          Skip to main content
        </a>
        <Toaster position="top-center" toastOptions={{ duration: 4000 }} />
        <Header />
        <NotificationBanner />
        <ErrorBoundary>
          <main id="main-content" className="flex-1">{children}</main>
        </ErrorBoundary>
        <Footer />
        <AuthModal />
        <AdModal />
        <PaymentModal />
        <PwaRegister />
        <CookieConsent />
      </body>
    </html>
  );
}
