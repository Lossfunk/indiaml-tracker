"use client" // Assuming this is still needed for the environment

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion" // Keep if ConferenceCard uses it, though it doesn't directly in the snippet
import type { Paper } from "@/types/paper" // Assuming Paper type is defined elsewhere

// Icons from lucide-react for ConferenceCard
import { Download, RotateCcw, ChevronDown, ChevronUp, List } from 'lucide-react';

// --- Helper Function for Class Merging (from ConferenceCard) ---
function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

// --- Helper Function to get Flag Emoji (from original PaperCard) ---
/**
 * Converts a 2-letter country code (ISO 3166-1 alpha-2) to a flag emoji.
 * @param countryCode - The 2-letter country code (e.g., "IN", "US").
 * @returns The corresponding flag emoji string, or an empty string if invalid.
 */
function getFlagEmoji(countryCode: string | null | undefined): string {
  if (!countryCode || countryCode.length !== 2) {
    return "";
  }
  const code = countryCode.toUpperCase();
  if (code.charCodeAt(0) < 65 || code.charCodeAt(0) > 90 || code.charCodeAt(1) < 65 || code.charCodeAt(1) > 90) {
    return "";
  }
  const codePoint1 = 0x1F1E6 + (code.charCodeAt(0) - 65);
  const codePoint2 = 0x1F1E6 + (code.charCodeAt(1) - 65);
  return String.fromCodePoint(codePoint1) + String.fromCodePoint(codePoint2);
}

// --- Helper functions for author display (from original PaperCard) ---
function getDisplayName(author: {
  name?: string
  openreview_id?: string
}): string {
  if (author.name && author.name.trim() !== "") {
    return author.name;
  }
  if (author.openreview_id) {
    return processOpenReviewId(author.openreview_id);
  }
  return "Unknown Author";
}

function processOpenReviewId(id: string): string {
  let processed = id.startsWith("~") ? id.slice(1) : id;
  processed = processed.replace(/\d+$/, "");
  processed = processed.replace(/_/g, " ");
  processed = processed.toLowerCase();
  return processed.charAt(0).toUpperCase() + processed.slice(1);
}


// --- Conference Card Component (Modified to accept pdfUrl) ---
/**
 * ConferenceCard Component
 * A 3D flipping card component to display conference paper details.
 */
const ConferenceCard = ({
  title,
  authors,
  conferenceInfo,
  shortSummary,
  fullSummary,
  accentColor = 'bg-orange-500', // Default accent color
  // presentationType, // Prop available, used for accent logic if needed in future
  isDarkMode,
  pdfUrl, // Added prop for PDF URL
}: {
  title: string;
  authors: { name: string; flag: string }[];
  conferenceInfo: string;
  shortSummary: string;
  fullSummary: string;
  accentColor?: string;
  presentationType?: string;
  isDarkMode: boolean;
  pdfUrl?: string; // Make it optional
}) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const [showAllAuthors, setShowAllAuthors] = useState(false);

  const handleFlip = () => setIsFlipped(!isFlipped);
  const toggleAuthors = () => setShowAllAuthors(!showAllAuthors);

  const handleDownload = () => {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank', 'noopener,noreferrer');
    } else {
      console.log(`No PDF URL available for: ${title}`);
    }
  };

  const cardBaseStyle = cn(
    "absolute w-full h-full bg-zinc-800 rounded-3xl border border-zinc-700 shadow-lg overflow-hidden",
    "[backface-visibility:hidden] flex flex-col transform translate-z-0",
    isDarkMode ? 'border-opacity-30' : 'border-opacity-50'
  );
  const cardShadowStyle = { boxShadow: '0 12px 40px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255, 226, 130, 0.08), inset 0 1px 1px rgba(255, 255, 255, 0.08)' };

  const primaryButtonStyle = cn(
    "flex items-center justify-center px-4 py-1.5 text-amber-400 text-xs font-semibold",
    "rounded-full border border-zinc-600 bg-zinc-700/80 shadow-md",
    "hover:bg-zinc-700 hover:text-amber-300 hover:border-zinc-500",
    "focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-opacity-60",
    "transition duration-300"
  );
  const ghostButtonStyle = cn(
    "flex items-center justify-center px-4 py-1.5 text-amber-100/60 text-xs font-medium rounded-full",
    "hover:bg-amber-100/5 hover:text-amber-100/80",
    "focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-opacity-50",
    "transition duration-300"
  );

  const lightModeGradient = 'radial-gradient(circle at bottom left, rgba(217, 119, 6, 0.15) 0%, rgba(0, 0, 0, 0) 70%)';
  const darkModeGradient = 'radial-gradient(circle at bottom left, rgba(217, 119, 6, 0.05) 0%, rgba(0, 0, 0, 0) 70%)';
  const backgroundGradientStyle = { background: isDarkMode ? darkModeGradient : lightModeGradient };

  const maxVisibleAuthorsFront = 3; // Max authors to show on front before "more"

  return (
    <motion.div // Added motion.div for potential top-level animations from parent
      className="w-96 h-96 [perspective:1000px]" // Size defined here as per ConferenceCard original
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      // whileHover={{ scale: 1.01 }} // This was on old PaperCard, can be added here if desired
    >
      <div
        className={`relative w-full h-full transition-transform duration-700 ease-in-out [transform-style:preserve-3d] ${isFlipped ? '[transform:rotateY(180deg)]' : ''}`}
      >
        {/* ========== Front Side Container ========== */}
        <div className={cardBaseStyle} style={cardShadowStyle}>
          <div className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden">
            <div className="absolute inset-0 w-full h-full" style={backgroundGradientStyle}>
              <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
                <pattern id="dotPatternCardDense" width="5" height="5" patternUnits="userSpaceOnUse">
                  <circle cx="2.5" cy="2.5" r="0.4" fill="rgba(251, 191, 36, 0.1)" />
                </pattern>
                <rect width="100%" height="100%" fill="url(#dotPatternCardDense)" />
              </svg>
            </div>
          </div>
          <div className="text-amber-200/70 text-sm tracking-wider mt-6 ml-6 mb-4 flex-shrink-0">
            {conferenceInfo}
          </div>
          <div className="relative mb-4 flex-shrink-0">
            <div className={cn("absolute left-0 top-0.5 w-1.5 h-8 rounded-r-full", accentColor)}></div>
            <div className="pl-6 pr-6">
              <h1 className="text-amber-100 text-3xl font-serif leading-tight overflow-hidden line-clamp-2" style={{ textShadow: '0 1px 5px rgba(251, 191, 36, 0.2), 0 2px 10px rgba(0, 0, 0, 0.4)' }}>
                {title}
              </h1>
            </div>
          </div>
          <div className="px-6 mb-3 flex-shrink-0">
            <p className="text-amber-100/70 text-xs line-clamp-2">
              {shortSummary}
            </p>
          </div>
          <div className={`px-6 mb-3 overflow-hidden transition-all duration-300 ease-in-out flex-grow ${showAllAuthors ? 'max-h-36 overflow-y-auto custom-scrollbar' : 'max-h-[4.5rem]'}`}>
            {!showAllAuthors ? (
              <div className="flex flex-wrap gap-1 items-center">
                {authors.slice(0, maxVisibleAuthorsFront).map((author, index) => (
                  <div key={index} className="flex items-center bg-zinc-700/50 rounded-full pl-1.5 pr-2 py-0.5">
                    <span className="text-lg mr-1.5" role="img" aria-label={`Flag for ${author.name}`}>{author.flag}</span>
                    <span className="text-amber-100 text-[11px] whitespace-nowrap font-medium">{author.name}</span>
                  </div>
                ))}
                {authors.length > maxVisibleAuthorsFront && (
                  <button onClick={toggleAuthors} className="bg-zinc-700/50 text-amber-100 rounded-full px-2.5 py-1 text-[11px] hover:bg-zinc-600/60 transition-colors flex items-center font-medium">
                    +{authors.length - maxVisibleAuthorsFront} more <ChevronDown className="w-3 h-3 ml-1" />
                  </button>
                )}
              </div>
            ) : (
              <div className="flex flex-col">
                <div className="flex flex-wrap gap-1 mb-1">
                  {authors.map((author, index) => (
                    <div key={index} className="flex items-center bg-zinc-700/50 rounded-full pl-1.5 pr-2 py-0.5">
                      <span className="text-lg mr-1.5" role="img" aria-label={`Flag for ${author.name}`}>{author.flag}</span>
                      <span className="text-amber-100 text-[11px] whitespace-nowrap font-medium">{author.name}</span>
                    </div>
                  ))}
                </div>
                <button onClick={toggleAuthors} className="self-center text-amber-200 text-[11px] hover:text-amber-100 transition-colors flex items-center mt-1 font-medium">
                  Show Less <ChevronUp className="w-3 h-3 ml-1" />
                </button>
              </div>
            )}
          </div>
          <div className="mt-auto mb-4 px-6 flex justify-end space-x-3 flex-shrink-0">
            {pdfUrl && ( // Only show button if pdfUrl exists
                <button onClick={handleDownload} aria-label="Paper" className={ghostButtonStyle}>
                    <Download className="w-4 h-4 mr-2" /> Paper
                </button>
            )}
            <button onClick={handleFlip} aria-label="Summary" className={primaryButtonStyle}>
              <List className="w-4 h-4 mr-2" /> Summary
            </button>
          </div>
        </div>

        {/* ========== Back Side Container ========== */}
        <div className={`${cardBaseStyle} [transform:rotateY(180deg)] p-5`} style={cardShadowStyle}>
          <div className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden -z-10">
            <div className="absolute inset-0 w-full h-full" style={backgroundGradientStyle}>
              <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
                <pattern id="dotPatternCardDenseBack" width="5" height="5" patternUnits="userSpaceOnUse">
                  <circle cx="2.5" cy="2.5" r="0.4" fill="rgba(251, 191, 36, 0.1)" />
                </pattern>
                <rect width="100%" height="100%" fill="url(#dotPatternCardDenseBack)" />
              </svg>
            </div>
          </div>
          <h2 className="text-amber-200 text-lg font-serif mb-3 flex-shrink-0 relative z-10">Paper Summary</h2>
          <div className="text-amber-100/90 text-base leading-relaxed overflow-y-auto flex-grow mb-3 pr-1 custom-scrollbar relative z-10">
            {fullSummary.split('\n\n').map((paragraph, index, arr) => (
              <p key={`p-${index}`} className={index < arr.length - 1 ? 'mb-4' : 'mb-6'}>
                {paragraph}
              </p>
            ))}
            <h3 className="text-amber-200 text-xs font-semibold mb-1 mt-4">Authors:</h3>
            <div className="text-amber-100/70 text-[11px] leading-snug">
              {authors.map((author, index) => (
                <span key={`a-${index}`}>
                  {author.name}{index < authors.length - 1 ? ', ' : ''}
                </span>
              ))}
            </div>
          </div>
          <div className="mt-auto pt-3 flex justify-end space-x-3 flex-shrink-0 relative z-10">
             {pdfUrl && ( // Only show button if pdfUrl exists
                <button onClick={handleDownload} aria-label="Paper" className={ghostButtonStyle}>
                    <Download className="w-4 h-4 mr-2" /> Paper
                </button>
            )}
            <button onClick={handleFlip} aria-label="Show Card Front" className={primaryButtonStyle}>
              <RotateCcw className="w-4 h-4 mr-2" /> Back
            </button>
          </div>
        </div>
      </div>
      {/* Scrollbar styles (can be global if preferred) */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(251, 191, 36, 0.3); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(251, 191, 36, 0.5); }
        .custom-scrollbar { scrollbar-width: thin; scrollbar-color: rgba(251, 191, 36, 0.3) rgba(255, 255, 255, 0.05); }
      `}</style>
    </motion.div>
  );
};


// --- Updated PaperCard component that uses ConferenceCard ---
interface PaperCardProps {
  paper: Paper
  isDarkMode: boolean // Add isDarkMode prop
  // You could add other props like accentColor here if you want to customize it per paper
}

export function PaperCard({ paper, isDarkMode }: PaperCardProps) {
  // Transform paper data for ConferenceCard
  const title = paper.paper_title || "Untitled Paper";

  const authors = (paper.author_list || []).map(author => ({
    name: getDisplayName(author),
    flag: getFlagEmoji(author.affiliation_country)
  }));

  // Construct conferenceInfo string
  // You might want to add presentation type if available in your Paper data
  const conferenceParts = [paper.conference, paper.year?.toString(), paper.venue].filter(Boolean);
  const conferenceInfo = conferenceParts.join(' / ') || "Conference info not available";

  // Determine short and full summaries
  let shortSummary = "Summary not available.";
  if (paper.paper_content && paper.paper_content.trim() !== "") {
    shortSummary = paper.paper_content;
  } else if (paper.abstract && paper.abstract.trim() !== "") {
    shortSummary = paper.abstract; // Or prefix with "(Abstract)"
  }

  let fullSummary = paper.abstract || paper.paper_content || "Detailed summary not available.";
  if (paper.abstract && paper.paper_content && paper.abstract !== paper.paper_content) {
    // If both exist and are different, you could decide which one is "fuller"
    // For now, prioritising abstract for full summary if available
    fullSummary = paper.abstract;
  }


  // Default accent color, can be customized based on paper.venue or other props
  const accentColor = 'bg-orange-500';
  const presentationType = paper.venue || undefined; // Pass venue as presentationType if desired

  return (
    <ConferenceCard
      title={title}
      authors={authors}
      conferenceInfo={conferenceInfo}
      shortSummary={shortSummary}
      fullSummary={fullSummary}
      accentColor={accentColor}
      presentationType={presentationType}
      isDarkMode={isDarkMode}
      pdfUrl={paper.pdf_url}
    />
  )
}