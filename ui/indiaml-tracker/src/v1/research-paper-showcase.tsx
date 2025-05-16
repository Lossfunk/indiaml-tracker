"use client"
import { useState, useEffect, useMemo } from "react"
import { FilterBar } from "./filter-bar" // Assuming this component exists
import { PaperCard } from "./paper-card"   // Assuming this component exists
import type { Paper } from "@/types/paper" // Assuming this type definition exists
import { useNavigate } from "react-router-dom" // Added for navigation

interface ConferenceIndex {
  label: string
  file: string
}

// Define Conference Priority using UPPERCASE keys to match derived names
const conferencePriority: Record<string, number> = {
  "NEURIPS": 3,
  "ICML": 2,
  "ICLR": 1,
  // Add other conferences with priority 0 or lower if needed (use UPPERCASE)
};

// Define Venue Priority for sorting papers within a conference group
const venuePriority: Record<string, number> = {
  "oral": 3,
  "spotlight": 2,
  "poster": 1,
  "unknown": 0, // Default priority for unspecified or other venues
};

// Define Indian Authorship Priority for primary sorting
const getIndianAuthorshipPriority = (paper: Paper): number => {
  if (paper.top_author_from_india === true) {
    return 3;
  } else if (paper.majority_authors_from_india === true) {
    return 2;
  } else {
    return 1;
  }
};

// Helper function to get conference priority, defaulting to 0
const getConferencePriority = (conferenceName: string | undefined): number => {
  return conferenceName ? (conferencePriority[conferenceName.toUpperCase()] || 0) : 0;
};

// Helper function to get venue priority, defaulting to 0
const getVenuePriority = (venueName: string | undefined): number => {
    return venueName ? (venuePriority[venueName.toLowerCase()] || 0) : 0;
};

// Helper function to capitalize the first letter of a string (no longer strictly needed for display but good utility)
const capitalizeFirstLetter = (string: string): string => {
  if (!string) return '';
  return string.charAt(0).toUpperCase() + string.slice(1);
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
  const navigate = useNavigate();

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
          const id = labelParts[0].toLowerCase().replace(/[^a-z0-9]/g, '')
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

  useEffect(() => {
    async function fetchAllPapers() {
        if (conferenceIndex.length === 0 || Object.keys(fileToKeyMap).length === 0) {
             return;
        }
        setLoading(true)
        const loadedPapers: Paper[] = []
        try {
            const fetchPromises = conferenceIndex.map(async (conf) => {
            try {
                const response = await fetch(`/tracker/${conf.file}`)
                if (!response.ok) {
                console.error(`Failed to fetch papers for ${conf.label} (Status: ${response.status})`)
                return []
                }
                const papersData = await response.json() as Paper[]

                return papersData.map((paper) => {
                    const fileId = conf.file.replace('.json', '');
                    const confKey = fileToKeyMap[fileId];

                    let year = paper.year || 0;
                    let conference = (paper.conference || 'UNKNOWN').toUpperCase();

                    if (confKey) {
                        const keyParts = confKey.split('-');
                        const derivedConfName = keyParts[0]?.toUpperCase();
                        const derivedYearStr = keyParts[keyParts.length - 1];

                        if (derivedConfName) {
                            conference = derivedConfName;
                        }
                        const parsedYear = parseInt(derivedYearStr, 10);
                        if (!isNaN(parsedYear)) {
                            year = parsedYear;
                        }
                    } else {
                         console.warn(`Could not find key for fileId: ${fileId} in fileToKeyMap`);
                    }
                    const venue = (paper.venue || 'unknown').toLowerCase();

                    return {
                        ...paper,
                        accepted_in: [fileId],
                        year: year,
                        conference: conference,
                        venue: venue,
                    };
                });
            } catch (error) {
                console.error(`Error processing papers for ${conf.label}:`, error)
                return []
            }
            })

            const papersArrays = await Promise.all(fetchPromises)
            papersArrays.forEach(papersList => {
                if (papersList) {
                   loadedPapers.push(...papersList)
                }
            })
            setAllPapers(loadedPapers)
        } catch (error) {
            console.error("Error loading papers:", error)
        } finally {
            setLoading(false)
        }
    }
     fetchAllPapers()
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

        const matchesConference =
          selectedConferences.length === 0 ||
          paper.accepted_in.some(confId => {
              const confKey = fileToKeyMap[confId];
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
    // 1. Sort the filtered papers (venue priority is still used for sorting within a conference)
    const sortedFilteredPapers = [...filteredPapers].sort((a, b) => {
        const authorshipPrioA = getIndianAuthorshipPriority(a);
        const authorshipPrioB = getIndianAuthorshipPriority(b);
        if (authorshipPrioA !== authorshipPrioB) return authorshipPrioB - authorshipPrioA;

        if (a.year !== b.year) return b.year - a.year;

        const conferencePrioA = getConferencePriority(a.conference);
        const conferencePrioB = getConferencePriority(b.conference);
        if (conferencePrioA !== conferencePrioB) return conferencePrioB - conferencePrioA;

        const venuePrioA = getVenuePriority(a.venue);
        const venuePrioB = getVenuePriority(b.venue);
        if (venuePrioA !== venuePrioB) return venuePrioB - venuePrioA;

        return a.paper_title.localeCompare(b.paper_title);
    });

    // 2. Group the sorted papers by Year and then by Conference (uppercase)
    const groups: Record<number, Record<string, Paper[]>> = {}; // Simplified grouping
    sortedFilteredPapers.forEach(paper => {
        const year = paper.year;
        const conference = paper.conference; // Already uppercase

        if (!groups[year]) groups[year] = {};
        if (!groups[year][conference]) groups[year][conference] = [];
        groups[year][conference].push(paper);
    });

     // 3. Prepare sorted structure for rendering
     const sortedYears = Object.keys(groups)
         .map(Number)
         .sort((a, b) => b - a);

     const finalGroupedStructure: {
        year: number;
        conferences: {
            name: string; // Conference name (UPPERCASE)
            papers: Paper[]; // All papers for this conference
        }[];
    }[] = sortedYears.map(year => {
         const yearConferences = groups[year];
         const sortedConferenceNames = Object.keys(yearConferences)
             .sort((a, b) => getConferencePriority(b) - getConferencePriority(a));

         return {
             year: year,
             conferences: sortedConferenceNames.map(confName => ({
                 name: confName,
                 papers: yearConferences[confName] // Get all papers for this conference
             }))
         };
     });

    return finalGroupedStructure;

  }, [filteredPapers]);

  // --- Rendering ---
  return (
    <div className="container mx-auto space-y-6 p-4 font-sans">
      <FilterBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        isFirstAuthorIndian={isFirstAuthorIndian}
        setIsFirstAuthorIndian={setIsFirstAuthorIndian}
        isMajorityAuthorsIndian={isMajorityAuthorsIndian}
        setIsMajorityAuthorsIndian={setIsMajorityAuthorsIndian}
        selectedConferences={selectedConferences}
        setSelectedConferences={setSelectedConferences}
        // conferenceOptions={Object.entries(fileToKeyMap).map(([fileId, confKey]) => ({ value: confKey, label: confKey }))}
      />

      {loading ? (
        <div className="flex justify-center items-center h-40">
          <p className="text-lg font-medium text-gray-600 dark:text-gray-400">Loading papers...</p> {/* Added dark mode text for loading */}
        </div>
      ) : groupedAndSortedPapers.length > 0 ? (
         groupedAndSortedPapers.map(({ year, conferences }) => (
           <div key={year} className="mt-8 first:mt-0">
             <h2 className="text-3xl font-bold mb-6 border-b border-gray-300 dark:border-gray-700 pb-3 text-gray-800 dark:text-gray-200">{year}</h2> {/* Added dark mode styles */}
             {conferences.map(({ name, papers }) => ( // `name` is conference name (UPPERCASE)
               <div key={`${year}-${name}`} className="mb-8">
                 <div className="flex items-center mb-4"> {/* Container for heading and button */}
                    <h3 className="text-2xl font-semibold text-gray-700 dark:text-gray-300"> {/* Added dark mode styles */}
                        {name} ({papers.length} accepted)
                    </h3>
                    <button
                        onClick={() => navigate(`/analytics?conference=${name}&year=${year}`)}
                        // Updated button classes for link-like appearance and dark mode
                        className="ml-4 px-3 py-1 text-sm font-medium rounded-md transition-colors 
                                   text-indigo-600 hover:text-indigo-800 hover:underline
                                   dark:text-indigo-400 dark:hover:text-indigo-300
                                   focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-black focus:ring-indigo-500"
                        aria-label={`View analytics for ${name} ${year}`}
                    >
                        Detailed Summary of India @ {name} {year}
                    </button>
                 </div>
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
           <p className="text-lg font-medium text-gray-500 dark:text-gray-400">No papers match your filters.</p> {/* Added dark mode text */}
         </div>
       )}
    </div>
  )
}

// Make sure FilterBar, PaperCard components and Paper type are defined elsewhere.
// Also, ensure react-router-dom is installed and <Router> (or <BrowserRouter>) is set up in your application's root.
