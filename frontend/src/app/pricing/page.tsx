"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Check, X, Sparkles, Loader2, ArrowRight } from "lucide-react";
import { useStore } from "@/lib/store";
import { api, loadTokens } from "@/lib/api";
import toast from "react-hot-toast";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Everything you need, completely free",
    popular: false,
    color: "from-primary-500 to-accent-600",
    features: [
      { text: "Unlimited downloads", included: true },
      { text: "4K quality", included: true },
      { text: "MP3 conversion (128-320kbps)", included: true },
      { text: "All formats (MP4, WebM, 3GP)", included: true },
      { text: "Batch download (up to 10 URLs)", included: true },
      { text: "No ads, no waiting", included: true },
      { text: "No registration required", included: true },
      { text: "11+ platforms supported", included: true },
      { text: "API access", included: false },
      { text: "Priority support", included: false },
    ],
  },
  {
    name: "Pro",
    price: "$4.99",
    period: "per month",
    description: "For power users who need API access",
    popular: true,
    color: "from-primary-500 to-accent-600",
    features: [
      { text: "All Free features", included: true },
      { text: "API access (1000 req/day)", included: true },
      { text: "Higher batch limit (50 URLs)", included: true },
      { text: "Priority email support", included: true },
      { text: "Download history search", included: true },
      { text: "No rate limits", included: true },
    ],
  },
  {
    name: "Unlimited",
    price: "$9.99",
    period: "per month",
    description: "For professionals and teams",
    color: "from-purple-500 to-pink-500",
    features: [
      { text: "All Pro features", included: true },
      { text: "API access (10000 req/day)", included: true },
      { text: "Unlimited batch downloads", included: true },
      { text: "10 concurrent downloads", included: true },
      { text: "Custom integrations", included: true },
      { text: "Priority 24/7 support", included: true },
    ],
  },
];

export default function PricingPage() {
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const { user, setAuthModalOpen } = useStore();

  const handleUpgrade = async (tier: string) => {
    if (tier === "free") {
      window.location.href = "/";
      return;
    }
    if (!user) {
      setAuthModalOpen(true);
      return;
    }
    setLoadingTier(tier);
    try {
      loadTokens();
      const result = await api.createSubscriptionCheckout(tier);
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch (err) {
      toast.error("Failed to start checkout");
    } finally {
      setLoadingTier(null);
    }
  };

  return (
    <div className="pt-32 pb-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-50 dark:bg-primary-900/30 border border-primary-200 dark:border-primary-800/50 mb-4">
            <Sparkles className="w-3.5 h-3.5 text-primary-600 dark:text-primary-400" />
            <span className="text-xs font-medium text-primary-700 dark:text-primary-300">
              Simple, transparent pricing
            </span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold">
            The Right Plan for{" "}
            <span className="text-gradient">Your Needs</span>
          </h1>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Start free, upgrade when you need more. No hidden fees, cancel anytime.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`relative p-8 rounded-2xl ${
                plan.popular
                  ? "bg-white dark:bg-gray-900 border-2 border-primary-500/50 shadow-2xl shadow-primary-500/10 scale-105 md:scale-110"
                  : "bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-primary-600 to-accent-600 text-xs font-semibold text-white shadow-lg">
                  Most Popular
                </div>
              )}

              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${plan.color} p-2.5 mb-4`}>
                <Sparkles className="w-full h-full text-white" />
              </div>

              <h3 className="text-2xl font-bold">{plan.name}</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-4xl font-extrabold">{plan.price}</span>
                <span className="text-sm text-gray-500">/{plan.period}</span>
              </div>
              <p className="mt-2 text-sm text-gray-500">{plan.description}</p>

              <ul className="mt-8 space-y-3">
                {plan.features.map((f) => (
                  <li key={f.text} className="flex items-start gap-3">
                    {f.included ? (
                      <Check className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                    ) : (
                      <X className="w-4 h-4 text-gray-300 dark:text-gray-600 mt-0.5 shrink-0" />
                    )}
                    <span className={`text-sm ${f.included ? "text-gray-700 dark:text-gray-300" : "text-gray-400 dark:text-gray-500"}`}>
                      {f.text}
                    </span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleUpgrade(plan.name.toLowerCase())}
                disabled={loadingTier === plan.name.toLowerCase() || (user?.role === plan.name.toLowerCase() && plan.name !== "Free")}
                className={`w-full mt-8 py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 ${
                  plan.popular
                    ? "bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white shadow-lg shadow-primary-500/25"
                    : "border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-900 dark:text-gray-100"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {loadingTier === plan.name.toLowerCase() ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : user?.role === plan.name.toLowerCase() && plan.name !== "Free" ? (
                  "Current Plan"
                ) : (
                  <>
                    {plan.name === "Free" ? "Get Started" : "Upgrade Now"}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </motion.div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            All plans include SSL encryption, 24/7 availability, and basic support.{" "}
            <span className="text-primary-600 dark:text-primary-400 font-medium cursor-pointer hover:underline">
              View full feature comparison
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
