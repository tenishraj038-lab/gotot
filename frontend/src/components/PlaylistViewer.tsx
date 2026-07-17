"use client";

import { motion } from "framer-motion";
import { CheckSquare, Square, Download, Loader2, Music, Monitor } from "lucide-react";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";
import { useState } from "react";
import toast from "react-hot-toast";
import { useLocale } from "@/lib/i18n";

function formatDuration(seconds: number): string {
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function PlaylistViewer() {
  const {
    videoInfo, playlistEntries, selectedPlaylistItems,
    togglePlaylistItem, selectAllPlaylist, clearPlaylistSelection,
  } = useStore();
  const { t } = useLocale();
  const [downloading, setDownloading] = useState(false);

  if (!videoInfo?.is_playlist || playlistEntries.length === 0) return null;

  const selectedCount = selectedPlaylistItems.size;

  const handleDownloadSelected = async () => {
    const selected = playlistEntries.filter((_, i) => selectedPlaylistItems.has(i));
    if (selected.length === 0) {
      toast.error(t.playlist.noSelection);
      return;
    }

    setDownloading(true);
    try {
      const urls = selected.map((e) => e.url);
      const result = await api.batchDownload(urls, "bestvideo+bestaudio");
      toast.success(`${result.successful} of ${result.total} downloaded`);
    } catch (err) {
      toast.error(t.download.downloadFailed);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
          {t.playlist.title} ({playlistEntries.length})
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={selectAllPlaylist}
            className="text-xs text-primary-600 hover:text-primary-500 font-medium"
          >
            {t.playlist.selectAll}
          </button>
          <span className="text-xs text-gray-400">|</span>
          <button
            onClick={clearPlaylistSelection}
            className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            {t.playlist.clearSelection}
          </button>
        </div>
      </div>

      <div className="space-y-1 max-h-[300px] overflow-y-auto">
        {playlistEntries.map((entry, i) => (
          <div
            key={entry.id || i}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
            onClick={() => togglePlaylistItem(i)}
          >
            {selectedPlaylistItems.has(i) ? (
              <CheckSquare className="w-4 h-4 text-primary-500 shrink-0" />
            ) : (
              <Square className="w-4 h-4 text-gray-300 dark:text-gray-600 shrink-0" />
            )}
            {entry.thumbnail && (
              <img src={entry.thumbnail} alt="" className="w-10 h-7 rounded object-cover shrink-0" />
            )}
            <span className="text-xs text-gray-700 dark:text-gray-300 flex-1 truncate">
              {entry.title}
            </span>
            {entry.duration > 0 && (
              <span className="text-[10px] text-gray-400 shrink-0">
                {formatDuration(entry.duration)}
              </span>
            )}
          </div>
        ))}
      </div>

      {selectedCount > 0 && (
        <button
          onClick={handleDownloadSelected}
          disabled={downloading}
          className="w-full mt-3 py-2 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white text-sm font-semibold rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {downloading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          {t.playlist.downloadSelected.replace("{count}", String(selectedCount))}
        </button>
      )}
    </motion.div>
  );
}
