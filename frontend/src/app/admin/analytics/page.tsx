"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, Users, Download, DollarSign, Activity, Zap, GitBranch, Key, Loader2 } from "lucide-react";
import { api, loadTokens } from "@/lib/api";
import { useStore } from "@/lib/store";
import { useRouter } from "next/navigation";

interface ExecutiveAnalytics {
  users: { total: number; today: number; this_month: number; returning_weekly: number };
  downloads: { total: number; today: number; this_month: number; by_platform: Record<string, number> };
  queue: { pending: number; processing: number; failed: number };
  revenue: { total_usd: number; mtd_usd: number };
  premium: { active_subscriptions: number; monthly_conversions: number };
  referrals: { total: number; this_month: number };
  api: { total_requests: number };
  period_days: number;
}

export default function AnalyticsPage() {
  const router = useRouter();
  const { user, setAuthModalOpen } = useStore();
  const [data, setData] = useState<ExecutiveAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTokens();
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      setAuthModalOpen(true);
      router.push("/");
      return;
    }
    fetchAnalytics();
  }, []);

  async function fetchAnalytics() {
    setLoading(true);
    try {
      const result = await api.getAdminExecutiveAnalytics(30);
      setData(result);
    } catch {
      setLoading(false);
    }
    setLoading(false);
  }

  if (loading) {
    return (
      <div className="pt-24 pb-16 max-w-7xl mx-auto px-4">
        <div className="space-y-4">{[1,2,3,4,5,6].map(i => <div key={i} className="h-24 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
      </div>
    );
  }

  if (!data) {
    return <div className="pt-24 pb-16 max-w-7xl mx-auto px-4 text-center text-gray-400">Analytics data unavailable</div>;
  }

  const sections = [
    {
      title: "Users",
      icon: Users,
      color: "from-blue-500 to-cyan-500",
      metrics: [
        { label: "Total", value: data.users.total.toLocaleString() },
        { label: "Today", value: data.users.today },
        { label: "This Month", value: data.users.this_month },
        { label: "Returning (7d)", value: data.users.returning_weekly },
      ],
    },
    {
      title: "Downloads",
      icon: Download,
      color: "from-purple-500 to-pink-500",
      metrics: [
        { label: "Total", value: data.downloads.total.toLocaleString() },
        { label: "Today", value: data.downloads.today },
        { label: "This Month", value: data.downloads.this_month },
        { label: "Platforms", value: Object.keys(data.downloads.by_platform).length },
      ],
    },
    {
      title: "Revenue",
      icon: DollarSign,
      color: "from-green-500 to-emerald-500",
      metrics: [
        { label: "Total", value: `$${data.revenue.total_usd}` },
        { label: "MTD", value: `$${data.revenue.mtd_usd}` },
      ],
    },
    {
      title: "Premium",
      icon: Zap,
      color: "from-amber-500 to-orange-500",
      metrics: [
        { label: "Active Subs", value: data.premium.active_subscriptions },
        { label: "Conversions (30d)", value: data.premium.monthly_conversions },
      ],
    },
    {
      title: "Queue",
      icon: Activity,
      color: "from-red-500 to-rose-500",
      metrics: [
        { label: "Pending", value: data.queue.pending },
        { label: "Processing", value: data.queue.processing },
        { label: "Failed", value: data.queue.failed },
      ],
    },
    {
      title: "Referrals & API",
      icon: GitBranch,
      color: "from-indigo-500 to-purple-500",
      metrics: [
        { label: "Referrals Total", value: data.referrals.total },
        { label: "Referrals (30d)", value: data.referrals.this_month },
        { label: "API Requests", value: data.api.total_requests.toLocaleString() },
      ],
    },
  ];

  return (
    <div className="pt-24 pb-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <BarChart3 className="w-8 h-8 text-primary-500" />
          <h1 className="text-3xl font-bold">Executive Analytics</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mb-8">Last {data.period_days} days performance overview</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {sections.map((section, i) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${section.color} p-2`}>
                  <section.icon className="w-full h-full text-white" />
                </div>
                <h3 className="text-lg font-semibold">{section.title}</h3>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {section.metrics.map((m) => (
                  <div key={m.label}>
                    <p className="text-2xl font-bold">{m.value}</p>
                    <p className="text-xs text-gray-500">{m.label}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6"
        >
          <h3 className="text-lg font-semibold mb-4">Downloads by Platform (30d)</h3>
          {Object.entries(data.downloads.by_platform).length === 0 ? (
            <p className="text-gray-400 text-sm">No data</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(data.downloads.by_platform)
                .sort(([, a], [, b]) => b - a)
                .map(([platform, count]) => {
                  const max = Math.max(...Object.values(data.downloads.by_platform));
                  return (
                    <div key={platform}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="capitalize">{platform}</span>
                        <span className="text-gray-500">{count.toLocaleString()}</span>
                      </div>
                      <div className="h-2.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all" style={{ width: `${(count / max) * 100}%` }} />
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </motion.div>
      </motion.div>
    </div>
  );
}
