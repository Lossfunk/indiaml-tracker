// src/components/dashboard/ConferenceSelector.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { TrackerIndexEntry } from '../../types/dashboard';
import { fetchConferenceOptions, getUrlParameters, updateUrlParameters } from '../../services/dashboard-api';

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
  
  // Handle conference change
  const handleChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
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
      <p className="text-xs sm:text-sm text-muted-foreground animate-pulse">
        Loading...
      </p>
    );
  }
  
  if (error && options.length === 0) {
    return (
      <p className="text-xs sm:text-sm text-destructive">
        Error loading list!
      </p>
    );
  }
  
  if (options.length === 0 && !loading) {
    return <p className="text-xs sm:text-sm text-muted-foreground">No conferences available</p>;
  }
  
  return (
    <div className="flex items-center gap-1 sm:gap-2">
      <label
        htmlFor="conference-select"
        className="sr-only text-xs sm:text-sm font-medium text-muted-foreground whitespace-nowrap"
      >
        Data:
      </label>
      <select
        id="conference-select"
        value={selectedValue}
        onChange={handleChange}
        className="bg-card/80 dark:bg-card/50 border-border text-foreground text-xs sm:text-sm rounded-md focus:ring-primary focus:border-primary p-1.5 sm:p-2 shadow-sm w-auto appearance-none focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-background"
        aria-label="Select a conference and year"
      >
        {!selectedValue && options.length > 0 && (
          <option value="" disabled>
            Select...
          </option>
        )}
        {options.map((option) => (
          <option
            key={`${option.venue}-${option.year}`}
            value={`${option.venue}|${option.year}`}
          >
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};
