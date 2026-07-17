import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "TikTok Video Downloader - Download TikTok Videos Free | GoTot",
  description:
    "Download TikTok videos without watermark in high quality. Save TikTok, TikTok Music, and TikTok slideshows for free.",
  keywords: ["tiktok downloader", "download tiktok videos", "tiktok without watermark", "tiktok video saver"],
  openGraph: {
    title: "TikTok Video Downloader - GoTot",
    description: "Download TikTok videos without watermark. Free and fast.",
    url: "https://gotot.app/download/tiktok",
  },
  alternates: {
    canonical: "https://gotot.app/download/tiktok",
  },
};

export default function TiktokDownloaderPage() {
  return (
    <DownloadClient
      platform="TikTok"
      defaultUrl="https://www.tiktok.com/@username/video/"
      seoContent={{
        heading: "TikTok Video Downloader",
        subheading: "Save TikTok videos without watermark. Free and no sign-up required.",
        sections: [
          { title: "How to download TikTok videos", steps: ["Open TikTok and copy the video link", "Paste the URL above", "Choose video or audio only", "Download and enjoy offline"] },
          { title: "Features", items: ["No watermark download", "Save TikTok slideshows", "MP4 and MP3 formats", "High quality preservation"] },
        ],
        faq: [
          { q: "Can I download TikTok without watermark?", a: "Yes, GoTot removes watermarks from TikTok downloads." },
          { q: "Is it free?", a: "Yes, GoTot is completely free. Download as many TikTok videos as you want with no limits." },
        ],
      }}
    />
  );
}
