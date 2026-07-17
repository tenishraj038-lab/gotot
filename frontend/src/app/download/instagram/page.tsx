import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "Instagram Video Downloader - Download IG Videos & Reels | GoTot",
  description: "Download Instagram videos, Reels, and Stories. Save IG content in high quality for free.",
  keywords: ["instagram downloader", "download instagram reels", "ig video downloader", "instagram story saver"],
  openGraph: {
    title: "Instagram Video Downloader - GoTot",
    description: "Download Instagram videos, Reels, and Stories. Save IG content in high quality for free.",
    url: "https://gotot.app/download/instagram",
  },
  alternates: {
    canonical: "https://gotot.app/download/instagram",
  },
};

export default function InstagramDownloaderPage() {
  return (
    <DownloadClient
      platform="Instagram"
      defaultUrl="https://www.instagram.com/p/"
      seoContent={{
        heading: "Instagram Video Downloader",
        subheading: "Save Instagram Reels, videos, and Stories. Free and anonymous.",
        sections: [
          { title: "How to download Instagram content", steps: ["Copy the Instagram post/Reel URL", "Paste it in the field above", "Select quality and format", "Download to your device"] },
          { title: "Supported Content", items: ["Instagram Reels", "Instagram Videos (posts)", "Instagram Stories", "IGTV videos"] },
        ],
        faq: [
          { q: "Can I download Instagram Stories?", a: "Yes, paste the Story URL and download anonymously." },
          { q: "Do you support Reels?", a: "Yes, GoTot fully supports Instagram Reels downloads." },
        ],
      }}
    />
  );
}
