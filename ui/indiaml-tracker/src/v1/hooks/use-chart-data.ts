 // src/hooks/use-chart-data.ts

import { useMemo } from 'react';
import { 
  DashboardDataInterface, 
  CountryData,
  ProcessedFocusCountryData,
  ChartDataItem,
  InstitutionData
} from '../types/dashboard';
import {
  createUsChinaDominancePieData,
  createAuthorshipData,
  createInstitutionTypeData,
  filterInstitutions
} from '../utils/data-transformers';

// Hook for context section data
export const useContextSectionData = (
  data: DashboardDataInterface | null,
  sortedCountries: CountryData[],
  usData?: CountryData,
  cnData?: CountryData
) => {
  const usChinaDominancePieData = useMemo(() => {
    if (!data || !usData || !cnData) return [];
    
    return createUsChinaDominancePieData(
      usData,
      cnData,
      data.conferenceInfo.totalAcceptedPapers,
      data.configuration.colorScheme
    );
  }, [data, usData, cnData]);
  
  const apacCountriesData = useMemo(() => {
    if (!data || !sortedCountries.length) return [];
    
    return sortedCountries
      .filter((country) =>
        data.configuration.apacCountries.includes(
          country.affiliation_country
        )
      )
      .sort((a, b) => b.paper_count - a.paper_count);
  }, [data, sortedCountries]);
  
  return {
    usChinaDominancePieData,
    apacCountriesData
  };
};

// Hook for focus country section data
export const useFocusCountrySectionData = (
  data: DashboardDataInterface | null,
  processedFocusData: ProcessedFocusCountryData | null
) => {
  const { majorityMinorityData, firstAuthorData } = useMemo(() => {
    if (!data || !processedFocusData) {
      return { majorityMinorityData: [], firstAuthorData: [] };
    }
    
    return createAuthorshipData(
      processedFocusData,
      data.focusCountry.country_name,
      data.configuration.colorScheme
    );
  }, [data, processedFocusData]);
  
  const { comparisonData, pieData: institutionTypePieData } = useMemo(() => {
    if (!data || !processedFocusData) {
      return { comparisonData: [], pieData: [] };
    }
    
    return createInstitutionTypeData(
      processedFocusData,
      data.configuration.colorScheme
    );
  }, [data, processedFocusData]);
  
  return {
    authorshipMajorityMinorityData: majorityMinorityData,
    authorshipFirstAuthorData: firstAuthorData,
    institutionTypeComparisonData: comparisonData,
    institutionTypePieData
  };
};

// Hook for institutions section data
export const useInstitutionSectionData = (
  processedFocusData: ProcessedFocusCountryData | null,
  institutionFilter: string
) => {
  const filteredInstitutions = useMemo(() => {
    if (!processedFocusData?.institutions) return [];
    
    return filterInstitutions(
      processedFocusData.institutions,
      institutionFilter
    );
  }, [processedFocusData, institutionFilter]);
  
  const topInstitutions = useMemo(() => 
    filteredInstitutions.slice(0, 8),
    [filteredInstitutions]
  );
  
  return {
    filteredInstitutions,
    topInstitutions
  };
};
