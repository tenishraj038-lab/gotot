import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "YouTube Video Downloader - Download YouTube Videos Free | GoTot",
  description:
    "Download YouTube videos in high quality up to 4K for free. Support for MP4, WebM, and MP3 formats. Fast, secure, and unlimited downloads.",
  keywords: [
    "youtube downloader",
    "download youtube videos",
    "youtube to mp4",
    "youtube to mp3",
    "free youtube downloader",
  ],
  openGraph: {
    title: "YouTube Video Downloader - GoTot",
    description: "Download YouTube videos free in 4K, MP4, or MP3. Fast and secure.",
    url: "https://gotot.app/download/youtube",
  },
  alternates: {
    canonical: "https://gotot.app/download/youtube",
  },
};

export default function YoutubeDownloaderPage() {
  return (
    <DownloadClient
      platform="YouTube"
      defaultUrl="https://www.youtube.com/watch?v="
      seoContent={{
        heading: "YouTube Video Downloader",
        subheading: "Download any YouTube video in high quality. Free, fast, and secure.",
        sections: [
          {
            title: "How to download YouTube videos",
            steps: [
              "Copy the URL of the YouTube video you want to download",
              "Paste the URL into the input field above",
              "Select your preferred format and quality",
              "Click download and save the file",
            ],
          },
          {
            title: "Supported Formats",
            items: [
              "MP4 Video - up to 4K (2160p)",
              "WebM Video - up to 4K",
              "MP3 Audio - 128kbps to 320kbps",
              "3GP - for mobile devices",
            ],
          },
          {
            title: "Features",
            items: [
              "Download YouTube Shorts",
              "Download entire playlists",
              "Extract audio from any video",
              "No registration required",
              "SSL encrypted connection",
            ],
          },
        ],
        faq: [
          { q: "Is it free to download YouTube videos?", a: "Yes, GoTot is completely free. No hidden charges, no limits. Download as many videos as you want." },
          { q: "What is the maximum quality?", a: "All users can download up to 4K (2160p) quality for free. No registration or payment required." },
          { q: "Can I download YouTube Shorts?", a: "Yes, GoTot supports downloading YouTube Shorts. Just paste the Shorts URL." },
          { q: "Is MP3 conversion available?", a: "Yes, MP3 conversion is completely free with bitrate options from 128kbps to 320kbps." },
        ],
      }}
    />
  );
}
