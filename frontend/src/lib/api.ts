const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

interface RequestOptions {
  method?: string;
  headers?: Record<string, string>;
  body?: unknown;
}

let authToken: string | null = null;
let refreshToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  authToken = access;
  refreshToken = refresh;
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }
}

export function loadTokens() {
  if (typeof window !== "undefined") {
    authToken = localStorage.getItem("access_token");
    refreshToken = localStorage.getItem("refresh_token");
  }
}

export function clearTokens() {
  authToken = null;
  refreshToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }
}

export function getAuthToken() {
  return authToken;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", headers = {}, body } = options;

  const config: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  if (authToken) {
    config.headers = { ...config.headers, Authorization: `Bearer ${authToken}` };
  }

  if (body) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config);

  if (response.status === 401 && refreshToken) {
    const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (refreshResponse.ok) {
      const data = await refreshResponse.json();
      setTokens(data.access_token, data.refresh_token);
      config.headers = { ...config.headers, Authorization: `Bearer ${data.access_token}` };
      const retryResponse = await fetch(`${API_BASE}${endpoint}`, config);
      if (!retryResponse.ok) {
        const error = await retryResponse.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(error.detail || `HTTP ${retryResponse.status}`);
      }
      return retryResponse.json();
    }
    clearTokens();
    throw new Error("Session expired. Please login again.");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export interface FormatInfo {
  format_id: string;
  ext: string;
  resolution: string;
  height?: number;
  filesize: number;
  filesize_approx?: number;
  filesize_human?: string;
  vcodec: string;
  acodec: string;
  fps: number | null;
  abr?: number;
  tbr?: number;
  quality_label?: string;
  has_video?: boolean;
  has_audio?: boolean;
  type?: "video" | "video_only" | "audio";
}

export interface VideoInfo {
  title: string;
  platform: string;
  duration: number;
  thumbnail: string;
  formats: FormatInfo[];
  url: string;
  is_playlist?: boolean;
  playlist_count?: number;
  requires_payment?: boolean;
}

export interface DownloadResult {
  file_name: string;
  file_size: number;
  format: string;
  download_url: string;
  title?: string;
  thumbnail?: string;
  require_payment?: boolean;
  require_ad?: boolean;
  pay_per_download?: boolean;
}

export interface UserInfo {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active?: boolean;
  is_admin?: boolean;
  downloads_today: number;
  daily_download_limit: number;
  download_credits: number;
  total_downloads: number;
  created_at?: string;
}

export interface SubscriptionStatus {
  tier: string;
  is_active: boolean;
  current_period_end: string | null;
  features: Record<string, boolean>;
  daily_downloads: number;
  max_quality: string;
}

export interface ApiKeyInfo {
  id: string;
  name: string;
  prefix: string;
  tier: string;
  requests_count: number;
  daily_limit: number;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

export interface PaymentRecord {
  id: string;
  amount: number;
  currency: string;
  status: string;
  payment_type: string;
  description: string | null;
  created_at: string;
}

export interface ReferralInfo {
  code: string;
  referral_url: string;
  total_referred: number;
  reward_per_referral: string;
}

export interface AdminStats {
  total_users: number;
  total_downloads: number;
  total_revenue: number;
  active_subscriptions: number;
  pro_users: number;
  unlimited_users: number;
  api_keys_count: number;
  completed_referrals: number;
}

export interface AffiliateLinkInfo {
  id: string;
  platform: string;
  name: string;
  url: string;
  description: string | null;
  commission_rate: string | null;
}

export interface PlaylistEntry {
  url: string;
  title: string;
  duration: number;
  thumbnail: string;
  id?: string;
}

export const api = {
  getVideoInfo: (url: string) =>
    request<VideoInfo>("/download/info", { method: "POST", body: { url } }),

  startDownload: (url: string, formatId: string, asMp3 = false, mp3Bitrate = "192") =>
    request<DownloadResult>("/download/start", {
      method: "POST",
      body: { url, format_id: formatId, as_mp3: asMp3, mp3_bitrate: mp3Bitrate },
    }),

  batchDownload: (urls: string[], formatId: string, asMp3 = false) =>
    request<{ results: Array<{ url: string; status: string; file_name?: string; file_size?: number; download_url?: string }>; total: number; successful: number }>(
      "/download/batch",
      { method: "POST", body: { urls, format_id: formatId, as_mp3: asMp3 } }
    ),

  getHealth: () => request<{ status: string; version: string }>("/health"),

  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: { email, password },
    }),

  register: (email: string, username: string, password: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>("/auth/register", {
      method: "POST",
      body: { email, username, password },
    }),

  getSubscriptionStatus: () =>
    request<SubscriptionStatus>("/subscription/status"),

  createSubscriptionCheckout: (tier: string) =>
    request<{ checkout_url: string }>("/payment/create-subscription", {
      method: "POST",
      body: { tier },
    }),

  createPayPerDownloadCheckout: (email = "") =>
    request<{ checkout_url: string }>("/payment/pay-per-download", {
      method: "POST",
      body: { email },
    }),

  cancelSubscription: () =>
    request<{ status: string }>("/subscription/cancel", { method: "POST" }),

  getPaymentHistory: (skip = 0, limit = 20) =>
    request<PaymentRecord[]>(`/payment/history?skip=${skip}&limit=${limit}`),

  getDownloadHistory: (skip = 0, limit = 50) =>
    request<Array<{ id: string; url: string; title?: string; thumbnail_url?: string; platform: string; format: string; status: string; file_size: number | null; created_at: string | null }>>(
      `/download/history?skip=${skip}&limit=${limit}`
    ),

  searchDownloads: (q: string) =>
    request<Array<{ id: string; url: string; title?: string; platform: string; format: string; status: string; created_at: string | null }>>(
      `/download/search?q=${encodeURIComponent(q)}`
    ),

  createApiKey: (name: string) =>
    request<{ id: string; name: string; key: string; daily_limit: number; created_at: string }>("/api-keys/create", {
      method: "POST",
      body: { name },
    }),

  listApiKeys: () =>
    request<ApiKeyInfo[]>("/api-keys/list"),

  revokeApiKey: (keyId: string) =>
    request<{ status: string }>(`/api-keys/${keyId}/revoke`, { method: "POST" }),

  getReferralCode: () =>
    request<ReferralInfo>("/referrals/my-code"),

  applyReferralCode: (code: string) =>
    request<{ status: string; bonus_downloads: number }>("/referrals/apply", {
      method: "POST",
      body: { code },
    }),

  getAffiliateLinks: () =>
    request<AffiliateLinkInfo[]>("/affiliates/links"),

  recordAffiliateClick: (linkId: string) =>
    request<{ status: string }>(`/affiliates/${linkId}/click`, { method: "POST" }),

  getAdminStats: () =>
    request<AdminStats>("/admin/stats"),

  getMe: () =>
    request<UserInfo>("/auth/me"),

  contactMessage: (name: string, email: string, message: string) =>
    request<{ status: string; message: string }>("/contact", {
      method: "POST",
      body: { name, email, message },
    }),

  getAdminUsers: (skip = 0, limit = 50) =>
    request<Array<{ id: string; email: string; username: string; role: string; is_active: boolean; downloads_today: number; created_at: string }>>(
      `/admin/users?skip=${skip}&limit=${limit}`
    ),

  getAdminSubscriptions: (skip = 0, limit = 50) =>
    request<Array<{ id: string; user_id: string; plan_id: string; status: string; current_period_start: string | null; current_period_end: string | null }>>(
      `/admin/subscriptions?skip=${skip}&limit=${limit}`
    ),

  toggleUserBan: (userId: string) =>
    request<{ id: string; is_active: boolean }>(`/admin/users/${userId}/toggle-ban`, { method: "POST" }),

  cancelSubscriptionAdmin: (subId: string) =>
    request<{ id: string; status: string }>(`/admin/subscriptions/${subId}/cancel`, { method: "POST" }),

  getPlaylistInfo: (url: string) =>
    request<{ entries: PlaylistEntry[]; total: number }>("/download/playlist", {
      method: "POST",
      body: { url },
    }),
};
