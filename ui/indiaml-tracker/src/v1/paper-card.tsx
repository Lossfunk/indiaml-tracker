"use client"
import { useState, forwardRef } from "react" // Added forwardRef
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { ChevronDown, ChevronUp } from "lucide-react"
import type { Paper } from "@/types/paper"

// Helper function for flag emoji (unchanged)
function getFlagEmoji(countryCode: string | null | undefined): string {
  if (!countryCode || countryCode.length !== 2) {
    return ""
  }
  const code = countryCode.toUpperCase();
  if (code.charCodeAt(0) < 65 || code.charCodeAt(0) > 90 || code.charCodeAt(1) < 65 || code.charCodeAt(1) > 90) {
      return "";
  }
  const codePoint1 = 0x1F1E6 + (code.charCodeAt(0) - 65);
  const codePoint2 = 0x1F1E6 + (code.charCodeAt(1) - 65);
  return String.fromCodePoint(codePoint1) + String.fromCodePoint(codePoint2);
}

interface PaperCardProps {
  paper: Paper
  dynamicMinHeight?: number // New prop for calculated min height from parent
}

// Use forwardRef to allow parent to get a ref to the motion.div
export const PaperCard = forwardRef<HTMLDivElement, PaperCardProps>(
  ({ paper, dynamicMinHeight }, ref) => {
    const [showAllAuthors, setShowAllAuthors] = useState(false)
    const [showSummary, setShowSummary] = useState(false)
    const authors = paper.author_list || []
    const maxVisibleAuthors = 3

    const visibleAuthors = showAllAuthors ? authors : authors.slice(0, maxVisibleAuthors)
    const remainingAuthorsCount = authors.length - maxVisibleAuthors

    // Styles for the outer motion.div, which will act as the flex/grid item.
    const motionDivStyle: React.CSSProperties = {
      display: 'flex',      // Allows Card to grow using flex-grow
      flexDirection: 'column', // Stacks Card vertically within motion.div
    };

    if (!showSummary && dynamicMinHeight && dynamicMinHeight > 0) {
      motionDivStyle.minHeight = `${dynamicMinHeight}px`;
    }
    // When showSummary is true, or if dynamicMinHeight is not provided,
    // motion.div will take its natural height based on content.

    return (
      <motion.div
        ref={ref} // Assign the forwarded ref to the outermost element
        className="flex flex-col" // Original: "flex flex-col overflow-visible". Retain flex structure.
        style={motionDivStyle}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        whileHover={{ scale: 1.01 }}
      >
        {/* Card should grow to fill the height of motion.div */}
        <Card className="flex flex-col p-2 dark:bg-slate-900 overflow-hidden flex-grow"> {/* Added flex-grow */}
          {/* CardContent should also grow if Card is taller than its content */}
          <CardContent className="flex flex-col px-4 flex-grow"> {/* Added flex-grow */}
            {/* Header Section: Title and Toggle Button */}
            <div className="flex justify-between items-start">
              <div className="pt-3 pb-3 text-xl font-serif dark:text-zinc-100 font-semibold flex-1">
                {paper.paper_title}
              </div>
              <button
                onClick={() => setShowSummary(!showSummary)}
                className="flex items-center justify-center w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700/20 text-slate-800 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors mt-3"
                aria-label={showSummary ? "Hide summary" : "Show summary"}
              >
                {showSummary ? (
                  <ChevronUp className="w-6 h-6" />
                ) : (
                  <ChevronDown className="w-6 h-6" />
                )}
              </button>
            </div>

            {/* Content area that expands/collapses */}
            {/* This div wrapper helps manage the main content body vs the footer */}
            <div className="flex-grow"> {/* This div will take up available space, pushing footer down if CardContent has extra height */}
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
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 italic">
                          (Abstract shown as summary)
                        </p>
                      ) : (
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 italic">
                          Summary not available.
                        </p>
                      )
                    )}

                    {paper.abstract && paper.abstract !== paper.paper_content && (
                      <>
                        <h3 className="font-medium text-gray-800 dark:text-gray-200 mb-1">
                          Abstract
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                          {paper.abstract}
                        </p>
                      </>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Author badges */}
              <div className="flex flex-wrap gap-2 mb-4">
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
                            >
                              <Badge
                                variant="secondary"
                                className="bg-slate-500/20 text-blue-200 cursor-pointer"
                              >
                                {displayName} {flag}
                              </Badge>
                            </a>
                          ) : (
                            <Badge
                              variant="secondary"
                              className="bg-slate-500/30 text-blue-200"
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
                            className="z-50 max-w-sm p-4 text-sm leading-normal text-white bg-slate-800 rounded-md shadow-lg whitespace-pre-line"
                          >
                            {getAuthorInfo(author)}
                          </TooltipContent>
                        </AnimatePresence>
                      </Tooltip>
                    )
                  })}
                  {!showAllAuthors && remainingAuthorsCount > 0 && (
                    <Badge
                      onClick={() => setShowAllAuthors(true)}
                      className="cursor-pointer bg-transparent border border-slate-400/20 text-gray-200/50"
                    >
                      +{remainingAuthorsCount} more
                    </Badge>
                  )}
                  {showAllAuthors && authors.length > maxVisibleAuthors && (
                    <Badge
                      onClick={() => setShowAllAuthors(false)}
                      className="cursor-pointer bg-transparent border border-slate-400/20 text-gray-200/50"
                    >
                      Show less
                    </Badge>
                  )}
                </TooltipProvider>
              </div>
            </div> {/* End of flex-grow content area */}


            {/* Footer: Badges + PDF link. mt-auto pushes it to the bottom of CardContent. */}
            <div className="mt-auto pt-2">
              <div className="flex flex-wrap gap-2 justify-between items-center">
                <div className="flex flex-wrap items-center gap-2">
                  {paper.conference && (
                    <Badge className="bg-purple-100 dark:bg-purple-800/10 text-purple-800 dark:text-purple-100 hover:bg-purple-200">
                      {paper.conference} {paper.year}
                    </Badge>
                  )}
                  {paper.venue && (
                    <Badge className="bg-blue-100 dark:bg-blue-800/10 text-blue-800 dark:text-blue-100 hover:bg-blue-200 capitalize">
                      {paper.venue}
                    </Badge>
                  )}
                  {paper.top_author_from_india === true && (
                    <TooltipProvider>
                      <Tooltip delayDuration={100}>
                        <TooltipTrigger>
                          <Badge className="bg-amber-100 dark:bg-amber-800/10 text-amber-800 dark:text-amber-100 hover:bg-amber-200 cursor-default">
                            🇮🇳 First Author
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent side="top" sideOffset={4}>
                          First Author affiliated with an Indian institution.
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                  {paper.majority_authors_from_india === true && paper.top_author_from_india !== true && (
                    <TooltipProvider>
                      <Tooltip delayDuration={100}>
                        <TooltipTrigger>
                          <Badge className="bg-green-100 text-green-800 hover:bg-green-200 cursor-default">
                            🇮🇳 Majority Authors
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent side="top" sideOffset={4}>
                          Majority of Authors affiliated with Indian institutions (but not first author).
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
                    className="text-sm text-gray-600 dark:text-gray-400 underline whitespace-nowrap ml-auto pl-2"
                  >
                    View PDF
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

PaperCard.displayName = "PaperCard" // For better debugging in React DevTools

// Helper functions (getDisplayName, processOpenReviewId, getAuthorInfo)
// (These are unchanged from your original code - ensure they are present here)
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
  return processed.charAt(0).toUpperCase() + processed.slice(1);
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
    </div>
  );
}