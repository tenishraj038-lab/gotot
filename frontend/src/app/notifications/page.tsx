"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { Bell, CheckCheck, Download, AlertTriangle, CreditCard, Users, Shield, Gift, Megaphone, ArrowUp, Loader2 } from "lucide-react";
import { api, loadTokens } from "@/lib/api";
import { useStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

interface NotificationItem {
  id: string;
  type: string;
  title: string;
  message: string;
  data: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}

const typeIcons: Record<string, typeof Bell> = {
  download_complete: Download,
  download_failed: AlertTriangle,
  subscription_expiring: CreditCard,
  payment_received: CreditCard,
  payment_failed: AlertTriangle,
  referral_reward: Gift,
  security_alert: Shield,
  admin_announcement: Megaphone,
  plan_upgrade: ArrowUp,
  welcome: Bell,
};

const typeColors: Record<string, string> = {
  download_complete: "from-blue-500 to-cyan-500",
  download_failed: "from-red-500 to-rose-500",
  subscription_expiring: "from-amber-500 to-orange-500",
  payment_received: "from-green-500 to-emerald-500",
  payment_failed: "from-red-500 to-rose-500",
  referral_reward: "from-purple-500 to-pink-500",
  security_alert: "from-red-500 to-orange-500",
  admin_announcement: "from-indigo-500 to-purple-500",
  plan_upgrade: "from-blue-500 to-indigo-500",
  welcome: "from-primary-500 to-accent-500",
};

export default function NotificationsPage() {
  const router = useRouter();
  const { setAuthModalOpen } = useStore();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const fetchId = useRef(0);

  useEffect(() => {
    loadTokens();
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      setAuthModalOpen(true);
      router.push("/");
      return;
    }
    fetchNotifications();
  }, [filter]);

  async function fetchNotifications() {
    const id = ++fetchId.current;
    setLoading(true);
    try {
      const data = await api.getNotifications(0, 50, filter === "unread");
      if (id !== fetchId.current) return; // stale response
      setNotifications(data.notifications);
      setUnread(data.unread);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load notifications");
    }
    setLoading(false);
  }

  async function markRead(id: string) {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnread((u) => Math.max(0, u - 1));
    } catch { /* ignore */ }
  }

  async function markAllRead() {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnread(0);
      toast.success("All marked as read");
    } catch {
      toast.error("Failed to mark all as read");
    }
  }

  function timeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return new Date(dateStr).toLocaleDateString();
  }

  return (
    <div className="pt-24 pb-16 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Bell className="w-8 h-8 text-primary-500" />
              <h1 className="text-3xl font-bold">Notifications</h1>
              {unread > 0 && (
                <span className="px-2.5 py-0.5 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 text-xs font-medium">
                  {unread} new
                </span>
              )}
            </div>
            <p className="text-gray-500 dark:text-gray-400">Stay updated with your activity</p>
          </div>
          {unread > 0 && (
            <button
              onClick={markAllRead}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl text-sm font-medium transition-all"
            >
              <CheckCheck className="w-4 h-4" />
              Mark All Read
            </button>
          )}
        </div>

        <div className="flex gap-2 mb-6">
          {(["all", "unread"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                filter === f
                  ? "bg-primary-600 text-white shadow-lg"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
              }`}
            >
              {f === "all" ? "All" : `Unread (${unread})`}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-24 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-16">
            <Bell className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-500">No notifications</p>
            <p className="text-sm text-gray-400">You're all caught up!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map((n) => {
              const Icon = typeIcons[n.type] || Bell;
              const color = typeColors[n.type] || "from-gray-400 to-gray-600";
              return (
                <motion.div
                  key={n.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  onClick={() => !n.is_read && markRead(n.id)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    n.is_read
                      ? "bg-white dark:bg-gray-900 border-gray-200/50 dark:border-gray-800/50"
                      : "bg-primary-50/50 dark:bg-primary-900/10 border-primary-200/50 dark:border-primary-800/50"
                  }`}
                >
                  <div className="flex gap-4">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} p-2 flex-shrink-0`}>
                      <Icon className="w-full h-full text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className={`font-medium text-sm ${n.is_read ? "text-gray-600 dark:text-gray-400" : "text-gray-900 dark:text-white"}`}>
                          {n.title}
                        </p>
                        <span className="text-xs text-gray-400 flex-shrink-0">{timeAgo(n.created_at)}</span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{n.message}</p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.div>
    </div>
  );
}
