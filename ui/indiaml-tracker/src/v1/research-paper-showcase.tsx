"use client"

import { useState } from "react"
import { FilterBar } from "./filter-bar"
import { PaperCard } from "./paper-card"
import type { Paper } from "@/types/paper"
import mockPapers from "@/assets/neurips-icml-2024.json";

export function ResearchPapersShowcase() {
  const [searchTerm, setSearchTerm] = useState("")
  const [isFirstAuthorIndian, setIsFirstAuthorIndian] = useState(false)
  const [isMajorityAuthorsIndian, setIsMajorityAuthorsIndian] = useState(false)
  const [selectedConferences, setSelectedConferences] = useState<string[]>([])

  const filteredPapers = mockPapers.filter((paper) => {
    const matchesSearch = paper.paper_title
      .toLowerCase()
      .includes(searchTerm.toLowerCase())

      const matchesFirstAuthorIndian =
      !isFirstAuthorIndian || paper.top_author_from_india === true

    const matchesMajorityAuthorsIndian =
      !isMajorityAuthorsIndian || paper.majority_authors_from_india === true

    const matchesConference =
      selectedConferences.length === 0 ||
      paper.accepted_in.some((conf) => selectedConferences.includes(conf))

    return (
      matchesSearch &&
      matchesFirstAuthorIndian &&
      matchesMajorityAuthorsIndian &&
      matchesConference
    )
  })

  return (
    <div className="container mx-auto space-y-6 p-4">
      <FilterBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        isFirstAuthorIndian={isFirstAuthorIndian}
        setIsFirstAuthorIndian={setIsFirstAuthorIndian}
        isMajorityAuthorsIndian={isMajorityAuthorsIndian}
        setIsMajorityAuthorsIndian={setIsMajorityAuthorsIndian}
        selectedConferences={selectedConferences}
        setSelectedConferences={setSelectedConferences}
      />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPapers.map((paper) => (
          <PaperCard key={paper.paper_id} paper={paper} />
        ))}
      </div>
    </div>
  )
}
