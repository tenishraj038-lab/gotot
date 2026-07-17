"use client";

import { motion } from "framer-motion";
import { Globe, TrendingUp, Youtube, Music, Video, Twitter, Facebook } from "lucide-react";

const mockDownloads = [
  { platform: "youtube", format: "mp4", size: "24.3 MB", time: "2m ago", color: "bg-red-500", icon: Youtube },
  { platform: "tiktok", format: "mp4", size: "8.7 MB", time: "5m ago", color: "bg-pink-500", icon: Music },
  { platform: "instagram", format: "mp4", size: "12.1 MB", time: "8m ago", color: "bg-purple-500", icon: Video },
  { platform: "twitter", format: "mp4", size: "5.2 MB", time: "11m ago", color: "bg-sky-500", icon: Twitter },
  { platform: "facebook", format: "mp4", size: "18.9 MB", time: "14m ago", color: "bg-blue-600", icon: Facebook },
  { platform: "youtube", format: "mp3", size: "4.1 MB", time: "17m ago", color: "bg-red-500", icon: Youtube },
];

export default function RecentDownloads() {
  return (
    <section className="py-16 bg-gray-50/30 dark:bg-gray-900/30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="flex items-center gap-3 mb-8"
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Downloads Happening Now</h2>
            <p className="text-sm text-gray-500">People are downloading from GoTot right now</p>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {mockDownloads.map((d, i) => (
            <motion.div
              key={`${d.platform}-${i}`}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-3 p-3 rounded-xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 hover:shadow-md transition-all"
            >
              <div className={`w-9 h-9 rounded-lg ${d.color} flex items-center justify-center shrink-0`}>
                <d.icon className="w-4 h-4 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium capitalize truncate">{d.platform}</p>
                <p className="text-xs text-gray-500">{d.size} &middot; {d.format.toUpperCase()}</p>
              </div>
              <span className="text-xs text-gray-400 shrink-0">{d.time}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
