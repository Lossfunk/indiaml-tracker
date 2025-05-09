"use client"
import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { Paper } from "@/types/paper" // Assuming Paper type includes top_author_from_india and majority_authors_from_india

interface PaperCardProps {
  paper: Paper
}

// --- Helper Function to get Flag Emoji ---
/**
 * Converts a 2-letter country code (ISO 3166-1 alpha-2) to a flag emoji.
 * Handles potential null/undefined/invalid codes.
 * @param countryCode - The 2-letter country code (e.g., "IN", "US").
 * @returns The corresponding flag emoji string, or an empty string if invalid.
 */
function getFlagEmoji(countryCode: string | null | undefined): string {
  if (!countryCode || countryCode.length !== 2) {
    return "" // Return empty if no code or not 2 letters
  }
  const code = countryCode.toUpperCase();
  // Ensure both characters are A-Z
  if (code.charCodeAt(0) < 65 || code.charCodeAt(0) > 90 || code.charCodeAt(1) < 65 || code.charCodeAt(1) > 90) {
      return ""; // Return empty if not valid A-Z characters
  }
  // Calculate Unicode code points for regional indicator symbols
  const codePoint1 = 0x1F1E6 + (code.charCodeAt(0) - 65); // 65 is 'A'
  const codePoint2 = 0x1F1E6 + (code.charCodeAt(1) - 65);
  return String.fromCodePoint(codePoint1) + String.fromCodePoint(codePoint2);
}
// --- End Helper Function ---


export function PaperCard({ paper }: PaperCardProps) {
  const [showAllAuthors, setShowAllAuthors] = useState(false)
  const authors = paper.author_list || [] // Ensure authors is always an array
  const maxVisibleAuthors = 3

  const visibleAuthors = showAllAuthors ? authors : authors.slice(0, maxVisibleAuthors)
  const remainingAuthorsCount = authors.length - maxVisibleAuthors

  return (
    <motion.div
      className="h-full flex flex-col overflow-visible"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      whileHover={{ scale: 1.01 }}
    >
      <Card className="flex flex-col h-full overflow-hidden">
        <CardHeader className="bg-zinc-900 border-b">
          <CardTitle className="text-lg text-zinc-100 font-semibold">
            {paper.paper_title}
          </CardTitle>
        </CardHeader>

        <CardContent className="flex-grow flex flex-col justify-between p-4">
          <div>
            {/* Paper Summary */}
            <h3 className="font-medium text-gray-800 dark:text-gray-200 mb-2">
              Paper Summary
            </h3>
            {paper.paper_content && paper.paper_content.trim() !== "" ? (
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{paper.paper_content}</p>
            ) : (
               // Display abstract if content is missing but abstract exists
              paper.abstract ? (
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 italic">(Abstract shown as summary)</p>
              ) : (
                 <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 italic">
                    Summary not available.
                 </p>
              )
            )}

            {/* Abstract - only show if different from summary */}
            {paper.abstract && paper.abstract !== paper.paper_content && (
              <>
                <h3 className="font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Abstract
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{paper.abstract}</p>
              </>
            )}

            {/* Author badges with tooltips and flags */}
            <div className="flex flex-wrap gap-2 mb-4">
              <TooltipProvider>
                {visibleAuthors.map((author, index) => {
                  const displayName = getDisplayName(author)
                  // Add flag emoji based on affiliation_country
                  const flag = getFlagEmoji(author.affiliation_country)

                  return (
                    <Tooltip key={index} delayDuration={200}>
                      <TooltipTrigger asChild>
                        {/* Link author badge if openreview_id exists */}
                        {author.openreview_id ? (
                          <a
                            href={`https://openreview.net/profile?id=${encodeURIComponent(
                              author.openreview_id
                            )}`}
                            target="_blank"
                            rel="noopener noreferrer"
                             className="inline-block" // Ensure link wraps badge correctly
                          >
                            <Badge
                              variant="secondary"
                              className="bg-slate-700 text-blue-200 cursor-pointer"
                            >
                              {displayName} {flag} {/* Display name and flag */}
                            </Badge>
                          </a>
                        ) : (
                           // Render badge without link if no ID
                           <Badge
                             variant="secondary"
                             className="bg-slate-700 text-blue-200"
                           >
                             {displayName} {flag} {/* Display name and flag */}
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
                          className="z-50 max-w-sm p-4 text-sm leading-normal text-white bg-gradient-to-r from-teal-700 to-emerald-800 rounded-md shadow-lg whitespace-pre-line"
                        >
                           {/* Pass author to getAuthorInfo which now also includes flag */}
                          {getAuthorInfo(author)}
                        </TooltipContent>
                      </AnimatePresence>
                    </Tooltip>
                  )
                })}

                {/* Expand/Collapse author list */}
                {!showAllAuthors && remainingAuthorsCount > 0 && (
                  <Badge
                    onClick={() => setShowAllAuthors(true)}
                    className="cursor-pointer bg-zinc-600 text-gray-100"
                  >
                    +{remainingAuthorsCount} more
                  </Badge>
                )}
                {showAllAuthors && authors.length > maxVisibleAuthors && (
                  <Badge
                    onClick={() => setShowAllAuthors(false)}
                    className="cursor-pointer bg-zinc-600 text-gray-100"
                  >
                    Show less
                  </Badge>
                )}
              </TooltipProvider>
            </div>
          </div>

          {/* Footer: Badges + PDF link */}
          <div className="flex flex-wrap gap-2 justify-between items-center pt-2 border-t">
             {/* Left side badges (Conference, Venue, Indian Authorship) */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Conference */}
              {paper.conference && (
                 <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-200">
                   {paper.conference} {paper.year}
                 </Badge>
              )}
              {/* Venue */}
              {paper.venue && (
                 <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200 capitalize">
                  {paper.venue}
                 </Badge>
              )}
              {/* Indian Authorship Badges */}
              {paper.top_author_from_india === true && (
                  <TooltipProvider>
                      <Tooltip delayDuration={100}>
                          <TooltipTrigger>
                              <Badge className="bg-green-100 text-green-800 hover:bg-green-200 cursor-default">
                                  🇮🇳 First Author
                              </Badge>
                          </TooltipTrigger>
                          <TooltipContent side="top" sideOffset={4}>First Author affiliated with an Indian institution.</TooltipContent>
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
                           <TooltipContent side="top" sideOffset={4}>Majority of Authors affiliated with Indian institutions (but not first author).</TooltipContent>
                      </Tooltip>
                  </TooltipProvider>
              )}
            </div>

             {/* Right side: PDF link */}
             {paper.pdf_url && (
                <a
                  href={paper.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-600 dark:text-gray-400 underline whitespace-nowrap ml-auto pl-2" // Added pl-2 for spacing
                >
                  View PDF
                </a>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

// --- Helper functions for author display ---

function getDisplayName(author: {
  name?: string
  openreview_id?: string // Make optional if not always present
}): string {
  if (author.name && author.name.trim() !== "") {
    return author.name;
  }
  // Fallback to processing OpenReview ID only if it exists
  if (author.openreview_id) {
     return processOpenReviewId(author.openreview_id);
  }
  return "Unknown Author"; // Default if no name or ID
}

function processOpenReviewId(id: string): string {
  let processed = id.startsWith("~") ? id.slice(1) : id
  processed = processed.replace(/\d+$/, "") // Remove trailing digits
  processed = processed.replace(/_/g, " ") // Replace underscores
  // Convert to sentence case robustly
  processed = processed.toLowerCase();
  return processed.charAt(0).toUpperCase() + processed.slice(1);
}

// Updated to include flag in tooltip
function getAuthorInfo(author: {
  name?: string;
  affiliation_name?: string; // Make optional
  affiliation_country?: string; // Make optional
  openreview_id?: string; // Make optional
}): JSX.Element {
  const displayName = getDisplayName(author);
  // Get flag for tooltip
  const flag = getFlagEmoji(author.affiliation_country);

  return (
    <div className="text-left space-y-1"> {/* Added space-y-1 for better spacing */}
      <div className="text-lg font-bold">{displayName} {flag}</div> {/* Added flag */}
      {author.affiliation_name && <div className="text-gray-100">Affiliation: {author.affiliation_name}</div>}
      {author.affiliation_country && <div className="text-gray-100">Country: {author.affiliation_country}</div>}
       {/* Optionally show OpenReview ID */}
       {/* {author.openreview_id && <div className="text-gray-300 text-xs">ID: {author.openreview_id}</div>} */}
    </div>
  );
}