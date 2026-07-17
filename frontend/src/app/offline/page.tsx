"use client";

import { WifiOff, RefreshCw } from "lucide-react";
import Link from "next/link";

export default function OfflinePage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 p-5 mx-auto mb-6">
          <WifiOff className="w-full h-full text-white" />
        </div>
        <h1 className="text-3xl font-bold mb-2">You&apos;re Offline</h1>
        <p className="text-gray-500 dark:text-gray-400 mb-8">
          Connection lost. GoTot needs an internet connection to process downloads. Please check your connection and try again.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => window.location.reload()}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-all font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
          <Link
            href="/"
            className="flex items-center justify-center px-6 py-3 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-all font-medium"
          >
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
