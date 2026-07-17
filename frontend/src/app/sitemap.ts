import { MetadataRoute } from "next";

const baseUrl = "https://gotot.app";

const platforms = ["youtube", "tiktok", "instagram", "twitter", "facebook", "reddit", "vimeo", "dailymotion", "twitch", "linkedin", "pinterest"];

export default function sitemap(): MetadataRoute.Sitemap {
  const staticPages = [
    { url: baseUrl, lastModified: new Date(), changeFrequency: "weekly" as const, priority: 1.0 },
    { url: `${baseUrl}/pricing`, lastModified: new Date(), changeFrequency: "monthly" as const, priority: 0.8 },
    { url: `${baseUrl}/terms`, lastModified: new Date(), changeFrequency: "yearly" as const, priority: 0.3 },
    { url: `${baseUrl}/privacy`, lastModified: new Date(), changeFrequency: "yearly" as const, priority: 0.3 },
    { url: `${baseUrl}/contact`, lastModified: new Date(), changeFrequency: "yearly" as const, priority: 0.4 },
  ];

  const downloaderPages = platforms.map((p) => ({
    url: `${baseUrl}/download/${p}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: 0.9,
  }));

  const blogPages = [
    { url: `${baseUrl}/blog`, lastModified: new Date(), changeFrequency: "weekly" as const, priority: 0.7 },
    { url: `${baseUrl}/blog/top-10-video-downloader-tips`, lastModified: new Date(), changeFrequency: "monthly" as const, priority: 0.6 },
    { url: `${baseUrl}/blog/how-to-download-tiktok-videos`, lastModified: new Date(), changeFrequency: "monthly" as const, priority: 0.6 },
    { url: `${baseUrl}/blog/youtube-vs-tiktok-downloader`, lastModified: new Date(), changeFrequency: "monthly" as const, priority: 0.6 },
  ];

  return [...staticPages, ...downloaderPages, ...blogPages];
}
