import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "Vimeo Video Downloader - Download Vimeo Videos Free | GoTot",
  description:
    "Download Vimeo videos in highest quality. Save Vimeo content in 4K, HD, and multiple formats.",
  keywords: ["vimeo downloader", "download vimeo videos", "vimeo video saver", "vimeo 4k downloader"],
  openGraph: {
    title: "Vimeo Video Downloader - GoTot",
    description: "Download Vimeo videos in highest quality. Free and fast.",
    url: "https://gotot.app/download/vimeo",
  },
  alternates: {
    canonical: "https://gotot.app/download/vimeo",
  },
};

export default function VimeoDownloaderPage() {
  return (
    <DownloadClient
      platform="Vimeo"
      defaultUrl="https://vimeo.com/"
      seoContent={{
        heading: "Vimeo Video Downloader",
        subheading: "Save Vimeo videos in original quality, up to 4K. Free and no sign-up.",
        sections: [
          { title: "How to download Vimeo videos", steps: ["Open the Vimeo video page", "Copy the video URL from the address bar", "Paste the URL above", "Select format and download"] },
          { title: "Supported Features", items: ["Up to 4K resolution", "MP4 and WebM formats", "Audio extraction", "Multiple quality options"] },
        ],
        faq: [
          { q: "Can I download 4K Vimeo videos?", a: "Yes, GoTot supports downloading Vimeo videos up to their original 4K resolution." },
          { q: "Are password-protected Vimeo videos supported?", a: "Only public Vimeo videos can be downloaded." },
          { q: "What formats are available?", a: "Vimeo videos are available in MP4, WebM, and audio-only MP3 formats." },
        ],
      }}
    />
  );
}
