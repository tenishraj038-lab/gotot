"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { CheckCircle, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import DownloadForm from "@/components/DownloadForm";
import ResultCard from "@/components/ResultCard";
import { useStore } from "@/lib/store";

interface SeoContent {
  heading: string;
  subheading: string;
  sections: Array<{
    title: string;
    steps?: string[];
    items?: string[];
  }>;
  faq: Array<{ q: string; a: string }>;
}

interface Props {
  platform: string;
  defaultUrl?: string;
  seoContent: SeoContent;
}

export default function DownloadClient({ platform, defaultUrl, seoContent }: Props) {
  const { setUrl } = useStore();
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  useEffect(() => {
    if (defaultUrl) setUrl(defaultUrl);
  }, []);

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: seoContent.faq.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.a,
      },
    })),
  };

  const howToJsonLd = {
    "@context": "https://schema.org",
    "@type": "HowTo",
    name: `How to download ${platform} videos`,
    description: seoContent.subheading,
    step: seoContent.sections[0]?.steps?.map((step, i) => ({
      "@type": "HowToStep",
      position: i + 1,
      text: step,
    })) || [],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToJsonLd) }}
      />
      <div className="pt-32 pb-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="text-4xl sm:text-5xl font-extrabold mb-4">
              {seoContent.heading}
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              {seoContent.subheading}
            </p>
          </motion.div>

          <div className="max-w-3xl mx-auto mb-16">
            <DownloadForm />
            <ResultCard />
          </div>

          <div className="max-w-4xl mx-auto space-y-12">
            {seoContent.sections.map((section, i) => (
              <motion.div
                key={section.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <h2 className="text-2xl font-bold mb-6">{section.title}</h2>
                {section.steps && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {section.steps.map((step, j) => (
                      <div key={j} className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center mb-2">
                          <span className="text-white font-bold text-sm">{j + 1}</span>
                        </div>
                        <p className="text-sm">{step}</p>
                      </div>
                    ))}
                  </div>
                )}
                {section.items && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {section.items.map((item, j) => (
                      <div key={j} className="flex items-center gap-3 p-3 rounded-xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50">
                        <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                        <span className="text-sm">{item}</span>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="text-2xl font-bold mb-6">Frequently Asked Questions</h2>
              <div className="space-y-3">
                {seoContent.faq.map((item, i) => (
                  <div
                    key={i}
                    className="rounded-xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 overflow-hidden"
                  >
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      className="w-full flex items-center justify-between p-4 text-left"
                    >
                      <span className="font-medium text-sm">{item.q}</span>
                      {openFaq === i ? (
                        <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
                      )}
                    </button>
                    {openFaq === i && (
                      <div className="px-4 pb-4">
                        <p className="text-sm text-gray-600 dark:text-gray-400">{item.a}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </>
  );
}
