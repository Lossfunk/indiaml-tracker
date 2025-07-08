import { useState, useEffect, useMemo } from "react"
import { FilterBar } from "./filter-bar"
import { PaperCard } from "./paper-card"
import type { ConferenceData, Paper as V2Paper } from "./types/conference"
import type { ConferenceStatistics } from "./types/conference_analytics"
import type { Paper } from "@/types/paper"
import { useNavigate } from "react-router-dom"

interface ConferenceIndex {
  label: string
  file: string
  analytics: string
  venue: string
  year: string
  sqlite_file: string
}

interface ConferenceKPIs {
  totalPapers: number
  spotlightCount: number
  oralCount: number
  authorCount: number
  indiaRank: number
  institutionCount: number
  academicInstitutions: number
  corporateInstitutions: number
  topInstitutions: Array<{
    name: string
    paperCount: number
    authorCount: number
  }>
}

// Define Conference Priority
const conferencePriority: Record<string, number> = {
  "NEURIPS": 3,
  "ICML": 2,
  "ICLR": 1,
}

// Define Status Priority for sorting papers within a conference group
const statusPriority: Record<string, number> = {
  "oral": 3,
  "spotlight": 2,
  "poster": 1,
  "rejected": 0,
  "withdrawn": 0,
}

// Helper function to get conference priority, defaulting to 0
const getConferencePriority = (conferenceName: string | undefined): number => {
  return conferenceName ? (conferencePriority[conferenceName.toUpperCase()] || 0) : 0
}

// Helper function to get status priority, defaulting to 0
const getStatusPriority = (status: string | undefined): number => {
  return status ? (statusPriority[status.toLowerCase()] || 0) : 0
}

// Helper function to convert V2Paper to Paper type
const convertV2PaperToPaper = (v2Paper: V2Paper, conferenceVenue: string, conferenceYear: number, conferenceLabel: string, fileId: string): Paper => {
  return {
    id: v2Paper.paper_id,
    title: v2Paper.title,
    paper_id: v2Paper.paper_id,
    author_list: [{
      name: v2Paper.author.name,
      openreview_id: v2Paper.author.openreview_id,
      affiliation_name: v2Paper.author.affiliations || undefined,
      affiliation_country: v2Paper.author.country_codes[0] || undefined,
    }],
    abstract: v2Paper.abstract,
    conference: conferenceVenue,
    year: conferenceYear,
    venue: v2Paper.normalized_status,
    paper_content: v2Paper.tldr || v2Paper.abstract,
    paper_title: v2Paper.title,
    accepted_in: [fileId],
    pdf_url: v2Paper.pdf_url || "",
    top_author_from_india: v2Paper.author.position === 1 && v2Paper.author.country_codes.includes("IN"),
    majority_authors_from_india: v2Paper.author.country_codes.includes("IN"),
  }
}

// Helper function to check if paper has Indian authorship
const hasIndianAuthorship = (paper: Paper): boolean => {
  return paper.majority_authors_from_india
}

// Helper function to check if paper has first author from India
const hasFirstAuthorFromIndia = (paper: Paper): boolean => {
  return paper.top_author_from_india
}

export function ResearchPapersShowcase() {
  const [conferenceIndex, setConferenceIndex] = useState<ConferenceIndex[]>([])
  const [allPapers, setAllPapers] = useState<Paper[]>([])
  const [analyticsData, setAnalyticsData] = useState<Record<string, ConferenceStatistics>>({})
  const [searchTerm, setSearchTerm] = useState("")
  const [isFirstAuthorIndian, setIsFirstAuthorIndian] = useState(false)
  const [isMajorityAuthorsIndian, setIsMajorityAuthorsIndian] = useState(false)
  const [selectedConferences, setSelectedConferences] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedConferences, setExpandedConferences] = useState<Set<string>>(new Set())
  const navigate = useNavigate()

  // Function to toggle conference expansion
  const toggleConferenceExpansion = (conferenceKey: string) => {
    setExpandedConferences(prev => {
      const newSet = new Set(prev)
      if (newSet.has(conferenceKey)) {
        newSet.delete(conferenceKey)
      } else {
        newSet.add(conferenceKey)
      }
      return newSet
    })
  }

  // Fetch conference index
  useEffect(() => {
    async function fetchConferenceIndex() {
      try {
        const response = await fetch('/tracker_v2/index.json')
        if (!response.ok) {
          throw new Error('Failed to fetch conference index')
        }
        const data = await response.json() as ConferenceIndex[]
        setConferenceIndex(data)
      } catch (error) {
        console.error("Error fetching conference index:", error)
      }
    }
    fetchConferenceIndex()
  }, [])

  // Fetch all papers
  useEffect(() => {
    async function fetchAllPapers() {
      if (conferenceIndex.length === 0) {
        return
      }
      setLoading(true)
      const loadedPapers: Paper[] = []
      
      try {
        const fetchPromises = conferenceIndex.map(async (conf) => {
          try {
            const response = await fetch(`/tracker_v2/${conf.file}`)
            if (!response.ok) {
              console.error(`Failed to fetch papers for ${conf.label} (Status: ${response.status})`)
              return []
            }
            const conferenceData = await response.json() as ConferenceData
            
            return conferenceData.papers.map((v2Paper) => 
              convertV2PaperToPaper(
                v2Paper,
                conf.venue.toUpperCase(),
                parseInt(conf.year),
                conf.label,
                conf.file.replace('.json', '')
              )
            )
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
  }, [conferenceIndex])

  // Fetch analytics data
  useEffect(() => {
    async function fetchAnalyticsData() {
      if (conferenceIndex.length === 0) {
        return
      }

      const analyticsMap: Record<string, ConferenceStatistics> = {}

      try {
        const fetchPromises = conferenceIndex.map(async (conf) => {
          if (!conf.analytics) return null

          try {
            const response = await fetch(`/tracker_v2/${conf.analytics}`)
            if (!response.ok) {
              console.error(`Failed to fetch analytics for ${conf.label}`)
              return null
            }
            
            const data = await response.json() as ConferenceStatistics
            const fileId = conf.file.replace('.json', '')
            return { fileId, data }
          } catch (error) {
            console.error(`Error processing analytics for ${conf.label}:`, error)
            return null
          }
        })

        const results = await Promise.all(fetchPromises)
        
        results.forEach(result => {
          if (result && result.fileId) {
            analyticsMap[result.fileId] = result.data
          }
        })

        setAnalyticsData(analyticsMap)
      } catch (error) {
        console.error("Error loading analytics data:", error)
      }
    }

    fetchAnalyticsData()
  }, [conferenceIndex])

  // Filtering Logic
  const filteredPapers = useMemo(() => {
    return allPapers.filter((paper) => {
      const matchesSearch = paper.title
        .toLowerCase()
        .includes(searchTerm.toLowerCase())

      const matchesFirstAuthorIndian =
        !isFirstAuthorIndian || hasFirstAuthorFromIndia(paper)

      const matchesMajorityAuthorsIndian =
        !isMajorityAuthorsIndian || hasIndianAuthorship(paper)

      const matchesConference =
        selectedConferences.length === 0 ||
        selectedConferences.some(confKey => {
          const [venue, year] = confKey.split('-')
          return paper.conference?.toLowerCase() === venue?.toLowerCase() &&
                 paper.year?.toString() === year
        })

      return (
        matchesSearch &&
        matchesFirstAuthorIndian &&
        matchesMajorityAuthorsIndian &&
        matchesConference
      )
    })
  }, [allPapers, searchTerm, isFirstAuthorIndian, isMajorityAuthorsIndian, selectedConferences])

  // Grouping and Sorting Logic
  const groupedAndSortedPapers = useMemo(() => {
    // Sort the filtered papers
    const sortedFilteredPapers = [...filteredPapers].sort((a, b) => {
      // First sort by Indian authorship priority
      const aHasIndian = hasIndianAuthorship(a)
      const bHasIndian = hasIndianAuthorship(b)
      if (aHasIndian !== bHasIndian) return bHasIndian ? 1 : -1

      // Then by year (descending)
      if (a.year !== b.year) {
        return (b.year || 0) - (a.year || 0)
      }

      // Then by conference priority
      const conferencePrioA = getConferencePriority(a.conference)
      const conferencePrioB = getConferencePriority(b.conference)
      if (conferencePrioA !== conferencePrioB) return conferencePrioB - conferencePrioA

      // Then by status priority
      const statusPrioA = getStatusPriority(a.venue)
      const statusPrioB = getStatusPriority(b.venue)
      if (statusPrioA !== statusPrioB) return statusPrioB - statusPrioA

      // Finally by title
      return a.title.localeCompare(b.title)
    })

    // Helper function to get conference KPIs from analytics data
    const getConferenceKPIs = (papers: Paper[], venue: string, year: number): ConferenceKPIs => {
      // Find the analytics data for this conference
      const analyticsForConference = Object.values(analyticsData).find(data => 
        data.conference?.toLowerCase() === venue.toLowerCase() && data.year === year
      )

      if (analyticsForConference) {
        const { focusCountrySummary, institutions } = analyticsForConference
        
        return {
          totalPapers: papers.length,
          spotlightCount: focusCountrySummary.spotlights,
          oralCount: focusCountrySummary.orals,
          authorCount: focusCountrySummary.author_count,
          indiaRank: focusCountrySummary.rank,
          institutionCount: focusCountrySummary.institution_count,
          academicInstitutions: focusCountrySummary.academic_institutions,
          corporateInstitutions: focusCountrySummary.corporate_institutions,
          topInstitutions: [], // Would need to extract from institutions.top_institutions
        }
      } else {
        // Fallback calculation if no analytics data is available
        const spotlightCount = papers.filter(
          paper => paper.venue === "spotlight"
        ).length
        const oralCount = papers.filter(
          paper => paper.venue === "oral"
        ).length
        
        return {
          totalPapers: papers.length,
          spotlightCount,
          oralCount,
          authorCount: papers.length * 3, // Rough estimate
          indiaRank: 15, // Default fallback value
          institutionCount: 0,
          academicInstitutions: 0,
          corporateInstitutions: 0,
          topInstitutions: [],
        }
      }
    }

    // Group the sorted papers by Year and then by Conference
    const groups: Record<number, Record<string, Paper[]>> = {}
    sortedFilteredPapers.forEach(paper => {
      const year = paper.year || 0
      const venue = paper.conference || 'UNKNOWN'

      if (!groups[year]) groups[year] = {}
      if (!groups[year][venue]) groups[year][venue] = []
      groups[year][venue].push(paper)
    })

    // Prepare sorted structure for rendering
    const sortedYears = Object.keys(groups)
      .map(Number)
      .sort((a, b) => b - a)

    const finalGroupedStructure: {
      year: number
      conferences: {
        name: string
        papers: Paper[]
        kpis: ConferenceKPIs
      }[]
    }[] = sortedYears.map(year => {
      const yearConferences = groups[year]
      const sortedVenueNames = Object.keys(yearConferences)
        .sort((a, b) => getConferencePriority(b) - getConferencePriority(a))

      return {
        year: year,
        conferences: sortedVenueNames.map(venueName => {
          const papers = yearConferences[venueName]
          const kpis = getConferenceKPIs(papers, venueName, year)
          
          return {
            name: venueName,
            papers: papers,
            kpis: kpis,
          }
        })
      }
    })

    return finalGroupedStructure
  }, [filteredPapers, analyticsData])

  // Paper Display Logic
  const [collapseAll, setCollapseAll] = useState<boolean>(false)
  
  // Effect to collapse all conferences when collapseAll is toggled
  useEffect(() => {
    if (collapseAll) {
      setExpandedConferences(new Set())
    }
  }, [collapseAll])
  
  // Determine number of papers to show for each conference
  const getPapersToShow = (papers: Paper[], conferenceKey: string) => {
    const isExpanded = expandedConferences.has(conferenceKey)
    
    if (isExpanded) {
      return papers // Show all papers if expanded
    } else {
      return papers.slice(0, 6) // Show first 6 papers if not expanded
    }
  }

  // Generate conference options for filter
  const conferenceOptions = useMemo(() => {
    const options = new Set<string>()
    conferenceIndex.forEach(conf => {
      const key = `${conf.venue}-${conf.year}`
      options.add(key)
    })
    return Array.from(options).map(key => ({
      value: key,
      label: key.replace('-', ' ').toUpperCase()
    }))
  }, [conferenceIndex])

  return (
    <div className="container mx-auto space-y-6 p-4 font-sans">
      {/* Sticky Wrapper for FilterBar */}
      <div className="sticky top-0 z-50 bg-white dark:bg-gray-950 -mx-4 px-4 py-3">
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
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-40">
          <p className="text-sm sm:text-lg font-medium text-gray-600 dark:text-gray-400">Loading papers...</p>
        </div>
      ) : groupedAndSortedPapers.length > 0 ? (
        groupedAndSortedPapers.map(({ year, conferences }) => (
          <div key={year} className="mt-4 sm:mt-8 first:mt-0">
            <div className="flex justify-between items-center mb-3 sm:mb-6 border-b border-gray-300 dark:border-gray-700 pb-2 sm:pb-3">
              <h2 className="text-xl sm:text-3xl font-bold text-gray-800 dark:text-gray-200">{year}</h2>
              <button
                onClick={() => setCollapseAll(prev => !prev)}
                className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 underline focus:outline-none transition-colors"
              >
                {collapseAll ? "Expand All" : "Collapse All"}
              </button>
            </div>
            {conferences.map(({ name, papers, kpis }) => {
              const conferenceKey = `${year}-${name}`
              const isExpanded = expandedConferences.has(conferenceKey)
              const papersToShow = getPapersToShow(papers, conferenceKey)
              const hasMorePapers = papers.length > papersToShow.length
              
              return (
                <div key={conferenceKey} className="mb-8">
                  {/* Enhanced KPI Card Section */}
                  <div className="mb-3 sm:mb-6 bg-white dark:bg-slate-800/95 rounded-lg border border-slate-700 shadow-md overflow-hidden">
                    <div className="flex flex-col">
                      {/* Title and View Analytics Button */}
                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center px-3 sm:px-5 py-2 sm:py-4 gap-2 sm:gap-0">
                        <div>
                          <h3 className="text-sm sm:text-xl font-semibold text-black dark:text-white">
                            {name} {year} ({kpis.totalPapers} accepted)
                          </h3>
                        </div>
                        
                        {/* View Analytics Button */}
                        <button
                          onClick={() => navigate(`/conference-summary?conference=${name}&year=${year}`)}
                          className="hover:bg-gray-600 py-1 sm:py-1.5 px-2 sm:px-4 rounded-md transition-colors 
                                  focus:outline-none focus:ring-1 focus:ring-white focus:ring-opacity-50 
                                  flex items-center shadow-md text-xs sm:text-sm"
                        >
                          <span className="font-medium dark:text-yellow-200 text-orange-500 hidden sm:inline">View detailed overview of </span> 
                          <span className="font-bold sm:ml-1 dark:text-yellow-200 text-orange-500">India@{name} {year}</span>
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 sm:h-4 sm:w-4 ml-1 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                          </svg>
                        </button>
                      </div>
                      
                      {/* Metrics Section */}
                      <div className="px-3 sm:px-5 pb-3 sm:pb-5 grid grid-cols-2 md:grid-cols-4 gap-x-2 sm:gap-x-4 gap-y-3 sm:gap-y-8">
                        {/* Accepted Papers */}
                        <div className="flex items-center">
                          <div className="text-black dark:text-white opacity-30 mr-2 sm:mr-4">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 sm:h-14 sm:w-14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[8px] sm:text-xs font-medium uppercase tracking-wider text-gray-700 dark:text-gray-400 mb-0.5 sm:mb-1">ACCEPTED PAPERS</span>
                            <span className="text-lg sm:text-4xl font-bold text-gray-700 dark:text-white leading-none">{kpis.totalPapers}</span>
                          </div>
                        </div>
                        
                        {/* Spotlights */}
                        <div className="flex items-center">
                          <div className="text-black dark:text-white opacity-30 mr-2 sm:mr-4">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 sm:h-14 sm:w-14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[8px] sm:text-xs font-medium uppercase tracking-wider text-gray-700 dark:text-gray-400 mb-0.5 sm:mb-1">SPOTLIGHTS</span>
                            <span className="text-lg sm:text-4xl font-bold text-gray-700 dark:text-white leading-none">{kpis.spotlightCount}</span>
                          </div>
                        </div>
                        
                        {/* Authors */}
                        <div className="flex items-center">
                          <div className="text-black dark:text-white opacity-30 mr-2 sm:mr-4">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 sm:h-14 sm:w-14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                            </svg>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[8px] sm:text-xs font-medium uppercase tracking-wider text-gray-700 dark:text-gray-400 mb-0.5 sm:mb-1">AUTHORS</span>
                            <span className="text-lg sm:text-4xl font-bold text-gray-700 dark:text-white leading-none">{kpis.authorCount}</span>
                          </div>
                        </div>
                        
                        {/* Global Rank */}
                        <div className="flex items-center">
                          <div className="text-black dark:text-white opacity-30 mr-2 sm:mr-4">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 sm:h-14 sm:w-14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                            </svg>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[8px] sm:text-xs font-medium uppercase tracking-wider text-gray-700 dark:text-gray-400 mb-0.5 sm:mb-1">GLOBAL RANK</span>
                            <span className="text-lg sm:text-4xl font-bold text-gray-700 dark:text-white leading-none">#{kpis.indiaRank}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-6">
                    {papersToShow.map((paper) => (
                      <PaperCard key={paper.paper_id} paper={paper} />
                    ))}
                  </div>
                  
                  {hasMorePapers && (
                    <div className="mt-2 sm:mt-3 ml-1 sm:ml-2">
                      <button
                        onClick={() => toggleConferenceExpansion(conferenceKey)}
                        className="text-xs sm:text-sm text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 
                                  underline focus:outline-none transition-colors"
                        aria-expanded={isExpanded}
                      >
                        {isExpanded ? `Show less papers` : `See more papers (${papers.length - papersToShow.length} more)`}
                      </button>
                    </div>
                  )}

                  {/* Show collapse button at the bottom when expanded */}
                  {isExpanded && papers.length > 6 && (
                    <div className="mt-4 sm:mt-6 mb-2 sm:mb-3 ml-1 sm:ml-2">
                      <button
                        onClick={() => toggleConferenceExpansion(conferenceKey)}
                        className="text-xs sm:text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 
                                  underline focus:outline-none transition-colors"
                      >
                        Collapse Section
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ))
      ) : (
        <div className="col-span-full text-center py-10">
          <p className="text-lg font-medium text-gray-500 dark:text-gray-400">No papers match your filters.</p>
        </div>
      )}
    </div>
  )
}
