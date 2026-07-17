"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CreditCard, Receipt, AlertTriangle, XCircle, Download, RefreshCw, ArrowLeft, CheckCircle, Clock, Loader2 } from "lucide-react";
import { api, loadTokens, PaymentRecord, SubscriptionStatus } from "@/lib/api";
import { useStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";

export default function BillingPage() {
  const router = useRouter();
  const { subscription, setSubscription, user, setAuthModalOpen } = useStore();
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

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
      const [paymentsData, subData] = await Promise.all([
        api.getPaymentHistory(),
        api.getSubscriptionStatus().catch(() => null),
      ]);
      setPayments(paymentsData);
      if (subData) setSubscription(subData);
    } catch {
      // ignore
    }
    setLoading(false);
  }

  async function handleCancel() {
    if (!confirm("Are you sure you want to cancel your subscription? You'll lose premium features at the end of your billing period.")) return;
    setCancelling(true);
    try {
      await api.cancelSubscription();
      toast.success("Subscription cancelled");
      fetchData();
    } catch {
      toast.error("Failed to cancel subscription");
    }
    setCancelling(false);
  }

  const currentPlan = subscription?.tier || user?.role || "free";

  return (
    <div className="pt-24 pb-16 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <CreditCard className="w-8 h-8 text-primary-500" />
          <h1 className="text-3xl font-bold">Billing</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mb-8">Manage your subscription, view invoices and payment history</p>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-8">
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-primary-500" />
                Current Plan
              </h2>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <p className="text-2xl font-bold capitalize">{currentPlan}</p>
                  <p className="text-sm text-gray-500">
                    {subscription?.is_active ? (
                      <>Active until {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : "N/A"}</>
                    ) : currentPlan === "free" ? (
                      "Free plan - upgrade for more features"
                    ) : (
                      "No active subscription"
                    )}
                  </p>
                </div>
                <div className="flex gap-2">
                  {currentPlan !== "free" && subscription?.is_active && (
                    <button
                      onClick={handleCancel}
                      disabled={cancelling}
                      className="flex items-center gap-2 px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 hover:bg-red-200 dark:hover:bg-red-900/50 rounded-xl text-sm font-medium transition-all disabled:opacity-50"
                    >
                      {cancelling ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                      Cancel Subscription
                    </button>
                  )}
                  {currentPlan === "free" && (
                    <Link
                      href="/pricing"
                      className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 text-sm font-medium transition-all"
                    >
                      Upgrade Plan
                    </Link>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Receipt className="w-5 h-5 text-primary-500" />
                Payment History
              </h2>
              {payments.length === 0 ? (
                <p className="text-gray-400 text-sm py-4 text-center">No payments yet</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-800">
                        <th className="text-left p-3 font-semibold">Date</th>
                        <th className="text-left p-3 font-semibold">Description</th>
                        <th className="text-center p-3 font-semibold">Amount</th>
                        <th className="text-center p-3 font-semibold">Status</th>
                        <th className="text-center p-3 font-semibold">Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payments.map((p) => (
                        <tr key={p.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                          <td className="p-3 text-gray-500 text-xs">{new Date(p.created_at).toLocaleDateString()}</td>
                          <td className="p-3">{p.description || p.payment_type.replace(/_/g, " ")}</td>
                          <td className="p-3 text-right font-medium">{p.currency} {p.amount}</td>
                          <td className="p-3 text-center">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                              p.status === "completed" ? "bg-green-100 dark:bg-green-900/30 text-green-600" :
                              p.status === "failed" ? "bg-red-100 dark:bg-red-900/30 text-red-600" :
                              p.status === "refunded" ? "bg-amber-100 dark:bg-amber-900/30 text-amber-600" :
                              "bg-gray-100 dark:bg-gray-800 text-gray-500"
                            }`}>
                              {p.status === "completed" && <CheckCircle className="w-3 h-3" />}
                              {p.status === "failed" && <AlertTriangle className="w-3 h-3" />}
                              {p.status === "refunded" && <RefreshCw className="w-3 h-3" />}
                              {p.status}
                            </span>
                          </td>
                          <td className="p-3 text-center text-xs text-gray-500 capitalize">{p.payment_type.replace(/_/g, " ")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 text-center">
                <p className="text-2xl font-bold text-green-500">{payments.filter((p) => p.status === "completed").length}</p>
                <p className="text-sm text-gray-500">Completed</p>
              </div>
              <div className="p-4 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 text-center">
                <p className="text-2xl font-bold text-red-500">{payments.filter((p) => p.status === "failed").length}</p>
                <p className="text-sm text-gray-500">Failed</p>
              </div>
              <div className="p-4 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 text-center">
                <p className="text-2xl font-bold text-amber-500">{payments.filter((p) => p.status === "refunded").length}</p>
                <p className="text-sm text-gray-500">Refunded</p>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
