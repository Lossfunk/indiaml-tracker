"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Checkbox } from "@/components/ui/checkbox"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { ChevronDown, Search, Filter, Users, User, X, Menu, Calendar } from "lucide-react"

interface FilterBarProps {
  searchTerm: string
  setSearchTerm: (value: string) => void
  isFirstAuthorIndian: boolean
  setIsFirstAuthorIndian: (value: boolean) => void
  isMajorityAuthorsIndian: boolean
  setIsMajorityAuthorsIndian: (value: boolean) => void
  selectedConferences: string[]
  setSelectedConferences: (value: string[]) => void
}

interface ConferenceIndex {
  label: string
  file: string
  analytics: string
  venue: string
  year: string
  sqlite_file: string
}

interface Conference {
  id: string
  label: string
  year: number
  venue: string
  file: string
}

interface ConferenceYearFilterProps {
  conferences: Conference[]
  selectedConferences: string[]
  onToggleConference: (conference: Conference) => void
}

function ConferenceYearFilter({ conferences, selectedConferences, onToggleConference }: ConferenceYearFilterProps) {
  const [activeTab, setActiveTab] = useState<'by-conference' | 'by-year'>('by-conference')
  const [expandedVenues, setExpandedVenues] = useState<Set<string>>(new Set())
  const [expandedYears, setExpandedYears] = useState<Set<number>>(new Set())

  // Group conferences by venue
  const conferencesByVenue = conferences.reduce((acc, conf) => {
    if (!acc[conf.venue]) {
      acc[conf.venue] = []
    }
    acc[conf.venue].push(conf)
    return acc
  }, {} as Record<string, Conference[]>)

  // Group conferences by year
  const conferencesByYear = conferences.reduce((acc, conf) => {
    if (!acc[conf.year]) {
      acc[conf.year] = []
    }
    acc[conf.year].push(conf)
    return acc
  }, {} as Record<number, Conference[]>)

  // Sort venues by priority
  const venuePriority: Record<string, number> = {
    'neurips': 3,
    'icml': 2,
    'iclr': 1
  }

  const sortedVenues = Object.keys(conferencesByVenue).sort((a, b) => {
    const aPriority = venuePriority[a.toLowerCase()] || 0
    const bPriority = venuePriority[b.toLowerCase()] || 0
    return bPriority - aPriority
  })

  const sortedYears = Object.keys(conferencesByYear)
    .map(Number)
    .sort((a, b) => b - a)

  // Toggle functions for expand/collapse
  const toggleVenueExpansion = (venue: string) => {
    setExpandedVenues(prev => {
      const newSet = new Set(prev)
      if (newSet.has(venue)) {
        newSet.delete(venue)
      } else {
        newSet.add(venue)
      }
      return newSet
    })
  }

  const toggleYearExpansion = (year: number) => {
    setExpandedYears(prev => {
      const newSet = new Set(prev)
      if (newSet.has(year)) {
        newSet.delete(year)
      } else {
        newSet.add(year)
      }
      return newSet
    })
  }

  // Helper functions for bulk selection
  const handleSelectAllVenue = (venue: string) => {
    const venueConferences = conferencesByVenue[venue]
    const allSelected = venueConferences.every(conf => 
      selectedConferences.includes(`${conf.id}-${conf.year}`)
    )
    
    if (allSelected) {
      // Deselect all conferences for this venue
      venueConferences.forEach(conf => {
        const conferenceKey = `${conf.id}-${conf.year}`
        if (selectedConferences.includes(conferenceKey)) {
          onToggleConference(conf)
        }
      })
    } else {
      // Select all conferences for this venue
      venueConferences.forEach(conf => {
        const conferenceKey = `${conf.id}-${conf.year}`
        if (!selectedConferences.includes(conferenceKey)) {
          onToggleConference(conf)
        }
      })
    }
  }

  const handleSelectAllYear = (year: number) => {
    const yearConferences = conferencesByYear[year]
    const allSelected = yearConferences.every(conf => 
      selectedConferences.includes(`${conf.id}-${conf.year}`)
    )
    
    if (allSelected) {
      // Deselect all conferences for this year
      yearConferences.forEach(conf => {
        const conferenceKey = `${conf.id}-${conf.year}`
        if (selectedConferences.includes(conferenceKey)) {
          onToggleConference(conf)
        }
      })
    } else {
      // Select all conferences for this year
      yearConferences.forEach(conf => {
        const conferenceKey = `${conf.id}-${conf.year}`
        if (!selectedConferences.includes(conferenceKey)) {
          onToggleConference(conf)
        }
      })
    }
  }

  return (
    <div className="p-2">
      {/* Tab Navigation */}
      <div className="flex mb-3 bg-gray-800 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('by-conference')}
          className={`flex-1 px-3 py-1.5 text-xs rounded-md transition-colors ${
            activeTab === 'by-conference'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <Filter className="h-3 w-3 inline mr-1" />
          By Conference
        </button>
        <button
          onClick={() => setActiveTab('by-year')}
          className={`flex-1 px-3 py-1.5 text-xs rounded-md transition-colors ${
            activeTab === 'by-year'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <Calendar className="h-3 w-3 inline mr-1" />
          By Year
        </button>
      </div>

      {/* Content based on active tab */}
      <div className="max-h-64 overflow-y-auto">
        {activeTab === 'by-conference' ? (
          <div className="space-y-2">
            {sortedVenues.map((venue) => {
              const venueConferences = conferencesByVenue[venue].sort((a, b) => b.year - a.year)
              const selectedCount = venueConferences.filter(conf => 
                selectedConferences.includes(`${conf.id}-${conf.year}`)
              ).length
              const allSelected = selectedCount === venueConferences.length
              const someSelected = selectedCount > 0 && selectedCount < venueConferences.length
              const isExpanded = expandedVenues.has(venue)
              
              return (
                <div key={venue} className="border border-gray-700 rounded-lg">
                  {/* Conference header with bulk select and expand/collapse */}
                  <div className="flex items-center justify-between p-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={`venue-${venue}`}
                        checked={allSelected}
                        ref={(el) => {
                          if (el) {
                            const input = el.querySelector('input')
                            if (input) input.indeterminate = someSelected
                          }
                        }}
                        onCheckedChange={() => handleSelectAllVenue(venue)}
                        className="border-white"
                      />
                      <button
                        onClick={() => toggleVenueExpansion(venue)}
                        className="flex items-center space-x-1 text-sm font-semibold text-gray-200 hover:text-white transition-colors"
                      >
                        <span>{venue.toUpperCase()} (All Years)</span>
                        <ChevronDown 
                          className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                        />
                      </button>
                    </div>
                    {selectedCount > 0 && (
                      <span className="text-xs bg-purple-500 text-white rounded-full px-2 py-0.5">
                        {selectedCount}/{venueConferences.length}
                      </span>
                    )}
                  </div>
                  
                  {/* Collapsible year selections */}
                  {isExpanded && (
                    <div className="px-2 pb-2 ml-6 space-y-1 border-t border-gray-600 pt-2">
                      {venueConferences.map((conference) => {
                        const conferenceKey = `${conference.id}-${conference.year}`
                        return (
                          <div key={conferenceKey} className="flex items-center space-x-2">
                            <Checkbox
                              id={conferenceKey}
                              checked={selectedConferences.includes(conferenceKey)}
                              onCheckedChange={() => onToggleConference(conference)}
                              className="border-white"
                            />
                            <label
                              htmlFor={conferenceKey}
                              className="text-xs text-gray-300 cursor-pointer"
                            >
                              {conference.year}
                            </label>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <div className="space-y-2">
            {sortedYears.map((year) => {
              const yearConferences = conferencesByYear[year].sort((a, b) => {
                const aPriority = venuePriority[a.venue.toLowerCase()] || 0
                const bPriority = venuePriority[b.venue.toLowerCase()] || 0
                return bPriority - aPriority
              })
              const selectedCount = yearConferences.filter(conf => 
                selectedConferences.includes(`${conf.id}-${conf.year}`)
              ).length
              const allSelected = selectedCount === yearConferences.length
              const someSelected = selectedCount > 0 && selectedCount < yearConferences.length
              const isExpanded = expandedYears.has(year)
              
              return (
                <div key={year} className="border border-gray-700 rounded-lg">
                  {/* Year header with bulk select and expand/collapse */}
                  <div className="flex items-center justify-between p-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={`year-${year}`}
                        checked={allSelected}
                        ref={(el) => {
                          if (el) {
                            const input = el.querySelector('input')
                            if (input) input.indeterminate = someSelected
                          }
                        }}
                        onCheckedChange={() => handleSelectAllYear(year)}
                        className="border-white"
                      />
                      <button
                        onClick={() => toggleYearExpansion(year)}
                        className="flex items-center space-x-1 text-sm font-semibold text-gray-200 hover:text-white transition-colors"
                      >
                        <span>{year} (All Conferences)</span>
                        <ChevronDown 
                          className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                        />
                      </button>
                    </div>
                    {selectedCount > 0 && (
                      <span className="text-xs bg-purple-500 text-white rounded-full px-2 py-0.5">
                        {selectedCount}/{yearConferences.length}
                      </span>
                    )}
                  </div>
                  
                  {/* Collapsible conference selections */}
                  {isExpanded && (
                    <div className="px-2 pb-2 ml-6 space-y-1 border-t border-gray-600 pt-2">
                      {yearConferences.map((conference) => {
                        const conferenceKey = `${conference.id}-${conference.year}`
                        return (
                          <div key={conferenceKey} className="flex items-center space-x-2">
                            <Checkbox
                              id={conferenceKey}
                              checked={selectedConferences.includes(conferenceKey)}
                              onCheckedChange={() => onToggleConference(conference)}
                              className="border-white"
                            />
                            <label
                              htmlFor={conferenceKey}
                              className="text-xs text-gray-300 cursor-pointer"
                            >
                              {conference.label.toUpperCase()}
                            </label>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export function FilterBar({
  searchTerm,
  setSearchTerm,
  isFirstAuthorIndian,
  setIsFirstAuthorIndian,
  isMajorityAuthorsIndian,
  setIsMajorityAuthorsIndian,
  selectedConferences,
  setSelectedConferences,
}: FilterBarProps) {
  const [conferences, setConferences] = useState<Conference[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [isSearchExpanded, setIsSearchExpanded] = useState(false)
  const [isFilterExpanded, setIsFilterExpanded] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Check if mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Fetch conference data from index.json
  useEffect(() => {
    async function fetchConferenceIndex() {
      try {
        const response = await fetch('/tracker_v2/index.json')
        if (!response.ok) {
          throw new Error('Failed to fetch conference index')
        }
        const data = await response.json() as ConferenceIndex[]

        // Transform the v2 data to match our Conference interface
        const transformedData = data.map((item: ConferenceIndex) => {
          // Use the venue and year directly from the v2 structure
          const year = parseInt(item.year, 10)
          const venue = item.venue.toLowerCase()

          return {
            id: venue,
            label: item.venue.toUpperCase(),
            year: year,
            venue: item.venue,
            file: item.file
          }
        })

        // Sort conferences by year (descending) and then by venue priority
        const venuePriority: Record<string, number> = {
          'neurips': 3,
          'icml': 2,
          'iclr': 1
        }

        transformedData.sort((a, b) => {
          // First sort by year (descending)
          if (a.year !== b.year) {
            return b.year - a.year
          }
          // Then by venue priority
          const aPriority = venuePriority[a.venue.toLowerCase()] || 0
          const bPriority = venuePriority[b.venue.toLowerCase()] || 0
          return bPriority - aPriority
        })

        setConferences(transformedData)
        setLoading(false)
      } catch (error) {
        console.error("Error fetching conference index:", error)
        setLoading(false)
      }
    }

    fetchConferenceIndex()
  }, [])

  // Toggles a conference (using a composite key of id and year) in or out of the selectedConferences array
  const handleConferenceToggle = (conference: Conference) => {
    const conferenceKey = `${conference.id}-${conference.year}`
    const newSelectedConferences = selectedConferences.includes(conferenceKey)
      ? selectedConferences.filter((c: string) => c !== conferenceKey)
      : [...selectedConferences, conferenceKey]
    setSelectedConferences(newSelectedConferences)
  }

  if (!isMobile) {
    // Desktop layout - simplified design
    return (
      <motion.div
        className="
          relative flex items-center gap-4 p-4 rounded-lg shadow-md border 
          bg-gradient-to-r dark:from-gray-900 dark:via-black dark:to-gray-900
          from-gray-200 to-slate-200 
          text-gray-100
        "
        initial={{ opacity: 0, y: 25 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        {/* Search Field with an icon and motion */}
        <motion.div
          className="flex items-center space-x-2 flex-grow"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <Search className="h-5 w-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Search Indian AI/ML papers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-grow min-w-[200px] bg-white/10 
                       placeholder:text-gray-400 
                       focus:ring-2 focus:ring-pink-500 focus:outline-none"
          />
        </motion.div>

        {/* Conference Filter Dropdown */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <Popover open={isOpen} onOpenChange={setIsOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[180px] justify-between text-gray-900 dark:text-gray-300">
                <Filter className="mr-2 h-4 w-4" />
                Filter ({selectedConferences.length})
                <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[320px] px-1 py-2 bg-black border border-white/20 text-gray-100">
              {loading ? (
                <div className="p-4 text-sm text-gray-400">Loading conferences...</div>
              ) : (
                <ConferenceYearFilter 
                  conferences={conferences}
                  selectedConferences={selectedConferences}
                  onToggleConference={handleConferenceToggle}
                />
              )}
            </PopoverContent>
          </Popover>
        </motion.div>

        {/* Hamburger menu for additional options */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <Popover open={isFilterExpanded} onOpenChange={setIsFilterExpanded}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="p-2 text-gray-900 dark:text-gray-300">
                <Menu className="h-4 w-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[250px] px-1 py-2 bg-black border border-white/20 text-gray-100">
              <div className="p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="first-author-desktop" className="text-sm text-gray-300">
                    First Author Indian
                  </Label>
                  <Switch
                    id="first-author-desktop"
                    checked={isFirstAuthorIndian}
                    onCheckedChange={setIsFirstAuthorIndian}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="majority-authors-desktop" className="text-sm text-gray-300">
                    Majority Authors Indian
                  </Label>
                  <Switch
                    id="majority-authors-desktop"
                    checked={isMajorityAuthorsIndian}
                    onCheckedChange={setIsMajorityAuthorsIndian}
                  />
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </motion.div>
      </motion.div>
    )
  }

  // Mobile layout - search bar, filter, and menu
  return (
    <TooltipProvider>
      <motion.div
        className="
          relative w-full bg-gradient-to-r dark:from-gray-900 dark:via-black dark:to-gray-900
          from-gray-200 to-slate-200 border rounded-lg shadow-md
        "
        initial={{ opacity: 0, y: 25 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        {/* Main row with search bar and action buttons */}
        <div className="flex items-center gap-2 p-3">
          {/* Search Field */}
          <div className="flex items-center space-x-2 flex-grow">
            <Search className="h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search Indian AI/ML papers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-grow bg-white/10 placeholder:text-gray-400 
                         focus:ring-2 focus:ring-pink-500 focus:outline-none"
            />
          </div>

          {/* Conferences filter */}
          <Popover open={isOpen} onOpenChange={setIsOpen}>
            <Tooltip>
              <TooltipTrigger asChild>
                <PopoverTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`p-2 transition-colors ${
                      selectedConferences.length > 0 
                        ? 'bg-purple-500/20 text-purple-400' 
                        : 'text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    <Filter className="h-4 w-4" />
                    {selectedConferences.length > 0 && (
                      <span className="ml-1 text-xs bg-purple-500 text-white rounded-full px-1">
                        {selectedConferences.length}
                      </span>
                    )}
                  </Button>
                </PopoverTrigger>
              </TooltipTrigger>
              <TooltipContent>
                <p>Filter conferences ({selectedConferences.length} selected)</p>
              </TooltipContent>
            </Tooltip>
            <PopoverContent className="w-[200px] px-1 py-2 bg-black border border-white/20 text-gray-100">
              <div className="p-2 flex flex-col space-y-2">
                {loading ? (
                  <div className="text-sm text-gray-400">Loading conferences...</div>
                ) : (
                  conferences.map((conference) => {
                    const conferenceKey = `${conference.id}-${conference.year}`
                    return (
                      <div key={conferenceKey} className="flex items-center space-x-2">
                        <Checkbox
                          id={conferenceKey}
                          checked={selectedConferences.includes(conferenceKey)}
                          onCheckedChange={() => handleConferenceToggle(conference)}
                          className="border-white"
                        />
                        <label
                          htmlFor={conferenceKey}
                          className="text-sm font-medium leading-none 
                                   peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                          {`${conference.label.toUpperCase()} (${conference.year})`}
                        </label>
                      </div>
                    )
                  })
                )}
              </div>
            </PopoverContent>
          </Popover>

          {/* Hamburger menu for additional options */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsFilterExpanded(!isFilterExpanded)}
                className="p-2 text-gray-600 dark:text-gray-400"
              >
                {isFilterExpanded ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{isFilterExpanded ? 'Hide filters' : 'Show all filters'}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Expandable detailed filters */}
        <AnimatePresence>
          {isFilterExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="border-t border-gray-300 dark:border-gray-700 px-3 pb-3"
            >
              <div className="pt-3 space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="first-author-mobile" className="text-sm text-gray-800 dark:text-gray-300">
                    First Author Indian
                  </Label>
                  <Switch
                    id="first-author-mobile"
                    checked={isFirstAuthorIndian}
                    onCheckedChange={setIsFirstAuthorIndian}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="majority-authors-mobile" className="text-sm text-gray-800 dark:text-gray-300">
                    Majority Authors Indian
                  </Label>
                  <Switch
                    id="majority-authors-mobile"
                    checked={isMajorityAuthorsIndian}
                    onCheckedChange={setIsMajorityAuthorsIndian}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </TooltipProvider>
  )
}
