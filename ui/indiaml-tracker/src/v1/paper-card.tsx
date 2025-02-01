import { useState } from "react"
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
    <Card className="h-full flex flex-col overflow-hidden transition-shadow hover:shadow-md">
      <CardHeader className="bg-zinc-900 border-b">
        <CardTitle className="text-lg text-zinc-200">{paper.paper_title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-grow flex flex-col justify-between p-4">
        <div>
          {/* Render abstract or a PDF link */}
          <p className="text-sm text-gray-600 mb-4">
            {paper.abstract ? (
              paper.abstract
            ) : (
              <a
                href={paper.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-100/60 underline"
              >
                View PDF
              </a>
            )}
          </p>
          <div className="flex flex-wrap gap-2 mb-4">
            <TooltipProvider>
              {visibleAuthors.map((author, index) => {
                const displayName = getDisplayName(author)
                return (
                  <Tooltip key={index}>
                    <TooltipTrigger asChild>
                      <a
                        href={`https://openreview.net/profile?id=${encodeURIComponent(
                          author.openreview_id
                        )}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Badge variant="secondary" className="bg-slate-700 text-blue-200">
                          {displayName}
                        </Badge>
                      </a>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{getAuthorInfo(author)}</p>
                    </TooltipContent>
                  </Tooltip>
                )
              })}
              {/* If not expanded and there are extra authors, show a badge to expand */}
              {!showAllAuthors && remainingAuthorsCount > 0 && (
                <Badge
                  onClick={() => setShowAllAuthors(true)}
                  className="cursor-pointer bg-zinc-600 text-gray-100"
                >
                  +{remainingAuthorsCount} more
                </Badge>
              )}
              {/* If expanded and there are extra authors, show a badge to collapse */}
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
 * Returns additional author information for tooltip display.
 */
function getAuthorInfo(author: {
  name?: string
  affiliation_name: string
  affiliation_country: string
  affiliation_domain: string
  openreview_id: string
}): string {
  const displayName = getDisplayName(author)
  return `${displayName}\nAffiliation: ${author.affiliation_name}\nCountry: ${author.affiliation_country}`
}
