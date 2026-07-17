"use client";

import { motion } from "framer-motion";
import {
  Zap, Shield, Globe, Download, Layers, Sparkles,
  Music, Users, Monitor, Clock,
} from "lucide-react";
import { useLocale } from "@/lib/i18n";

export default function Features() {
  const { t } = useLocale();

  const features = [
    { icon: Globe, title: t.features.platformsTitle, description: t.features.platformsDesc, color: "from-blue-500 to-cyan-500" },
    { icon: Zap, title: t.features.fastTitle, description: t.features.fastDesc, color: "from-amber-500 to-orange-500" },
    { icon: Shield, title: t.features.secureTitle, description: t.features.secureDesc, color: "from-green-500 to-emerald-500" },
    { icon: Layers, title: t.features.formatsTitle, description: t.features.formatsDesc, color: "from-purple-500 to-pink-500" },
    { icon: Download, title: t.features.qualityTitle, description: t.features.qualityDesc, color: "from-red-500 to-rose-500" },
    { icon: Music, title: t.features.mp3Title, description: t.features.mp3Desc, color: "from-indigo-500 to-violet-500" },
    { icon: Users, title: t.features.batchTitle, description: t.features.batchDesc, color: "from-teal-500 to-cyan-500" },
    { icon: Clock, title: t.features.noWaitTitle, description: t.features.noWaitDesc, color: "from-orange-500 to-red-500" },
    { icon: Sparkles, title: t.features.freeTitle, description: t.features.freeDesc, color: "from-primary-500 to-accent-600" },
  ];

  return (
    <section id="features" className="py-24 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl md:text-4xl font-bold">
            {t.features.title}{" "}
            <span className="text-gradient">GoTot</span>
            ?
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            {t.features.subtitle}
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="group relative p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200/50 dark:border-gray-800/50 hover:shadow-xl hover:shadow-gray-200/50 dark:hover:shadow-gray-900/50 transition-all duration-300"
            >
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} p-2.5 mb-4 shadow-lg`}
              >
                <feature.icon className="w-full h-full text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
