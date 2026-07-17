"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ExternalLink, Star, TrendingUp } from "lucide-react";
import { api, AffiliateLinkInfo } from "@/lib/api";

export default function AffiliateSection() {
  const [links, setLinks] = useState<AffiliateLinkInfo[]>([]);

  useEffect(() => {
    api.getAffiliateLinks().then(setLinks).catch(() => {});
  }, []);

  if (links.length === 0) return null;

  return (
    <section className="py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-10"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800/50 mb-4">
            <Star className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            <span className="text-xs font-medium text-amber-700 dark:text-amber-300">
              Recommended Tools
            </span>
          </div>
          <h2 className="text-3xl font-bold">
            Tools We <span className="text-gradient">Recommend</span>
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            We earn a commission when you purchase through these links.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {links.map((link, i) => (
            <motion.a
              key={link.id}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer sponsored"
              onClick={() => api.recordAffiliateClick(link.id).catch(() => {})}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="group p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 hover:shadow-xl hover:border-primary-500/30 transition-all duration-300"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm font-semibold group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                    {link.name}
                  </p>
                  <p className="text-xs text-gray-500 capitalize">{link.platform}</p>
                </div>
              </div>
              {link.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {link.description}
                </p>
              )}
              <div className="mt-3 flex items-center justify-between">
                {link.commission_rate && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                    {link.commission_rate} commission
                  </span>
                )}
                <span className="flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  Learn More <ExternalLink className="w-3 h-3" />
                </span>
              </div>
            </motion.a>
          ))}
        </div>
      </div>
    </section>
  );
}
