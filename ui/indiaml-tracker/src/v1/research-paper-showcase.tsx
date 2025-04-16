"use client"
import { useState, useEffect } from "react"
import { FilterBar } from "./filter-bar"
import { PaperCard } from "./paper-card"
import type { Paper } from "@/types/paper"

interface ConferenceIndex {
  label: string
  file: string
}


const conferencePriority = {
  "NeurIPS": 3,
  "ICML": 2,
  "ICLR": 1 // Added ICLR as per your sort requirement, although not in the initial type. Adjust if needed.
  // Add other conferences if necessary, perhaps with priority 0 or lower
};

const venuePriority = {
  "oral": 3,
  "spotlight": 2,
  "poster": 1
  // Assign 0 for papers with no venue specified or other venue types
};

const getIndianAuthorshipPriority = (paper: Paper): number => {
  if (paper.top_author_from_india === true) {
    return 3; // Group 1: First author Indian (Highest priority)
  } else if (paper.majority_authors_from_india === true) {
    // This condition implies top_author_from_india is false
    return 2; // Group 2: Majority authors Indian (but first is not)
  } else {
    // This condition implies both top_author_from_india and majority_authors_from_india are false
    return 1; // Group 3: Remaining papers (Lowest priority among these groups)
  }
};


export function ResearchPapersShowcase() {
  const [conferenceIndex, setConferenceIndex] = useState<ConferenceIndex[]>([])
  const [allPapers, setAllPapers] = useState<Paper[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [isFirstAuthorIndian, setIsFirstAuthorIndian] = useState(false)
  const [isMajorityAuthorsIndian, setIsMajorityAuthorsIndian] = useState(false)
  const [selectedConferences, setSelectedConferences] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  
  // Create mapping between conference file names and conference-year keys
  const [fileToKeyMap, setFileToKeyMap] = useState<Record<string, string>>({})
  
  // Load the conference index
  useEffect(() => {
    async function fetchConferenceIndex() {
      try {
        const response = await fetch('/tracker/index.json')
        if (!response.ok) {
          throw new Error('Failed to fetch conference index')
        }
        const data = await response.json()
        setConferenceIndex(data)
        
        // Create mapping from file (without .json) to conference-year key
        const mapping: Record<string, string> = {}
        data.forEach((conf: ConferenceIndex) => {
          const labelParts = conf.label.split(' ')
          const id = labelParts[0].toLowerCase().replace('-', '')
          const year = labelParts[labelParts.length - 1]
          const key = `${id}-${year}`
          mapping[conf.file.replace('.json', '')] = key
        })
        
        setFileToKeyMap(mapping)
      } catch (error) {
        console.error("Error fetching conference index:", error)
      }
    }
    
    fetchConferenceIndex()
  }, [])
  
  // Load papers when conference index is loaded
  useEffect(() => {
    async function fetchAllPapers() {
      if (conferenceIndex.length === 0) return
      
      setLoading(true)
      const loadedPapers: Paper[] = []
      
      try {
        // Fetch papers from each conference file
        const fetchPromises = conferenceIndex.map(async (conf) => {
          try {
            const response = await fetch(`/tracker/${conf.file}`)
            if (!response.ok) {
              throw new Error(`Failed to fetch papers for ${conf.label}`)
            }
            const papers = await response.json()
            
            // Map each paper to include its conference file
            return papers.map((paper: Paper) => ({
              ...paper,
              // Store the conference file ID (without .json extension)
              accepted_in: [conf.file.replace('.json', '')]
            }))
          } catch (error) {
            console.error(`Error fetching papers for ${conf.label}:`, error)
            return []
          }
        })
        
        const papersArrays = await Promise.all(fetchPromises)
        papersArrays.forEach(papers => {
          loadedPapers.push(...papers)
        })
        
        setAllPapers(loadedPapers)
      } catch (error) {
        console.error("Error loading papers:", error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchAllPapers()
  }, [conferenceIndex])
  
  const filteredPapers = allPapers.filter((paper) => {
    const matchesSearch = paper.paper_title
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
    
    const matchesFirstAuthorIndian =
      !isFirstAuthorIndian || paper.top_author_from_india === true
    
    const matchesMajorityAuthorsIndian =
      !isMajorityAuthorsIndian || paper.majority_authors_from_india === true
    
    // Check if the paper's conference matches any selected conference
    const matchesConference =
      selectedConferences.length === 0 ||
      paper.accepted_in.some(confId => {
        const confKey = fileToKeyMap[confId]
        return selectedConferences.includes(confKey)
      })
    
    return (
      matchesSearch &&
      matchesFirstAuthorIndian &&
      matchesMajorityAuthorsIndian &&
      matchesConference
    )
  })
  .sort((a, b) => {
    // 1. Sort by Indian Authorship Priority (Descending: 3 -> 2 -> 1)
    const authorshipPrioA = getIndianAuthorshipPriority(a);
    const authorshipPrioB = getIndianAuthorshipPriority(b);
  
    if (authorshipPrioA !== authorshipPrioB) {
      // If priorities differ, sort based on this primary criterion
      return authorshipPrioB - authorshipPrioA; // Higher priority value comes first
    }
  
    // --- If authorship priority is the same, proceed to secondary criteria ---
  
    // 2. Sort by Year (Descending - recent first)
    if (a.year !== b.year) {
      return b.year - a.year;
    }
  
    // 3. Sort by Conference (NeurIPS > ICML > ICLR)
    const conferencePrioA = conferencePriority[a.conference as keyof typeof conferencePriority] || 0;
    const conferencePrioB = conferencePriority[b.conference as keyof typeof conferencePriority] || 0;
    if (conferencePrioA !== conferencePrioB) {
      return conferencePrioB - conferencePrioA;
    }
  
    // 4. Sort by Venue (Oral > Spotlight > Poster)
    const venuePrioA = venuePriority[a.venue as keyof typeof venuePriority] ?? 0;
    const venuePrioB = venuePriority[b.venue as keyof typeof venuePriority] ?? 0;
    if (venuePrioA !== venuePrioB) {
      return venuePrioB - venuePrioA;
    }
  
    // 5. If all criteria are equal, maintain relative order (or return 0)
    return 0;
  });
  
  
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
      
      {loading ? (
        <div className="flex justify-center items-center h-40">
          <p className="text-lg font-medium">Loading papers...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPapers.length > 0 ? (
            filteredPapers.map((paper) => (
              <PaperCard key={paper.paper_id} paper={paper} />
            ))
          ) : (
            <div className="col-span-3 text-center py-10">
              <p className="text-lg font-medium">No papers match your filters</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}