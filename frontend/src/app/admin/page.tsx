"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Users, CreditCard, TrendingUp, Ban, CheckCircle, XCircle, Shield, Flag, Activity, BarChart, Plus, Trash2, ExternalLink, DollarSign, MousePointer } from "lucide-react";
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

interface FeatureFlag {
  id: string;
  key: string;
  name: string;
  description: string | null;
  enabled: boolean;
  updated_at: string;
}

interface HealthCheck {
  database?: string;
  redis?: string;
  environment?: string;
  version?: string;
  [key: string]: string | undefined;
}

interface DownloadAnalytics {
  total: number;
  days: number;
  by_platform: Record<string, number>;
  by_format: Record<string, number>;
  daily: Array<{ date: string; count: number }>;
}

export default function AdminPage() {
  const router = useRouter();
  const { user, setAuthModalOpen } = useStore();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [subs, setSubs] = useState<AdminSub[]>([]);
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [analytics, setAnalytics] = useState<DownloadAnalytics | null>(null);
  const [tab, setTab] = useState<"overview" | "users" | "subscriptions" | "flags" | "health" | "analytics" | "affiliates">("overview");
  const [loading, setLoading] = useState(true);
  const [newFlagKey, setNewFlagKey] = useState("");
  const [newFlagName, setNewFlagName] = useState("");
  const [newFlagDesc, setNewFlagDesc] = useState("");

  const [affiliates, setAffiliates] = useState<Array<{
    id: string; platform: string; name: string; url: string;
    description: string | null; commission_rate: string | null;
    is_active: boolean; clicks: number; created_at: string;
  }>>([]);
  const [affForm, setAffForm] = useState({ platform: "", name: "", url: "", description: "", commission_rate: "" });
  const [editingAff, setEditingAff] = useState<string | null>(null);

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
      const [statsRes, usersRes, subsRes, flagsRes, healthRes, analyticsRes, affRes] = await Promise.all([
        api.getAdminStats().catch(() => null),
        api.getAdminUsers().catch(() => []),
        api.getAdminSubscriptions().catch(() => []),
        api.getAdminFeatureFlags().catch(() => []),
        api.getAdminSystemHealth().catch(() => null),
        api.getAdminDownloadAnalytics().catch(() => null),
        api.getAdminAffiliates().catch(() => null),
      ]);
      if (statsRes) setStats(statsRes);
      if (usersRes) setUsers(usersRes);
      if (subsRes) setSubs(subsRes);
      if (flagsRes) setFlags(flagsRes);
      if (healthRes) setHealth(healthRes);
      if (analyticsRes) setAnalytics(analyticsRes);
      if (affRes) setAffiliates(affRes.affiliates);
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

  async function toggleFlag(flagId: string, enabled: boolean) {
    try {
      await api.toggleAdminFeatureFlag(flagId, !enabled);
      toast.success("Feature flag toggled");
      fetchData();
    } catch {
      toast.error("Failed to toggle feature flag");
    }
  }

  async function createFlag() {
    if (!newFlagKey.trim() || !newFlagName.trim()) {
      toast.error("Key and name are required");
      return;
    }
    try {
      await api.createAdminFeatureFlag({
        key: newFlagKey.trim(),
        name: newFlagName.trim(),
        description: newFlagDesc.trim() || undefined,
      });
      toast.success("Feature flag created");
      setNewFlagKey("");
      setNewFlagName("");
      setNewFlagDesc("");
      fetchData();
    } catch {
      toast.error("Failed to create feature flag");
    }
  }

  const healthColor = (status: string) => {
    if (status === "healthy") return "text-green-500";
    if (status?.startsWith("unhealthy")) return "text-red-500";
    return "text-yellow-500";
  };

  async function createAffiliate() {
    if (!affForm.platform || !affForm.name || !affForm.url) {
      toast.error("Platform, name, and URL are required");
      return;
    }
    try {
      await api.createAdminAffiliate({
        platform: affForm.platform,
        name: affForm.name,
        url: affForm.url,
        description: affForm.description || undefined,
        commission_rate: affForm.commission_rate || undefined,
      });
      toast.success("Affiliate link created");
      setAffForm({ platform: "", name: "", url: "", description: "", commission_rate: "" });
      fetchData();
    } catch { toast.error("Failed to create affiliate link"); }
  }

  async function updateAffiliateToggle(linkId: string, isActive: boolean) {
    try {
      await api.updateAdminAffiliate(linkId, { is_active: !isActive });
      toast.success("Affiliate link updated");
      fetchData();
    } catch { toast.error("Failed to update"); }
  }

  async function deleteAffiliate(linkId: string) {
    if (!confirm("Delete this affiliate link?")) return;
    try {
      await api.deleteAdminAffiliate(linkId);
      toast.success("Affiliate link deleted");
      fetchData();
    } catch { toast.error("Failed to delete"); }
  }

  const tabs = [
    { key: "overview" as const, label: "Overview", icon: TrendingUp },
    { key: "users" as const, label: "Users", icon: Users },
    { key: "subscriptions" as const, label: "Subscriptions", icon: CreditCard },
    { key: "flags" as const, label: "Feature Flags", icon: Flag },
    { key: "health" as const, label: "System Health", icon: Activity },
    { key: "analytics" as const, label: "Analytics", icon: BarChart },
    { key: "affiliates" as const, label: "Affiliates", icon: DollarSign },
  ];

  return (
    <div className="pt-24 pb-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-8 h-8 text-primary-500" />
          <h1 className="text-3xl font-bold">Admin Panel</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mb-8">Manage users, subscriptions, feature flags, and view analytics</p>

        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all flex-shrink-0 ${
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

        {!loading && tab === "flags" && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Plus className="w-5 h-5 text-primary-500" />
                New Feature Flag
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
                <input
                  placeholder="Key (e.g., new_downloader)"
                  value={newFlagKey}
                  onChange={(e) => setNewFlagKey(e.target.value)}
                  className="px-4 py-2 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                />
                <input
                  placeholder="Name (e.g., New Downloader)"
                  value={newFlagName}
                  onChange={(e) => setNewFlagName(e.target.value)}
                  className="px-4 py-2 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                />
                <input
                  placeholder="Description (optional)"
                  value={newFlagDesc}
                  onChange={(e) => setNewFlagDesc(e.target.value)}
                  className="px-4 py-2 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                />
              </div>
              <button
                onClick={createFlag}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 text-sm font-medium transition-all"
              >
                <Plus className="w-4 h-4" />
                Create Flag
              </button>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                    <th className="text-left p-4 font-semibold">Key</th>
                    <th className="text-left p-4 font-semibold">Name</th>
                    <th className="text-left p-4 font-semibold">Description</th>
                    <th className="text-center p-4 font-semibold">Enabled</th>
                    <th className="text-right p-4 font-semibold">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {flags.length === 0 && (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-gray-400">No feature flags yet</td>
                    </tr>
                  )}
                  {flags.map((f) => (
                    <tr key={f.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="p-4 font-mono text-xs">{f.key}</td>
                      <td className="p-4 font-medium">{f.name}</td>
                      <td className="p-4 text-gray-500 text-xs">{f.description || "-"}</td>
                      <td className="p-4 text-center">
                        <button
                          onClick={() => toggleFlag(f.id, f.enabled)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            f.enabled ? "bg-green-500" : "bg-gray-300 dark:bg-gray-600"
                          }`}
                        >
                          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            f.enabled ? "translate-x-6" : "translate-x-1"
                          }`} />
                        </button>
                      </td>
                      <td className="p-4 text-right text-xs text-gray-400">
                        {new Date(f.updated_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!loading && tab === "health" && health && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(health).map(([key, value]) => (
              <div key={key} className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-3 h-3 rounded-full ${
                    value === "healthy" ? "bg-green-500" :
                    value?.startsWith("unhealthy") ? "bg-red-500" : "bg-yellow-400"
                  }`} />
                  <p className="font-semibold capitalize">{key.replace(/_/g, " ")}</p>
                </div>
                <p className={`text-sm ${healthColor(value ?? "")}`}>{value}</p>
              </div>
            ))}
          </div>
        )}

        {!loading && tab === "affiliates" && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Plus className="w-5 h-5 text-primary-500" />
                {editingAff ? "Edit Affiliate Link" : "New Affiliate Link"}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mb-3">
                <input placeholder="Platform" value={affForm.platform} onChange={(e) => setAffForm(p => ({ ...p, platform: e.target.value }))}
                  className="px-3 py-2 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                <input placeholder="Name" value={affForm.name} onChange={(e) => setAffForm(p => ({ ...p, name: e.target.value }))}
                  className="px-3 py-2 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                <input placeholder="URL" value={affForm.url} onChange={(e) => setAffForm(p => ({ ...p, url: e.target.value }))}
                  className="px-3 py-2 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                <input placeholder="Description" value={affForm.description} onChange={(e) => setAffForm(p => ({ ...p, description: e.target.value }))}
                  className="px-3 py-2 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                <input placeholder="Commission %" value={affForm.commission_rate} onChange={(e) => setAffForm(p => ({ ...p, commission_rate: e.target.value }))}
                  className="px-3 py-2 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
              </div>
              <button onClick={createAffiliate}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 text-sm font-medium transition-all">
                <Plus className="w-4 h-4" /> Create Affiliate
              </button>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                    <th className="text-left p-4 font-semibold">Platform</th>
                    <th className="text-left p-4 font-semibold">Name</th>
                    <th className="text-left p-4 font-semibold">URL</th>
                    <th className="text-center p-4 font-semibold">Commission</th>
                    <th className="text-center p-4 font-semibold">Clicks</th>
                    <th className="text-center p-4 font-semibold">Active</th>
                    <th className="text-right p-4 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {affiliates.length === 0 && (
                    <tr><td colSpan={7} className="p-8 text-center text-gray-400">No affiliate links yet</td></tr>
                  )}
                  {affiliates.map((a) => (
                    <tr key={a.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="p-4 font-medium capitalize">{a.platform}</td>
                      <td className="p-4">{a.name}</td>
                      <td className="p-4">
                        <a href={a.url} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-1 text-primary-500 hover:text-primary-600 text-xs">
                          {a.url.substring(0, 30)}... <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                      <td className="p-4 text-center">{a.commission_rate || "-"}</td>
                      <td className="p-4 text-center">
                        <span className="flex items-center justify-center gap-1">
                          <MousePointer className="w-3 h-3 text-gray-400" />
                          {a.clicks}
                        </span>
                      </td>
                      <td className="p-4 text-center">
                        <button onClick={() => updateAffiliateToggle(a.id, a.is_active)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            a.is_active ? "bg-green-500" : "bg-gray-300 dark:bg-gray-600"
                          }`}>
                          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            a.is_active ? "translate-x-6" : "translate-x-1"
                          }`} />
                        </button>
                      </td>
                      <td className="p-4 text-right">
                        <button onClick={() => deleteAffiliate(a.id)}
                          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-600 hover:bg-red-200 text-xs font-medium transition-all">
                          <Trash2 className="w-3 h-3" /> Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!loading && tab === "analytics" && analytics && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                <p className="text-sm text-gray-500 mb-1">Total Downloads</p>
                <p className="text-2xl font-bold">{analytics.total.toLocaleString()}</p>
                <p className="text-xs text-gray-400">Last {analytics.days} days</p>
              </div>
              <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                <p className="text-sm text-gray-500 mb-1">Platforms Used</p>
                <p className="text-2xl font-bold">{Object.keys(analytics.by_platform).length}</p>
              </div>
              <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                <p className="text-sm text-gray-500 mb-1">Formats</p>
                <p className="text-2xl font-bold">{Object.keys(analytics.by_format).length}</p>
              </div>
              <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                <p className="text-sm text-gray-500 mb-1">Avg Daily</p>
                <p className="text-2xl font-bold">
                  {Math.round(analytics.total / Math.max(analytics.daily.length, 1))}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6">
                <h3 className="text-lg font-semibold mb-4">Downloads by Platform</h3>
                {Object.entries(analytics.by_platform).length === 0 ? (
                  <p className="text-gray-400 text-sm">No data yet</p>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(analytics.by_platform)
                      .sort(([, a], [, b]) => b - a)
                      .map(([platform, count]) => {
                        const max = Math.max(...Object.values(analytics.by_platform));
                        const pct = Math.round((count / max) * 100);
                        return (
                          <div key={platform}>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="capitalize">{platform}</span>
                              <span className="text-gray-500">{count.toLocaleString()}</span>
                            </div>
                            <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                              <div className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>

              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6">
                <h3 className="text-lg font-semibold mb-4">Downloads by Format</h3>
                {Object.entries(analytics.by_format).length === 0 ? (
                  <p className="text-gray-400 text-sm">No data yet</p>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(analytics.by_format)
                      .sort(([, a], [, b]) => b - a)
                      .map(([fmt, count]) => {
                        const max = Math.max(...Object.values(analytics.by_format));
                        const pct = Math.round((count / max) * 100);
                        return (
                          <div key={fmt}>
                            <div className="flex justify-between text-sm mb-1">
                              <span>{fmt}</span>
                              <span className="text-gray-500">{count.toLocaleString()}</span>
                            </div>
                            <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                              <div className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6">
              <h3 className="text-lg font-semibold mb-4">Daily Downloads (Last {analytics.days} Days)</h3>
              {analytics.daily.length === 0 ? (
                <p className="text-gray-400 text-sm">No data yet</p>
              ) : (
                <div className="h-48 flex items-end gap-1">
                  {analytics.daily.map((d) => {
                    const max = Math.max(...analytics.daily.map((x) => x.count));
                    const height = max > 0 ? (d.count / max) * 100 : 0;
                    return (
                      <div key={d.date} className="flex-1 flex flex-col items-center gap-1 min-w-0">
                        <span className="text-[10px] text-gray-400">{d.count}</span>
                        <div
                          className="w-full bg-gradient-to-t from-primary-500 to-accent-500 rounded-t transition-all"
                          style={{ height: `${Math.max(height, 2)}%` }}
                        />
                        <span className="text-[10px] text-gray-400 truncate w-full text-center">
                          {new Date(d.date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
