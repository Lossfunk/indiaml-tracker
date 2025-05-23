import { motion } from "framer-motion";
import { FaGithub, FaRegSmileWink } from "react-icons/fa";
import { ResearchPapersShowcase } from "./research-paper-showcase";
import { ExternalLinkIcon } from "lucide-react";

export default function Home() {
  return (
    <main className="relative container mx-auto p-4 min-h-screen overflow-visible text-gray-900 dark:text-gray-200">
      {/* Main Card Container with glassmorphic outline */}
      <div
        className="
        max-w-[700px] mx-auto mt-10 p-6 
        bg-white/10             
        border border-white/20   
        backdrop-blur-md        
        rounded-xl shadow-2xl  
        relative z-10 text-center
      "
      >
        {/* Animated Title (one-time animation) */}
        <motion.h1
          className="text-3xl md:text-4xl font-semibold  mb-6 flex flex-col items-center justify-center gap-2"
          initial={{ scale: 1, opacity: 0 }}
          animate={{ scale: 1, opacity: 1, y: [50, 0] }}
          transition={{ duration: 1, ease: "anticipate" }}
        >
          Indian Research Papers 🇮🇳 accepted at Top AI/ML conferences
        </motion.h1>

        {/* Subtitle (slides in once) */}
        <motion.h6
          className="text-base md:text-lg text-gray-800 dark:text-gray-300"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          These are the papers that were accepted where at least one author
          could be verified to have done their research from an Indian Institute
          or Research Unit.
        </motion.h6>

        <motion.div
          className="mt-5"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7 }}
        >
          <a
            href="https://github.com/lossfunk/indiaml-tracker/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex  font-semibold items-center px-4 py-2 text-sm rounded-md text-gray-100 bg-indigo-600 hover:bg-indigo-500 transition-colors"
          >
            <FaGithub className="mr-2" />
            View Research Data & Pipelines  
            <ExternalLinkIcon className="h-3"/>
          </a>
          <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">
            Explore data pipelines and research materials for India's ML
            landscape
          </p>
        </motion.div>
      </div>

      {/* Showcase Section (slide-in, o-time animation) */}
      <motion.div
        className="relative z-10 mt-8"
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 1, duration: 1 }}
      >
        <ResearchPapersShowcase />
      </motion.div>
    </main>
  );
}
