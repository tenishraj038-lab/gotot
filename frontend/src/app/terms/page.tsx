import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service - GoTot",
  description: "GoTot Terms of Service - Please read these terms carefully before using our video downloading service.",
};

export default function TermsPage() {
  return (
    <div className="pt-32 pb-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <div className="prose dark:prose-invert max-w-none space-y-6 text-gray-600 dark:text-gray-400">
          <p>Last updated: {new Date().toLocaleDateString()}</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">1. Acceptance of Terms</h2>
          <p>By accessing or using GoTot (&quot;the Service&quot;), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">2. Description of Service</h2>
          <p>GoTot provides a platform that allows users to download videos from various third-party websites. The Service is provided &quot;as is&quot; and we make no guarantees about its availability or functionality.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">3. User Responsibilities</h2>
          <p>You agree to:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li>Only download content you have the right to access</li>
            <li>Comply with all applicable laws and third-party terms of service</li>
            <li>Not use the Service for any illegal or unauthorized purpose</li>
            <li>Not attempt to circumvent any usage limits or security measures</li>
            <li>Not upload or distribute malicious content through the Service</li>
          </ul>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">4. Intellectual Property</h2>
          <p>Users must respect copyright laws. Downloading copyrighted content without permission may violate the rights of the content owner. You are solely responsible for ensuring your use complies with applicable copyright laws.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">5. Limitation of Liability</h2>
          <p>GoTot shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of the Service.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">6. Termination</h2>
          <p>We reserve the right to terminate or suspend access to the Service at any time, without prior notice, for any violation of these terms.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">7. Changes to Terms</h2>
          <p>We may modify these terms at any time. Continued use of the Service after changes constitutes acceptance of the new terms.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">8. Contact</h2>
          <p>For questions about these terms, contact us at support@gotot.app.</p>
        </div>
      </div>
    </div>
  );
}
