"use client"
import { useState, forwardRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card" // Assuming these are from shadcn/ui
import { Badge } from "@/components/ui/badge" // Assuming this is from shadcn/ui
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip" // Assuming these are from shadcn/ui
import { ChevronDown, ChevronUp, ExternalLink, Trophy, Presentation, Star, Image as ImageIcon, MessageCircle } from "lucide-react"
import type { Paper } from "@/types/paper" // Assuming Paper type is defined elsewhere

// Helper function for flag emoji (unchanged)
function getFlagEmoji(countryCode: string | null | undefined): string {
  if (!countryCode || countryCode.length !== 2) {
    return ""
  }
  const code = countryCode.toUpperCase();
  // Ensure the country code consists of two uppercase letters
  if (code.charCodeAt(0) < 65 || code.charCodeAt(0) > 90 || code.charCodeAt(1) < 65 || code.charCodeAt(1) > 90) {
      return "";
  }
  const codePoint1 = 0x1F1E6 + (code.charCodeAt(0) - 65);
  const codePoint2 = 0x1F1E6 + (code.charCodeAt(1) - 65);
  return String.fromCodePoint(codePoint1) + String.fromCodePoint(codePoint2);
}

// Helper functions (getDisplayName, processOpenReviewId, getAuthorInfo - unchanged)
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
  let processed = id.startsWith("~") ? id.slice(1) : id
  processed = processed.replace(/\d+$/, "")
  processed = processed.replace(/_/g, " ")
  processed = processed.toLowerCase();
  // Capitalize the first letter
  if (processed.length > 0) {
    processed = processed.charAt(0).toUpperCase() + processed.slice(1);
  }
  return processed;
}

function getAuthorInfo(author: {
  name?: string;
  affiliation_name?: string;
  affiliation_country?: string;
  openreview_id?: string;
}): JSX.Element {
  const displayName = getDisplayName(author);
  const flag = getFlagEmoji(author.affiliation_country);

  return (
    <div className="text-left space-y-1">
      <div className="text-lg font-bold">{displayName}</div>
      {author.affiliation_country && <div className="text-gray-300">{flag} {author.affiliation_country}</div>}
      {author.affiliation_name && <div className="text-gray-100 pt-2 text-base">{author.affiliation_name}</div>}
      {/* Optionally, add OpenReview ID if available and desired in tooltip */}
      {/* {author.openreview_id && <div className="text-xs text-gray-400">ID: {author.openreview_id}</div>} */}
    </div>
  );
}

// Helper function to determine presentation type icon
const getPresentationIcon = (venue?: string): { icon: JSX.Element; text: string } => {
  if (!venue) return { icon: <MessageCircle className="h-4 w-4" />, text: "Venue N/A" };

  const lowerVenue = venue.toLowerCase();

  if (lowerVenue.includes("oral")) {
    return {
      icon: <Presentation className="h-4 w-4" />,
      text: "Oral Presentation",
    };
  }
  if (lowerVenue.includes("spotlight")) {
    return {
      icon: <Star className="h-4 w-4" />,
      text: "Spotlight Presentation",
    };
  }
  if (lowerVenue.includes("poster")) {
    return {
      icon: <ImageIcon className="h-4 w-4" />,
      text: "Poster Presentation",
    };
  }
  // Default icon
  return {
    icon: <MessageCircle className="h-4 w-4" />,
    text: venue || "Presentation Type",
  };
};


interface PaperCardProps {
  paper: Paper
  dynamicMinHeight?: number
}

export const PaperCard = forwardRef<HTMLDivElement, PaperCardProps>(
  ({ paper, dynamicMinHeight }, ref) => {
    const [showAllAuthors, setShowAllAuthors] = useState(false)
    const [showSummary, setShowSummary] = useState(false)
    const authors = paper.author_list || []
    const maxVisibleAuthors = 3

    const visibleAuthors = showAllAuthors ? authors : authors.slice(0, maxVisibleAuthors)
    const remainingAuthorsCount = authors.length - maxVisibleAuthors

    const motionDivStyle: React.CSSProperties = {
      display: 'flex',
      flexDirection: 'column',
    };

    if (!showSummary && dynamicMinHeight && dynamicMinHeight > 0) {
      motionDivStyle.minHeight = `${dynamicMinHeight}px`;
    }

    const presentationInfo = getPresentationIcon(paper.venue);

    const handleCardClick = (e: React.MouseEvent<HTMLDivElement>) => {
      // Only toggle if the click is directly on the card and not on an interactive element
      if ((e.target as HTMLElement).closest('a, button, [role="button"]')) {
        return; // Don't toggle if clicked on a link or button
      }
      setShowSummary(!showSummary);
    };

    return (
      <motion.div
        ref={ref}
        className="flex flex-col"
        style={motionDivStyle}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        whileHover={{ scale: 1.01 }}
      >
        <Card 
          className="flex flex-col p-2 dark:bg-slate-900 overflow-hidden flex-grow rounded-lg shadow-md hover:shadow-lg transition-shadow relative cursor-pointer"
          onClick={handleCardClick}
        >
          {/* Dot grid background with gradient overlay */}
          <div className="absolute inset-0 bg-[radial-gradient(circle,_rgba(120,120,120,0.1)_1px,_transparent_1px)] dark:bg-[radial-gradient(circle,_rgba(255,255,255,0.03)_1px,_transparent_1px)] [background-size:20px_20px] pointer-events-none"></div>
          <div className="absolute inset-0 bg-gradient-to-br from-slate-50/10 to-slate-100/5 dark:from-slate-800/10 dark:to-slate-900/50 pointer-events-none"></div>
          <CardContent className="flex flex-col px-4 flex-grow relative z-10">
            {/* Header Section: Title and Toggle Button */}
            <div className="flex justify-between items-start">
              <div className="pt-3 pb-3 text-xl font-serif dark:text-zinc-100 font-semibold flex-1 mr-2">
                {paper.paper_title || "Untitled Paper"}
              </div>
              <div className="flex items-center space-x-2 mt-3">
                <ChevronDown className={`w-6 h-6 text-slate-400 transition-opacity duration-200 ${showSummary ? 'opacity-0' : 'opacity-100'}`} />
              </div>
            </div>

            {/* Content area that expands/collapses */}
            <div className="flex-grow">
              <AnimatePresence>
                {showSummary && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="overflow-hidden"
                  >
                    {paper.paper_content && paper.paper_content.trim() !== "" ? (
                      <p className="text-sm text-gray-600 leading-relaxed dark:text-gray-300 mb-3">
                        {paper.paper_content}
                      </p>
                    ) : (
                      paper.abstract ? (
                        <>
                          <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 italic">
                            (Abstract shown as summary)
                          </p>
                           <p className="text-sm text-gray-600 leading-relaxed dark:text-gray-300 mb-3">
                            {paper.abstract}
                          </p>
                        </>
                      ) : (
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 italic">
                          Summary not available.
                        </p>
                      )
                    )}

                    {/* Show full abstract only if it's different from paper_content and summary is shown */}
                    {showSummary && paper.abstract && paper.abstract !== paper.paper_content && (
                      <>
                        <h3 className="font-medium text-gray-800 dark:text-gray-200 mb-1 mt-2 text-base">
                          Full Abstract
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                          {paper.abstract}
                        </p>
                      </>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Author badges - UPDATED to be more subdued */}
              <div className="flex flex-wrap gap-2 mb-4 mt-1">
                <TooltipProvider>
                  {visibleAuthors.map((author, index) => {
                    const displayName = getDisplayName(author)
                    const flag = getFlagEmoji(author.affiliation_country)
                    return (
                      <Tooltip key={index} delayDuration={200}>
                        <TooltipTrigger asChild>
                          {author.openreview_id ? (
                            <a
                              href={`https://openreview.net/profile?id=${encodeURIComponent(
                                author.openreview_id
                              )}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-block"
                              onClick={(e) => e.stopPropagation()} // Prevent card expansion when clicking author link
                            >
                              <Badge
                                variant="secondary"
                                className="bg-slate-200/70 dark:bg-slate-800/50 text-slate-700 dark:text-slate-400 cursor-pointer hover:bg-slate-300/70 dark:hover:bg-slate-700/60 px-2.5 py-1 text-xs"
                              >
                                {displayName} {flag}
                              </Badge>
                            </a>
                          ) : (
                            <Badge
                              variant="secondary"
                              className="bg-slate-200/70 dark:bg-slate-800/50 text-slate-700 dark:text-slate-400 px-2.5 py-1 text-xs"
                            >
                              {displayName} {flag}
                            </Badge>
                          )}
                        </TooltipTrigger>
                        <AnimatePresence>
                          <TooltipContent
                            as={motion.div}
                            initial={{ opacity: 0, y: 4 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 4 }}
                            transition={{ duration: 0.2 }}
                            side="top"
                            sideOffset={10}
                            className="z-50 max-w-xs sm:max-w-sm p-3 text-sm leading-normal text-white bg-slate-800 rounded-lg shadow-xl whitespace-pre-line"
                          >
                            {getAuthorInfo(author)}
                          </TooltipContent>
                        </AnimatePresence>
                      </Tooltip>
                    )
                  })}
                  {!showAllAuthors && remainingAuthorsCount > 0 && (
                    <Badge
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent card expansion
                        setShowAllAuthors(true);
                      }}
                      className="cursor-pointer bg-transparent border border-slate-400/20 dark:border-slate-700/50 text-gray-500 dark:text-gray-500 hover:bg-slate-100/30 dark:hover:bg-slate-800/70 px-2.5 py-1 text-xs"
                    >
                      +{remainingAuthorsCount} more
                    </Badge>
                  )}
                  {showAllAuthors && authors.length > maxVisibleAuthors && (
                    <Badge
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent card expansion
                        setShowAllAuthors(false);
                      }}
                      className="cursor-pointer bg-transparent border border-slate-400/20 dark:border-slate-700/50 text-gray-500 dark:text-gray-500 hover:bg-slate-100/30 dark:hover:bg-slate-800/70 px-2.5 py-1 text-xs"
                    >
                      Show less
                    </Badge>
                  )}
                </TooltipProvider>
              </div>
            </div>

            {/* Footer: Badges + PDF link - UPDATED with more subdued styling */}
            <div className="mt-auto pt-3 border-t border-slate-200 dark:border-slate-800/70">
              <div className="flex flex-wrap gap-x-3 gap-y-2 justify-between items-center">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-2">
                  {/* Conference & Year Badge as Icon */}
                  {paper.conference && (
                    <span className="text-xs text-slate-600 dark:text-slate-400">
                      {paper.conference} {paper.year}
                    </span>
                  )}

                  {/* Presentation Type Icon - Enhanced with color */}
                  {paper.venue && (
                    <TooltipProvider>
                      <Tooltip delayDuration={100}>
                        <TooltipTrigger>
                          {paper.venue.toLowerCase().includes("oral") ? (
                            <div className="p-1.5 bg-teal-100/30 dark:bg-teal-900/20 rounded-full text-teal-600 dark:text-teal-300 hover:bg-teal-200/40 dark:hover:bg-teal-800/30">
                              <Presentation className="h-4 w-4" />
                            </div>
                          ) : paper.venue.toLowerCase().includes("spotlight") ? (
                            <div className="p-1.5 bg-amber-100/30 dark:bg-amber-900/20 rounded-full text-amber-600 dark:text-amber-300 hover:bg-amber-200/40 dark:hover:bg-amber-800/30">
                              <Star className="h-4 w-4" />
                            </div>
                          ) : (
                            <div className="p-1.5 bg-slate-100/30 dark:bg-slate-800/40 rounded-full text-indigo-400 dark:text-indigo-400/70 hover:bg-slate-200/40 dark:hover:bg-slate-700/50">
                              <ImageIcon className="h-4 w-4" />
                            </div>
                          )}
                        </TooltipTrigger>
                        <TooltipContent side="top" sideOffset={4} className="bg-slate-800 text-white p-2 rounded-md text-xs">
                          {presentationInfo.text}
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}

                  {/* First Author Icon - With muted color */}
                  {paper.top_author_from_india === true && (
                    <TooltipProvider>
                      <Tooltip delayDuration={100}>
                        <TooltipTrigger>
                          <div className="p-1.5 bg-slate-100/30 dark:bg-slate-800/40 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-200/40 dark:hover:bg-slate-700/50">
                            <Trophy className="h-4 w-4" />
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="top" sideOffset={4} className="bg-slate-800 text-white p-2 rounded-md text-xs">
                          First Author affiliated with an Indian institution
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                  
                  {/* Majority Authors Icon - With muted color */}
                  {paper.majority_authors_from_india === true && paper.top_author_from_india !== true && (
                    <TooltipProvider>
                      <Tooltip delayDuration={100}>
                        <TooltipTrigger>
                          <div className="p-1.5 bg-slate-100/30 dark:bg-slate-800/40 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-200/40 dark:hover:bg-slate-700/50">
                            <Trophy className="h-4 w-4" />
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="top" sideOffset={4} className="bg-slate-800 text-white p-2 rounded-md text-xs">
                          Majority of Authors affiliated with Indian institutions
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </div>

                {paper.pdf_url && (
                  <a
                    href={paper.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 dark:text-blue-400/90 hover:text-blue-700 dark:hover:text-blue-300 underline whitespace-nowrap ml-auto pl-2 flex-shrink-0 flex items-center gap-1"
                    onClick={(e) => e.stopPropagation()} // Prevent card expansion when clicking the link
                  >
                    View PDF <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    )
  }
)

PaperCard.displayName = "PaperCard"