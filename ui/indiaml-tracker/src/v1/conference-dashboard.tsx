// src/App.tsx

import React, { useState, useCallback } from 'react';
import { DashboardProvider } from './contexts/dashboard-context';
import { ConferenceSelector } from './components/dashboard/conference-selector';
import { useDashboardData } from './hooks/use-dashboard-data';
import { createColorMap } from './utils/data-transformers';
import { ConferenceDashboard } from './components/dashboard/conference-dashboard';

const App: React.FC = () => {
  // State for selected conference and year
  const [currentConference, setCurrentConference] = useState<string>("");
  const [currentYear, setCurrentYear] = useState<string>("");
  
  // Handler for conference selector changes
  const handleConferenceChange = useCallback((conference: string, year: string) => {
    setCurrentConference(conference);
    setCurrentYear(year);
  }, []);
  
  // Fetch and process dashboard data
  const {
    data,
    loading,
    error,
    sortedCountries,
    topCountriesByPaper,
    usData,
    cnData,
    focusCountryGlobalStats,
    processedFocusData,
    colorMap
  } = useDashboardData({
    conference: currentConference,
    year: currentYear
  });
  
  // Create context value
  const contextValue = {
    conference: currentConference,
    year: currentYear,
    data,
    loading,
    error,
    colorMap: colorMap || createColorMap({} as any)
  };
  
  // Show loading state if no conference selected yet
  if (!currentConference || !currentYear) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center">
          <ConferenceSelector onSelectionChange={handleConferenceChange} />
          <p className="mt-4 text-muted-foreground">
            Please select a conference to access analytics dashboard
          </p>
        </div>
      </div>
    );
  }
  
  // Render the dashboard with all data
  return (
    <DashboardProvider value={contextValue}>
      <ConferenceDashboard 
        loading={loading}
        error={error}
        data={data}
        sortedCountries={sortedCountries}
        topCountriesByPaper={topCountriesByPaper}
        usData={usData}
        cnData={cnData}
        focusCountryGlobalStats={focusCountryGlobalStats}
        processedFocusData={processedFocusData}
        conferenceSelectorElement={
          <ConferenceSelector 
            onSelectionChange={handleConferenceChange}
            initialConference={currentConference}
            initialYear={currentYear}
          />
        }
      />
    </DashboardProvider>
  );
};

export default App;
