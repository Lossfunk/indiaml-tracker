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
import type { Paper } from "@/types/paper"

interface PaperCardProps {
  paper: Paper
}

export function PaperCard({ paper }: PaperCardProps) {
  const [showAllAuthors, setShowAllAuthors] = useState(false)
  const authors = paper.author_list
  const maxVisibleAuthors = 3

  // Determine which authors to show based on the expanded state.
  const visibleAuthors = showAllAuthors ? authors : authors.slice(0, maxVisibleAuthors)
  const remainingAuthorsCount = authors.length - maxVisibleAuthors

  return (
    // If you're seeing clipping, remove or override 'overflow-hidden' from here.
    <motion.div
      className="h-full flex flex-col overflow-visible" // <--- ensure visible if needed
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
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                Loading...
              </p>
            )}

            {/* Abstract or PDF link (optional) */}
            {paper.abstract ? (
              <>
                <h3 className="font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Abstract
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{paper.abstract}</p>
              </>
            ) : (
              <p className="text-sm text-blue-100/60 underline mb-4">
                <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer">
                  View PDF
                </a>
              </p>
            )}

            {/* Author badges with tooltips */}
            <div className="flex flex-wrap gap-2 mb-4">
              <TooltipProvider>
                {visibleAuthors.map((author, index) => {
                  const displayName = getDisplayName(author)
                  return (
                    <Tooltip key={index} delayDuration={200}>
                      <TooltipTrigger asChild>
                        <a
                          href={`https://openreview.net/profile?id=${encodeURIComponent(
                            author.openreview_id
                          )}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <Badge
                            variant="secondary"
                            className="bg-slate-700 text-blue-200 cursor-pointer"
                          >
                            {displayName}
                          </Badge>
                        </a>
                      </TooltipTrigger>

                      {/* AnimatePresence ensures we can animate the tooltip in/out */}
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
                          {getAuthorInfo(author)}
                        </TooltipContent>
                      </AnimatePresence>
                    </Tooltip>
                  )
                })}

                {/* Expand/Collapse author list if needed */}
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

          {/* Footer: accepted_in + PDF link */}
          <div className="flex justify-between items-center">
            <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-200">
              {paper.accepted_in.join(", ")}
            </Badge>
            <a
              href={paper.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-gray-500 underline"
            >
              PDF
            </a>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

/**
 * Returns a display name for an author.
 * If `author.name` is present, it is returned.
 * Otherwise, the `openreview_id` is processed to:
 * 1. Remove a leading tilde (~),
 * 2. Remove trailing digits,
 * 3. Replace underscores with spaces,
 * 4. Convert to sentence case.
 */
function getDisplayName(author: {
  name?: string
  openreview_id: string
}): string {
  if (author.name && author.name.trim() !== "") {
    return author.name
  }
  return processOpenReviewId(author.openreview_id)
}

function processOpenReviewId(id: string): string {
  // Remove leading tilde (~)
  let processed = id.startsWith("~") ? id.slice(1) : id
  // Remove trailing digits using a regex
  processed = processed.replace(/\d+$/, "")
  // Replace underscores with spaces
  processed = processed.replace(/_/g, " ")
  // Convert to sentence case: lowercase entire string and then uppercase first letter
  processed = processed.toLowerCase()
  processed = processed.charAt(0).toUpperCase() + processed.slice(1)
  return processed
}

/**
 * Returns additional author information for tooltip display as a React component.
* Using Tailwind CSS for styling.
*/
function getAuthorInfo(author: {
  name?: string;
  affiliation_name: string;
  affiliation_country: string;
  affiliation_domain: string;
  openreview_id: string;
}): JSX.Element {
  const displayName = getDisplayName(author);

  return (
    <div className="text-left">
      <div className="text-lg font-bold">{displayName}</div>
      <div className="text-gray-100">Affiliation: {author.affiliation_name}</div>
      <div className="text-gray-100">Country: {author.affiliation_country}</div>
    </div>
  );
}
