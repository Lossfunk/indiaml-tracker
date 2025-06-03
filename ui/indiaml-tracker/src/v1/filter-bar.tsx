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
import { ChevronDown, Search, Filter, Users, User, X, Menu } from "lucide-react"

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

interface Conference {
  id: string
  label: string
  year: number
  file: string // Added to store the original filename
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
        const response = await fetch('/tracker/index.json')
        if (!response.ok) {
          throw new Error('Failed to fetch conference index')
        }
        const data = await response.json()

        // Transform the data to match our Conference interface
        const transformedData = data.map((item: { label: string, file: string }) => {
          // Parse the label to extract conference name and year
          // Assuming format like "ICLR 2024"
          const labelParts = item.label.split(' ')
          const year = parseInt(labelParts[labelParts.length - 1], 10)
          const id = labelParts[0].toLowerCase().replace('-', '')

          return {
            id,
            label: labelParts[0],
            year,
            file: item.file
          }
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

        {/* Conferences dropdown */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <Popover open={isOpen} onOpenChange={setIsOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[180px] justify-between text-gray-900 dark:text-gray-300">
                <Filter className="mr-2 h-4 w-4" />
                Conferences
                <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[180px] px-1 py-2 bg-black border border-white/20 text-gray-100">
              <div className="p-2 flex flex-col space-y-2">
                {loading ? (
                  <div className="text-sm text-gray-400">Loading conferences...</div>
                ) : (
                  conferences.map((conference) => {
                    const conferenceKey = `${conference.id}-${conference.year}`
                    return (
                      <div key={conferenceKey} className="flex items-center space-x-2 mb-">
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
