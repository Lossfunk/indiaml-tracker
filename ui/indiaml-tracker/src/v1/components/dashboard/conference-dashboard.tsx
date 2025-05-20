// src/components/dashboard/ConferenceDashboard.tsx

import React, { useState } from 'react';
import { 
  DashboardDataInterface, 
  CountryData, 
  ProcessedFocusCountryData 
} from '../../types/dashboard';
import { 
  useContextSectionData, 
  useFocusCountrySectionData, 
  useInstitutionSectionData 
} from '../../hooks/use-chart-data';
import { Section } from '../shared/section';
import { StatCard } from '../shared/stat-card';
import { InterpretationPanel } from '../shared/interpretation-panel';
import { InstitutionCard } from './institution-card';
import { exportInstitutionData } from '../../utils/export-utils';
import { useDashboardContext } from '../../contexts/dashboard-context';
import { 
  FaFileAlt, 
  FaUsers, 
  FaUserTie, 
  FaStar, 
  FaUniversity, 
  FaBalanceScale, 
  FaBullseye, 
  FaGlobeAsia,
  FaProjectDiagram,
  FaSearch,
  FaDownload,
  FaTrophy
} from 'react-icons/fa';

// Allow overriding context with props for better flexibility
interface ConferenceDashboardProps {
  loading?: boolean;
  error?: string | null;
  data?: DashboardDataInterface | null;
  sortedCountries: CountryData[];
  topCountriesByPaper: CountryData[];
  usData?: CountryData;
  cnData?: CountryData;
  focusCountryGlobalStats?: CountryData;
  processedFocusData: ProcessedFocusCountryData | null;
  conferenceSelectorElement: React.ReactNode;
}

export const ConferenceDashboard: React.FC<ConferenceDashboardProps> = ({
  loading: propLoading,
  error: propError,
  data: propData,
  sortedCountries,
  topCountriesByPaper,
  usData,
  cnData,
  focusCountryGlobalStats,
  processedFocusData,
  conferenceSelectorElement
}) => {
  // Use context as a base, override with props
  const context = useDashboardContext();
  
  // Determine which values to use (props take precedence)
  const loading = propLoading !== undefined ? propLoading : context.loading;
  const error = propError !== undefined ? propError : context.error;
  const data = propData !== undefined ? propData : context.data;
  
  // Institution filter state
  const [institutionFilter, setInstitutionFilter] = useState<string>("");
  
  // Get derived data for different sections
  const { 
    usChinaDominancePieData,
    apacCountriesData
  } = useContextSectionData(data, sortedCountries, usData, cnData);
  
  const {
    authorshipMajorityMinorityData,
    authorshipFirstAuthorData,
    institutionTypeComparisonData,
    institutionTypePieData
  } = useFocusCountrySectionData(data, processedFocusData);
  
  const {
    filteredInstitutions,
    topInstitutions
  } = useInstitutionSectionData(processedFocusData, institutionFilter);
  
  // Early returns for loading and error states
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6 text-foreground">
        <div className="text-xl">
          Loading dashboard data...
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="bg-destructive/10 border border-destructive/30 text-destructive px-6 py-4 rounded-lg shadow-lg text-center max-w-md">
          <h2 className="font-bold text-lg mb-2">Error Loading Dashboard</h2>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }
  
  if (!data || !processedFocusData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6 text-muted-foreground">
        No data available.
      </div>
    );
  }
  
  // Extract commonly used data
  const { conferenceInfo, focusCountry, configuration } = data;
  const totalPapers = conferenceInfo.totalAcceptedPapers;
  const totalAuthors = conferenceInfo.totalAcceptedAuthors;
  const focusCountryCode = focusCountry.country_code;
  const focusCountryName = focusCountry.country_name || "Focus Country";
  
  // Handle export for institutions
  const handleExportInstitutions = () => {
    if (!filteredInstitutions.length || !data) return;
    
    exportInstitutionData(
      filteredInstitutions,
      focusCountryCode,
      conferenceInfo.name,
      conferenceInfo.year
    );
  };
  
  // Main render
  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      {/* Header */}
      <header className="py-6 md:py-8 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 border-b border-border shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center mb-2 sm:mb-3">
            <div className="flex-grow text-center sm:text-left mb-3 sm:mb-0">
              <h1 className="text-3xl sm:text-4xl font-bold text-foreground flex items-center justify-center sm:justify-start">
                <FaTrophy className="mr-3 text-amber-500" />{" "}
                {configuration.dashboardTitle}
              </h1>
            </div>
            <div className="ml-0 sm:ml-4 flex-shrink-0">
              {conferenceSelectorElement}
            </div>
          </div>

          <div className="text-center sm:text-left">
            <p className="text-muted-foreground text-base sm:text-lg mb-3">
              {configuration.dashboardSubtitle}
            </p>

            {/* Stats Display */}
            <div className="flex flex-col sm:flex-row items-center justify-center sm:justify-start gap-3 mb-2">
              <div className="bg-card/70 dark:bg-card/40 border border-border rounded-lg px-3 py-1.5 shadow-sm text-sm">
                <span className="text-muted-foreground">Global Papers in index: </span>
                <span className="font-semibold text-foreground">
                  {totalPapers?.toLocaleString() ?? "N/A"}
                </span>
              </div>
              <div className="bg-card/70 dark:bg-card/40 border border-border rounded-lg px-3 py-1.5 shadow-sm text-sm">
                <span className="text-muted-foreground">Global Authors in index: </span>
                <span className="font-semibold text-foreground">
                  {totalAuthors?.toLocaleString() ?? "N/A"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main>
        {/* Summary Section */}
        <Section
          title={configuration.sections.summary.title}
          id="summary"
          className="bg-muted/30"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Papers Accepted"
              value={processedFocusData.paper_count ?? 0}
              icon={<FaFileAlt />}
              colorClass="text-amber-500 dark:text-amber-400"
              subtitle={`#${processedFocusData.rank ?? "N/A"} globally | ${(
                ((processedFocusData.paper_count ?? 0) / (totalPapers || 1)) *
                100
              ).toFixed(1)}% of all ${conferenceInfo.name} papers`}
            />
            <StatCard
              title="Authors Accepted"
              value={processedFocusData.author_count ?? 0}
              icon={<FaUsers />}
              colorClass="text-blue-500 dark:text-blue-400"
              subtitle={`Avg ${(
                processedFocusData?.authors_per_paper ?? 0
              ).toFixed(1)} authors/paper`}
            />
            <StatCard
              title="First Authors"
              value={processedFocusData?.first_focus_country_author?.count ?? 0}
              icon={<FaUserTie />}
              colorClass="text-emerald-500 dark:text-emerald-400"
              subtitle={`${(
                ((processedFocusData?.first_focus_country_author?.count ?? 0) /
                  (processedFocusData?.paper_count || 1)) *
                100
              ).toFixed(0)}% of papers led by ${focusCountryName}n authors`}
            />
            <StatCard
              title="Spotlight Papers"
              value={processedFocusData.spotlights ?? 0}
              icon={<FaStar />}
              colorClass="text-yellow-500 dark:text-yellow-400"
              subtitle={`${Math.round(
                processedFocusData.spotlight_oral_rate * 100
              )}% spotlight rate`}
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
              <div className="flex items-start mb-3">
                <FaUniversity className="text-blue-500 mr-3 mt-1" size={20} />
                <div>
                  <p className="text-foreground font-medium text-lg">
                    Institutional Leaders:
                  </p>
                  <p className="text-muted-foreground text-sm">
                    {topInstitutions.length > 0
                      ? `${topInstitutions[0].institute} leads volume (${
                          topInstitutions[0].total_paper_count
                        } papers, ${topInstitutions[0].author_count} authors)${
                          topInstitutions.length > 1
                            ? `; ${topInstitutions[1].institute} follows with ${topInstitutions[1].total_paper_count} papers and ${topInstitutions[1].author_count} authors`
                            : ""
                        }`
                      : "Institution data unavailable"}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
              <div className="flex items-start mb-3">
                <FaBalanceScale
                  className="text-green-500 mr-3 mt-1"
                  size={20}
                />
                <div>
                  <p className="text-foreground font-medium text-lg">
                    Quality Focus:
                  </p>
                  <p className="text-muted-foreground text-sm">
                    {focusCountryName} secured{" "}
                    {processedFocusData.spotlights} spotlight{" "}
                    {processedFocusData.spotlights === 1 ? "paper" : "papers"}{" "}
                    at {conferenceInfo.name} {conferenceInfo.year},
                    demonstrating quality research capability
                    {processedFocusData.paper_count &&
                    processedFocusData.paper_count < 100
                      ? " despite smaller overall representation"
                      : ""}
                    .
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          <InterpretationPanel
            title="Key Findings Overview"
            icon={<FaBullseye />}
            iconColorClass="text-red-500 dark:text-red-400"
            insights={configuration.sections.summary.insights}
          />
        </Section>

        {/* Global Context Section - Abbreviated for brevity */}
        <Section
          title={configuration.sections.context.title}
          id="context"
          subtitle={configuration.sections.context.subtitle}
        >
          {/* In a real implementation, you would include the charts for global context here */}
          <InterpretationPanel
            title="APAC at ICLR 2025 and India's position"
            icon={<FaGlobeAsia />}
            iconColorClass="text-blue-500 dark:text-blue-400"
            insights={configuration.sections.context.insights}
          />
        </Section>

        {/* Focus Country Section - Abbreviated for brevity */}
        <Section
          title={configuration.sections.focusCountry.title}
          id="focus-country"
          subtitle={configuration.sections.focusCountry.subtitle}
          className="bg-muted/30"
        >
          {/* In a real implementation, you would include the charts for focus country here */}
          <InterpretationPanel
            title={`${focusCountryName}-Specific Insights`}
            icon={<FaProjectDiagram />}
            iconColorClass="text-purple-500 dark:text-purple-400"
            insights={configuration.sections.focusCountry.insights}
          />
        </Section>

        {/* Institutions Section */}
        <Section
          title={configuration.sections.institutions.title}
          id="institutions"
          subtitle={configuration.sections.institutions.subtitle}
        >
          <div className="mb-6 max-w-md mx-auto">
            <div className="relative">
              <label htmlFor="institution-search" className="sr-only">
                Search Institutions
              </label>
              <input
                id="institution-search"
                type="search"
                placeholder={`Search ${focusCountryName} institutions...`}
                className="bg-input border border-border rounded-lg py-2 pl-10 pr-4 text-foreground w-full focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent shadow-sm placeholder-muted-foreground"
                value={institutionFilter}
                onChange={(e) => setInstitutionFilter(e.target.value)}
              />
              <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground pointer-events-none" />
            </div>
          </div>
          
          <div>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
              <h3 className="text-xl font-semibold text-foreground">
                Detailed Institution List
              </h3>
              {filteredInstitutions.length > 0 && (
                <button
                  onClick={handleExportInstitutions}
                  className="flex items-center bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs px-3 py-1.5 rounded transition-colors shadow-sm"
                  aria-label="Export detailed institution list to CSV"
                >
                  <FaDownload className="mr-1.5" size={10} /> Export Details
                </button>
              )}
            </div>
            
            {filteredInstitutions.length > 0 ? (
              <div className="space-y-4">
                {filteredInstitutions.map((institution, index) => (
                  <InstitutionCard
                    key={`${institution.institute}-${index}`}
                    institution={institution}
                    index={index}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-10 text-muted-foreground bg-card rounded-lg border border-border shadow-sm">
                <FaUniversity size={36} className="mx-auto mb-3" />
                <p>No institutions found matching "{institutionFilter}".</p>
                <p className="text-sm mt-1">
                  Try refining your search term or clear the filter.
                </p>
              </div>
            )}
          </div>
          
          <InterpretationPanel
            title="Institutional Ecosystem Insights"
            icon={<FaUniversity />}
            iconColorClass="text-green-500 dark:text-green-400"
            insights={configuration.sections.institutions.insights}
          />
        </Section>
      </main>

      <footer className="mt-10 md:mt-12 max-w-7xl px-7 mx-auto text-muted-foreground text-xs border-t border-border pt-6 pb-6 bg-gradient-to-r from-amber-50/30 to-orange-50/30 dark:from-amber-950/10 dark:to-orange-950/10">
        <p className="font-bold ">
          {conferenceInfo?.name ?? "Conference"} {conferenceInfo?.year ?? ""}{" "}
          Dashboard{" "}
        </p>
        <p className="mt-2">
          {" "}
          <span className="mr-1">Report Prepared by: </span>
          {data.credits.length === 0 ? null : data.credits.length === 1 ? (
            <a href={data.credits[0].link}>
              {data.credits[0].name}
            </a>
          ) : (
            data.credits.map((x, index) => (
              <span key={index}>
                <a href={x.link}>{x.name}</a>
                {index < data.credits.length - 2 && ", "}
                {index === data.credits.length - 2 && " and "}
              </span>
            ))
          )}

          {" "} at <a href="https://lossfunk.com">Lossfunk</a>
        </p>
        <p className="mt-1">
          Dashboard was prepared in part with the help of Generative AI
          technology and there may be inaccuracies or omissions. Please report
          data quality issues{" "}
          <a href="https://github.com/Lossfunk/indiaml-tracker/issues">
            on Github
          </a>{" "}
        </p>
        <p className="mt-1">
          &copy; {new Date().getFullYear()}{" "}
          <a href="https://lossfunk.com">Lossfunk</a> India@ML
        </p>
      </footer>

      {/* Global styles */}
      <style jsx global>{`
        body {
          scroll-behavior: smooth;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fadeIn 0.5s ease-out forwards;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: hsl(var(--muted));
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: hsl(var(--border));
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: hsl(var(--primary) / 0.7);
        }
      `}</style>
    </div>
  );
};
