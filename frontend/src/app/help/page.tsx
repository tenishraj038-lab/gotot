"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { HelpCircle, MessageSquare, Bug, Lightbulb, Star, Send, Loader2, Mail, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import Link from "next/link";

export default function HelpPage() {
  const [tab, setTab] = useState<"feedback" | "bug" | "feature" | "survey">("feedback");
  const [sending, setSending] = useState(false);

  const [feedback, setFeedback] = useState({ type: "general", title: "", description: "", email: "" });
  const [bug, setBug] = useState({ title: "", description: "", steps: "", browser: "", os: "" });
  const [feature, setFeature] = useState({ title: "", description: "", use_case: "", priority: "medium" });
  const [survey, setSurvey] = useState({ rating: 5, category: "general", comment: "" });

  async function submitFeedback() {
    if (!feedback.title || !feedback.description) return toast.error("Title and description required");
    setSending(true);
    try {
      await api.contactMessage(feedback.title, feedback.email || "anonymous@gotot.app", feedback.description);
      toast.success("Feedback sent! Thank you.");
      setFeedback({ type: "general", title: "", description: "", email: "" });
    } catch { toast.error("Failed to send feedback"); }
    setSending(false);
  }

  async function submitBug() {
    if (!bug.title || !bug.description) return toast.error("Title and description required");
    setSending(true);
    try {
      await api.contactMessage(`Bug: ${bug.title}`, "bug-report@gotot.app",
        `${bug.description}\nSteps: ${bug.steps}\nBrowser: ${bug.browser}\nOS: ${bug.os}`);
      toast.success("Bug report submitted!");
      setBug({ title: "", description: "", steps: "", browser: "", os: "" });
    } catch { toast.error("Failed to submit bug report"); }
    setSending(false);
  }

  async function submitFeature() {
    if (!feature.title || !feature.description) return toast.error("Title and description required");
    setSending(true);
    try {
      await api.contactMessage(`Feature: ${feature.title}`, "feature-requests@gotot.app",
        `${feature.description}\nUse case: ${feature.use_case}\nPriority: ${feature.priority}`);
      toast.success("Feature request submitted!");
      setFeature({ title: "", description: "", use_case: "", priority: "medium" });
    } catch { toast.error("Failed to submit feature request"); }
    setSending(false);
  }

  async function submitSurvey() {
    setSending(true);
    try {
      await api.contactMessage(`Survey: ${survey.category} - ${survey.rating}/5`, "survey@gotot.app", survey.comment || "No comment");
      toast.success("Thank you for your feedback!");
    } catch { toast.error("Failed to submit survey"); }
    setSending(false);
  }

  const tabs = [
    { key: "feedback" as const, label: "Feedback", icon: MessageSquare },
    { key: "bug" as const, label: "Bug Report", icon: Bug },
    { key: "feature" as const, label: "Feature Request", icon: Lightbulb },
    { key: "survey" as const, label: "Satisfaction Survey", icon: Star },
  ];

  return (
    <div className="pt-24 pb-16 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <HelpCircle className="w-8 h-8 text-primary-500" />
          <h1 className="text-3xl font-bold">Help & Support</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mb-4">Get help, report issues, or suggest improvements</p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <Link href="/docs" className="flex items-center gap-2 p-3 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-sm font-medium transition-all">
            <BookOpen className="w-4 h-4 text-primary-500" /> API Docs
          </Link>
          <Link href="/contact" className="flex items-center gap-2 p-3 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-sm font-medium transition-all">
            <Mail className="w-4 h-4 text-primary-500" /> Contact
          </Link>
        </div>

        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all flex-shrink-0 ${
                tab === key ? "bg-primary-600 text-white shadow-lg" : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
              }`}
            ><Icon className="w-4 h-4" />{label}</button>
          ))}
        </div>

        {tab === "feedback" && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Title</label>
              <input value={feedback.title} onChange={e => setFeedback(f => ({ ...f, title: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea rows={4} value={feedback.description} onChange={e => setFeedback(f => ({ ...f, description: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <button onClick={submitFeedback} disabled={sending}
              className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 font-medium disabled:opacity-50">
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Send Feedback
            </button>
          </div>
        )}

        {tab === "bug" && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Bug Title</label>
              <input value={bug.title} onChange={e => setBug(b => ({ ...b, title: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea rows={4} value={bug.description} onChange={e => setBug(b => ({ ...b, description: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Steps to Reproduce</label>
                <textarea rows={3} value={bug.steps} onChange={e => setBug(b => ({ ...b, steps: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Browser</label>
                  <input value={bug.browser} onChange={e => setBug(b => ({ ...b, browser: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Operating System</label>
                  <input value={bug.os} onChange={e => setBug(b => ({ ...b, os: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
                </div>
              </div>
            </div>
            <button onClick={submitBug} disabled={sending}
              className="flex items-center gap-2 px-6 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 font-medium disabled:opacity-50">
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bug className="w-4 h-4" />}
              Submit Bug Report
            </button>
          </div>
        )}

        {tab === "feature" && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Feature Title</label>
              <input value={feature.title} onChange={e => setFeature(f => ({ ...f, title: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea rows={4} value={feature.description} onChange={e => setFeature(f => ({ ...f, description: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Use Case</label>
              <textarea rows={3} value={feature.use_case} onChange={e => setFeature(f => ({ ...f, use_case: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <button onClick={submitFeature} disabled={sending}
              className="flex items-center gap-2 px-6 py-2.5 bg-purple-600 text-white rounded-xl hover:bg-purple-700 font-medium disabled:opacity-50">
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lightbulb className="w-4 h-4" />}
              Submit Feature Request
            </button>
          </div>
        )}

        {tab === "survey" && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6 space-y-6">
            <div className="text-center">
              <p className="text-lg font-medium mb-2">How would you rate your experience?</p>
              <div className="flex justify-center gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button key={n} onClick={() => setSurvey(s => ({ ...s, rating: n }))}
                    className={`p-3 rounded-xl transition-all ${survey.rating >= n ? "text-yellow-400 scale-110" : "text-gray-300 dark:text-gray-600"}`}>
                    <Star className="w-8 h-8 fill-current" />
                  </button>
                ))}
              </div>
              <p className="text-sm text-gray-400 mt-2">{survey.rating}/5</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Additional Comments</label>
              <textarea rows={3} value={survey.comment} onChange={e => setSurvey(s => ({ ...s, comment: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <button onClick={submitSurvey} disabled={sending}
              className="flex items-center gap-2 px-6 py-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 font-medium disabled:opacity-50 mx-auto">
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Star className="w-4 h-4" />}
              Submit Rating
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
