"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Trophy, Medal, Users, Copy, Check, TrendingUp, Clock, Gift, BarChart3, Award, List, Loader2 } from "lucide-react";
import { api, loadTokens } from "@/lib/api";
import { useStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  count: number;
  badge: string;
}

interface LeaderboardData {
  period: string;
  entries: LeaderboardEntry[];
  my_rank: number;
}

interface ReferralStats {
  code: string | null;
  total_referred: number;
  this_week: number;
  this_month: number;
  pending: number;
  total_credits: number;
  rank: number;
  badge: string;
  reward_per_referral: number;
}

interface ReferralHistoryItem {
  id: string;
  referred_email: string;
  status: string;
  reward_credits: number;
  created_at: string;
  completed_at: string | null;
}

const badgeColors: Record<string, string> = {
  gold: "from-yellow-400 to-amber-600",
  silver: "from-gray-300 to-gray-500",
  bronze: "from-orange-400 to-amber-700",
  top10: "from-blue-400 to-blue-600",
  top50: "from-green-400 to-green-600",
  top100: "from-purple-400 to-purple-600",
  referrer: "from-gray-400 to-gray-600",
};

const badgeIcon = (badge: string) => {
  if (badge === "gold") return "🥇";
  if (badge === "silver") return "🥈";
  if (badge === "bronze") return "🥉";
  return "🏅";
};

export default function ReferralsPage() {
  const router = useRouter();
  const { setAuthModalOpen } = useStore();
  const [tab, setTab] = useState<"leaderboard" | "stats" | "history">("leaderboard");
  const [period, setPeriod] = useState<"global" | "weekly" | "monthly" | "all_time">("all_time");
  const [loading, setLoading] = useState(true);
  const [leaderboard, setLeaderboard] = useState<LeaderboardData | null>(null);
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [history, setHistory] = useState<{ referrals: ReferralHistoryItem[]; total: number } | null>(null);
  const [copied, setCopied] = useState(false);
  const [applyCode, setApplyCode] = useState("");
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    loadTokens();
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      setAuthModalOpen(true);
      router.push("/");
      return;
    }
    fetchAll();
  }, []);

  useEffect(() => {
    if (tab === "leaderboard") fetchLeaderboard();
  }, [period]);

  async function fetchAll() {
    setLoading(true);
    await Promise.all([fetchStats(), fetchLeaderboard(), fetchHistory()]);
    setLoading(false);
  }

  async function fetchStats() {
    try {
      const data = await api.getReferralStats();
      setStats(data);
    } catch { /* ignore */ }
  }

  async function fetchLeaderboard() {
    try {
      const data = await api.getReferralLeaderboard(period);
      setLeaderboard(data);
    } catch { /* ignore */ }
  }

  async function fetchHistory() {
    try {
      const data = await api.getReferralHistory();
      setHistory(data);
    } catch { /* ignore */ }
  }

  async function copyReferralLink() {
    if (!stats?.code) return;
    const url = `${window.location.origin}?ref=${stats.code}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Link copied!");
    } catch {
      toast.error("Failed to copy");
    }
  }

  async function handleApplyCode() {
    if (!applyCode.trim()) return;
    setApplying(true);
    try {
      const data = await api.applyReferralCode(applyCode.trim());
      toast.success(`Applied! +${data.bonus_downloads} bonus downloads`);
      setApplyCode("");
      fetchAll();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Invalid code";
      toast.error(msg);
    }
    setApplying(false);
  }

  const tabs = [
    { key: "leaderboard" as const, label: "Leaderboard", icon: Trophy },
    { key: "stats" as const, label: "My Stats", icon: BarChart3 },
    { key: "history" as const, label: "History", icon: List },
  ];

  return (
    <div className="pt-24 pb-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-8 h-8 text-primary-500" />
          <h1 className="text-3xl font-bold">Referral Program</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mb-4">Refer friends and earn +{stats?.reward_per_referral ?? 3} bonus downloads each</p>

        {stats?.code && (
          <div className="flex flex-col sm:flex-row gap-3 mb-8 p-4 rounded-2xl bg-gradient-to-r from-primary-500/10 to-accent-500/10 border border-primary-500/20">
            <div className="flex-1">
              <p className="text-xs text-gray-500 mb-1">Your referral link</p>
              <p className="text-sm font-mono break-all">{`${typeof window !== "undefined" ? window.location.origin : ""}?ref=${stats.code}`}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={copyReferralLink}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 text-sm font-medium transition-all"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? "Copied" : "Copy Link"}
              </button>
              <div className="flex gap-2">
                <input
                  placeholder="Enter referral code"
                  value={applyCode}
                  onChange={(e) => setApplyCode(e.target.value)}
                  className="px-3 py-2 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm w-36 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <button
                  onClick={handleApplyCode}
                  disabled={applying || !applyCode.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 text-sm font-medium transition-all disabled:opacity-50"
                >
                  {applying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Gift className="w-4 h-4" />}
                  Apply
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-2 mb-8">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                tab === key
                  ? "bg-primary-600 text-white shadow-lg"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {tab === "leaderboard" && (
          <div>
            <div className="flex gap-2 mb-6">
              {(["global", "weekly", "monthly", "all_time"] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    period === p
                      ? "bg-primary-600 text-white shadow-lg"
                      : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
                  }`}
                >
                  {p === "all_time" ? "All Time" : p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-16 rounded-xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 overflow-hidden">
                {leaderboard?.entries.length === 0 ? (
                  <p className="p-8 text-center text-gray-400">No referrals yet. Be the first!</p>
                ) : (
                  <div className="divide-y divide-gray-100 dark:divide-gray-800">
                    {leaderboard?.entries.map((entry, i) => (
                      <div
                        key={entry.user_id}
                        className={`flex items-center gap-4 p-4 ${
                          entry.rank <= 3 ? "bg-gradient-to-r from-amber-50/50 dark:from-amber-900/10" : ""
                        }`}
                      >
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${badgeColors[entry.badge]} p-2 flex items-center justify-center text-lg font-bold text-white flex-shrink-0`}>
                          {entry.rank <= 3 ? badgeIcon(entry.badge) : entry.rank}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{entry.username}</p>
                          <p className="text-xs text-gray-400 capitalize">{entry.badge} referrer</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-lg">{entry.count}</p>
                          <p className="text-xs text-gray-400">referred</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {tab === "stats" && stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[
              { label: "Total Referred", value: stats.total_referred, icon: Users, color: "from-blue-500 to-cyan-500" },
              { label: "This Week", value: stats.this_week, icon: TrendingUp, color: "from-green-500 to-emerald-500" },
              { label: "This Month", value: stats.this_month, icon: Clock, color: "from-amber-500 to-orange-500" },
              { label: "Bonus Downloads", value: stats.total_credits, icon: Gift, color: "from-purple-500 to-pink-500" },
            ].map((card, i) => (
              <motion.div
                key={card.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} p-2 mb-3`}>
                  <card.icon className="w-full h-full text-white" />
                </div>
                <p className="text-2xl font-bold">{card.value}</p>
                <p className="text-sm text-gray-500">{card.label}</p>
              </motion.div>
            ))}

            <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 col-span-full sm:col-span-2 lg:col-span-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${badgeColors[stats.badge]} p-3 mx-auto mb-2 flex items-center justify-center text-3xl`}>
                    {badgeIcon(stats.badge)}
                  </div>
                  <p className="font-semibold capitalize">{stats.badge} Referrer</p>
                  <p className="text-xs text-gray-400">Rank #{stats.rank}</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-primary-500">{stats.pending}</p>
                  <p className="text-sm text-gray-500">Pending Referrals</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-500">+{stats.reward_per_referral}</p>
                  <p className="text-sm text-gray-500">Bonus per Referral</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {tab === "history" && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 overflow-hidden">
            {history?.referrals.length === 0 ? (
              <p className="p-8 text-center text-gray-400">No referral history yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                      <th className="text-left p-4 font-semibold">Referred User</th>
                      <th className="text-center p-4 font-semibold">Status</th>
                      <th className="text-right p-4 font-semibold">Reward</th>
                      <th className="text-right p-4 font-semibold">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history?.referrals.map((r) => (
                      <tr key={r.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                        <td className="p-4 font-medium">{r.referred_email}</td>
                        <td className="p-4 text-center">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            r.status === "completed"
                              ? "bg-green-100 dark:bg-green-900/30 text-green-600"
                              : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600"
                          }`}>
                            {r.status}
                          </span>
                        </td>
                        <td className="p-4 text-right font-medium">+{r.reward_credits}</td>
                        <td className="p-4 text-right text-gray-400 text-xs">
                          {r.completed_at ? new Date(r.completed_at).toLocaleDateString() : new Date(r.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}
