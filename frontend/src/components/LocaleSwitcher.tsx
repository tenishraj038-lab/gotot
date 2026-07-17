"use client";

import { useEffect, useState } from "react";
import { Globe } from "lucide-react";
import { Locale, getLocale, setLocale } from "@/lib/i18n";

export default function LocaleSwitcher() {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    setLocaleState(getLocale());
  }, []);

  const toggle = () => {
    const next: Locale = locale === "en" ? "es" : "en";
    setLocale(next);
    setLocaleState(next);
    if (typeof window !== "undefined") {
      window.location.reload();
    }
  };

  return (
    <button
      onClick={toggle}
      className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200 flex items-center gap-1.5"
      aria-label="Toggle language"
    >
      <Globe className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">{locale}</span>
    </button>
  );
}
