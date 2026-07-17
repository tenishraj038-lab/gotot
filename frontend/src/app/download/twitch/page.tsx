import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "Twitch Clip Downloader - Download Twitch Videos Free | GoTot",
  description:
    "Download Twitch clips and VODs in high quality. Save Twitch content to your device for free.",
  keywords: ["twitch downloader", "download twitch clips", "twitch vod downloader", "twitch clip saver"],
  openGraph: {
    title: "Twitch Clip Downloader - GoTot",
    description: "Download Twitch clips and VODs. Free and fast.",
    url: "https://gotot.app/download/twitch",
  },
  alternates: {
    canonical: "https://gotot.app/download/twitch",
  },
};

export default function TwitchDownloaderPage() {
  return (
    <DownloadClient
      platform="Twitch"
      defaultUrl="https://www.twitch.tv/"
      seoContent={{
        heading: "Twitch Clip Downloader",
        subheading: "Save Twitch clips and highlights in high quality. Free and no sign-up.",
        sections: [
          { title: "How to download Twitch content", steps: ["Find the Twitch clip or VOD", "Copy the URL from the address bar", "Paste the URL above", "Download in your preferred quality"] },
          { title: "Supported Content", items: ["Twitch Clips", "Twitch Highlights", "Twitch VODs (past broadcasts)", "Multiple quality options"] },
        ],
        faq: [
          { q: "Can I download Twitch clips?", a: "Yes, GoTot supports downloading Twitch clips in their original quality." },
          { q: "Are VODs supported?", a: "Yes, available Twitch VODs and highlights can be downloaded." },
          { q: "What quality options are there?", a: "Twitch content is available in multiple qualities from 360p to 1080p." },
        ],
      }}
    />
  );
}
