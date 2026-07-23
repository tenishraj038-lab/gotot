import { MetadataRoute } from "next";

const baseUrl = "https://gotot.app";
const lastModified = new Date("2026-07-23");

const platforms = ["tiktok", "instagram", "twitter", "facebook", "reddit", "vimeo", "dailymotion", "twitch", "linkedin", "pinterest"];

export default function sitemap(): MetadataRoute.Sitemap {
  const staticPages = [
    { url: baseUrl, lastModified, changeFrequency: "weekly" as const, priority: 1.0 },
    { url: `${baseUrl}/pricing`, lastModified, changeFrequency: "monthly" as const, priority: 0.8 },
    { url: `${baseUrl}/terms`, lastModified, changeFrequency: "yearly" as const, priority: 0.3 },
    { url: `${baseUrl}/privacy`, lastModified, changeFrequency: "yearly" as const, priority: 0.3 },
    { url: `${baseUrl}/dmca`, lastModified, changeFrequency: "yearly" as const, priority: 0.3 },
    { url: `${baseUrl}/copyright`, lastModified, changeFrequency: "yearly" as const, priority: 0.3 },
    { url: `${baseUrl}/contact`, lastModified, changeFrequency: "yearly" as const, priority: 0.4 },
    { url: `${baseUrl}/docs`, lastModified, changeFrequency: "monthly" as const, priority: 0.7 },
    { url: `${baseUrl}/help`, lastModified, changeFrequency: "monthly" as const, priority: 0.5 },
    { url: `${baseUrl}/blog`, lastModified, changeFrequency: "weekly" as const, priority: 0.7 },
  ];

  const downloaderPages = platforms.map((p) => ({
    url: `${baseUrl}/download/${p}`,
    lastModified,
    changeFrequency: "weekly" as const,
    priority: 0.9,
  }));

  const blogPages = [
    { url: `${baseUrl}/blog/top-10-video-downloader-tips`, lastModified, changeFrequency: "monthly" as const, priority: 0.6 },
    { url: `${baseUrl}/blog/how-to-download-tiktok-videos`, lastModified, changeFrequency: "monthly" as const, priority: 0.6 },
    { url: `${baseUrl}/blog/the-ultimate-guide-to-video-download-tools`, lastModified, changeFrequency: "monthly" as const, priority: 0.6 },
  ];

  return [...staticPages, ...downloaderPages, ...blogPages];
}
