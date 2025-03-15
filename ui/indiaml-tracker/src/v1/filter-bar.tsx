"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Checkbox } from "@/components/ui/checkbox"
import { ChevronDown, Search, Filter } from "lucide-react"

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
    setSelectedConferences((prev) =>
      prev.includes(conferenceKey)
        ? prev.filter((c) => c !== conferenceKey)
        : [...prev, conferenceKey]
    )
  }

  return (
    // Outer container with some entry animation
    <motion.div
      className="
        relative flex flex-wrap items-center gap-4 p-4 rounded-lg shadow-md border 
        bg-gradient-to-r from-gray-900 via-black to-gray-900 
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

      {/* Toggles for Indian authors */}
      <motion.div
        className="flex flex-col md:flex-row items-center md:space-x-4 space-y-4 md:space-y-0 justify-start"
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        <div className="flex items-center space-x-2 -ml-8 md:ml-0">
          <Switch
            id="first-author"
            checked={isFirstAuthorIndian}
            onCheckedChange={setIsFirstAuthorIndian}
          />
          <Label htmlFor="first-author" className="text-sm text-gray-300">
            First Author Indian
          </Label>
        </div>
        <div className="flex items-center space-x-2">
          <Switch
            id="majority-authors"
            checked={isMajorityAuthorsIndian}
            onCheckedChange={setIsMajorityAuthorsIndian}
          />
          <Label htmlFor="majority-authors" className="text-sm text-gray-300">
            Majority Authors Indian
          </Label>
        </div>
      </motion.div>

      {/* Conferences dropdown */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.5 }}
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
    </motion.div>
  )
}