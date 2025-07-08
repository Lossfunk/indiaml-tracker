export type ConferenceStatistics = {
  conference: string; // Changed from "ICLR" to string
  year: number;
  track: "Conference";
  focus_country: string;
  focus_country_code: string;
  generated_at: string; // ISO 8601 date-time string
  globalStats: GlobalStats;
  focusCountrySummary: FocusCountrySummary;
  focusCountry: FocusCountry;
  institutions: Institutions;
  config: Config;
  dashboard: Dashboard;
};

export type GlobalStats = {
  totalPapers: number;
  totalAuthors: number;
  totalCountries: number;
  countries: string[];
};

export type FocusCountrySummary = {
  country: string;
  country_code: string;
  rank: number;
  paper_count: number;
  author_count: number;
  percentage: number;
  spotlights: number;
  orals: number;
  institution_count: number;
  academic_institutions: number;
  corporate_institutions: number;
};

export type FocusCountry = {
  authorship: {
    at_least_one: AuthorshipDetail;
    majority: AuthorshipDetail;
    first_author: AuthorshipDetail;
  };
  institutions: any[]; // The schema specifies an empty object for items
};

export type Institutions = {
  summary: {
    total_institutions: number;
    academic_institutions: number;
    corporate_institutions: number;
    total_papers: number;
    total_authors: number;
    avg_papers_per_institution: number;
    avg_authors_per_institution: number;
  };
  top_institutions: any[]; // The schema specifies an empty object for items
  total_institutions: number;
};

export type Config = {
  focus_country_code: string;
  focus_country_name: string;
  colors: {
    [key: string]: string; // An HSL color string
  };
};

export type Dashboard = {
  summary: DashboardSection;
  context: DashboardSectionWithSubtitle;
  focusCountry: DashboardSectionWithSubtitle;
  institutions: DashboardSectionWithSubtitle;
};

// Definitions
export type AuthorshipDetail = {
  count: number;
  papers: any[]; // The schema specifies an empty object for items
};

export type DashboardSection = {
  title: string;
  content: string[];
};

export type DashboardSectionWithSubtitle = DashboardSection & {
  subtitle: string;
};