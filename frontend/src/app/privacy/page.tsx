import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy - GoTot",
  description: "GoTot Privacy Policy - Learn how we collect, use, and protect your data.",
};

export default function PrivacyPage() {
  return (
    <div className="pt-32 pb-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        <div className="prose dark:prose-invert max-w-none space-y-6 text-gray-600 dark:text-gray-400">
          <p>Last updated: July 23, 2026</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">1. Information We Collect</h2>
          <p>We collect minimal information necessary to provide the Service:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong>Account data:</strong> Email, username, and hashed password if you create an account</li>
            <li><strong>Download data:</strong> URLs you submit for downloading (processed temporarily, not stored long-term)</li>
            <li><strong>Usage data:</strong> Anonymous usage statistics to improve the Service</li>
            <li><strong>Payment data:</strong> Processed securely through Razorpay; we never store full payment details</li>
          </ul>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">2. How We Use Your Data</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li>To provide and maintain the Service</li>
            <li>To process payments and manage subscriptions</li>
            <li>To improve user experience and develop new features</li>
            <li>To communicate important service updates</li>
          </ul>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">3. Data Storage & Security</h2>
          <p>We implement industry-standard security measures including encryption at rest and in transit. Passwords are hashed using bcrypt. We retain data only as long as necessary to provide the Service.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">4. Third-Party Services</h2>
          <p>We use the following third-party services:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li><strong>Razorpay:</strong> Payment processing</li>
            <li><strong>Redis:</strong> Caching and rate limiting</li>
            <li><strong>PostgreSQL:</strong> Database storage</li>
          </ul>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">5. Your Rights</h2>
          <p>You have the right to:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li>Access your personal data</li>
            <li>Request deletion of your data</li>
            <li>Export your data</li>
            <li>Withdraw consent at any time</li>
          </ul>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">6. Cookies</h2>
          <p>We use essential cookies for authentication and service functionality. With your explicit consent, we also use analytics cookies (Google Analytics) to understand how our service is used and improve your experience. You can withdraw consent at any time by clearing your site data.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">7. Your Rights (GDPR &amp; Similar)</h2>
          <p>Depending on your jurisdiction, you may have the right to access, correct, delete, or export your personal data. You may also object to or restrict certain processing. To exercise these rights, contact us at privacy@gotot.app. We will respond within 30 days.</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">8. Contact</h2>
          <p>For privacy inquiries, contact us at privacy@gotot.app.</p>
        </div>
      </div>
    </div>
  );
}
