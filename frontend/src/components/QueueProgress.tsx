"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, CheckCircle, XCircle, X, Download } from "lucide-react";
import { API_BASE } from "@/lib/api";

interface QueueStatus {
  task_id: string;
  status: string;
  progress: number;
  message: string;
}

export default function QueueProgress({ taskId, onComplete }: { taskId: string | null; onComplete?: () => void }) {
  const [status, setStatus] = useState<QueueStatus | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!taskId) {
      setVisible(false);
      return;
    }

    setVisible(true);
    const wsUrl = (typeof window !== "undefined" && process.env.NEXT_PUBLIC_WS_URL) || API_BASE.replace(/^http/, "ws");
    let ws: WebSocket | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;

    try {
      ws = new WebSocket(`${wsUrl}/ws/progress/${taskId}`);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setStatus(data);
          if (data.status === "completed" || data.status === "error") {
            setTimeout(() => { setVisible(false); onComplete?.(); }, 3000);
          }
        } catch {}
      };

      ws.onerror = () => {
        ws?.close();
        pollTimer = setInterval(async () => {
          try {
            const resp = await fetch(`${API_BASE}/download/queue/${taskId}`);
            if (resp.ok) {
              const data = await resp.json();
              setStatus(data);
              if (data.status === "completed" || data.status === "error") {
                if (pollTimer) clearInterval(pollTimer);
                setTimeout(() => { setVisible(false); onComplete?.(); }, 3000);
              }
            }
          } catch {}
        }, 2000);
      };
    } catch {
      pollTimer = setInterval(async () => {
        try {
          const resp = await fetch(`${API_BASE}/download/queue/${taskId}`);
          if (resp.ok) {
            const data = await resp.json();
            setStatus(data);
            if (data.status === "completed" || data.status === "error") {
              if (pollTimer) clearInterval(pollTimer);
              setTimeout(() => { setVisible(false); onComplete?.(); }, 3000);
            }
          }
        } catch {}
      }, 2000);
    }

    return () => {
      ws?.close();
      if (pollTimer) clearInterval(pollTimer);
    };
  }, [taskId, onComplete]);

  if (!visible || !status) return null;

  const isError = status.status === "error";
  const isDone = status.status === "completed";

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="mt-4 p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-lg"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {isDone ? (
                <CheckCircle className="w-5 h-5 text-green-500" aria-hidden="true" />
              ) : isError ? (
                <XCircle className="w-5 h-5 text-red-500" aria-hidden="true" />
              ) : (
                <Loader2 className="w-5 h-5 text-primary-500 animate-spin" aria-hidden="true" />
              )}
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {status.message || status.status}
              </span>
            </div>
            <button
              onClick={() => setVisible(false)}
              className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Dismiss progress"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>

          <div className="w-full h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
            <motion.div
              className={`h-full rounded-full transition-colors ${
                isError ? "bg-red-500" : isDone ? "bg-green-500" : "bg-gradient-to-r from-primary-500 to-accent-500"
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${status.progress}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </div>

          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">{status.progress}%</span>
            {isDone && (
              <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                <Download className="w-3 h-3" /> Ready
              </span>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
