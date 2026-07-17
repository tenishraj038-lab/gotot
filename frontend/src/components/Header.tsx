"use client";

import { useEffect } from "react";
import { Moon, Sun, Github, User, LogOut, LayoutDashboard, Menu, X, Globe } from "lucide-react";
import { useStore } from "@/lib/store";
import { loadTokens, clearTokens, getAuthToken } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import toast from "react-hot-toast";
import LocaleSwitcher from "./LocaleSwitcher";
import { useLocale } from "@/lib/i18n";

export default function Header() {
  const { t } = useLocale();
  const { isDarkMode, toggleDarkMode, user, setUser, setSubscription, setAuthModalOpen } = useStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const saved = localStorage.getItem("darkMode") === "true";
    if (saved !== isDarkMode) {
      document.documentElement.classList.toggle("dark", saved);
    }
    loadTokens();
    if (getAuthToken()) {
      import("@/lib/api").then(({ api }) => {
        api.getSubscriptionStatus().then((sub) => {
          setSubscription(sub);
          setUser({ id: "", email: "", username: "", role: sub.tier, downloads_today: 0, daily_download_limit: sub.daily_downloads, download_credits: 0, total_downloads: 0 });
        }).catch(() => {});
      });
    }
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    setSubscription(null);
    toast.success("Signed out");
    router.push("/");
  };

  const isAuthenticated = !!getAuthToken();

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? "glass border-b border-gray-200/50 dark:border-gray-800/50" : "bg-transparent"
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">G</span>
            </div>
            <span className="text-2xl font-bold">
              <span className="text-gradient">GoTot</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link href="/" className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
              {t.nav.home}
            </Link>
            <Link href="/pricing" className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
              {t.nav.pricing}
            </Link>
            <div className="relative group">
              <button className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors flex items-center gap-1">
                {t.nav.features}
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </button>
              <div className="absolute top-full left-0 mt-2 w-48 py-2 rounded-xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                {[
                  { name: "YouTube", href: "/download/youtube" },
                  { name: "TikTok", href: "/download/tiktok" },
                  { name: "Instagram", href: "/download/instagram" },
                  { name: "Twitter/X", href: "/download/twitter" },
                  { name: "Facebook", href: "/download/facebook" },
                  { name: "Reddit", href: "/download/reddit" },
                  { name: "Vimeo", href: "/download/vimeo" },
                  { name: "Twitch", href: "/download/twitch" },
                  { name: "Dailymotion", href: "/download/dailymotion" },
                  { name: "LinkedIn", href: "/download/linkedin" },
                  { name: "Pinterest", href: "/download/pinterest" },
                ].map((p) => (
                  <Link key={p.name} href={p.href} className="block px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white">
                    {p.name}
                  </Link>
                ))}
              </div>
            </div>
          </nav>

          <div className="flex items-center gap-2">
            <LocaleSwitcher />
            <button
              onClick={toggleDarkMode}
              className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200"
              aria-label="Toggle dark mode"
            >
              {isDarkMode ? (
                <Sun className="w-4 h-4 text-yellow-500" />
              ) : (
                <Moon className="w-4 h-4 text-gray-600" />
              )}
            </button>

            {isAuthenticated ? (
              <div className="hidden md:flex items-center gap-2">
                <Link
                  href="/dashboard"
                  className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200"
                >
                  <LayoutDashboard className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200"
                >
                  <LogOut className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setAuthModalOpen(true)}
                className="hidden md:flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-primary-500/25"
              >
                <User className="w-4 h-4" />
                {t.nav.signIn}
              </button>
            )}

            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden md:flex p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200"
            >
              <Github className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </a>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200/50 dark:border-gray-800/50 space-y-1">
            <Link href="/" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>{t.nav.home}</Link>
            <Link href="/pricing" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>{t.nav.pricing}</Link>
            <Link href="/download/youtube" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>YouTube</Link>
            <Link href="/download/tiktok" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>TikTok</Link>
            <Link href="/download/instagram" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>Instagram</Link>
            <Link href="/download/twitter" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>Twitter/X</Link>
            <Link href="/download/facebook" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>Facebook</Link>
            <Link href="/download/reddit" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>Reddit</Link>
            <Link href="/download/vimeo" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>Vimeo</Link>
            <Link href="/download/twitch" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>Twitch</Link>
            <Link href="/download/dailymotion" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>Dailymotion</Link>
            <Link href="/download/linkedin" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>LinkedIn</Link>
            <Link href="/download/pinterest" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>Pinterest</Link>
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="block px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => setMobileMenuOpen(false)}>{t.nav.dashboard}</Link>
                <button onClick={() => { handleLogout(); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800">{t.nav.signOut}</button>
              </>
            ) : (
              <button onClick={() => { setAuthModalOpen(true); setMobileMenuOpen(false); }} className="block w-full text-left px-3 py-2 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-800">{t.nav.signIn}</button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
