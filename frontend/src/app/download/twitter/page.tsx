import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "Twitter/X Video Downloader - Download Twitter Videos | GoTot",
  description: "Download Twitter/X videos and GIFs in high quality. Save any Twitter video for free.",
  keywords: ["twitter video downloader", "x video downloader", "download twitter videos", "twitter media saver"],
  openGraph: {
    title: "Twitter/X Video Downloader - GoTot",
    description: "Download Twitter/X videos and GIFs in high quality. Save any Twitter video for free.",
    url: "https://gotot.app/download/twitter",
  },
  alternates: {
    canonical: "https://gotot.app/download/twitter",
  },
};

export default function TwitterDownloaderPage() {
  return (
    <DownloadClient
      platform="Twitter"
      defaultUrl="https://twitter.com/username/status/"
      seoContent={{
        heading: "Twitter/X Video Downloader",
        subheading: "Download any video from Twitter/X. Save in MP4 or MP3 format.",
        sections: [
          { title: "How to download Twitter videos", steps: ["Find the tweet with the video", "Copy the tweet URL", "Paste it above and select format", "Download your video"] },
          { title: "Features", items: ["Download videos from Twitter/X", "Save GIFs", "Extract audio from video tweets", "High resolution downloads"] },
        ],
        faq: [
          { q: "Does it work with X (formerly Twitter)?", a: "Yes, both twitter.com and x.com URLs are supported." },
          { q: "Can I download Twitter GIFs?", a: "Yes, GIFs can be downloaded as MP4 videos." },
        ],
      }}
    />
  );
}
