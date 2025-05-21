// src/components/dashboard/ConferenceDashboard.tsx

import React, { useState } from 'react';
import {
  DashboardDataInterface,
  CountryData,
  ProcessedFocusCountryData,
  ChartDataItem
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
import { GlobalDistributionChart } from '../charts/global-distribution-chart';
import { PieChart } from '../charts/pie-chart';
import { BarChart } from '../charts/bar-chart';
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
  FaTrophy,
  FaChartPie,
  FaChartBar,
  FaGlobeAmericas
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
                (processedFocusData?.spotlight_oral_rate || 0) * 100
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

        {/* Global Distribution Section - Full Width */}
        <Section
          title="Global Research Distribution"
          id="global-distribution"
          subtitle="Worldwide paper distribution across countries at the conference"
        >
          {/* Full-width Global Distribution Chart */}
          <div className="mb-10">
            <h3 className="text-xl font-semibold flex items-center mb-4">
              <FaGlobeAmericas className="mr-2 text-blue-500" />
              Global Research Landscape
            </h3>
            <div className="bg-card border border-border rounded-lg p-5 shadow-sm">
              {/* Summary Stats */}
              <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
                <p className="text-sm text-muted-foreground">
                  Global distribution of papers across top {Math.min(15, sortedCountries.length)} countries at {conferenceInfo.name} {conferenceInfo.year}
                  {focusCountryGlobalStats && focusCountryGlobalStats.rank > 15 ? `, including ${focusCountryName} (rank #${focusCountryGlobalStats.rank})` : ''}
                </p>
                
                <div className="flex flex-wrap gap-3">
                  <div className="px-3 py-1 bg-muted/30 rounded-full text-xs flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{backgroundColor: data.configuration.colorScheme.papers}}></span>
                    <span>Total Countries: <b>{sortedCountries.length}</b></span>
                  </div>
                  <div className="px-3 py-1 bg-muted/30 rounded-full text-xs flex items-center gap-1.5"
                       style={{backgroundColor: `${data.configuration.colorScheme.focusCountry}20`}}>
                    <span>{focusCountryName} Rank: <b>#{focusCountryGlobalStats?.rank || 'N/A'}</b></span>
                  </div>
                </div>
              </div>
              
              {/* Enhanced Global Chart */}
              <GlobalDistributionChart
                countries={sortedCountries}
                focusCountry={focusCountryGlobalStats}
                colorMap={{
                  us: data.configuration.colorScheme.us,
                  cn: data.configuration.colorScheme.cn,
                  focusCountry: data.configuration.colorScheme.focusCountry,
                  rest: "hsl(var(--muted))"
                }}
                height={550}
                maxBars={15}
                showFocusCountryIfOutsideMax={true}
                title="Global Paper Distribution"
              />
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-4 border-t border-border">
                <div className="flex items-center p-3 bg-muted/30 rounded-lg">
                  <div className="w-3 h-3 rounded-full mr-2" style={{backgroundColor: data.configuration.colorScheme.us}}></div>
                  <div>
                    <p className="text-xs font-medium">United States</p>
                    <p className="text-xs text-muted-foreground">{usData?.paper_count || 0} papers ({((usData?.paper_count || 0) / (data.conferenceInfo.totalAcceptedPapers || 1) * 100).toFixed(1)}%)</p>
                  </div>
                </div>
                
                <div className="flex items-center p-3 bg-muted/30 rounded-lg">
                  <div className="w-3 h-3 rounded-full mr-2" style={{backgroundColor: data.configuration.colorScheme.cn}}></div>
                  <div>
                    <p className="text-xs font-medium">China</p>
                    <p className="text-xs text-muted-foreground">{cnData?.paper_count || 0} papers ({((cnData?.paper_count || 0) / (data.conferenceInfo.totalAcceptedPapers || 1) * 100).toFixed(1)}%)</p>
                  </div>
                </div>
                
                <div className="flex items-center p-3 bg-muted/30 rounded-lg">
                  <div className="w-3 h-3 rounded-full mr-2" style={{backgroundColor: data.configuration.colorScheme.focusCountry}}></div>
                  <div>
                    <p className="text-xs font-medium">{focusCountryName}</p>
                    <p className="text-xs text-muted-foreground">{focusCountryGlobalStats?.paper_count || 0} papers ({((focusCountryGlobalStats?.paper_count || 0) / (data.conferenceInfo.totalAcceptedPapers || 1) * 100).toFixed(1)}%)</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <InterpretationPanel
            title="Global Research Insights"
            icon={<FaGlobeAmericas />}
            iconColorClass="text-blue-500 dark:text-blue-400"
            insights={[
              `The global research landscape shows participation from ${sortedCountries.length} countries.`,
              `${focusCountryName} ranks #${focusCountryGlobalStats?.rank || 'N/A'} globally in research contributions.`,
              `Top contributors demonstrate strong presence in both paper count and author representation.`
            ]}
          />
        </Section>

        {/* Global Context Section */}
        <Section
          title={configuration.sections.context.title}
          id="context"
          subtitle={configuration.sections.context.subtitle}
          className="bg-muted/30"
        >
          {/* Global Distribution Chart - Full Width */}
          <div className="mb-10">
            <h3 className="text-xl font-semibold flex items-center mb-4">
              <FaGlobeAmericas className="mr-2 text-blue-500" />
              Global Research Distribution
            </h3>
            <div className="bg-card border border-border rounded-lg p-5 shadow-sm">
              <GlobalDistributionChart
                countries={sortedCountries}
                focusCountry={focusCountryGlobalStats}
                colorMap={{
                  us: data.configuration.colorScheme.us,
                  cn: data.configuration.colorScheme.cn,
                  focusCountry: data.configuration.colorScheme.focusCountry,
                  rest: data.configuration.colorScheme.rest
                }}
                height={450}
                maxBars={15}
                showFocusCountryIfOutsideMax={true}
                title={`Top Contributors at ${conferenceInfo.name} ${conferenceInfo.year}`}
              />
            </div>
          </div>
          
          {/* US-China Duopoly - Enhanced */}
          <div className="mb-10">
            <h3 className="text-xl font-semibold flex items-center mb-4">
              <FaChartPie className="mr-2 text-yellow-500" />
              US-China Duopoly & {focusCountryName}'s Position
            </h3>
            <div className="bg-card border border-border rounded-lg p-5 shadow-sm">
              <div className="flex flex-col md:flex-row gap-6">
                <div className="w-full md:w-1/2 flex flex-col items-center justify-center">
                  <PieChart
                    data={usChinaDominancePieData}
                    title="Global Research Distribution"
                    height={320}
                    showLabels={true}
                    showLegend={true}
                    outerRadius={130}
                    innerRadius={50}
                  />
                  <p className="text-xs text-muted-foreground mt-3 text-center px-4">
                    Papers distribution showing US-China duopoly vs. {focusCountryName} and Rest of World
                  </p>
                </div>
                
                <div className="w-full md:w-1/2">
                  <h4 className="text-lg font-medium mb-4">Key Insights</h4>
                  <div className="grid grid-cols-1 gap-4">
                    <div className="bg-muted/30 p-4 rounded-lg border border-border/50">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-3 h-3 rounded-full" style={{backgroundColor: data.configuration.colorScheme.us}}></div>
                        <p className="text-sm font-medium">US-China AI Duopoly</p>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <span className="text-xs text-muted-foreground block">Combined papers</span>
                          <span className="text-base font-medium">{(usData?.paper_count || 0) + (cnData?.paper_count || 0)}</span>
                        </div>
                        <div>
                          <span className="text-xs text-muted-foreground block">Global share</span>
                          <span className="text-base font-medium text-amber-600 dark:text-amber-500">
                            {(((usData?.paper_count || 0) + (cnData?.paper_count || 0)) / (data.conferenceInfo.totalAcceptedPapers) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-muted/30 p-4 rounded-lg border border-border/50"
                         style={{borderColor: data.configuration.colorScheme.focusCountry}}>
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-3 h-3 rounded-full" style={{backgroundColor: data.configuration.colorScheme.focusCountry}}></div>
                        <p className="text-sm font-medium">{focusCountryName}'s Position</p>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <span className="text-xs text-muted-foreground block">Global rank</span>
                          <span className="text-base font-medium">#{focusCountryGlobalStats?.rank || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-xs text-muted-foreground block">Global share</span>
                          <span className="text-base font-medium" style={{color: data.configuration.colorScheme.focusCountry}}>
                            {((focusCountryGlobalStats?.paper_count || 0) / (data.conferenceInfo.totalAcceptedPapers) * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-xs text-muted-foreground block">Relative to US</span>
                          <span className="text-base font-medium">
                            {((focusCountryGlobalStats?.paper_count || 1) / (usData?.paper_count || 1) * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-xs text-muted-foreground block">Relative to China</span>
                          <span className="text-base font-medium">
                            {((focusCountryGlobalStats?.paper_count || 1) / (cnData?.paper_count || 1) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-muted/30 p-3 rounded-lg border border-border/50">
                      <p className="text-sm">The {focusCountryName} AI ecosystem shows
                        <span className="font-medium"> {
                          (focusCountryGlobalStats?.rank || 0) <= 5 ? 'exceptionally strong' :
                          (focusCountryGlobalStats?.rank || 0) <= 10 ? 'strong' :
                          (focusCountryGlobalStats?.rank || 0) <= 20 ? 'moderate' : 'emerging'
                        } </span>
                        global presence in the {conferenceInfo.name} {conferenceInfo.year} research landscape
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* APAC Dynamics */}
          <div className="mb-6">
            <h3 className="text-xl font-semibold flex items-center mb-4">
              <FaGlobeAsia className="mr-2 text-green-500" />
              APAC Regional Dynamics
            </h3>
            
            {/* Enhanced APAC Overview */}
            <div className="bg-muted/30 p-4 rounded-lg border border-border mb-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h4 className="text-base font-medium">APAC at {conferenceInfo.name} {conferenceInfo.year}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Asia-Pacific's collective contribution and {focusCountryName}'s impact on the region
                  </p>
                </div>
                
                <div className="flex flex-wrap gap-3">
                  <div className="bg-card px-3 py-2 rounded-md border border-border shadow-sm">
                    <p className="text-xs text-muted-foreground">APAC Countries</p>
                    <p className="text-base font-medium">{apacCountriesData.length}</p>
                  </div>
                  <div className="bg-card px-3 py-2 rounded-md border border-border shadow-sm">
                    <p className="text-xs text-muted-foreground">Total APAC Papers</p>
                    <p className="text-base font-medium">{apacCountriesData.reduce((sum, country) => sum + country.paper_count, 0)}</p>
                  </div>
                  <div className="bg-card px-3 py-2 rounded-md border border-border shadow-sm" style={{borderColor: data.configuration.colorScheme.focusCountry}}>
                    <p className="text-xs text-muted-foreground">{focusCountryName} APAC Rank</p>
                    <p className="text-base font-medium">
                      #{apacCountriesData.findIndex(c => c.affiliation_country === focusCountryCode) + 1}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* APAC Visualizations - Enhanced */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Enhanced APAC Bar Chart */}
              <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
                <h4 className="text-base font-medium mb-4">APAC Countries Research Output</h4>
                <BarChart
                  data={apacCountriesData}
                  xAxisDataKey="country_name"
                  height={350}
                  bars={[
                    { dataKey: "paper_count", name: "Papers", fill: data.configuration.colorScheme.papers },
                    { dataKey: "author_count", name: "Authors", fill: data.configuration.colorScheme.authors }
                  ]}
                  layout="horizontal"
                  highlightIndex={apacCountriesData.findIndex(
                    c => c.affiliation_country === focusCountryCode
                  )}
                  highlightColor={data.configuration.colorScheme.focusCountry}
                />
                <div className="mt-4 p-3 bg-muted/30 rounded-lg border border-border/50">
                  <h5 className="text-sm font-medium flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{backgroundColor: data.configuration.colorScheme.focusCountry}}></div>
                    {focusCountryName}'s position within APAC
                  </h5>
                  <p className="text-xs text-muted-foreground mt-1">
                    {(() => {
                      const index = apacCountriesData.findIndex(c => c.affiliation_country === focusCountryCode);
                      if (index === -1) return "Not available";
                      if (index === 0) return "Leading APAC research output with dominant presence";
                      if (index <= 2) return `Among top 3 APAC contributors with strong regional influence`;
                      if (index <= 4) return `Among top 5 APAC contributors with significant research output`;
                      return `Ranks #${index + 1} in APAC research output, showing ${index <= 7 ? 'notable' : 'growing'} regional presence`;
                    })()}
                  </p>
                </div>
              </div>
              
              {/* Enhanced APAC Distribution Pie Chart */}
              <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
                <h4 className="text-base font-medium mb-4">APAC Regional Impact</h4>
                <div className="flex flex-col items-center">
                  <PieChart
                    data={apacCountriesData.map(country => ({
                      name: country.country_name,
                      value: country.paper_count,
                      color: country.affiliation_country === focusCountryCode
                        ? data.configuration.colorScheme.focusCountry
                        : country.affiliation_country === 'cn'
                          ? data.configuration.colorScheme.cn
                          : undefined
                    }))}
                    title="APAC Paper Distribution"
                    height={300}
                    showLabels={false}
                    showLegend={true}
                    outerRadius={120}
                    innerRadius={40}
                  />
                  <div className="w-full mt-3 p-3 bg-muted/30 rounded-lg border border-border/50">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <span className="text-xs text-muted-foreground block">APAC Contribution</span>
                        <span className="text-sm font-medium" style={{color: data.configuration.colorScheme.focusCountry}}>
                          {((apacCountriesData.find(c => c.affiliation_country === focusCountryCode)?.paper_count || 0) /
                          apacCountriesData.reduce((sum, country) => sum + country.paper_count, 0) * 100).toFixed(1)}%
                        </span>
                        <span className="text-xs text-muted-foreground ml-1">of APAC papers</span>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground block">Global Position</span>
                        <span className="text-sm font-medium">#{focusCountryGlobalStats?.rank || 'N/A'}</span>
                        <span className="text-xs text-muted-foreground ml-1">globally</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* APAC Authorship Analysis */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
                <h4 className="text-base font-medium mb-3">{focusCountryName} Contribution Level</h4>
                <div className="flex flex-col md:flex-row items-center">
                  <div className="w-full md:w-7/12">
                    <PieChart
                      data={authorshipMajorityMinorityData}
                      title={`Majority vs Minority Contribution`}
                      height={220}
                      showLabels={true}
                    />
                  </div>
                  <div className="w-full md:w-5/12 mt-4 md:mt-0 p-3">
                    <h5 className="text-sm font-medium mb-2">Key Insights</h5>
                    <ul className="list-disc pl-5 space-y-1.5 text-xs text-muted-foreground">
                      <li>Papers with majority {focusCountryName} authors: <span className="font-medium text-foreground">
                        {processedFocusData?.majority_focus_country_authors?.count || 0} papers</span></li>
                      <li>Papers with minority {focusCountryName} authors: <span className="font-medium text-foreground">
                        {(processedFocusData?.at_least_one_focus_country_author?.count || 0) - (processedFocusData?.majority_focus_country_authors?.count || 0)} papers</span></li>
                      <li>Shows {(processedFocusData?.majority_focus_country_authors?.count || 0) >
                        ((processedFocusData?.at_least_one_focus_country_author?.count || 0) - (processedFocusData?.majority_focus_country_authors?.count || 0)) ?
                        'stronger independent research capabilities' : 'significant collaborative tendencies'}</li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
                <h4 className="text-base font-medium mb-3">{focusCountryName} Author Position Analysis</h4>
                <div className="flex flex-col md:flex-row items-center">
                  <div className="w-full md:w-7/12">
                    <PieChart
                      data={authorshipFirstAuthorData}
                      title={`First vs Non-First Author Papers`}
                      height={220}
                      showLabels={true}
                    />
                  </div>
                  <div className="w-full md:w-5/12 mt-4 md:mt-0 p-3">
                    <h5 className="text-sm font-medium mb-2">Leadership Insights</h5>
                    <ul className="list-disc pl-5 space-y-1.5 text-xs text-muted-foreground">
                      <li>Papers with {focusCountryName} first authors: <span className="font-medium text-foreground">
                        {processedFocusData?.first_focus_country_author?.count || 0}</span></li>
                      <li>Papers with {focusCountryName} contributors but not as first author: <span className="font-medium text-foreground">
                        {(processedFocusData?.at_least_one_focus_country_author?.count || 0) - (processedFocusData?.first_focus_country_author?.count || 0)}</span></li>
                      <li>Shows {((processedFocusData?.first_focus_country_author?.count || 0) /
                        (processedFocusData?.at_least_one_focus_country_author?.count || 1) > 0.5) ?
                        'strong research leadership' : 'growing but developing research leadership'} capabilities</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <InterpretationPanel
            title={`APAC at ${conferenceInfo.name} ${conferenceInfo.year} and ${focusCountryName}'s Position`}
            icon={<FaGlobeAsia />}
            iconColorClass="text-blue-500 dark:text-blue-400"
            insights={configuration.sections.context.insights}
          />
        </Section>

        {/* Focus Country Section */}
        <Section
          title={configuration.sections.focusCountry.title}
          id="focus-country"
          subtitle={configuration.sections.focusCountry.subtitle}
          className="bg-muted/30"
        >
          {/* Top Institutes Chart */}
          <div className="mb-10">
            <h3 className="text-xl font-semibold flex items-center mb-4">
              <FaUniversity className="mr-2 text-indigo-500" />
              Top 10 Institutes in {focusCountryName}
            </h3>
            <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
              <BarChart
                data={topInstitutions.slice(0, 10)}
                xAxisDataKey="institute"
                height={450}
                bars={[
                  { dataKey: "unique_paper_count", name: "Papers", fill: "hsl(210, 70%, 60%)" },
                  { dataKey: "author_count", name: "Authors", fill: "hsl(330, 60%, 70%)" }
                ]}
                layout="vertical"
                margin={{ top: 5, right: 20, left: 170, bottom: 5 }}
              />
            </div>
          </div>

          {/* Academic vs Corporate */}
          <div className="mb-10">
            <h3 className="text-xl font-semibold flex items-center mb-4">
              <FaChartBar className="mr-2 text-orange-500" />
              Academic vs Corporate Impact in {focusCountryName}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
                <BarChart
                  data={institutionTypeComparisonData}
                  xAxisDataKey="type"
                  height={300}
                  bars={[
                    { dataKey: "Papers", fill: data.configuration.colorScheme.papers, name: "Research Papers" },
                    { dataKey: "Spotlights/Orals", fill: data.configuration.colorScheme.spotlight, name: "High-Impact Papers" }
                  ]}
                />
              </div>
              <div className="bg-card border border-border rounded-lg p-4 shadow-sm">
                <div className="flex items-center justify-center h-full">
                  <PieChart
                    data={institutionTypePieData}
                    title="Institution Type Distribution"
                    height={250}
                    showLabels={true}
                    innerRadius={60}
                    outerRadius={100}
                  />
                </div>
              </div>
            </div>
            <p className="text-sm text-muted-foreground mt-4 text-center">
              {focusCountryName}'s AI research ecosystem shows {
                (processedFocusData?.institution_types?.academic || 0) > (processedFocusData?.institution_types?.corporate || 0) * 2
                  ? 'strong academic dominance'
                  : (processedFocusData?.institution_types?.corporate || 0) > (processedFocusData?.institution_types?.academic || 0) * 2
                    ? 'strong corporate dominance'
                    : 'a balanced mix of academic and corporate contributions'
              }
            </p>
          </div>

          <InterpretationPanel
            title={`${focusCountryName}-Specific Insights and Research Ecosystem`}
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

          {/* Stats summary for institutions */}
          {filteredInstitutions.length > 0 && (
            <div className="mt-8 mb-6 p-4 bg-muted/30 border border-border rounded-lg">
              <h4 className="text-base font-medium mb-3">Institutional Ecosystem Overview</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-card p-3 rounded-lg border border-border shadow-sm">
                  <p className="text-sm text-muted-foreground">Total Institutions</p>
                  <p className="text-2xl font-bold">{processedFocusData?.institutions.length || 0}</p>
                </div>
                <div className="bg-card p-3 rounded-lg border border-border shadow-sm">
                  <p className="text-sm text-muted-foreground">Academic</p>
                  <p className="text-2xl font-bold text-blue-500">
                    {processedFocusData?.institutions.filter(i => i.type === 'academic').length || 0}
                  </p>
                </div>
                <div className="bg-card p-3 rounded-lg border border-border shadow-sm">
                  <p className="text-sm text-muted-foreground">Corporate</p>
                  <p className="text-2xl font-bold text-pink-500">
                    {processedFocusData?.institutions.filter(i => i.type === 'corporate').length || 0}
                  </p>
                </div>
                <div className="bg-card p-3 rounded-lg border border-border shadow-sm">
                  <p className="text-sm text-muted-foreground">High-Impact Papers</p>
                  <p className="text-2xl font-bold text-yellow-500">
                    {processedFocusData?.total_spotlights || 0} + {processedFocusData?.total_orals || 0}
                  </p>
                </div>
              </div>
            </div>
          )}
          
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
      <style>{`
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
