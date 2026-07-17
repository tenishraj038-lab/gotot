import { create } from "zustand";
import { VideoInfo, DownloadResult, UserInfo, SubscriptionStatus } from "./api";

interface PlaylistEntry {
  url: string;
  title: string;
  duration: number;
  thumbnail: string;
  id?: string;
}

interface DownloadState {
  url: string;
  setUrl: (url: string) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  videoInfo: VideoInfo | null;
  setVideoInfo: (info: VideoInfo | null) => void;
  downloadResult: DownloadResult | null;
  setDownloadResult: (result: DownloadResult | null) => void;
  error: string | null;
  setError: (error: string | null) => void;
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  recentUrls: string[];
  addRecentUrl: (url: string) => void;

  user: UserInfo | null;
  setUser: (user: UserInfo | null) => void;
  subscription: SubscriptionStatus | null;
  setSubscription: (sub: SubscriptionStatus | null) => void;
  isAuthModalOpen: boolean;
  setAuthModalOpen: (open: boolean) => void;
  adModalOpen: boolean;
  setAdModalOpen: (open: boolean) => void;
  paymentModalOpen: boolean;
  setPaymentModalOpen: (open: boolean) => void;
  pendingDownload: { url: string; formatId: string; asMp3: boolean } | null;
  setPendingDownload: (pending: { url: string; formatId: string; asMp3: boolean } | null) => void;

  playlistEntries: PlaylistEntry[];
  setPlaylistEntries: (entries: PlaylistEntry[]) => void;
  selectedPlaylistItems: Set<number>;
  togglePlaylistItem: (index: number) => void;
  selectAllPlaylist: () => void;
  clearPlaylistSelection: () => void;
  detectedPlatform: string | null;
  setDetectedPlatform: (p: string | null) => void;
}

export const useStore = create<DownloadState>((set, get) => ({
  url: "",
  setUrl: (url) => set({ url }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading, error: null }),
  videoInfo: null,
  setVideoInfo: (info) => set({ videoInfo: info, error: null }),
  downloadResult: null,
  setDownloadResult: (result) => set({ downloadResult: result }),
  error: null,
  setError: (error) => set({ error, isLoading: false, videoInfo: null }),
  isDarkMode: false,
  toggleDarkMode: () =>
    set((state) => {
      const newMode = !state.isDarkMode;
      if (typeof window !== "undefined") {
        document.documentElement.classList.toggle("dark", newMode);
        localStorage.setItem("darkMode", String(newMode));
      }
      return { isDarkMode: newMode };
    }),
  recentUrls: [],
  addRecentUrl: (url) =>
    set((state) => ({
      recentUrls: [url, ...state.recentUrls.filter((u) => u !== url)].slice(0, 10),
    })),

  user: null,
  setUser: (user) => set({ user }),
  subscription: null,
  setSubscription: (sub) => set({ subscription: sub }),
  isAuthModalOpen: false,
  setAuthModalOpen: (open) => set({ isAuthModalOpen: open }),
  adModalOpen: false,
  setAdModalOpen: (open) => set({ adModalOpen: open }),
  paymentModalOpen: false,
  setPaymentModalOpen: (open) => set({ paymentModalOpen: open }),
  pendingDownload: null,
  setPendingDownload: (pending) => set({ pendingDownload: pending }),

  playlistEntries: [],
  setPlaylistEntries: (entries) => set({ playlistEntries: entries, selectedPlaylistItems: new Set(entries.map((_, i) => i)) }),
  selectedPlaylistItems: new Set(),
  togglePlaylistItem: (index) =>
    set((state) => {
      const next = new Set(state.selectedPlaylistItems);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return { selectedPlaylistItems: next };
    }),
  selectAllPlaylist: () =>
    set((state) => ({
      selectedPlaylistItems: new Set(state.playlistEntries.map((_, i) => i)),
    })),
  clearPlaylistSelection: () => set({ selectedPlaylistItems: new Set() }),

  detectedPlatform: null,
  setDetectedPlatform: (p) => set({ detectedPlatform: p }),
}));
