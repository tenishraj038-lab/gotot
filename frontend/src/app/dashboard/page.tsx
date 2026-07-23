"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import {
  User, CreditCard, Key, Gift, Download, LogOut,
  Copy, Check, Loader2, Plus, X, ExternalLink, Clock,
  Shield, Zap, TrendingUp,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { api, loadTokens, clearTokens, ApiKeyInfo, PaymentRecord, ReferralInfo, UserInfo } from "@/lib/api";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

type Tab = "overview" | "api-keys" | "billing" | "referrals" | "history";

export default function DashboardPage() {
  const router = useRouter();
  const { user, setUser, subscription, setSubscription, setAuthModalOpen } = useStore();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>([]);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [referral, setReferral] = useState<ReferralInfo | null>(null);
  const [history, setHistory] = useState<Array<{ id: string; url: string; platform: string; format: string; status: string; file_size: number | null; created_at: string | null }>>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [creatingKey, setCreatingKey] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [refCode, setRefCode] = useState("");

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    loadTokens();
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      setAuthModalOpen(true);
      router.push("/");
      return;
    }
    loadDashboard();
    return () => { mounted.current = false; };
  }, []);

  const loadDashboard = async () => {
    try {
      const [me, sub, keys, pays, ref, hist] = await Promise.all([
        api.getMe().catch(() => null),
        api.getSubscriptionStatus().catch(() => null),
        api.listApiKeys().catch(() => []),
        api.getPaymentHistory().catch(() => []),
        api.getReferralCode().catch(() => null),
        api.getDownloadHistory().catch(() => []),
      ]);
      if (me) setUser(me);
      if (sub) setSubscription(sub);
      setApiKeys(keys);
      setPayments(pays);
      setReferral(ref);
      setHistory(hist);
    } catch {
      toast.error("Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async () => {
    if (!newKeyName.trim()) return;
    setCreatingKey(true);
    try {
      const result = await api.createApiKey(newKeyName.trim());
      setCopiedKey(result.key);
      toast.success("API key created!");
      setNewKeyName("");
      const keys = await api.listApiKeys();
      setApiKeys(keys);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create key");
    } finally {
      setCreatingKey(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    try {
      await api.revokeApiKey(keyId);
      toast.success("API key revoked");
      setApiKeys(apiKeys.filter((k) => k.id !== keyId));
    } catch {
      toast.error("Failed to revoke key");
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(text);
    setTimeout(() => setCopiedKey(null), 2000);
    toast.success("Copied!");
  };

  const handleApplyReferral = async () => {
    if (!refCode.trim()) return;
    try {
      const result = await api.applyReferralCode(refCode.trim());
      toast.success(`Referral applied! +${result.bonus_downloads} bonus downloads`);
      setRefCode("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Invalid code");
    }
  };

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    setSubscription(null);
    toast.success("Logged out");
    router.push("/");
  };

  if (loading) {
    return (
      <div className="pt-32 flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "overview", label: "Overview", icon: <User className="w-4 h-4" /> },
    { id: "api-keys", label: "API Keys", icon: <Key className="w-4 h-4" /> },
    { id: "billing", label: "Billing", icon: <CreditCard className="w-4 h-4" /> },
    { id: "referrals", label: "Referrals", icon: <Gift className="w-4 h-4" /> },
    { id: "history", label: "History", icon: <Clock className="w-4 h-4" /> },
  ];

  const dailyPercent = user ? Math.min((user.downloads_today / user.daily_download_limit) * 100, 100) : 0;

  return (
    <div className="pt-32 pb-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              {user ? `Welcome, ${user.username}` : "Manage your account and settings"}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all text-sm"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-1">
            <nav className="space-y-1 sticky top-24">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? "bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                      : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="lg:col-span-3">
            {activeTab === "overview" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                  <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center">
                        <Shield className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Plan</p>
                        <p className="text-sm font-semibold capitalize">{subscription?.tier || user?.role || "Free"}</p>
                      </div>
                    </div>
                    {(subscription?.tier === "free" || (!subscription && user?.role === "free")) && (
                      <a href="/pricing" className="text-xs text-primary-600 hover:underline mt-2 inline-block">Upgrade</a>
                    )}
                  </div>
                  <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
                        <Download className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Downloads Today</p>
                        <p className="text-sm font-semibold">{user?.downloads_today || 0} / {user?.daily_download_limit || subscription?.daily_downloads || 5}</p>
                      </div>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-gray-200 dark:bg-gray-800 mt-2 overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all" style={{ width: `${dailyPercent}%` }} />
                    </div>
                  </div>
                  <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                        <TrendingUp className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Total Downloads</p>
                        <p className="text-sm font-semibold">{user?.total_downloads || 0}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                  <h3 className="font-semibold mb-4">Quick Actions</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <a href="/pricing" className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                      <Zap className="w-5 h-5 text-primary-500" />
                      <span className="text-sm font-medium">Upgrade Plan</span>
                    </a>
                    <button onClick={() => setActiveTab("api-keys")} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left">
                      <Key className="w-5 h-5 text-accent-500" />
                      <span className="text-sm font-medium">Create API Key</span>
                    </button>
                    <button onClick={() => setActiveTab("referrals")} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left">
                      <Gift className="w-5 h-5 text-green-500" />
                      <span className="text-sm font-medium">Refer a Friend</span>
                    </button>
                    <button onClick={() => setActiveTab("billing")} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left">
                      <CreditCard className="w-5 h-5 text-blue-500" />
                      <span className="text-sm font-medium">Billing History</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === "api-keys" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                  <h3 className="font-semibold mb-4">Create API Key</h3>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                      placeholder="e.g., My App"
                      className="flex-1 px-4 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-primary-500/50 outline-none text-sm"
                    />
                    <button
                      onClick={handleCreateApiKey}
                      disabled={creatingKey || !newKeyName.trim()}
                      className="px-6 py-2.5 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white font-semibold rounded-xl transition-all disabled:opacity-50 flex items-center gap-2"
                    >
                      {creatingKey ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                      Create
                    </button>
                  </div>
                  {copiedKey && (
                    <div className="mt-3 p-3 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/50">
                      <p className="text-xs font-medium text-green-800 dark:text-green-200 mb-1">Key created! Copy it now - it won&apos;t be shown again:</p>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 text-xs bg-white dark:bg-gray-800 px-3 py-1.5 rounded-lg border border-green-200 dark:border-green-800/50 font-mono break-all">{copiedKey}</code>
                        <button onClick={() => handleCopy(copiedKey)} className="p-1.5 rounded-lg hover:bg-green-100 dark:hover:bg-green-800/50">
                          <Check className="w-4 h-4 text-green-600" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                  <h3 className="font-semibold mb-4">Your API Keys ({apiKeys.length})</h3>
                  {apiKeys.length === 0 ? (
                    <p className="text-sm text-gray-500">No API keys yet. Create one above.</p>
                  ) : (
                    <div className="space-y-3">
                      {apiKeys.map((key) => (
                        <div key={key.id} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
                          <div>
                            <p className="text-sm font-medium">{key.name}</p>
                            <div className="flex items-center gap-3 mt-1">
                              <code className="text-xs text-gray-500 font-mono">{key.prefix}</code>
                              <span className="text-xs text-gray-400">{key.requests_count}/{key.daily_limit} requests today</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              key.is_active ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                            }`}>
                              {key.is_active ? "Active" : "Revoked"}
                            </span>
                            {key.is_active && (
                              <button
                                onClick={() => handleRevokeKey(key.id)}
                                className="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === "billing" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                  <h3 className="font-semibold mb-4">Subscription</h3>
                  <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800">
                    <div>
                      <p className="text-sm font-medium capitalize">Current Plan: {subscription?.tier || user?.role || "Free"}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {subscription?.current_period_end
                          ? `Renews ${new Date(subscription.current_period_end).toLocaleDateString()}`
                          : "No active subscription"}
                      </p>
                    </div>
                    <a
                      href="/pricing"
                      className="px-4 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white text-sm font-medium rounded-xl hover:from-primary-500 hover:to-accent-500 transition-all"
                    >
                      {(subscription?.tier === "free" || (!subscription && user?.role === "free")) ? "Upgrade" : "Manage"}
                    </a>
                  </div>
                </div>

                <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                  <h3 className="font-semibold mb-4">Payment History</h3>
                  {payments.length === 0 ? (
                    <p className="text-sm text-gray-500">No payments yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {payments.map((p) => (
                        <div key={p.id} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
                          <div>
                            <p className="text-sm font-medium capitalize">{p.payment_type.replace("_", " ")}</p>
                            <p className="text-xs text-gray-500">{new Date(p.created_at).toLocaleDateString()}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold">${p.amount.toFixed(2)}</p>
                            <span className={`text-xs px-1.5 py-0.5 rounded ${
                              p.status === "completed" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" :
                              p.status === "failed" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"
                            }`}>
                              {p.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === "referrals" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                  <h3 className="font-semibold mb-4">Your Referral Link</h3>
                  <p className="text-sm text-gray-500 mb-4">Share your referral link and earn free downloads when friends sign up!</p>
                  {referral && (
                    <div className="flex items-center gap-3">
                      <input
                        type="text"
                        value={referral.referral_url}
                        readOnly
                        className="flex-1 px-4 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm font-mono"
                      />
                      <button
                        onClick={() => handleCopy(referral.referral_url)}
                        className="p-2.5 rounded-xl bg-primary-50 dark:bg-primary-900/30 text-primary-600 hover:bg-primary-100 dark:hover:bg-primary-900/50 transition-colors"
                      >
                        {copiedKey === referral.referral_url ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                  )}
                  <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-primary-50 to-accent-50 dark:from-primary-900/20 dark:to-accent-900/20 border border-primary-200 dark:border-primary-800/50">
                    <p className="text-sm font-medium text-primary-700 dark:text-primary-300">
                      {referral?.reward_per_referral || "+3 free downloads per referral"} &middot; {referral?.total_referred || 0} friends referred
                    </p>
                  </div>
                </div>

                <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                  <h3 className="font-semibold mb-4">Have a Referral Code?</h3>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={refCode}
                      onChange={(e) => setRefCode(e.target.value)}
                      placeholder="Enter referral code (e.g., GOTOTABC123)"
                      className="flex-1 px-4 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-primary-500/50 outline-none text-sm uppercase"
                    />
                    <button
                      onClick={handleApplyReferral}
                      disabled={!refCode.trim()}
                      className="px-6 py-2.5 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white font-semibold rounded-xl transition-all disabled:opacity-50"
                    >
                      Apply
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === "history" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                  <h3 className="font-semibold mb-4">Download History</h3>
                  {history.length === 0 ? (
                    <p className="text-sm text-gray-500">No downloads yet. Start downloading to see your history here.</p>
                  ) : (
                    <div className="space-y-2">
                      {history.map((h) => (
                        <div key={h.id} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium truncate">{h.url}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs px-2 py-0.5 rounded-full bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 capitalize">{h.platform}</span>
                              <span className="text-xs text-gray-500">{h.format.toUpperCase()}</span>
                              {h.file_size && <span className="text-xs text-gray-400">{(h.file_size / 1024 / 1024).toFixed(1)} MB</span>}
                            </div>
                          </div>
                          <div className="text-right shrink-0 ml-4">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              h.status === "completed" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" : "bg-red-100 text-red-700"
                            }`}>
                              {h.status}
                            </span>
                            {h.created_at && <p className="text-xs text-gray-400 mt-1">{new Date(h.created_at).toLocaleDateString()}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
