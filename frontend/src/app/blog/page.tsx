import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "GoTot Blog - Video Downloading Tips & Guides",
  description: "Learn how to download videos from TikTok, Instagram, and more. Tips, tricks, and guides.",
};

const posts = [
  {
    slug: "top-10-video-downloader-tips",
    title: "Top 10 Video Downloader Tips for 2025",
    excerpt: "Master the art of video downloading with these pro tips. Save time, get better quality, and download from any platform.",
    date: "2025-06-15",
    readTime: "5 min read",
    category: "Tips",
  },
  {
    slug: "how-to-download-tiktok-videos",
    title: "How to Download TikTok Videos Without Watermark",
    excerpt: "Complete guide to downloading TikTok videos without watermark in HD quality. Free and easy methods.",
    date: "2025-06-10",
    readTime: "4 min read",
    category: "Tutorial",
  },
  {
    slug: "tiktok-vs-instagram-downloader",
    title: "TikTok vs Instagram Downloader: Which One Do You Need?",
    excerpt: "Compare TikTok and Instagram downloaders. Features, quality, formats, and which platform fits your needs.",
    date: "2025-06-05",
    readTime: "6 min read",
    category: "Comparison",
  },
];

export default function BlogPage() {
  return (
    <div className="pt-32 pb-24">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold mb-4">GoTot Blog</h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Video downloading tips, guides, and platform comparisons.
          </p>
        </div>
        <div className="space-y-6">
          {posts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="block p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 hover:shadow-xl transition-all group"
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs px-2 py-0.5 rounded-full bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 font-medium">
                  {post.category}
                </span>
                <span className="text-xs text-gray-500">{post.date}</span>
                <span className="text-xs text-gray-500">{post.readTime}</span>
              </div>
              <h2 className="text-xl font-bold group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                {post.title}
              </h2>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {post.excerpt}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
