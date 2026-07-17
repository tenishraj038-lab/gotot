"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, Link, Loader2, Youtube, Music, Video, Twitter, Facebook, Globe, Clapperboard, Tv, Briefcase, Pin, PlayCircle } from "lucide-react";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";

const PLATFORM_ICONS: Record<string, { icon: React.ElementType; color: string }> = {
  youtube: { icon: Youtube, color: "text-red-500" },
  tiktok: { icon: Music, color: "text-pink-500" },
  instagram: { icon: Video, color: "text-purple-500" },
  twitter: { icon: Twitter, color: "text-sky-500" },
  facebook: { icon: Facebook, color: "text-blue-600" },
  reddit: { icon: Globe, color: "text-orange-500" },
  vimeo: { icon: Clapperboard, color: "text-teal-500" },
  twitch: { icon: Tv, color: "text-violet-500" },
  dailymotion: { icon: PlayCircle, color: "text-blue-500" },
  linkedin: { icon: Briefcase, color: "text-blue-700" },
  pinterest: { icon: Pin, color: "text-rose-500" },
};

const PLATFORM_PATTERNS: Record<string, RegExp[]> = {
  youtube: [/youtube\.com/, /youtu\.be/],
  tiktok: [/tiktok\.com/, /vm\.tiktok\.com/],
  instagram: [/instagram\.com/],
  twitter: [/twitter\.com/, /x\.com/],
  facebook: [/facebook\.com/, /fb\.watch/],
  reddit: [/reddit\.com/, /v\.redd\.it/],
  vimeo: [/vimeo\.com/],
  dailymotion: [/dailymotion\.com/, /dai\.ly/],
  twitch: [/twitch\.tv/, /clips\.twitch\.tv/],
  linkedin: [/linkedin\.com/],
  pinterest: [/pinterest\.com/, /pin\.it/],
};

function detectPlatformFromUrl(url: string): string | null {
  for (const [platform, patterns] of Object.entries(PLATFORM_PATTERNS)) {
    for (const p of patterns) {
      if (p.test(url)) return platform;
    }
  }
  return null;
}

const allPlatforms = [
  { name: "YouTube", icon: Youtube, color: "text-red-500" },
  { name: "TikTok", icon: Music, color: "text-pink-500" },
  { name: "Instagram", icon: Video, color: "text-purple-500" },
  { name: "Twitter/X", icon: Twitter, color: "text-sky-500" },
  { name: "Facebook", icon: Facebook, color: "text-blue-600" },
  { name: "Reddit", icon: Globe, color: "text-orange-500" },
  { name: "Vimeo", icon: Clapperboard, color: "text-teal-500" },
  { name: "Twitch", icon: Tv, color: "text-violet-500" },
  { name: "Dailymotion", icon: PlayCircle, color: "text-blue-500" },
  { name: "LinkedIn", icon: Briefcase, color: "text-blue-700" },
  { name: "Pinterest", icon: Pin, color: "text-rose-500" },
];

export default function DownloadForm() {
  const { url, setUrl, isLoading, setIsLoading, setVideoInfo, setError, addRecentUrl, detectedPlatform, setDetectedPlatform, setPlaylistEntries } = useStore();
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    const platform = detectPlatformFromUrl(url);
    setDetectedPlatform(platform);
  }, [url, setDetectedPlatform]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setError("Please enter a video URL");
      return;
    }

    setIsLoading(true);
    try {
      const info = await api.getVideoInfo(url.trim());
      setVideoInfo(info);
      addRecentUrl(url.trim());
      if (info.is_playlist) {
        try {
          const playlistData = await api.getPlaylistInfo(url.trim());
          setPlaylistEntries(playlistData.entries);
        } catch {}
      } else {
        setPlaylistEntries([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get video info");
    }
  };

  const DetectedIcon = detectedPlatform ? PLATFORM_ICONS[detectedPlatform]?.icon : null;
  const detectedColor = detectedPlatform ? PLATFORM_ICONS[detectedPlatform]?.color : "";

  return (
    <div className="w-full max-w-3xl mx-auto">
      <motion.form
        onSubmit={handleSubmit}
        className="relative"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div
          className={`relative flex items-center transition-all duration-300 ${
            isFocused
              ? "ring-2 ring-primary-500/50 ring-offset-2 ring-offset-white dark:ring-offset-gray-950 shadow-2xl shadow-primary-500/20"
              : "shadow-xl shadow-gray-200/50 dark:shadow-gray-900/50"
          }`}
        >
          <div className="absolute left-4 flex items-center pointer-events-none">
            {DetectedIcon ? (
              <DetectedIcon className={`w-5 h-5 ${detectedColor}`} />
            ) : (
              <Link className="w-5 h-5 text-gray-400" />
            )}
          </div>

          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Paste video URL here..."
            className="w-full pl-12 pr-36 py-5 rounded-2xl bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 text-base input-glow focus:outline-none focus:border-transparent transition-all duration-200"
            disabled={isLoading}
          />

          <div className="absolute right-2 flex items-center gap-2">
            <motion.button
              type="submit"
              disabled={isLoading || !url.trim()}
              className="px-6 py-2.5 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-primary-500/25"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">{isLoading ? "Analyzing..." : "Get Video"}</span>
            </motion.button>
          </div>
        </div>

        {detectedPlatform && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute -bottom-7 left-4 text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1"
          >
            {DetectedIcon && <DetectedIcon className={`w-3 h-3 ${detectedColor}`} />}
            {detectedPlatform.charAt(0).toUpperCase() + detectedPlatform.slice(1)} detected
          </motion.div>
        )}
      </motion.form>

      <motion.div
        className="flex flex-wrap items-center justify-center gap-2 mt-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        {allPlatforms.map((platform) => (
          <div
            key={platform.name}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800/50 text-[10px] font-medium text-gray-600 dark:text-gray-400"
          >
            <platform.icon className={`w-3 h-3 ${platform.color}`} />
            {platform.name}
          </div>
        ))}
      </motion.div>
    </div>
  );
}
