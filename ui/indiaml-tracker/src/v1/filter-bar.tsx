import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Checkbox } from "@/components/ui/checkbox"
import { ChevronDown } from "lucide-react"

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
  const conferences = ["neurips", "icml"]
  const [isOpen, setIsOpen] = useState(false)

  const handleConferenceToggle = (conference: string) => {
    setSelectedConferences((prev) =>
      prev.includes(conference) ? prev.filter((c) => c !== conference) : [...prev, conference],
    )
  }

  return (
    <div className="flex flex-wrap items-center gap-4 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
      <Input
        type="text"
        placeholder="Search papers..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="flex-grow min-w-[200px]"
      />
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <Switch id="first-author" checked={isFirstAuthorIndian} onCheckedChange={setIsFirstAuthorIndian} />
          <Label htmlFor="first-author" className="text-sm text-gray-600">
            First author Indian
          </Label>
        </div>
        <div className="flex items-center space-x-2">
          <Switch
            id="majority-authors"
            checked={isMajorityAuthorsIndian}
            onCheckedChange={setIsMajorityAuthorsIndian}
          />
          <Label htmlFor="majority-authors" className="text-sm text-gray-600">
            Majority authors Indian
          </Label>
        </div>
      </div>
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-[180px] justify-between">
            Conferences
            <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[180px] p-0">
          <div className="p-2">
            {conferences.map((conference) => (
              <div key={conference} className="flex items-center space-x-2 mb-2">
                <Checkbox
                  id={conference}
                  checked={selectedConferences.includes(conference)}
                  onCheckedChange={() => handleConferenceToggle(conference)}
                />
                <label
                  htmlFor={conference}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {conference}
                </label>
              </div>
            ))}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}

