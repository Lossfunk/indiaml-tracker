// src/components/dashboard/ConferenceSelector.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { TrackerIndexEntry } from '../../types/dashboard';
import { fetchConferenceOptions, getUrlParameters, updateUrlParameters } from '../../services/dashboard-api';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FiFilter } from 'react-icons/fi';

interface ConferenceSelectorProps {
  onSelectionChange: (conference: string, year: string) => void;
  initialConference?: string;
  initialYear?: string;
}

export const ConferenceSelector: React.FC<ConferenceSelectorProps> = ({
  onSelectionChange,
  initialConference,
  initialYear
}) => {
  // State
  const [options, setOptions] = useState<TrackerIndexEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedValue, setSelectedValue] = useState<string>("");
  
  // Load conference options
  useEffect(() => {
    const loadOptions = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await fetchConferenceOptions();
        setOptions(data);
        
        // Set initial selection from props or URL parameters
        const urlParams = getUrlParameters();
        const conference = initialConference || urlParams.conference;
        const year = initialYear || urlParams.year;
        
        if (conference && year) {
          const matchingOption = data.find(
            (opt) => 
              opt.venue.toLowerCase() === conference.toLowerCase() && 
              opt.year === year
          );
          
          if (matchingOption) {
            setSelectedValue(`${matchingOption.venue}|${matchingOption.year}`);
            onSelectionChange(matchingOption.venue, matchingOption.year);
          } else if (data.length > 0) {
            // Use first option if no match
            setSelectedValue(`${data[0].venue}|${data[0].year}`);
            onSelectionChange(data[0].venue, data[0].year);
          }
        } else if (data.length > 0) {
          // Default to first option
          setSelectedValue(`${data[0].venue}|${data[0].year}`);
          onSelectionChange(data[0].venue, data[0].year);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load conferences");
        console.error("Error loading conference options:", err);
      } finally {
        setLoading(false);
      }
    };
    
    loadOptions();
  }, [initialConference, initialYear, onSelectionChange]);
  
  // Handle conference change - updated for shadcn Select
  const handleChange = useCallback((value: string) => {
    if (value) {
      setSelectedValue(value);
      const [conference, year] = value.split("|");
      onSelectionChange(conference, year);
      updateUrlParameters(conference, year);
    }
  }, [onSelectionChange]);
  
  // Render based on state
  if (loading) {
    return (
      <div className="flex items-center gap-1 sm:gap-2">
        <FiFilter className="h-4 w-4 text-muted-foreground animate-pulse" />
        <p className="text-xs sm:text-sm text-muted-foreground animate-pulse">
          Loading...
        </p>
      </div>
    );
  }
  
  if (error && options.length === 0) {
    return (
      <div className="flex items-center gap-1 sm:gap-2">
        <FiFilter className="h-4 w-4 text-muted-foreground" />
        <p className="text-xs sm:text-sm text-destructive">
          Error loading list!
        </p>
      </div>
    );
  }
  
  if (options.length === 0 && !loading) {
    return (
      <div className="flex items-center gap-1 sm:gap-2">
        <FiFilter className="h-4 w-4 text-muted-foreground" />
        <p className="text-xs sm:text-sm text-muted-foreground">No conferences available</p>
      </div>
    );
  }
  
  return (
    <div className="flex items-center gap-1 sm:gap-2">
      <label
        htmlFor="conference-select"
        className="sr-only text-xs sm:text-sm font-medium text-muted-foreground whitespace-nowrap"
      >
        Data:
      </label>
      <FiFilter className="h-4 w-4 text-muted-foreground" />
      <Select value={selectedValue} onValueChange={handleChange}>
        <SelectTrigger 
          id="conference-select"
          className="bg-card/80 dark:bg-card/50 border-border text-foreground text-xs sm:text-sm rounded-md focus:ring-primary focus:border-primary shadow-sm w-auto"
          aria-label="Select a conference and year"
        >
          <SelectValue placeholder="Select..." />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem
              key={`${option.venue}-${option.year}`}
              value={`${option.venue}|${option.year}`}
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};