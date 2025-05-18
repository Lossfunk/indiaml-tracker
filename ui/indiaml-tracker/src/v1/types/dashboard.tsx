// src/types/dashboard.ts

/**
 * Core data interfaces for conference dashboard
 */

export interface DashboardDataInterface {
    conferenceInfo: {
      name: string;
      year: number;
      track: string;
      totalAcceptedPapers: number;
      totalAcceptedAuthors: number;
    };
    globalStats: {
      countries: Array<{
        affiliation_country: string;
        paper_count: number;
        author_count: number;
        spotlights: number;
        orals: number;
      }>;
    };
    focusCountry: {
      country_code: string;
      country_name?: string;
      total_authors: number;
      total_spotlights: number;
      total_orals: number;
      institution_types: {
        academic: number;
        corporate: number;
      };
      at_least_one_focus_country_author: {
        count: number;
        papers: PaperSummary[];
      };
      majority_focus_country_authors: {
        count: number;
        papers: PaperSummary[];
      };
      first_focus_country_author: {
        count: number;
        papers: PaperSummary[];
      };
      institutions: Array<InstitutionData>;
    };
    configuration: {
      countryMap: { [key: string]: string };
      apacCountries: string[];
      colorScheme: {
        us: string;
        cn: string;
        focusCountry: string;
        primary: string;
        secondary: string;
        academic: string;
        corporate: string;
        spotlight: string;
        oral: string;
        [key: string]: string;
      };
      dashboardTitle: string;
      dashboardSubtitle: string;
      sections: {
        summary: { title: string; insights: string[] };
        context: { title: string; subtitle: string; insights: string[] };
        focusCountry: { title: string; subtitle: string; insights: string[] };
        institutions: { title: string; subtitle: string; insights: string[] };
      };
    };
    credits: {
      name: string;
      link: string;
    }[];
  }
  
  export interface PaperSummary {
    id: string;
    title: string;
    isSpotlight?: boolean;
    isOral?: boolean;
  }
  
  export interface InstitutionData {
    institute: string;
    total_paper_count: number;
    unique_paper_count: number;
    author_count: number;
    spotlights: number;
    orals: number;
    type: "academic" | "corporate" | "unknown";
    papers: PaperSummary[];
    authors: string[];
    authors_per_paper?: number;
    impact_score?: number;
    normalized_papers?: number;
    normalized_authors?: number;
  }
  
  export interface CountryData {
    affiliation_country: string;
    country_name: string;
    paper_count: number;
    author_count: number;
    spotlights: number;
    orals: number;
    rank: number;
    isHighlight?: boolean;
    spotlight_oral_rate?: number;
    authors_per_paper?: number;
    normalized_papers?: number;
    normalized_authors?: number;
  }
  
  export interface ProcessedFocusCountryData {
    country_code: string;
    country_name?: string;
    total_authors: number;
    total_spotlights: number;
    total_orals: number;
    institution_types: {
      academic: number;
      corporate: number;
    };
    at_least_one_focus_country_author: {
      count: number;
      papers: PaperSummary[];
    };
    majority_focus_country_authors: {
      count: number;
      papers: PaperSummary[];
    };
    first_focus_country_author: {
      count: number;
      papers: PaperSummary[];
    };
    institutions: InstitutionData[];
    rank?: number;
    paper_count?: number;
    author_count: number;
    spotlights: number;
    orals: number;
    spotlight_oral_rate?: number;
    authors_per_paper?: number;
  }
  
  export interface TrackerIndexEntry {
    label: string;
    file: string;
    analytics: string;
    venue: string;
    year: string;
  }
  
  export interface ColorMapInterface {
    us: string;
    cn: string;
    focusCountry: string;
    primary: string;
    secondary: string;
    academic: string;
    corporate: string;
    spotlight: string;
    oral: string;
    grid: string;
    textAxis: string;
    highlight: string;
    accent: string;
    warning: string;
    rest: string;
    papers: string;
    authors: string;
    [key: string]: string;
  }
  
  export interface ChartDataItem {
    name: string;
    value: number;
    percent?: number;
    fill?: string;
    [key: string]: any;
  }
  
  export interface StatCardProps {
    title: string;
    value: string | number;
    icon?: React.ReactNode;
    colorClass: string;
    subtitle?: string;
    className?: string;
  }
  
  export interface SectionProps {
    title: string;
    subtitle?: string;
    children: React.ReactNode;
    id?: string;
    className?: string;
  }
  
  export interface DashboardContextState {
    conference: string;
    year: string;
    data: DashboardDataInterface | null;
    loading: boolean;
    error: string | null;
    colorMap: ColorMapInterface;
  }
  