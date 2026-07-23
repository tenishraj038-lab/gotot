import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Copyright Policy - GoTot",
  description: "GoTot Copyright Policy — respecting intellectual property and complying with copyright laws.",
};

export default function CopyrightPage() {
  return (
    <div className="pt-32 pb-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold mb-8">Copyright Policy</h1>
        <div className="prose dark:prose-invert max-w-none space-y-6 text-gray-600 dark:text-gray-400">
          <p>Last updated: July 23, 2026</p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">1. Respect for Intellectual Property</h2>
          <p>
            GoTot respects the intellectual property rights of others and expects its users to do the same.
            We comply with the Digital Millennium Copyright Act (DMCA) and other applicable copyright laws.
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">2. User Responsibility</h2>
          <p>
            By using GoTot, you agree that:
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>You will only download content that you own or have explicit permission to download.</li>
            <li>You are solely responsible for complying with all applicable copyright laws.</li>
            <li>GoTot does not encourage, promote, or facilitate copyright infringement.</li>
            <li>Downloading copyrighted content without authorization may violate the rights of the content owner.</li>
            <li>You assume all liability for any copyright violations resulting from your use of the Service.</li>
          </ul>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">3. Fair Use</h2>
          <p>
            In some jurisdictions, limited use of copyrighted material may be permitted under
            &quot;fair use&quot; or &quot;fair dealing&quot; provisions. It is your responsibility to
            determine whether your intended use qualifies as fair use under applicable law.
            GoTot does not provide legal advice regarding fair use.
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">4. DMCA Compliance</h2>
          <p>
            If you believe that your copyrighted work has been made available through GoTot in a way
            that constitutes copyright infringement, please submit a DMCA takedown notice to{" "}
            <a href="mailto:dmca@gotot.app" className="text-primary-600 hover:underline">
              dmca@gotot.app
            </a>{" "}
            with the following information:
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>A physical or electronic signature of the copyright owner or authorized agent.</li>
            <li>Identification of the copyrighted work claimed to have been infringed.</li>
            <li>Identification of the material that is claimed to be infringing, including its URL.</li>
            <li>Your contact information: name, address, telephone number, and email address.</li>
            <li>A statement that you have a good faith belief that use of the material is not authorized.</li>
            <li>A statement under penalty of perjury that the information is accurate.</li>
          </ul>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">5. Repeat Infringers</h2>
          <p>
            GoTot reserves the right to terminate the accounts of users who are repeat infringers
            of copyright. We may also remove or disable access to content alleged to be infringing.
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-8">6. Contact</h2>
          <p>
            For copyright-related inquiries, DMCA notices, or to report infringement, contact us at{" "}
            <a href="mailto:dmca@gotot.app" className="text-primary-600 hover:underline">
              dmca@gotot.app
            </a>.
          </p>
        </div>
      </div>
    </div>
  );
}
