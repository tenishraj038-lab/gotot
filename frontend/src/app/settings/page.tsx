"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Settings, User, Lock, Bell, Save, Loader2 } from "lucide-react";
import { ListShimmer } from "@/components/LoadingShimmer";
import { api, loadTokens, setTokens, UserInfo } from "@/lib/api";
import { useStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

export default function SettingsPage() {
  const router = useRouter();
  const { user, setUser, setAuthModalOpen } = useStore();
  const [tab, setTab] = useState<"profile" | "password" | "notifications">("profile");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [username, setUsername] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [emailPrefs, setEmailPrefs] = useState({
    marketing: true,
    product_updates: true,
    security_alerts: true,
  });

  useEffect(() => {
    loadTokens();
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!token) {
      setAuthModalOpen(true);
      router.push("/");
      return;
    }
    fetchUserData();
  }, []);

  async function fetchUserData() {
    setLoading(true);
    try {
      const data = await api.getMe();
      setUser(data);
      setUsername(data.username);
      if (data.email_preferences) {
        setEmailPrefs({
          marketing: data.email_preferences.marketing ?? true,
          product_updates: data.email_preferences.product_updates ?? true,
          security_alerts: data.email_preferences.security_alerts ?? true,
        });
      }
    } catch {
      toast.error("Failed to load profile");
    }
    setLoading(false);
  }

  async function saveProfile() {
    if (!username.trim() || username.length < 3) {
      toast.error("Username must be at least 3 characters");
      return;
    }
    setSaving(true);
    try {
      const data = await api.updateProfile({ username: username.trim() });
      setUser(data);
      toast.success("Profile updated");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to update profile";
      toast.error(msg);
    }
    setSaving(false);
  }

  async function savePassword() {
    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    if (!/[A-Z]/.test(newPassword)) {
      toast.error("Password must contain an uppercase letter");
      return;
    }
    if (!/[0-9]/.test(newPassword)) {
      toast.error("Password must contain a digit");
      return;
    }
    setSaving(true);
    try {
      const data = await api.changePassword(currentPassword, newPassword);
      setTokens(data.access_token, data.refresh_token);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast.success("Password changed successfully");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to change password";
      toast.error(msg);
    }
    setSaving(false);
  }

  async function saveNotificationPrefs() {
    setSaving(true);
    try {
      const data = await api.updateProfile({ email_preferences: emailPrefs });
      setUser(data);
      toast.success("Notification preferences saved");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to save preferences";
      toast.error(msg);
    }
    setSaving(false);
  }

  const tabs = [
    { key: "profile" as const, label: "Profile", icon: User },
    { key: "password" as const, label: "Password", icon: Lock },
    { key: "notifications" as const, label: "Notifications", icon: Bell },
  ];

  if (loading) {
    return (
      <div className="pt-24 pb-16 max-w-3xl mx-auto px-4">
        <ListShimmer rows={6} />
      </div>
    );
  }

  return (
    <div className="pt-24 pb-16 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <Settings className="w-8 h-8 text-primary-500" />
          <h1 className="text-3xl font-bold">Settings</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mb-8">Manage your account settings and preferences</p>

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

        {tab === "profile" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6 space-y-6"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
              <input
                type="email"
                value={user?.email ?? ""}
                disabled
                className="w-full px-4 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-500 cursor-not-allowed"
              />
              <p className="text-xs text-gray-400 mt-1">Email cannot be changed</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Plan</label>
                <p className="text-lg font-semibold capitalize">{user?.role ?? "free"}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Member Since</label>
                <p className="text-lg font-semibold">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "-"}
                </p>
              </div>
            </div>

            <button
              onClick={saveProfile}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-all font-medium disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </motion.div>
        )}

        {tab === "password" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6 space-y-6"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Current Password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
              />
              <p className="text-xs text-gray-400 mt-1">Min 8 chars, 1 uppercase, 1 digit</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
              />
            </div>

            <button
              onClick={savePassword}
              disabled={saving || !currentPassword || !newPassword || !confirmPassword}
              className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-all font-medium disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
              {saving ? "Changing..." : "Change Password"}
            </button>
          </motion.div>
        )}

        {tab === "notifications" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6 space-y-6"
          >
            <p className="text-sm text-gray-500">Choose which emails you receive from GoTot</p>

            {[
              { key: "marketing", label: "Marketing emails", desc: "Tips, new features, and special offers" },
              { key: "product_updates", label: "Product updates", desc: "New platform support and feature releases" },
              { key: "security_alerts", label: "Security alerts", desc: "Login notifications and security warnings" },
            ].map(({ key, label, desc }) => (
              <label key={key} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800 cursor-pointer">
                <div>
                  <p className="font-medium text-sm">{label}</p>
                  <p className="text-xs text-gray-400">{desc}</p>
                </div>
                <input
                  type="checkbox"
                  checked={emailPrefs[key as keyof typeof emailPrefs]}
                  onChange={() =>
                    setEmailPrefs((prev) => ({ ...prev, [key]: !prev[key as keyof typeof emailPrefs] }))
                  }
                  className="w-5 h-5 rounded-lg text-primary-600 focus:ring-primary-500 cursor-pointer"
                />
              </label>
            ))}

            <button
              onClick={saveNotificationPrefs}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-all font-medium disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {saving ? "Saving..." : "Save Preferences"}
            </button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
