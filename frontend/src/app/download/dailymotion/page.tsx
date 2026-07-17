import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "Dailymotion Video Downloader - Download DM Videos Free | GoTot",
  description:
    "Download Dailymotion videos in high quality. Save DM content to your device for free.",
  keywords: ["dailymotion downloader", "download dailymotion videos", "dm video downloader"],
  openGraph: {
    title: "Dailymotion Video Downloader - GoTot",
    description: "Download Dailymotion videos. Free and fast.",
    url: "https://gotot.app/download/dailymotion",
  },
  alternates: {
    canonical: "https://gotot.app/download/dailymotion",
  },
};

export default function DailymotionDownloaderPage() {
  return (
    <DownloadClient
      platform="Dailymotion"
      defaultUrl="https://www.dailymotion.com/video/"
      seoContent={{
        heading: "Dailymotion Video Downloader",
        subheading: "Save Dailymotion videos in HD quality. Free and no sign-up required.",
        sections: [
          { title: "How to download Dailymotion videos", steps: ["Open the Dailymotion video", "Copy the video URL", "Paste it in the field above", "Choose quality and download"] },
          { title: "Supported Features", items: ["HD and SD quality options", "MP4 format", "Fast download speeds", "No registration needed"] },
        ],
        faq: [
          { q: "What quality are Dailymotion downloads?", a: "GoTot downloads Dailymotion videos in their available quality, up to 1080p." },
          { q: "Is it free?", a: "Yes, Dailymotion downloads are completely free." },
          { q: "Do I need an account?", a: "No account is needed to download Dailymotion videos." },
        ],
      }}
    />
  );
}
