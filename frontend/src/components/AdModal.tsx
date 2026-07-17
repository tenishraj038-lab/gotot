"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ExternalLink } from "lucide-react";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

export default function AdModal() {
  const {
    adModalOpen, setAdModalOpen, pendingDownload, setPendingDownload,
    setDownloadResult, setIsLoading,
  } = useStore();

  const handleSkip = async () => {
    setAdModalOpen(false);
    if (pendingDownload) {
      const { url, formatId, asMp3 } = pendingDownload;
      setPendingDownload(null);
      setIsLoading(true);
      try {
        const result = await api.startDownload(url, formatId, asMp3);
        setDownloadResult(result);
        toast.success("Download ready!");
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Download failed");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleSupport = () => {
    window.open("https://buymeacoffee.com/gotot", "_blank");
  };

  return (
    <AnimatePresence>
      {adModalOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleSkip} />
          <motion.div
            className="relative w-full max-w-md rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 shadow-2xl overflow-hidden"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
          >
            <button
              onClick={handleSkip}
              className="absolute top-4 right-4 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>

            <div className="p-8 text-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-lg">Go</span>
              </div>

              <h3 className="text-xl font-bold mb-2">Support GoTot</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                GoTot is free and always will be. If you find it useful, consider supporting us!
              </p>

              <div className="space-y-3">
                <button
                  onClick={handleSkip}
                  className="w-full py-2.5 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500 text-white font-semibold rounded-xl transition-all"
                >
                  Skip & Continue to Download
                </button>
                <button
                  onClick={handleSupport}
                  className="w-full py-2.5 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium rounded-xl transition-all flex items-center justify-center gap-2"
                >
                  Buy us a coffee
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
