"use client"
import { useState, useEffect, useMemo } from "react"
import { FilterBar } from "./filter-bar"
import { PaperCard } from "./paper-card"
import type { Paper } from "@/types/paper"

interface ConferenceIndex {
  label: string
  file: string
}

// Define Conference Priority using UPPERCASE keys to match derived names
// ***** THIS IS THE FIX *****
const conferencePriority: Record<string, number> = {
  "NEURIPS": 3, // Use UPPERCASE to match derived paper.conference
  "ICML": 2,    // Use UPPERCASE
  "ICLR": 1,    // Use UPPERCASE
  // Add other conferences with priority 0 or lower if needed (use UPPERCASE)
};

// Define Venue Priority for sorting papers within a conference group
const venuePriority: Record<string, number> = {
  "oral": 3,
  "spotlight": 2,
  "poster": 1,
  // Assign 0 for papers with no venue specified or other venue types
};

// Define Indian Authorship Priority for primary sorting
const getIndianAuthorshipPriority = (paper: Paper): number => {
  if (paper.top_author_from_india === true) {
    return 3; // Group 1: First author Indian (Highest priority)
  } else if (paper.majority_authors_from_india === true) {
    return 2; // Group 2: Majority authors Indian (but first is not)
  } else {
    return 1; // Group 3: Remaining papers (Lowest priority among these groups)
  }
};

// Helper function to get conference priority, defaulting to 0
// Now correctly looks up using uppercase keys from the map above
const getConferencePriority = (conferenceName: string | undefined): number => {
  // Ensure we handle potential undefined input gracefully
  return conferenceName ? (conferencePriority[conferenceName] || 0) : 0;
};


// Helper function to get venue priority, defaulting to 0
const getVenuePriority = (venueName: string | undefined): number => {
    return venueName ? (venuePriority[venueName] || 0) : 0;
};


export function ResearchPapersShowcase() {
  const [conferenceIndex, setConferenceIndex] = useState<ConferenceIndex[]>([])
  const [allPapers, setAllPapers] = useState<Paper[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [isFirstAuthorIndian, setIsFirstAuthorIndian] = useState(false)
  const [isMajorityAuthorsIndian, setIsMajorityAuthorsIndian] = useState(false)
  const [selectedConferences, setSelectedConferences] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [fileToKeyMap, setFileToKeyMap] = useState<Record<string, string>>({})

  // --- Fetching Logic ---
  useEffect(() => {
    async function fetchConferenceIndex() {
      try {
        const response = await fetch('/tracker/index.json')
        if (!response.ok) {
          throw new Error('Failed to fetch conference index')
        }
        const data = await response.json()
        setConferenceIndex(data)

        const mapping: Record<string, string> = {}
        data.forEach((conf: ConferenceIndex) => {
          const labelParts = conf.label.split(' ')
          // Ensure consistent key generation (lowercase id)
          const id = labelParts[0].toLowerCase().replace(/[^a-z0-9]/g, '') // More robust cleaning
          const year = labelParts[labelParts.length - 1]
          const key = `${id}-${year}` // e.g., "neurips-2023"
          mapping[conf.file.replace('.json', '')] = key
        })
        setFileToKeyMap(mapping)
      } catch (error) {
        console.error("Error fetching conference index:", error)
      }
    }
    fetchConferenceIndex()
  }, [])

  useEffect(() => {
    async function fetchAllPapers() {
        // Guard clauses
        if (conferenceIndex.length === 0 || Object.keys(fileToKeyMap).length === 0) {
             // console.log("Skipping paper fetch: Conference index or file map not ready.");
             return;
        }
        setLoading(true)
        // console.log("Starting to fetch all papers...");
        const loadedPapers: Paper[] = []
        try {
            const fetchPromises = conferenceIndex.map(async (conf) => {
            try {
                const response = await fetch(`/tracker/${conf.file}`)
                if (!response.ok) {
                console.error(`Failed to fetch papers for ${conf.label} (Status: ${response.status})`)
                // Optionally throw or return empty array based on desired error handling
                return [] // Skip this conference on fetch error
                }
                const papers = await response.json() as Paper[]

                return papers.map((paper) => {
                    const fileId = conf.file.replace('.json', '');
                    const confKey = fileToKeyMap[fileId]; // e.g., "neurips-2023"

                    // Defensive programming for derivation
                    let year = paper.year || 0; // Initialize with paper's year or 0
                    let conference = (paper.conference || 'UNKNOWN').toUpperCase(); // Initialize with paper's conf or UNKNOWN

                    if (confKey) {
                        const keyParts = confKey.split('-');
                        const derivedConfName = keyParts[0]?.toUpperCase(); // Extract and uppercase name part
                        const derivedYearStr = keyParts[keyParts.length - 1]; // Extract year part

                        if (derivedConfName) {
                            conference = derivedConfName; // Use derived name (e.g., NEURIPS)
                        }
                        const parsedYear = parseInt(derivedYearStr, 10);
                        if (!isNaN(parsedYear)) {
                            year = parsedYear; // Use derived year if valid
                        }
                    } else {
                         console.warn(`Could not find key for fileId: ${fileId} in fileToKeyMap`);
                    }

                    return {
                        ...paper,
                        accepted_in: [fileId], // Keep original file ID for filtering if needed
                        year: year,            // Assign derived/fallback year
                        conference: conference // Assign derived/fallback conference name (UPPERCASE)
                    };
                });
            } catch (error) {
                console.error(`Error processing papers for ${conf.label}:`, error)
                return [] // Skip this conference on processing error
            }
            })

            const papersArrays = await Promise.all(fetchPromises)
            papersArrays.forEach(papers => {
                if (papers) { // Check if papers array is not null/undefined
                   loadedPapers.push(...papers)
                }
            })
            // console.log(`Total papers loaded: ${loadedPapers.length}`);
            setAllPapers(loadedPapers)
        } catch (error) {
            console.error("Error loading papers:", error)
        } finally {
            // console.log("Finished fetching papers.");
            setLoading(false)
        }
    }
     fetchAllPapers()
    // Dependencies ensure this runs when index or map is ready/updated
  }, [conferenceIndex, fileToKeyMap])


  // --- Filtering Logic ---
  const filteredPapers = useMemo(() => {
      return allPapers.filter((paper) => {
        const matchesSearch = paper.paper_title
          .toLowerCase()
          .includes(searchTerm.toLowerCase())

        const matchesFirstAuthorIndian =
          !isFirstAuthorIndian || paper.top_author_from_india === true

        const matchesMajorityAuthorsIndian =
          !isMajorityAuthorsIndian || paper.majority_authors_from_india === true

        // Filter based on the selected 'conference-year' keys
        const matchesConference =
          selectedConferences.length === 0 ||
          paper.accepted_in.some(confId => {
              const confKey = fileToKeyMap[confId]; // Get 'neurips-2023' style key
              // Ensure confKey exists before checking inclusion
              return confKey && selectedConferences.includes(confKey);
          })

        return (
          matchesSearch &&
          matchesFirstAuthorIndian &&
          matchesMajorityAuthorsIndian &&
          matchesConference
        )
      });
  }, [allPapers, searchTerm, isFirstAuthorIndian, isMajorityAuthorsIndian, selectedConferences, fileToKeyMap]);


  // --- Grouping and Sorting Logic ---
  const groupedAndSortedPapers = useMemo(() => {
    // 1. Sort the filtered papers
    const sortedFilteredPapers = [...filteredPapers].sort((a, b) => {
        // Primary: Indian Authorship Priority (Descending)
        const authorshipPrioA = getIndianAuthorshipPriority(a);
        const authorshipPrioB = getIndianAuthorshipPriority(b);
        if (authorshipPrioA !== authorshipPrioB) return authorshipPrioB - authorshipPrioA;

        // Secondary: Year (Descending)
        if (a.year !== b.year) return b.year - a.year;

        // Tertiary: Conference Priority (Descending) - Uses uppercase lookup now
        const conferencePrioA = getConferencePriority(a.conference);
        const conferencePrioB = getConferencePriority(b.conference);
        if (conferencePrioA !== conferencePrioB) return conferencePrioB - conferencePrioA;

        // Quaternary: Venue Priority (Descending)
        const venuePrioA = getVenuePriority(a.venue);
        const venuePrioB = getVenuePriority(b.venue);
        if (venuePrioA !== venuePrioB) return venuePrioB - venuePrioA;

        // Fallback: Sort alphabetically by title
        return a.paper_title.localeCompare(b.paper_title);
    });

    // 2. Group the sorted papers by Year and then by Conference (using uppercase conference name)
    const groups: Record<number, Record<string, Paper[]>> = {};
    sortedFilteredPapers.forEach(paper => {
        const year = paper.year;
        // Ensure conference is treated as string, default to 'UNKNOWN' if somehow undefined/null
        const conference = typeof paper.conference === 'string' ? paper.conference : 'UNKNOWN';

        if (!groups[year]) {
            groups[year] = {};
        }
        if (!groups[year][conference]) {
            groups[year][conference] = [];
        }
        groups[year][conference].push(paper);
    });

     // 3. Prepare sorted structure for rendering
     const sortedYears = Object.keys(groups)
         .map(Number)
         .sort((a, b) => b - a); // Sort years descending

     const finalGroupedStructure: { year: number; conferences: { name: string; papers: Paper[] }[] }[] = sortedYears.map(year => {
         const yearConferences = groups[year];
         // Sort conference names within the year based on priority (uses uppercase lookup)
         const sortedConferenceNames = Object.keys(yearConferences)
             .sort((a, b) => getConferencePriority(b) - getConferencePriority(a)); // Sort conferences by priority descending

         return {
             year: year,
             conferences: sortedConferenceNames.map(confName => ({
                 name: confName, // The name is already uppercase (e.g., NEURIPS)
                 papers: yearConferences[confName]
             }))
         };
     });

    return finalGroupedStructure;

  }, [filteredPapers]); // Recalculate when filtered papers change

  // --- Rendering ---
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
        // You might want to derive options for FilterBar based on available data
        // conferenceOptions={Object.entries(fileToKeyMap).map(([fileId, confKey]) => ({ value: confKey, label: confKey }))} // Example
      />

      {loading ? (
        <div className="flex justify-center items-center h-40">
          <p className="text-lg font-medium">Loading papers...</p>
        </div>
      ) : groupedAndSortedPapers.length > 0 ? (
         groupedAndSortedPapers.map(({ year, conferences }) => (
           <div key={year} className="mt-8 first:mt-0">
             <h2 className="text-2xl font-semibold mb-4 border-b pb-2">{year}</h2>
             {conferences.map(({ name, papers }) => (
               <div key={`${year}-${name}`} className="mb-6">
                 {/* Display the conference name (which is uppercase) */}
                 <h3 className="text-xl font-medium mb-3 text-gray-700">{name} ({papers.length} accepted) </h3>
                 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                   {papers.map((paper) => (
                     <PaperCard key={paper.paper_id} paper={paper} />
                   ))}
                 </div>
               </div>
             ))}
           </div>
         ))
       ) : (
         <div className="col-span-full text-center py-10">
           <p className="text-lg font-medium">No papers match your filters</p>
         </div>
       )}
    </div>
  )
}