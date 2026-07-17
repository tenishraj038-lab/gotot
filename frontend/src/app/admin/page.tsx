"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Users, CreditCard, TrendingUp, Ban, CheckCircle, XCircle, Shield } from "lucide-react";
import { ListShimmer } from "@/components/LoadingShimmer";
import { api, loadTokens } from "@/lib/api";
import { useStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

interface AdminStats {
  total_users: number;
  total_downloads: number;
  total_revenue: number;
  active_subscriptions: number;
  pro_users: number;
  unlimited_users: number;
  api_keys_count: number;
  completed_referrals: number;
}

interface AdminUser {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  downloads_today: number;
  created_at: string;
}

interface AdminSub {
  id: string;
  user_id: string;
  plan_id: string;
  status: string;
  current_period_start: string | null;
  current_period_end: string | null;
}

export default function AdminPage() {
  const router = useRouter();
  const { user, setAuthModalOpen } = useStore();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [subs, setSubs] = useState<AdminSub[]>([]);
  const [tab, setTab] = useState<"overview" | "users" | "subscriptions">("overview");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTokens();
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      setAuthModalOpen(true);
      router.push("/");
      return;
    }
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [statsRes, usersRes, subsRes] = await Promise.all([
        api.getAdminStats().catch(() => null),
        api.getAdminUsers().catch(() => []),
        api.getAdminSubscriptions().catch(() => []),
      ]);
      if (statsRes) setStats(statsRes);
      if (usersRes) setUsers(usersRes);
      if (subsRes) setSubs(subsRes);
    } catch {
      toast.error("Failed to load admin data. Are you an admin?");
    }
    setLoading(false);
  }

  async function toggleBan(userId: string) {
    try {
      await api.toggleUserBan(userId);
      toast.success("User status updated");
      fetchData();
    } catch {
      toast.error("Failed to toggle ban");
    }
  }

  async function cancelSub(subId: string) {
    try {
      await api.cancelSubscriptionAdmin(subId);
      toast.success("Subscription cancelled");
      fetchData();
    } catch {
      toast.error("Failed to cancel subscription");
    }
  }

  const tabs = [
    { key: "overview" as const, label: "Overview", icon: TrendingUp },
    { key: "users" as const, label: "Users", icon: Users },
    { key: "subscriptions" as const, label: "Subscriptions", icon: CreditCard },
  ];

  return (
    <div className="pt-24 pb-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-8 h-8 text-primary-500" />
          <h1 className="text-3xl font-bold">Admin Panel</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mb-8">Manage users, subscriptions, and view analytics</p>

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

        {loading && <ListShimmer rows={5} />}

        {!loading && tab === "overview" && stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[
              { label: "Total Users", value: stats.total_users.toLocaleString(), icon: Users, color: "from-blue-500 to-cyan-500" },
              { label: "Active Subscriptions", value: stats.active_subscriptions.toLocaleString(), icon: CreditCard, color: "from-green-500 to-emerald-500" },
              { label: "Total Revenue", value: `$${stats.total_revenue}`, icon: TrendingUp, color: "from-amber-500 to-orange-500" },
              { label: "Total Downloads", value: stats.total_downloads.toLocaleString(), icon: TrendingUp, color: "from-purple-500 to-pink-500" },
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
          </div>
        )}

        {!loading && tab === "users" && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                    <th className="text-left p-4 font-semibold">Email</th>
                    <th className="text-left p-4 font-semibold">Username</th>
                    <th className="text-left p-4 font-semibold">Tier</th>
                    <th className="text-center p-4 font-semibold">Active</th>
                    <th className="text-center p-4 font-semibold">Admin</th>
                    <th className="text-center p-4 font-semibold">Downloads</th>
                    <th className="text-right p-4 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="p-4 font-medium">{u.email}</td>
                      <td className="p-4 text-gray-500">{u.username}</td>
                      <td className="p-4 capitalize">{u.role}</td>
                      <td className="p-4 text-center">
                        {u.is_active ? <CheckCircle className="w-4 h-4 text-green-500 inline" /> : <XCircle className="w-4 h-4 text-red-500 inline" />}
                      </td>
                      <td className="p-4 text-center">
                        {u.role === "admin" ? <CheckCircle className="w-4 h-4 text-green-500 inline" /> : <XCircle className="w-4 h-4 text-gray-400 inline" />}
                      </td>
                      <td className="p-4 text-center">{u.downloads_today}</td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => toggleBan(u.id)}
                          className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                            u.is_active
                              ? "bg-red-100 dark:bg-red-900/30 text-red-600 hover:bg-red-200"
                              : "bg-green-100 dark:bg-green-900/30 text-green-600 hover:bg-green-200"
                          }`}
                        >
                          <Ban className="w-3 h-3" />
                          {u.is_active ? "Ban" : "Unban"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!loading && tab === "subscriptions" && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                    <th className="text-left p-4 font-semibold">ID</th>
                    <th className="text-left p-4 font-semibold">Plan</th>
                    <th className="text-center p-4 font-semibold">Status</th>
                    <th className="text-left p-4 font-semibold">Start</th>
                    <th className="text-left p-4 font-semibold">End</th>
                    <th className="text-right p-4 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {subs.map((s) => (
                    <tr key={s.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="p-4 font-mono text-xs">{s.id.substring(0, 8)}...</td>
                      <td className="p-4 capitalize">{s.plan_id.replace(/_/g, " ")}</td>
                      <td className="p-4 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          s.status === "active" ? "bg-green-100 dark:bg-green-900/30 text-green-600" :
                          s.status === "canceled" ? "bg-red-100 dark:bg-red-900/30 text-red-600" :
                          "bg-gray-100 dark:bg-gray-800 text-gray-500"
                        }`}>
                          {s.status}
                        </span>
                      </td>
                      <td className="p-4 text-xs">{s.current_period_start ? new Date(s.current_period_start).toLocaleDateString() : "-"}</td>
                      <td className="p-4 text-xs">{s.current_period_end ? new Date(s.current_period_end).toLocaleDateString() : "-"}</td>
                      <td className="p-4 text-right">
                        {s.status === "active" && (
                          <button
                            onClick={() => cancelSub(s.id)}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-600 hover:bg-red-200 text-xs font-medium transition-all"
                          >
                            <XCircle className="w-3 h-3" />
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
