"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Megaphone } from "lucide-react";
import { api } from "@/lib/api";

interface Announcement {
  id: string;
  message: string;
  type: "info" | "warning" | "success";
}

export default function NotificationBanner() {
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("dismissed_announcement");
    api.getActiveAnnouncement()
      .then((data) => {
        if (data && data.id !== stored) {
          setAnnouncement(data as Announcement);
        }
      })
      .catch(() => {
        console.warn("[NotificationBanner] Failed to fetch announcement");
      });
  }, []);

  function dismiss() {
    if (announcement) {
      sessionStorage.setItem("dismissed_announcement", announcement.id);
    }
    setDismissed(true);
  }

  const typeStyles = {
    info: "bg-blue-50 dark:bg-blue-950/50 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300",
    warning: "bg-amber-50 dark:bg-amber-950/50 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300",
    success: "bg-green-50 dark:bg-green-950/50 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300",
  };

  return (
    <AnimatePresence>
      {announcement && !dismissed && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className={`fixed top-16 left-0 right-0 z-40 border-b ${typeStyles[announcement.type]}`}
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <Megaphone className="w-4 h-4 shrink-0" />
              <span>{announcement.message}</span>
            </div>
            <button onClick={dismiss} className="shrink-0 p-1 hover:opacity-70 transition-opacity">
              <X className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
