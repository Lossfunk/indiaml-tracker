import React from "react";
import { motion } from "framer-motion";
import { FaRegSmileWink } from "react-icons/fa";
import Confetti from "react-confetti";
import { ResearchPapersShowcase } from "./research-paper-showcase";

export default function Home() {
  return (
    <main className="relative container mx-auto p-4 min-h-screen overflow-visible text-gray-100">
      {/* Main Card Container with glassmorphic outline */}
      <div className="
        max-w-[700px] mx-auto mt-10 p-6 
        bg-white/10             
        border border-white/20   
        backdrop-blur-md        
        rounded-xl shadow-2xl  
        relative z-10 text-center
      ">
        
        {/* Animated Title (one-time animation) */}
        <motion.h1
          className="text-3xl md:text-4xl font-extrabold mb-6 flex items-center justify-center gap-2"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1, rotate: [0, 3, -3, 0] }}
          transition={{ duration: 1 }}
        >
          Indian Research Papers accepted at Top AI/ML conferences in 2024!
        </motion.h1>

        {/* Subtitle (slides in once) */}
        <motion.h6
          className="text-base md:text-lg text-gray-200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          These are the papers that were accepted where at least one author could
          be verified to have done their research from an Indian Institute or
          Research Unit.
        </motion.h6>
      </div>

      {/* Showcase Section (slide-in, one-time animation) */}
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
