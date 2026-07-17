"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Download, Clock, AlertCircle, CheckCircle,
  Loader2, ExternalLink, Monitor, Music,
  FileDown, Share2, ChevronDown, ChevronUp,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { api, FormatInfo } from "@/lib/api";
import { useState } from "react";
import toast from "react-hot-toast";
import PlaylistViewer from "./PlaylistViewer";

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatSize(bytes: number): string {
  if (!bytes) return "";
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

function ShareButtons({ title, url }: { title: string; url: string }) {
  const shareText = `Download "${title}" - GoTot`;
  const encoded = encodeURIComponent(shareText);
  const encodedUrl = encodeURIComponent(url);

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-400">Share:</span>
      <a href={`https://wa.me/?text=${encoded}%20${encodedUrl}`} target="_blank" rel="noopener" className="p-1.5 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors" title="WhatsApp">
        <svg className="w-3.5 h-3.5 text-green-600" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
      </a>
      <a href={`https://twitter.com/intent/tweet?text=${encoded}&url=${encodedUrl}`} target="_blank" rel="noopener" className="p-1.5 rounded-lg hover:bg-sky-100 dark:hover:bg-sky-900/30 transition-colors" title="Twitter">
        <svg className="w-3.5 h-3.5 text-sky-500" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </a>
      <a href={`https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`} target="_blank" rel="noopener" className="p-1.5 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors" title="Facebook">
        <svg className="w-3.5 h-3.5 text-blue-600" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
      </a>
      <button
        onClick={() => { navigator.clipboard.writeText(window.location.href); toast.success("Link copied!"); }}
        className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        title="Copy link"
      >
        <svg className="w-3.5 h-3.5 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
      </button>
    </div>
  );
}

export default function ResultCard() {
  const {
    videoInfo, isLoading, error, downloadResult, setDownloadResult,
    setError, setAdModalOpen, setPendingDownload,
  } = useStore();
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);
  const [mp3Bitrate, setMp3Bitrate] = useState("192");
  const [showAllFormats, setShowAllFormats] = useState(false);
  const [activeTab, setActiveTab] = useState<"video" | "audio">("video");

  const handleDownload = async (format: FormatInfo, asMp3 = false) => {
    if (!videoInfo) return;
    setDownloadingFormat(format.format_id);

    try {
      const result = await api.startDownload(videoInfo.url, format.format_id, asMp3, mp3Bitrate);

      if (result.require_ad) {
        setPendingDownload({ url: videoInfo.url, formatId: format.format_id, asMp3 });
        setAdModalOpen(true);
        return;
      }

      setDownloadResult(result);
      toast.success("Download ready!");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Download failed";
      setError(msg);
    } finally {
      setDownloadingFormat(null);
    }
  };

  const videoFormats = videoInfo?.formats.filter(f => f.has_video && f.has_audio) || [];
  const audioFormats = videoInfo?.formats.filter(f => !f.has_video && f.has_audio) || [];
  const displayedVideo = showAllFormats ? videoFormats : videoFormats.slice(0, 8);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

  return (
    <AnimatePresence mode="wait">
      {error && (
        <motion.div
          key="error"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="mt-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800 dark:text-red-200">Error</p>
            <p className="text-sm text-red-600 dark:text-red-300 mt-1">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 text-sm shrink-0">
            Dismiss
          </button>
        </motion.div>
      )}

      {isLoading && (
        <motion.div
          key="loading"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="mt-8 flex flex-col items-center gap-4 py-12"
        >
          <div className="relative">
            <Loader2 className="w-10 h-10 animate-spin text-primary-500" />
            <div className="absolute inset-0 blur-xl bg-primary-500/20 rounded-full animate-pulse" />
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 animate-pulse">
            Analyzing video...
          </p>
        </motion.div>
      )}

      {videoInfo && !isLoading && !error && (
        <motion.div
          key="result"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="mt-8"
        >
          <div className="glass rounded-2xl overflow-hidden border border-gray-200/50 dark:border-gray-800/50">
            <div className="p-6">
              <div className="flex flex-col sm:flex-row items-start gap-4">
                <div className="w-full sm:w-80 h-48 sm:h-44 rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 shrink-0 relative group">
                  {videoInfo.thumbnail && (
                    <img
                      src={videoInfo.thumbnail}
                      alt={videoInfo.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  )}
                  <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/70 text-white text-xs font-medium">
                    {formatDuration(videoInfo.duration)}
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 line-clamp-2">
                    {videoInfo.title}
                  </h3>
                  <div className="flex items-center gap-3 mt-2 flex-wrap">
                    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 font-medium capitalize">
                      <ExternalLink className="w-3 h-3" />
                      {videoInfo.platform}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {videoFormats.length} video formats
                    </span>
                    {audioFormats.length > 0 && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {audioFormats.length} audio formats
                      </span>
                    )}
                  </div>
                  {videoInfo.is_playlist && (
                    <div className="mt-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/30">
                      <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                        Playlist detected - {videoInfo.playlist_count} videos
                      </p>
                      <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                        Each video can be downloaded individually below
                      </p>
                    </div>
                  )}
                  <PlaylistViewer />
                  <div className="mt-3">
                    <ShareButtons title={videoInfo.title} url={videoInfo.url} />
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200/50 dark:border-gray-800/50">
              <div className="flex border-b border-gray-200/50 dark:border-gray-800/50">
                <button
                  onClick={() => setActiveTab("video")}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                    activeTab === "video"
                      ? "text-primary-600 border-b-2 border-primary-600"
                      : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                  }`}
                >
                  <Monitor className="w-4 h-4 inline mr-1.5" />
                  Video ({videoFormats.length})
                </button>
                <button
                  onClick={() => setActiveTab("audio")}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                    activeTab === "audio"
                      ? "text-primary-600 border-b-2 border-primary-600"
                      : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                  }`}
                >
                  <Music className="w-4 h-4 inline mr-1.5" />
                  Audio ({audioFormats.length + 1})
                </button>
              </div>

              <div className="p-4 space-y-2 max-h-[400px] overflow-y-auto">
                {activeTab === "video" && displayedVideo.map((f) => (
                  <div
                    key={f.format_id}
                    className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Monitor className="w-4 h-4 text-primary-500 shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {f.quality_label || `${f.ext.toUpperCase()} ${f.height || f.resolution || "HD"}`}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {formatSize(f.filesize || f.filesize_approx || 0)}
                          {f.fps && f.fps > 30 ? ` - ${f.fps}fps` : ""}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDownload(f, true)}
                        disabled={downloadingFormat === f.format_id}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-all disabled:opacity-50"
                      >
                        MP3
                      </button>
                      <button
                        onClick={() => handleDownload(f)}
                        disabled={downloadingFormat === f.format_id}
                        className="px-4 py-1.5 bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium rounded-lg transition-all disabled:opacity-50 flex items-center gap-1.5"
                      >
                        {downloadingFormat === f.format_id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Download className="w-3.5 h-3.5" />
                        )}
                        Download
                      </button>
                    </div>
                  </div>
                ))}

                {activeTab === "video" && videoFormats.length > 8 && !showAllFormats && (
                  <button
                    onClick={() => setShowAllFormats(true)}
                    className="w-full p-2 text-sm text-primary-600 hover:text-primary-500 font-medium flex items-center justify-center gap-1"
                  >
                    Show all {videoFormats.length} formats
                    <ChevronDown className="w-4 h-4" />
                  </button>
                )}
                {activeTab === "video" && showAllFormats && videoFormats.length > 8 && (
                  <button
                    onClick={() => setShowAllFormats(false)}
                    className="w-full p-2 text-sm text-primary-600 hover:text-primary-500 font-medium flex items-center justify-center gap-1"
                  >
                    Show fewer formats
                    <ChevronUp className="w-4 h-4" />
                  </button>
                )}

                {activeTab === "audio" && (
                  <>
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/30">
                      <Music className="w-4 h-4 text-amber-600 shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                          MP3 Audio Extract
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-amber-600 dark:text-amber-400">Quality:</span>
                          {["128", "192", "256", "320"].map((br) => (
                            <button
                              key={br}
                              onClick={() => setMp3Bitrate(br)}
                              className={`px-2 py-0.5 text-xs rounded-md transition-colors ${
                                mp3Bitrate === br
                                  ? "bg-amber-600 text-white"
                                  : "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-900/60"
                              }`}
                            >
                              {br}kbps
                            </button>
                          ))}
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          if (videoFormats[0]) handleDownload(videoFormats[0], true);
                        }}
                        disabled={downloadingFormat === "mp3"}
                        className="px-4 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white text-sm font-medium rounded-lg transition-all disabled:opacity-50 flex items-center gap-1.5"
                      >
                        {downloadingFormat === "mp3" ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Music className="w-3.5 h-3.5" />
                        )}
                        Extract MP3
                      </button>
                    </div>

                    {audioFormats.map((f) => (
                      <div
                        key={f.format_id}
                        className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <Music className="w-4 h-4 text-accent-500 shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                              {f.quality_label || `Audio ${f.ext.toUpperCase()}`}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {formatSize(f.filesize || f.filesize_approx || 0)}
                              {f.abr ? ` - ${f.abr}kbps` : ""}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDownload(f)}
                          disabled={downloadingFormat === f.format_id}
                          className="px-4 py-1.5 bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium rounded-lg transition-all disabled:opacity-50 flex items-center gap-1.5"
                        >
                          {downloadingFormat === f.format_id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Download className="w-3.5 h-3.5" />
                          )}
                          Download
                        </button>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
          </div>

          {downloadResult && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-5 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/50"
            >
              <div className="flex items-start gap-3 mb-4">
                <CheckCircle className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-800 dark:text-green-200">
                    Download ready!
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-300 mt-1">
                    {downloadResult.title || downloadResult.file_name}.{downloadResult.format}
                    {downloadResult.file_size ? ` (${(downloadResult.file_size / 1024 / 1024).toFixed(1)} MB)` : ""}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 flex-wrap">
                <a
                  href={`${API_BASE}${downloadResult.download_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-green-500/25"
                >
                  <FileDown className="w-4 h-4" />
                  Save File to Device
                </a>
                <button
                  onClick={() => setDownloadResult(null)}
                  className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  Clear
                </button>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
