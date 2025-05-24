// src/hooks/use-dashboard-data.ts

import { useState, useEffect, useMemo } from 'react';
import { 
  DashboardDataInterface, 
  CountryData, 
  ProcessedFocusCountryData,
  ColorMapInterface 
} from '../types/dashboard';
import { fetchDashboardData } from '../services/dashboard-api';
import { 
  processSortedCountries, 
  processFocusCountryData,
  createColorMap
} from '../utils/data-transformers';

interface UseDashboardDataProps {
  conference: string;
  year: string;
}

interface UseDashboardDataReturn {
  data: DashboardDataInterface | null;
  loading: boolean;
  error: string | null;
  sortedCountries: CountryData[];
  topCountriesByPaper: CountryData[];
  usData: CountryData | undefined;
  cnData: CountryData | undefined;
  focusCountryGlobalStats: CountryData | undefined;
  processedFocusData: ProcessedFocusCountryData | null;
  colorMap: ColorMapInterface | null;
}

export const useDashboardData = ({ 
  conference, 
  year 
}: UseDashboardDataProps): UseDashboardDataReturn => {
  // State
  const [data, setData] = useState<DashboardDataInterface | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch data effect
  useEffect(() => {
    const fetchData = async () => {
      if (!conference || !year) {
        setLoading(false);
        setError("Conference and year must be selected.");
        return;
      }
      
      setLoading(true);
      setError(null);
      setData(null);
      
      try {
        const dashboardData = await fetchDashboardData(conference, year);
        setData(dashboardData);
      } catch (e: any) {
        console.error("Dashboard data fetching error:", e);
        setError(e.message || "An unknown error occurred.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [conference, year]);
  
  // Derived state
  const sortedCountries = useMemo(() => {
    if (!data) return [];
    
    return processSortedCountries(
      data.globalStats,
      data.configuration,
      data.focusCountry.country_code
    );
  }, [data]);
  
  const topCountriesByPaper = useMemo(() => 
    sortedCountries.slice(0, 15), 
    [sortedCountries]
  );
  
  const usData = useMemo(() => 
    sortedCountries.find((c) => c.affiliation_country === "US"),
    [sortedCountries]
  );
  
  const cnData = useMemo(() => 
    sortedCountries.find((c) => c.affiliation_country === "CN"),
    [sortedCountries]
  );
  
  const focusCountryGlobalStats = useMemo(() => {
    const focusCode = data?.focusCountry?.country_code;
    if (!focusCode) return undefined;
    return sortedCountries.find((c) => c.affiliation_country === focusCode);
  }, [sortedCountries, data?.focusCountry?.country_code]);
  
  const processedFocusData = useMemo(() => {
    if (!focusCountryGlobalStats || !data?.focusCountry) return null;
    
    return processFocusCountryData(
      data.focusCountry,
      focusCountryGlobalStats
    );
  }, [focusCountryGlobalStats, data?.focusCountry]);
  
  const colorMap = useMemo(() => {
    if (!data?.configuration?.colorScheme) return null;
    return createColorMap(data.configuration.colorScheme);
  }, [data?.configuration?.colorScheme]);
  
  return {
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
  };
};
