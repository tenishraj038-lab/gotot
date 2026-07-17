"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Lock, Loader2, Download, CreditCard, Sparkles } from "lucide-react";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

export default function PaymentModal() {
  const { paymentModalOpen, setPaymentModalOpen, pendingDownload } = useStore();
  const [loading, setLoading] = useState(false);

  const handlePayPerDownload = async () => {
    setLoading(true);
    try {
      const result = await api.createPayPerDownloadCheckout();
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch (err) {
      toast.error("Failed to create checkout");
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (tier: string) => {
    setLoading(true);
    try {
      const result = await api.createSubscriptionCheckout(tier);
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch (err) {
      toast.error("Failed to create checkout");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {paymentModalOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setPaymentModalOpen(false)} />
          <motion.div
            className="relative w-full max-w-lg rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 shadow-2xl overflow-hidden"
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
          >
            <button
              onClick={() => setPaymentModalOpen(false)}
              className="absolute top-4 right-4 p-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors z-10"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="p-8">
              <div className="text-center mb-8">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center mx-auto mb-4">
                  <Lock className="w-7 h-7 text-white" />
                </div>
                <h2 className="text-2xl font-bold">Download Limit Reached</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  You've hit your daily limit. Choose how you'd like to continue.
                </p>
              </div>

              <div className="space-y-4">
                <button
                  onClick={handlePayPerDownload}
                  disabled={loading}
                  className="w-full p-4 rounded-xl border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all text-left flex items-center gap-4"
                >
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shrink-0">
                    <Download className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-sm">Pay per Download</p>
                    <p className="text-xs text-gray-500">$0.50 for a single download, no commitment</p>
                  </div>
                  <CreditCard className="w-5 h-5 text-gray-400" />
                </button>

                <button
                  onClick={() => handleUpgrade("pro")}
                  disabled={loading}
                  className="w-full p-4 rounded-xl border-2 border-primary-500/50 bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-all text-left flex items-center gap-4"
                >
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center shrink-0">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-sm">Go Pro - $4.99/month</p>
                    <p className="text-xs text-gray-500">100 downloads/day, 4K quality, no ads, batch download</p>
                  </div>
                  <span className="text-xs font-semibold text-primary-600 bg-primary-100 dark:bg-primary-900/50 px-2 py-1 rounded-full">Popular</span>
                </button>

                <button
                  onClick={() => handleUpgrade("unlimited")}
                  disabled={loading}
                  className="w-full p-4 rounded-xl border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all text-left flex items-center gap-4"
                >
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shrink-0">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-sm">Unlimited - $9.99/month</p>
                    <p className="text-xs text-gray-500">Everything unlimited, priority support</p>
                  </div>
                </button>
              </div>

              {loading && (
                <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Redirecting to secure checkout...
                </div>
              )}

              <p className="mt-6 text-center text-xs text-gray-400 flex items-center justify-center gap-1">
                <Lock className="w-3 h-3" />
                Secure payment powered by Razorpay
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
