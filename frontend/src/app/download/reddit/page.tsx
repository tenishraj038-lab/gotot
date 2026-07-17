import { Metadata } from "next";
import DownloadClient from "../DownloadClient";

export const metadata: Metadata = {
  title: "Reddit Video Downloader - Download Reddit Videos Free | GoTot",
  description:
    "Download Reddit videos with audio. Save Reddit GIFs, videos, and v.redd.it content in high quality.",
  keywords: ["reddit downloader", "download reddit videos", "reddit video saver", "v.redd.it downloader"],
  openGraph: {
    title: "Reddit Video Downloader - GoTot",
    description: "Download Reddit videos with audio. Free and fast.",
    url: "https://gotot.app/download/reddit",
  },
  alternates: {
    canonical: "https://gotot.app/download/reddit",
  },
};

export default function RedditDownloaderPage() {
  return (
    <DownloadClient
      platform="Reddit"
      defaultUrl="https://www.reddit.com/r/"
      seoContent={{
        heading: "Reddit Video Downloader",
        subheading: "Save Reddit videos with audio. Free, fast, and no sign-up required.",
        sections: [
          { title: "How to download Reddit videos", steps: ["Find the Reddit post with the video", "Click Share and copy the link", "Paste the URL above", "Download with audio included"] },
          { title: "Supported Content", items: ["Reddit videos (v.redd.it)", "Reddit GIFs (RedGifs)", "Reddit gallery videos", "All subreddits supported"] },
        ],
        faq: [
          { q: "Do Reddit downloads include audio?", a: "Yes, GoTot merges Reddit video and audio streams for a complete download." },
          { q: "Can I download from any subreddit?", a: "Yes, GoTot supports videos from all public subreddits." },
          { q: "What formats are available?", a: "Reddit videos are available in MP4 format at original quality." },
        ],
      }}
    />
  );
}
