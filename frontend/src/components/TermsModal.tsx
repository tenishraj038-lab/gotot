"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check } from "lucide-react";
import Link from "next/link";

const TERMS_COOKIE = "terms_accepted";

export function hasAcceptedTerms(): boolean {
  if (typeof document === "undefined") return false;
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${TERMS_COOKIE}=([^;]+)`));
  return match?.[1] === "true";
}

interface TermsModalProps {
  isOpen: boolean;
  onAccept: () => void;
  onDecline: () => void;
}

export default function TermsModal({ isOpen, onAccept, onDecline }: TermsModalProps) {
  const [checked, setChecked] = useState(false);

  const handleAccept = () => {
    document.cookie = `${TERMS_COOKIE}=true; path=/; max-age=${30 * 86400}; SameSite=Lax`;
    onAccept();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onDecline} />
          <motion.div
            className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto border border-gray-200 dark:border-gray-800"
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Terms of Service</h2>
                <button
                  onClick={onDecline}
                  className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  aria-label="Close"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="prose dark:prose-invert text-sm text-gray-600 dark:text-gray-400 max-w-none space-y-3 mb-6">
                <p>
                  By using GoTot, you agree to comply with all applicable laws and respect the
                  intellectual property rights of content creators.
                </p>

                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 my-3">
                  <p className="text-amber-800 dark:text-amber-200 font-medium text-sm mb-1">
                    ⚠ Important Legal Notice
                  </p>
                  <p className="text-amber-700 dark:text-amber-300 text-xs">
                    You may only download content that you own or have explicit permission to download.
                    Downloading copyrighted content without authorization may violate copyright laws.
                    You are solely responsible for ensuring your use complies with all applicable laws.
                    GoTot does not encourage, promote, or facilitate copyright infringement.
                  </p>
                </div>

                <ul className="list-disc pl-5 space-y-1 text-xs">
                  <li>Only download content you have the right to access.</li>
                  <li>Respect all copyright laws and each platform&apos;s Terms of Service.</li>
                  <li>This includes TikTok, Instagram, X (Twitter), Facebook, Reddit, Vimeo, Dailymotion, Twitch, LinkedIn, Pinterest, Snapchat, Bilibili, SoundCloud, Rumble, and Odysee.</li>
                  <li>Do not use the Service for any illegal purpose.</li>
                  <li>Do not redistribute downloaded content without permission.</li>
                  <li>You accept full liability for your use of the Service.</li>
                </ul>

                <p className="text-xs">
                  Read the full{" "}
                  <Link href="/terms" className="text-primary-600 hover:underline font-medium">
                    Terms of Service
                  </Link>
                  ,{" "}
                  <Link href="/privacy" className="text-primary-600 hover:underline font-medium">
                    Privacy Policy
                  </Link>
                  ,{" "}
                  <Link href="/copyright" className="text-primary-600 hover:underline font-medium">
                    Copyright Policy
                  </Link>
                  , and{" "}
                  <Link href="/dmca" className="text-primary-600 hover:underline font-medium">
                    DMCA Policy
                  </Link>
                  .
                </p>
              </div>

              <label className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800 cursor-pointer mb-4">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => setChecked(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  I have read and agree to the Terms of Service, Privacy Policy, and Copyright Policy.
                  I understand that I may only download content I own or have permission to download.
                </span>
              </label>

              <div className="flex gap-3">
                <button
                  onClick={onDecline}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm"
                >
                  Decline
                </button>
                <button
                  onClick={handleAccept}
                  disabled={!checked}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary-600 to-accent-600 text-white font-semibold hover:from-primary-500 hover:to-accent-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm flex items-center justify-center gap-2"
                >
                  <Check className="w-4 h-4" />
                  Accept & Continue
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
