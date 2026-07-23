"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, X } from "lucide-react";

const COOKIE_CONSENT_KEY = "gotot_cookie_consent";

export function getConsent(): boolean | null {
  if (typeof window === "undefined") return null;
  const val = localStorage.getItem(COOKIE_CONSENT_KEY);
  if (val === null) return null;
  return val === "true";
}

export function setConsent(accepted: boolean) {
  if (typeof window !== "undefined") {
    localStorage.setItem(COOKIE_CONSENT_KEY, String(accepted));
  }
}

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = getConsent();
    if (consent === null) {
      const timer = setTimeout(() => setVisible(true), 800);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    setConsent(true);
    setVisible(false);
    window.dispatchEvent(new Event("cookie-consent-changed"));
  };

  const handleDecline = () => {
    setConsent(false);
    setVisible(false);
    window.dispatchEvent(new Event("cookie-consent-changed"));
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className="fixed bottom-0 left-0 right-0 z-[60] p-4"
        >
          <div className="max-w-3xl mx-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl p-5">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center shrink-0">
                <Shield className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
                  Cookie Consent
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  We use essential cookies to provide our service and optional analytics cookies to
                  improve your experience. By accepting, you consent to our use of analytics cookies.
                  See our{" "}
                  <a href="/privacy" className="text-primary-600 hover:text-primary-500 underline">
                    Privacy Policy
                  </a>{" "}
                  for details.
                </p>
              </div>
              <button
                onClick={() => setVisible(false)}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center gap-3 mt-4">
              <button
                onClick={handleAccept}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Accept All
              </button>
              <button
                onClick={handleDecline}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors"
              >
                Essential Only
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
