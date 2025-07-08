// src/v2/utils/data-transformer.ts

import { ConferenceStatistics } from '../types/conference_analytics';
import { DashboardDataInterface, PaperSummary, InstitutionData } from '../types/dashboard';
import { createColorMap } from './data-transformers';

/**
 * Transforms the new ConferenceStatistics format to the legacy DashboardDataInterface format
 * to maintain compatibility with existing dashboard components
 */
export function transformConferenceStatistics(data: ConferenceStatistics): DashboardDataInterface {
  // Transform global stats countries
  const globalStatsCountries = data.focusCountrySummary ? [{
    affiliation_country: data.focusCountrySummary.country_code,
    paper_count: data.focusCountrySummary.paper_count,
    author_count: data.focusCountrySummary.author_count,
    spotlights: data.focusCountrySummary.spotlights,
    orals: data.focusCountrySummary.orals,
  }] : [];

  // Transform focus country institutions
  const institutions: InstitutionData[] = data.focusCountry.institutions.map((inst: any) => ({
    institute: inst.name || inst.institute || 'Unknown',
    total_paper_count: inst.total_paper_count || inst.paper_count || 0,
    unique_paper_count: inst.unique_paper_count || inst.paper_count || 0,
    author_count: inst.author_count || 0,
    spotlights: inst.spotlights || 0,
    orals: inst.orals || 0,
    type: inst.type || 'unknown',
    papers: inst.papers || [],
    authors: inst.authors || [],
    authors_per_paper: inst.authors_per_paper,
    impact_score: inst.impact_score,
    normalized_papers: inst.normalized_papers,
    normalized_authors: inst.normalized_authors,
  }));

  // Transform papers arrays
  const transformPapers = (papers: any[]): PaperSummary[] => {
    return papers.map((paper: any) => ({
      id: paper.id || paper.paper_id || '',
      title: paper.title || '',
      isSpotlight: paper.isSpotlight || paper.is_spotlight || false,
      isOral: paper.isOral || paper.is_oral || false,
    }));
  };

  const transformed: DashboardDataInterface = {
    conferenceInfo: {
      name: data.conference,
      year: data.year,
      track: data.track,
      totalAcceptedPapers: data.globalStats.totalPapers,
      totalAcceptedAuthors: data.globalStats.totalAuthors,
    },
    globalStats: {
      countries: globalStatsCountries,
    },
    focusCountry: {
      country_code: data.focus_country_code,
      country_name: data.focus_country,
      total_authors: data.focusCountrySummary.author_count,
      total_spotlights: data.focusCountrySummary.spotlights,
      total_orals: data.focusCountrySummary.orals,
      institution_types: {
        academic: data.focusCountrySummary.academic_institutions,
        corporate: data.focusCountrySummary.corporate_institutions,
      },
      at_least_one_focus_country_author: {
        count: data.focusCountry.authorship.at_least_one.count,
        papers: transformPapers(data.focusCountry.authorship.at_least_one.papers),
      },
      majority_focus_country_authors: {
        count: data.focusCountry.authorship.majority.count,
        papers: transformPapers(data.focusCountry.authorship.majority.papers),
      },
      first_focus_country_author: {
        count: data.focusCountry.authorship.first_author.count,
        papers: transformPapers(data.focusCountry.authorship.first_author.papers),
      },
      institutions: institutions,
    },
    configuration: {
      countryMap: {}, // This might need to be populated based on available data
      apacCountries: [], // This might need to be populated based on available data
      colorScheme: {
        us: data.config.colors.us || '#1f77b4',
        cn: data.config.colors.cn || '#ff7f0e',
        focusCountry: data.config.colors.focusCountry || data.config.colors.focus_country || '#2ca02c',
        primary: data.config.colors.primary || '#1f77b4',
        secondary: data.config.colors.secondary || '#ff7f0e',
        academic: data.config.colors.academic || '#2ca02c',
        corporate: data.config.colors.corporate || '#d62728',
        spotlight: data.config.colors.spotlight || '#ff7f0e',
        oral: data.config.colors.oral || '#d62728',
        ...data.config.colors,
      },
      dashboardTitle: data.dashboard.summary.title,
      dashboardSubtitle: data.dashboard.context.subtitle || '',
      sections: {
        summary: {
          title: data.dashboard.summary.title,
          insights: data.dashboard.summary.content,
        },
        context: {
          title: data.dashboard.context.title,
          subtitle: data.dashboard.context.subtitle,
          insights: data.dashboard.context.content,
        },
        focusCountry: {
          title: data.dashboard.focusCountry.title,
          subtitle: data.dashboard.focusCountry.subtitle,
          insights: data.dashboard.focusCountry.content,
        },
        institutions: {
          title: data.dashboard.institutions.title,
          subtitle: data.dashboard.institutions.subtitle,
          insights: data.dashboard.institutions.content,
        },
      },
    },
    credits: [
      {
        name: "IndiaML Tracker",
        link: "https://github.com/Lossfunk/indiaml-tracker",
      },
    ],
  };

  return transformed;
}
