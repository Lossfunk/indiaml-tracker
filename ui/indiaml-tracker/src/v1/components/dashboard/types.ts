import { DashboardData } from '@/components/dashboard-data';
import * as PlotlyJS from 'plotly.js';

// --- Constants ---

// APAC country codes for filtering
export const APAC_COUNTRIES: string[] = ['CN', 'IN', 'HK', 'SG', 'JP', 'KR', 'AU'];

export const CountryMap: { [key: string]: string } = {
    "US": "United States",
    "CN": "China",
    "GB": "United Kingdom",
    "UK": "United Kingdom", // Keep both for mapping potential raw data variations
    "IN": "India",
    "CA": "Canada",
    "HK": "Hong Kong",
    "SG": "Singapore",
    "DE": "Germany",
    "CH": "Switzerland",
    "KR": "South Korea",
    "JP": "Japan",
    "AU": "Australia",
    "IL": "Israel",
    "FR": "France",
    "NL": "Netherlands",
};

export const TABS: string[] = ["Overview", "Global Stats", "India Focus", "Institutions"];

// --- Type Definitions ---

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
    type: 'academic' | 'corporate' | 'unknown';
    papers: PaperSummary[];
}

export interface CountryData {
    affiliation_country: string;
    country_name: string;
    paper_count: number;
    author_count: number;
    spotlights: number;
    orals: number;
    rank: number;
    isHighlight?: boolean; // Flag for special styling (US, CN, IN)
}

export type ProcessedIndiaData = DashboardData['indiaFocus'] & {
    rank?: number;
    paper_count?: number;
    author_count: number;
    spotlights: number;
    orals: number;
}

export interface RechartsTooltipPayload {
    dataKey?: string | number;
    name?: string;
    value?: number | string;
    payload?: any;
    fill?: string;
    stroke?: string;
    color?: string;
}

export interface ActiveShapeProps {
    cx?: number;
    cy?: number;
    midAngle?: number;
    innerRadius?: number;
    outerRadius?: number;
    startAngle?: number;
    endAngle?: number;
    fill?: string;
    payload?: any;
    percent?: number;
    value?: number;
    name?: string;
}

export interface NameValueData {
    name: string;
    value: number;
    fillColorClass?: string;
    fillVariable?: string;
    percent?: number;
    [key: string]: any;
}

export interface PlotlyDatum {
  data: PlotlyJS.Data[];
  layout: Partial<PlotlyJS.Layout>;
  config?: Partial<PlotlyJS.Config>;
}

export interface MapChartViewToggleProps {
  activeView: 'map' | 'chart';
  setActiveView: (view: 'map' | 'chart') => void;
}

export type ViewMode = 'chart' | 'table';

// NEW: Map 2-letter to 3-letter ISO codes for Plotly
export const COUNTRY_CODE_MAP_2_TO_3: { [key: string]: string } = {
  "US": "USA", "CN": "CHN", "GB": "GBR", "UK": "GBR", "IN": "IND", "CA": "CAN",
  "HK": "HKG", "SG": "SGP", "DE": "DEU", "CH": "CHE", "KR": "KOR", "JP": "JPN",
  "AU": "AUS", "IL": "ISR", "FR": "FRA", "NL": "NLD",
};
