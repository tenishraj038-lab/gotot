"use client";

import { useState } from "react";
import { Mail, Check, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

export default function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !email.includes("@")) return toast.error("Valid email required");
    setLoading(true);
    try {
      const { api } = await import("@/lib/api");
      await api.contactMessage("Newsletter Signup", email, "Newsletter subscription request");
      setSubscribed(true);
      toast.success("Subscribed to newsletter!");
    } catch {
      toast.error("Failed to subscribe");
    }
    setLoading(false);
  }

  if (subscribed) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400">
        <Check className="w-5 h-5" />
        <p className="text-sm font-medium">You're subscribed! Check your inbox.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1">
        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full pl-10 pr-4 py-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
          required
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-xl hover:from-primary-500 hover:to-accent-500 font-medium text-sm transition-all disabled:opacity-50 flex items-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
        Subscribe
      </button>
    </form>
  );
}
