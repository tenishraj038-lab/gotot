import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "Facebook Video Downloader - Download FB Videos Free | GoTot",
  description:
    "Download Facebook videos, Reels, and Stories in high quality. Save FB content to your device for free.",
  keywords: ["facebook downloader", "download facebook videos", "fb video downloader", "facebook reel downloader"],
  openGraph: {
    title: "Facebook Video Downloader - GoTot",
    description: "Download Facebook videos and Reels. Free and fast.",
    url: "https://gotot.app/download/facebook",
  },
  alternates: {
    canonical: "https://gotot.app/download/facebook",
  },
};

export default function FacebookDownloaderPage() {
  return (
    <DownloadClient
      platform="Facebook"
      defaultUrl="https://www.facebook.com/watch/"
      seoContent={{
        heading: "Facebook Video Downloader",
        subheading: "Save Facebook videos, Reels, and Stories. Free and no sign-up required.",
        sections: [
          { title: "How to download Facebook videos", steps: ["Open Facebook and find the video", "Click the three dots and copy the link", "Paste the URL above", "Choose quality and download"] },
          { title: "Supported Content", items: ["Facebook Videos", "Facebook Reels", "Facebook Stories", "Facebook Live recordings"] },
        ],
        faq: [
          { q: "Can I download private Facebook videos?", a: "GoTot only supports public Facebook videos due to privacy restrictions." },
          { q: "What quality are Facebook downloads?", a: "GoTot downloads Facebook videos in their original quality, up to 1080p." },
          { q: "Is it free?", a: "Yes, basic Facebook video downloads are completely free." },
        ],
      }}
    />
  );
}
