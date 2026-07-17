import { en } from "./en";
import { es } from "./es";

export type Locale = "en" | "es";
export type TranslationDict = typeof en;

const translations: Record<Locale, TranslationDict> = { en, es };

export function getLocale(): Locale {
  if (typeof window === "undefined") return "en";
  const stored = localStorage.getItem("locale") as Locale | null;
  if (stored && (stored === "en" || stored === "es")) return stored;
  const browser = navigator.language?.split("-")[0];
  if (browser === "es") return "es";
  return "en";
}

export function setLocale(locale: Locale) {
  if (typeof window !== "undefined") {
    localStorage.setItem("locale", locale);
  }
}

export function t(locale: Locale): TranslationDict {
  return translations[locale] || en;
}

export function useLocale(): { locale: Locale; t: TranslationDict; setLocale: (l: Locale) => void } {
  if (typeof window === "undefined") return { locale: "en", t: en, setLocale };
  const locale = getLocale();
  return { locale, t: translations[locale] || en, setLocale };
}
