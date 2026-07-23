import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service - GoTot",
  description: "GoTot Terms of Service — Please read these terms carefully before using our video downloading service.",
};

export default function TermsPage() {
  return (
    <div className="pt-32 pb-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <div className="prose dark:prose-invert max-w-none space-y-6 text-gray-600 dark:text-gray-400">
          <p>Last updated: July 23, 2026</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">1. Acceptance of Terms</h2>
          <p>By accessing or using GoTot (&quot;the Service&quot;), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service. You must accept these terms before initiating any download.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">2. Description of Service</h2>
          <p>GoTot provides a platform that allows users to download videos from supported third-party websites. The Service is provided &quot;as is&quot; and we make no guarantees about its availability or functionality.</p>
          <p className="mt-2">Supported platforms include TikTok, Instagram, Twitter/X, Facebook, Reddit, Vimeo, Dailymotion, Twitch, LinkedIn, Pinterest, Snapchat, Bilibili, SoundCloud, Rumble, and Odysee. GoTot is an independent service and is not affiliated with, endorsed by, or sponsored by any of these platforms. All trademarks belong to their respective owners. Each platform has its own Terms of Service, and it is your responsibility to comply with both our terms and the terms of the platform from which you download content.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">3. User Responsibilities & Copyright Compliance</h2>
          <p>You agree to:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li>Only download content that you own or have explicit permission to download.</li>
            <li>Comply with all applicable laws, including copyright laws, and third-party platform terms of service.</li>
            <li>Not use the Service to violate any platform&apos;s Terms of Service, including but not limited to TikTok, Instagram, X (Twitter), Facebook, Reddit, Vimeo, Dailymotion, Twitch, LinkedIn, Pinterest, Snapchat, Bilibili, SoundCloud, Rumble, and Odysee.</li>
            <li>Not use the Service for any illegal or unauthorized purpose.</li>
            <li>Not attempt to circumvent any usage limits, platform restrictions, or security measures.</li>
            <li>Not upload, distribute, or facilitate distribution of malicious or unauthorized content through the Service.</li>
          </ul>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 p-6 rounded-lg my-6">
            <p className="text-amber-800 dark:text-amber-200 font-semibold mb-2">
              ⚠ Important Copyright Notice
            </p>
            <p className="text-amber-800 dark:text-amber-200 text-sm">
              GoTot does not host, store, or distribute any copyrighted content. All content is downloaded
              directly from the source platform. Users are solely responsible for ensuring they have the
              right to download any content. GoTot does not encourage, promote, or facilitate copyright
              infringement. If you do not own the content or have permission to download it, do not use
              this Service. Violation of copyright laws may result in civil and criminal penalties.
            </p>
          </div>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">4. Intellectual Property</h2>
          <p>Users must respect copyright laws and intellectual property rights. Downloading copyrighted content without permission may violate the rights of the content owner. You are solely responsible for ensuring your use complies with all applicable copyright laws and platform terms of service.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">5. Limitation of Liability</h2>
          <p>GoTot shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of the Service. You assume all liability for any legal issues arising from content you download using our Service.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">6. Termination</h2>
          <p>We reserve the right to terminate or suspend access to the Service at any time, without prior notice, for any violation of these terms, including copyright infringement.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">7. Changes to Terms</h2>
          <p>We may modify these terms at any time. Continued use of the Service after changes constitutes acceptance of the new terms.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">8. Contact</h2>
          <p>For questions about these terms, contact us at support@gotot.app.</p>
        </div>
      </div>
    </div>
  );
}
