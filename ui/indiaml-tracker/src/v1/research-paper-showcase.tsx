"use client"

import { useState } from "react"
import { FilterBar } from "./filter-bar"
import { PaperCard } from "./paper-card"
import type { Paper } from "@/types/paper"

const mockPapers: Paper[] = [
  {
    id: "1",
    title: "Advanced Deep Learning Techniques for Natural Language Processing",
    abstract:
      "This paper explores cutting-edge deep learning techniques applied to various NLP tasks, showcasing significant improvements in performance and efficiency.",
    authors: ["Priya Sharma", "Rahul Patel", "John Smith"],
    conference: "NeurIPS",
    year: 2024,
  },
  {
    id: "2",
    title: "Efficient Algorithms for Large-Scale Machine Learning",
    abstract:
      "We present novel algorithms that significantly reduce computational complexity in large-scale machine learning problems, enabling faster training on massive datasets.",
    authors: ["Amit Kumar", "Sarah Johnson", "Michael Chen"],
    conference: "ICML",
    year: 2024,
  },
  {
    id: "3",
    title: "Explainable AI: Bridging the Gap Between Performance and Interpretability",
    abstract:
      "This research introduces new methods for making complex AI models more interpretable without sacrificing performance, addressing a critical challenge in AI adoption.",
    authors: ["Neha Gupta", "David Lee", "Emma Watson"],
    conference: "NeurIPS",
    year: 2024,
  },
  // Add more mock papers as needed
]

function isIndianName(name: string): boolean {
  const indianNames = ["Sharma", "Patel", "Kumar", "Gupta", "Singh", "Reddy", "Chopra", "Bose", "Joshi", "Malhotra"]
  return indianNames.some((indianName) => name.includes(indianName))
}

export function ResearchPapersShowcase() {
  const [searchTerm, setSearchTerm] = useState("")
  const [isFirstAuthorIndian, setIsFirstAuthorIndian] = useState(false)
  const [isMajorityAuthorsIndian, setIsMajorityAuthorsIndian] = useState(false)
  const [selectedConferences, setSelectedConferences] = useState<string[]>([])

  const filteredPapers = mockPapers.filter((paper) => {
    const matchesSearch =
      paper.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      paper.abstract.toLowerCase().includes(searchTerm.toLowerCase())

    const firstAuthorIndian = isFirstAuthorIndian ? isIndianName(paper.authors[0]) : true
    const majorityAuthorsIndian = isMajorityAuthorsIndian
      ? paper.authors.filter(isIndianName).length > paper.authors.length / 2
      : true
    const matchesConference = selectedConferences.length === 0 || selectedConferences.includes(paper.conference)

    return matchesSearch && firstAuthorIndian && majorityAuthorsIndian && matchesConference
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
          <PaperCard key={paper.id} paper={paper} />
        ))}
      </div>
    </div>
  )
}

