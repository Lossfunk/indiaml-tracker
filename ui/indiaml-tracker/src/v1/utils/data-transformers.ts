// src/utils/dataTransformers.ts

import { chartColors, colorSchemes } from './chart-colors';
import {
    CountryData,
    DashboardDataInterface,
    InstitutionData,
    ProcessedFocusCountryData,
    ChartDataItem,
    ColorMapInterface
  } from "../types/dashboard";
  
  /**
   * Normalizes values in a data array by a specified key
   * @param data Array of data items
   * @param key The property to normalize
   * @returns Array with normalized values added
   */
  export const normalizeValues = <T extends Record<string, any>>(data: T[], key: string): T[] => {
    if (!data || data.length === 0) return [];
    
    const values = data.map((item) => item[key] || 0);
    if (values.length === 0) {
      return data.map((item) => ({ 
        ...item, 
        [`normalized_${key}`]: 0 
      }));
    }
  
    const maxValue = Math.max(...values);
    return data.map((item) => ({
      ...item,
      [`normalized_${key}`]: maxValue > 0 ? (item[key] || 0) / maxValue : 0,
    }));
  };
  
  /**
   * Processes raw country data from the API response
   */
  export const processSortedCountries = (
    globalStats: DashboardDataInterface['globalStats'],
    configuration: DashboardDataInterface['configuration'],
    focusCountryCode: string
  ): CountryData[] => {
    if (
      !globalStats?.countries ||
      !configuration?.countryMap
    ) {
      return [];
    }
  
    const currentCountryMap = new Map<string, CountryData>();
    
    globalStats.countries.forEach((rawCountry) => {
      const countryCode = rawCountry.affiliation_country;
      const countryName =
        countryCode === "UK" || countryCode === "GB"
          ? configuration.countryMap["GB"] || "United Kingdom"
          : configuration.countryMap[countryCode] || countryCode;
  
      const existing = currentCountryMap.get(countryName);
      const paperCount = rawCountry.paper_count || 0;
      const authorCount = rawCountry.author_count || 0;
      const spotlights = rawCountry.spotlights || 0;
      const orals = rawCountry.orals || 0;
  
      if (existing) {
        existing.paper_count += paperCount;
        existing.author_count += authorCount;
        existing.spotlights += spotlights;
        existing.orals += orals;
      } else {
        currentCountryMap.set(countryName, {
          affiliation_country: countryCode === "UK" ? "GB" : countryCode,
          country_name: countryName,
          paper_count: paperCount,
          author_count: authorCount,
          spotlights: spotlights,
          orals: orals,
          rank: 0,
          isHighlight:
            countryCode === "US" ||
            countryCode === "CN" ||
            countryCode === focusCountryCode,
        });
      }
    });
  
    const sorted = Array.from(currentCountryMap.values()).sort(
      (a, b) => b.paper_count - a.paper_count || b.author_count - a.author_count
    );
  
    sorted.forEach((country, index) => {
      country.rank = index + 1;
      country.spotlight_oral_rate =
        country.paper_count > 0
          ? (country.spotlights + country.orals) / country.paper_count
          : 0;
      country.authors_per_paper =
        country.paper_count > 0
          ? country.author_count / country.paper_count
          : 0;
    });
  
    const normalizedPapers = normalizeValues(sorted, "paper_count");
    return normalizeValues(normalizedPapers, "author_count");
  };
  
  /**
   * Process focus country data by combining with global stats
   */
  export const processFocusCountryData = (
    focusCountry: DashboardDataInterface['focusCountry'],
    focusCountryGlobalStats: CountryData | undefined
  ): ProcessedFocusCountryData | null => {
    if (!focusCountryGlobalStats || !focusCountry) return null;
    
    const institutions = (focusCountry.institutions || []).map((inst) => ({
      ...inst,
      authors_per_paper:
        inst.unique_paper_count > 0
          ? inst.author_count / inst.unique_paper_count
          : 0,
      impact_score: (inst.spotlights ?? 0) + (inst.orals ?? 0),
      authors: inst.authors || [],
    }));
    
    const normalizedInstitutions = normalizeValues(
      institutions,
      "unique_paper_count"
    );
    
    const processedInstitutions = normalizeValues(
      normalizedInstitutions,
      "author_count"
    );
    
    const data: ProcessedFocusCountryData = {
      ...focusCountry,
      institutions: processedInstitutions,
      rank: focusCountryGlobalStats.rank,
      paper_count: focusCountryGlobalStats.paper_count,
      author_count: focusCountryGlobalStats.author_count,
      spotlights: focusCountryGlobalStats.spotlights,
      orals: focusCountryGlobalStats.orals,
      spotlight_oral_rate: focusCountryGlobalStats.spotlight_oral_rate ?? 0,
      authors_per_paper: focusCountryGlobalStats.authors_per_paper ?? 0,
    };
    
    return data;
  };
  
  /**
   * Generate data for US-China scientific contribution comparative analysis
   */
  export const createUsChinaDominancePieData = (
    usData: CountryData | undefined,
    cnData: CountryData | undefined,
    totalPapers: number,
    colorScheme: DashboardDataInterface['configuration']['colorScheme']
  ): ChartDataItem[] => {
    if (!usData || !cnData || !totalPapers || !colorScheme) return [];
    
    if (totalPapers === 0) return [];
    
    const usCount = usData.paper_count;
    const cnCount = cnData.paper_count;
    const restCount = Math.max(0, totalPapers - usCount - cnCount);
    
    return [
      {
        name: "United States",
        value: usCount,
        percent: usCount / totalPapers,
        fill: colorScheme.us,
      },
      {
        name: "China",
        value: cnCount,
        percent: cnCount / totalPapers,
        fill: colorScheme.cn,
      },
      {
        name: "Rest",
        value: restCount,
        percent: restCount / totalPapers,
        fill: colorScheme.rest || "hsl(var(--muted))",
      },
    ];
  };
  
  /**
   * Generate comprehensive publication authorship composition analytics
   */
  export const createAuthorshipData = (
    processedFocusData: ProcessedFocusCountryData | null,
    focusCountryName: string = "Focus Country",
    colorScheme?: DashboardDataInterface['configuration']['colorScheme']
  ): {
    majorityMinorityData: ChartDataItem[],
    firstAuthorData: ChartDataItem[]
  } => {
    // Default empty arrays
    const emptyResult = {
      majorityMinorityData: [],
      firstAuthorData: []
    };
  
    if (!processedFocusData) return emptyResult;
    
    const totalWithFocusCountry =
      processedFocusData.at_least_one_focus_country_author?.count ?? 0;
      
    if (totalWithFocusCountry === 0) return emptyResult;
    
    // Create majority/minority data
    const majorityFocusCountry =
      processedFocusData.majority_focus_country_authors?.count ?? 0;
      
    const minorityFocusCountry = Math.max(
      0,
      totalWithFocusCountry - majorityFocusCountry
    );
    
    const majorityMinorityData = [
      {
        name: `Primary ${focusCountryName} Authorship`,
        value: majorityFocusCountry,
        fill: colorScheme?.focusCountry || "hsl(142, 71%, 45%)",
      },
      {
        name: `Collaborative ${focusCountryName} Contribution`,
        value: minorityFocusCountry,
        fill: colorScheme?.secondary || "hsl(var(--secondary-foreground))",
      },
    ];
    
    // Create first author data
    const firstAuthorFocusCountry =
      processedFocusData.first_focus_country_author?.count ?? 0;
      
    const nonFirstAuthorFocusCountry = Math.max(
      0,
      totalWithFocusCountry - firstAuthorFocusCountry
    );
    
    const firstAuthorData = [
      {
        name: `${focusCountryName} Principal Investigator`,
        value: firstAuthorFocusCountry,
        fill: colorScheme?.primary || "hsl(330, 80%, 60%)",
      },
      {
        name: "Secondary Contributor",
        value: nonFirstAuthorFocusCountry,
        fill: colorScheme?.warning || "hsl(36, 96%, 50%)",
      },
    ];
    
    return {
      majorityMinorityData,
      firstAuthorData
    };
  };
  
  /**
   * Generate institutional affiliation classification analytics
   */
  export const createInstitutionTypeData = (
    processedFocusData: ProcessedFocusCountryData | null,
    colorScheme: DashboardDataInterface['configuration']['colorScheme']
  ): {
   comparisonData: Array<{ type: string; Publications: number; "Distinguished Publications": number }>,
   pieData: ChartDataItem[]
  } => {
    // Default empty arrays
    const emptyResult = {
      comparisonData: [],
      pieData: []
    };
  
    if (
      !processedFocusData?.institutions ||
      !processedFocusData?.institution_types ||
      !colorScheme
    ) return emptyResult;
    
    // Create comparison bar chart data
    const academicPapers = processedFocusData.institution_types?.academic ?? 0;
    const corporatePapers = processedFocusData.institution_types?.corporate ?? 0;
    
    const academicImpact = processedFocusData.institutions
      .filter((i) => i.type === "academic")
      .reduce((sum, i) => sum + (i.spotlights ?? 0) + (i.orals ?? 0), 0);
      
    const corporateImpact = processedFocusData.institutions
      .filter((i) => i.type === "corporate")
      .reduce((sum, i) => sum + (i.spotlights ?? 0) + (i.orals ?? 0), 0);
      
    const comparisonData = [
      {
        type: "Academic",
        Publications: academicPapers,
        "Distinguished Publications": academicImpact,
      },
      {
        type: "Corporate",
        Publications: corporatePapers,
        "Distinguished Publications": corporateImpact,
      },
    ];
    
    // Create pie chart data
    const total = academicPapers + corporatePapers;
    if (total === 0) return { comparisonData, pieData: [] };
    
    const pieData = [
      {
        name: "Academic",
        value: academicPapers,
        percent: academicPapers / total,
        fill: colorScheme.academic,
      },
      {
        name: "Corporate",
        value: corporatePapers,
        percent: corporatePapers / total,
        fill: colorScheme.corporate,
      },
    ];
    
    return {
      comparisonData,
      pieData
    };
  };
  
  /**
   * Filter and prioritize institutional research contributions
   */
  export const filterInstitutions = (
    institutions: InstitutionData[] = [],
    filter: string
  ): InstitutionData[] => {
    return institutions
      .filter((inst) =>
        inst.institute?.toLowerCase().includes(filter.toLowerCase())
      )
      .sort(
        (a, b) =>
          (b.unique_paper_count ?? 0) - (a.unique_paper_count ?? 0) ||
          (b.impact_score ?? 0) - (a.impact_score ?? 0) ||
          (b.author_count ?? 0) - (a.author_count ?? 0)
      );
  };
  
  /**
   * Establish comprehensive visual identity system from configuration
   * Leverages the centralized chart color scheme for design consistency
   */
  export const createColorMap = (
    colorScheme: DashboardDataInterface['configuration']['colorScheme']
  ): ColorMapInterface => {
    return {
      // Main country colors - Override with config or use our new chart colors
      us: colorScheme.us || chartColors.us,
      cn: colorScheme.cn || chartColors.cn,
      focusCountry: colorScheme.focusCountry || chartColors.focusCountry,
      
      // Theme colors
      primary: colorScheme.primary || chartColors.accent,
      secondary: colorScheme.secondary || chartColors.withOpacity(chartColors.muted, 0.9),
      
      // Institution types
      academic: colorScheme.academic || chartColors.academic,
      corporate: colorScheme.corporate || chartColors.corporate,
      
      // Paper types
      spotlight: colorScheme.spotlight || chartColors.spotlight,
      oral: colorScheme.oral || chartColors.oral,
      
      // Chart elements
      grid: chartColors.grid,
      textAxis: "hsl(var(--muted-foreground))",
      
      // Accents and highlights
      highlight: chartColors.highlight,
      accent: chartColors.accent,
      warning: chartColors.warning,
      rest: chartColors.rest,
      
      // Data types
      papers: chartColors.papers,
      authors: chartColors.authors,
    };
  };
  