import React, { useState } from 'react';
// Make sure to install lucide-react: npm install lucide-react
// (You might need to add this dependency if running locally)
import { Download, RotateCcw, ChevronDown, ChevronUp, List, Sun, Moon } from 'lucide-react';

// --- Helper Function for Class Merging ---
function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

// --- Conference Card Component (Final Style Adjustments) ---
/**
 * ConferenceCard Component
 *
 * A 3D flipping card component to display conference paper details.
 * Accepts props for data and styling. Borders are much less prominent.
 * Accent hierarchy uses opacity on the same base color. Dots are denser.
 * Background gradient opacity adjusts with dark/light mode.
 */
const ConferenceCard = ({
  title,
  authors,
  conferenceInfo,
  shortSummary,
  fullSummary,
  accentColor = 'bg-orange-500',
  presentationType = 'Oral',
  isDarkMode // Receive dark mode state from parent
}) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const [showAllAuthors, setShowAllAuthors] = useState(false);

  const handleFlip = () => setIsFlipped(!isFlipped);
  const toggleAuthors = () => setShowAllAuthors(!showAllAuthors);
  const handleDownload = () => console.log(`Download clicked for: ${title}`);

  // --- Base Styles ---
  const cardBaseStyle = cn(
    "absolute w-full h-full bg-zinc-800 rounded-3xl border border-zinc-700 shadow-lg overflow-hidden", // Neutral border color
    "[backface-visibility:hidden] flex flex-col transform translate-z-0",
    isDarkMode ? 'border-opacity-30' : 'border-opacity-50' // Reduced border opacity
  );
  const cardShadowStyle = { boxShadow: '0 12px 40px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255, 226, 130, 0.08), inset 0 1px 1px rgba(255, 255, 255, 0.08)' };

  // --- Button Styles ---
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

  // --- Conditional Background Gradient ---
  const lightModeGradient = 'radial-gradient(circle at bottom left, rgba(217, 119, 6, 0.15) 0%, rgba(0, 0, 0, 0) 70%)';
  const darkModeGradient = 'radial-gradient(circle at bottom left, rgba(217, 119, 6, 0.05) 0%, rgba(0, 0, 0, 0) 70%)';
  const backgroundGradientStyle = { background: isDarkMode ? darkModeGradient : lightModeGradient };

  return (
    // Container for perspective (width is now controlled by parent)
    <div className="w-96 h-96 [perspective:1000px]">
      <div
        className={`relative w-full h-full transition-transform duration-700 ease-in-out [transform-style:preserve-3d] ${isFlipped ? '[transform:rotateY(180deg)]' : ''}`}
      >
        {/* ========== Front Side Container ========== */}
        <div className={cardBaseStyle} style={cardShadowStyle}>
          {/* Background pattern & Conditional Gradient */}
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

          {/* --- Front Content --- */}
          <div className="text-amber-200/70 text-sm tracking-wider mt-6 ml-6 mb-4 flex-shrink-0">
            {conferenceInfo}
          </div>
          <div className="relative mb-4 flex-shrink-0">
            <div className={cn("absolute left-0 top-0.5 w-1.5 h-8 rounded-r-full", accentColor)}></div>
            <div className="pl-6 pr-6">
              <h1 className="text-amber-100 text-3xl font-serif leading-tight overflow-hidden" style={{ textShadow: '0 1px 5px rgba(251, 191, 36, 0.2), 0 2px 10px rgba(0, 0, 0, 0.4)' }}>
                {title}
              </h1>
            </div>
          </div>
          <div className="px-6 mb-3 flex-shrink-0">
            <p className="text-amber-100/70 text-xs line-clamp-2">
              {shortSummary}
            </p>
          </div>
          {/* Author Section */}
          <div className={`px-6 mb-3 overflow-hidden transition-all duration-300 ease-in-out flex-grow ${showAllAuthors ? 'max-h-36 overflow-y-auto custom-scrollbar' : 'max-h-[4.5rem]'}`}>
            {!showAllAuthors ? (
              <div className="flex flex-wrap gap-1 items-center">
                {authors.slice(0, 3).map((author, index) => (
                  <div key={index} className="flex items-center bg-zinc-700/50 rounded-full pl-1.5 pr-2 py-0.5">
                    <span className="text-lg mr-1.5" role="img" aria-label={`Flag for ${author.name}`}>{author.flag}</span>
                    <span className="text-amber-100 text-[11px] whitespace-nowrap font-medium">{author.name}</span>
                  </div>
                ))}
                {authors.length > 3 && (
                  <button onClick={toggleAuthors} className="bg-zinc-700/50 text-amber-100 rounded-full px-2.5 py-1 text-[11px] hover:bg-zinc-600/60 transition-colors flex items-center font-medium">
                    +{authors.length - 3} more <ChevronDown className="w-3 h-3 ml-1" />
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
          {/* Control buttons (Front) */}
          <div className="mt-auto mb-4 px-6 flex justify-end space-x-3 flex-shrink-0">
              <button onClick={handleDownload} aria-label="Paper" className={ghostButtonStyle}>
                <Download className="w-4 h-4 mr-2" /> Paper
              </button>
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
            {/* --- Back Content --- */}
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
              <button onClick={handleDownload} aria-label="Paper" className={ghostButtonStyle}>
                <Download className="w-4 h-4 mr-2" /> Paper
              </button>
              <button onClick={handleFlip} aria-label="Show Card Front" className={primaryButtonStyle}>
                <RotateCcw className="w-4 h-4 mr-2" /> Back
              </button>
            </div>
        </div>
      </div>
      {/* Scrollbar styles */}
       <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(251, 191, 36, 0.3); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(251, 191, 36, 0.5); }
        .custom-scrollbar { scrollbar-width: thin; scrollbar-color: rgba(251, 191, 36, 0.3) rgba(255, 255, 255, 0.05); }
      `}</style>
    </div>
  );
};

// --- Sample Data (Only first card needed now) ---
const flags = ['🇮🇳', '🇺🇸', '🇬🇧', '🇨🇦', '🇩🇪', '🇯🇵', '🇫🇷', '🇦🇺', '🇧🇷', '🇿🇦', '🇰🇷', '🇨🇳'];
const sampleAuthors = [
    { name: 'S. R. OOTA', flag: flags[0] }, { name: 'K. PAHWA', flag: flags[1] },
    { name: 'M. MARREDDY', flag: flags[2] }, { name: 'J. WILSON', flag: flags[3] },
    { name: 'L. ZHANG', flag: flags[4] }, { name: 'N. PATEL', flag: flags[5] },
    { name: 'A. RODRIGUEZ', flag: flags[6] }, { name: 'K. MULLER', flag: flags[7] },
    { name: 'H. TANAKA', flag: flags[8] }, { name: 'B. JOHNSON', flag: flags[9] },
    { name: 'S. KIM', flag: flags[10] }, { name: 'Y. WANG', flag: flags[11] },
];

// Using only the first card's data
const singleCardData = {
    id: 1,
    title: "Multi-modal brain encoding models",
    authors: sampleAuthors.slice(0, 8),
    conferenceInfo: "ICLR / 2025 / Oral",
    shortSummary: "Novel multi-modal brain encoding models processing diverse sensory inputs simultaneously.",
    fullSummary: "This research introduces novel multi-modal brain encoding models that effectively process and interpret diverse sensory inputs simultaneously. The approach integrates visual, auditory, and tactile neural representations to create a unified computational framework that more accurately mimics human cognitive processing. Our findings demonstrate a 37% improvement in predictive accuracy over single-modality models, with particular strength in cross-modal inference tasks where limited data is available for certain modalities.",
    presentationType: 'Oral',
    accentColor: 'bg-orange-500', // Oral: Full opacity
};


// --- Main App Component (Displays Single Card) ---
/**
 * App Component
 *
 * Manages dark mode state and renders a single Conference Card.
 */
const App = () => {
  const [isDarkMode, setIsDarkMode] = useState(true);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  // Get the data for the single card to display
  const data = singleCardData;

  return (
    // Main container - Adjusted for single card centering
    <div className={cn(
      "flex flex-col items-center justify-center w-full min-h-screen p-8 transition-colors duration-300 font-sans", // Added justify-center
      isDarkMode ? 'bg-zinc-900' : 'bg-amber-100'
    )}>
      {/* Dark Mode Toggle Button */}
      <button
        onClick={toggleDarkMode}
        className={cn(
          "fixed top-4 right-4 p-2 rounded-full z-50",
          "transition-colors duration-300",
          isDarkMode ? 'bg-amber-400 text-zinc-900 hover:bg-amber-300' : 'bg-zinc-700 text-amber-100 hover:bg-zinc-600'
        )}
        aria-label={isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
      >
        {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
      </button>

      {/* Render Single Conference Card */}
      {/* Removed grid container */}
      <ConferenceCard
          key={data.id}
          title={data.title}
          authors={data.authors}
          conferenceInfo={data.conferenceInfo}
          shortSummary={data.shortSummary}
          fullSummary={data.fullSummary}
          accentColor={data.accentColor}
          presentationType={data.presentationType}
          isDarkMode={isDarkMode}
        />

    </div>
  );
};

export default App;
