import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "LinkedIn Video Downloader - Download LinkedIn Videos Free | GoTot",
  description:
    "Download LinkedIn videos and learning content. Save professional videos to your device for free.",
  keywords: ["linkedin downloader", "download linkedin videos", "linkedin video saver"],
  openGraph: {
    title: "LinkedIn Video Downloader - GoTot",
    description: "Download LinkedIn videos. Free and fast.",
    url: "https://gotot.app/download/linkedin",
  },
  alternates: {
    canonical: "https://gotot.app/download/linkedin",
  },
};

export default function LinkedInDownloaderPage() {
  return (
    <DownloadClient
      platform="LinkedIn"
      defaultUrl="https://www.linkedin.com/feed/update/"
      seoContent={{
        heading: "LinkedIn Video Downloader",
        subheading: "Save LinkedIn videos and professional content. Free and no sign-up required.",
        sections: [
          { title: "How to download LinkedIn videos", steps: ["Find the LinkedIn post with a video", "Click the three dots and copy the link", "Paste the URL above", "Download to your device"] },
          { title: "Supported Content", items: ["LinkedIn feed videos", "LinkedIn Learning content", "LinkedIn article videos", "Company page videos"] },
        ],
        faq: [
          { q: "Can I download LinkedIn Learning videos?", a: "GoTot supports publicly available LinkedIn video content." },
          { q: "Is it free?", a: "Yes, LinkedIn video downloads are completely free." },
          { q: "What quality are the downloads?", a: "LinkedIn videos are downloaded in their original available quality." },
        ],
      }}
    />
  );
}
