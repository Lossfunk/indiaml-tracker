import React, { useState, useMemo, useCallback } from 'react';
import { DashboardData } from '@/components/dashboard-data';
import { TABS, ViewMode, CountryMap, APAC_COUNTRIES, COUNTRY_CODE_MAP_2_TO_3 } from './types';
import OverviewTab from './OverviewTab';
import GlobalStatsTab from './GlobalStatsTab';
import IndiaFocusTab from './IndiaFocusTab';
import InstitutionsTab from './InstitutionsTab';

// --- Define color mapping for charts ---
const colorMap = {
    primary: 'hsl(var(--primary))',
    secondary: 'hsl(var(--secondary))',
    us: 'hsl(221, 83%, 53%)', // blue-600
    cn: 'hsl(0, 84%, 60%)', // red-600
    in: 'hsl(36, 96%, 50%)', // amber-500
    accent: 'hsl(var(--accent))',
    grid: 'hsl(var(--border))',
    textAxis: 'hsl(var(--muted-foreground))'
};

interface DashboardProps {
    dashboardData: DashboardData;
}

const Dashboard: React.FC<DashboardProps> = ({ dashboardData }) => {
    const [activeTabIndex, setActiveTabIndex] = useState<number>(0);
    const [institutionFilter, setInstitutionFilter] = useState<string>('');
    const [activePieIndex, setActivePieIndex] = useState<number>(0);
    const [viewModes, setViewModes] = useState<Record<string, ViewMode>>({
        global: 'chart',
        apac: 'chart',
        authorship: 'chart',
        comparison: 'chart',
        institutions: 'chart',
    });
    const [globalMapChartMode, setGlobalMapChartMode] = useState<'map' | 'chart'>('map');

    const { conferenceInfo, globalStats, indiaFocus, interpretations } = dashboardData;

    // --- Memoized Data Processing ---

    const sortedCountries = useMemo(() => {
        const countryMap = new Map();
        globalStats.countries.forEach(rawCountry => {
            const countryCode = rawCountry.affiliation_country;
            const countryName = CountryMap[countryCode] || countryCode;
            const existing = countryMap.get(countryName);

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
                countryMap.set(countryName, {
                    affiliation_country: countryCode,
                    country_name: countryName,
                    paper_count: paperCount,
                    author_count: authorCount,
                    spotlights: spotlights,
                    orals: orals,
                    rank: 0, // To be assigned
                    isHighlight: (countryCode === 'US' || countryCode === 'CN' || countryCode === 'IN'),
                });
            }
        });

        const sorted = Array.from(countryMap.values())
                       .sort((a, b) => b.paper_count - a.paper_count || b.author_count - a.author_count);
        sorted.forEach((country, index) => { country.rank = index + 1; });
        return sorted;
    }, [globalStats.countries]);

    const topCountriesByPaper = useMemo(() => sortedCountries.slice(0, 15), [sortedCountries]);
    const usData = useMemo(() => sortedCountries.find(c => c.country_name === 'United States'), [sortedCountries]);
    const cnData = useMemo(() => sortedCountries.find(c => c.country_name === 'China'), [sortedCountries]);
    const indiaGlobalStats = useMemo(() => sortedCountries.find(c => c.country_name === 'India'), [sortedCountries]);

    const processedIndiaData = useMemo(() => {
        if (!indiaGlobalStats) return null;
        const data = { ...indiaFocus };
        data.rank = indiaGlobalStats.rank;
        data.paper_count = indiaGlobalStats.paper_count;
        data.author_count = indiaGlobalStats.author_count;
        data.spotlights = indiaGlobalStats.spotlights;
        data.orals = indiaGlobalStats.orals;
        return data;
    }, [indiaFocus, indiaGlobalStats]);

    const usVsChinaVsRest = useMemo(() => {
        if (!usData || !cnData) return [];
        const usCount = usData.paper_count;
        const cnCount = cnData.paper_count;
        const totalCount = conferenceInfo.totalAcceptedPapers || sortedCountries.reduce((sum, country) => sum + country.paper_count, 0);
        const restCount = Math.max(0, totalCount - usCount - cnCount);
        const totalForPercent = usCount + cnCount + restCount || 1;

        return [
            { name: 'US + China', value: usCount + cnCount, fillVariable: 'hsl(221, 83%, 53%)', percent: (usCount + cnCount) / totalForPercent },
            { name: 'Rest of World', value: restCount, fillVariable: 'hsl(var(--secondary-foreground))', percent: restCount / totalForPercent }
        ];
    }, [usData, cnData, sortedCountries, conferenceInfo.totalAcceptedPapers]);

    const apacCountries = useMemo(() => {
        const filtered = sortedCountries
            .filter(country => APAC_COUNTRIES.includes(country.affiliation_country))
            .sort((a, b) => b.paper_count - a.paper_count);
        const totalApacPapers = filtered.reduce((sum, c) => sum + c.paper_count, 0) || 1;

        return filtered.map(country => ({
            name: country.country_name,
            value: country.paper_count,
            fillVariable: country.country_name === 'China' ? 'hsl(0, 84%, 60%)' :
                           country.country_name === 'India' ? 'hsl(36, 96%, 50%)' :
                           'hsl(var(--secondary-foreground))',
            percent: country.paper_count / totalApacPapers
        }));
    }, [sortedCountries]);

    const authorshipPieData = useMemo(() => {
        if (!processedIndiaData || !processedIndiaData.at_least_one_indian_author) return null;
        const totalWithIndianAuthor = processedIndiaData.at_least_one_indian_author.count || 1;
        const majority = processedIndiaData.majority_indian_authors.count;
        const minority = totalWithIndianAuthor - majority;
        const firstAuthor = processedIndiaData.first_indian_author.count;
        const nonFirstAuthor = totalWithIndianAuthor - firstAuthor;

        return {
            authorship: [
                { name: 'Majority Indian', value: majority, fillVariable: 'hsl(142, 71%, 45%)', percent: majority / totalWithIndianAuthor },
                { name: 'Minority Indian', value: minority, fillVariable: 'hsl(var(--primary))', percent: minority / totalWithIndianAuthor }
            ],
            firstAuthor: [
                { name: 'First Indian Author', value: firstAuthor, fillVariable: 'hsl(330, 80%, 60%)', percent: firstAuthor / totalWithIndianAuthor },
                { name: 'Non-First Indian Author', value: nonFirstAuthor, fillVariable: 'hsl(var(--primary))', percent: nonFirstAuthor / totalWithIndianAuthor }
            ]
        };
    }, [processedIndiaData]);

    const institutionTypePieData = useMemo(() => {
        if (!processedIndiaData || !processedIndiaData.institution_types) return [];
        const academic = processedIndiaData.institution_types.academic || 0;
        const corporate = processedIndiaData.institution_types.corporate || 0;
        const total = academic + corporate || 1;
        return [
            { name: 'Academic', value: academic, fillVariable: 'hsl(221, 83%, 53%)', percent: academic / total },
            { name: 'Corporate', value: corporate, fillVariable: 'hsl(330, 80%, 60%)', percent: corporate / total }
        ];
    }, [processedIndiaData]);

    const filteredInstitutions = useMemo(() => {
        if (!processedIndiaData || !processedIndiaData.institutions) return [];
        return processedIndiaData.institutions
            .filter(inst => inst.institute.toLowerCase().includes(institutionFilter.toLowerCase()))
            .sort((a, b) => b.unique_paper_count - a.unique_paper_count || b.spotlights - a.spotlights || b.orals - a.orals || b.author_count - a.author_count);
    }, [processedIndiaData, institutionFilter]);

    const topIndianInstitution = useMemo(() => filteredInstitutions[0] || null, [filteredInstitutions]);

    const institutionChartData = useMemo(() => {
        return filteredInstitutions.slice(0, 8).map(institution => ({
            ...institution,
            fillVariable: institution.type === 'academic' ? 'hsl(221, 83%, 53%)' : 'hsl(330, 80%, 60%)' // Blue vs Pink
        }));
    }, [filteredInstitutions]);

    const institutionContributionPieData = useMemo(() => {
        if (!filteredInstitutions.length) return [];
        const academicPapers = filteredInstitutions.filter(inst => inst.type === 'academic').reduce((sum, inst) => sum + inst.unique_paper_count, 0);
        const corporatePapers = filteredInstitutions.filter(inst => inst.type === 'corporate').reduce((sum, inst) => sum + inst.unique_paper_count, 0);
        const total = academicPapers + corporatePapers || 1;
        return [
            { name: 'Academic', value: academicPapers, fillVariable: 'hsl(221, 83%, 53%)', percent: academicPapers / total },
            { name: 'Corporate', value: corporatePapers, fillVariable: 'hsl(330, 80%, 60%)', percent: corporatePapers / total }
        ];
    }, [filteredInstitutions]);

    // World Map Data for Plotly
    const worldMapData = useMemo(() => {
        const countryGroups = new Map();

        sortedCountries.forEach(country => {
            const iso3code = COUNTRY_CODE_MAP_2_TO_3[country.affiliation_country];
            if (iso3code) {
                countryGroups.set(iso3code, {
                    iso3code,
                    paperCount: country.paper_count,
                    authorCount: country.author_count,
                    spotlights: country.spotlights,
                    orals: country.orals,
                    countryName: country.country_name
                });
            }
        });

        const groupedData = Array.from(countryGroups.values());
        
        return {
            data: [{
                type: "choropleth",
                locationmode: "ISO-3",
                locations: groupedData.map(d => d.iso3code),
                z: groupedData.map(d => d.paperCount),
                text: groupedData.map(d => `${d.countryName}<br>Papers: ${d.paperCount}<br>Authors: ${d.authorCount}<br>Spotlights: ${d.spotlights}<br>Orals: ${d.orals}`),
                hovertemplate: '%{text}<extra></extra>',
                colorscale: 'Blues',
                colorbar: {
                    title: 'Paper Count',
                    thickness: 20,
                },
                marker: {
                    line: {
                        color: 'rgb(100,100,100)',
                        width: 0.5
                    }
                },
                zmin: 0
            }],
            layout: {
                geo: {
                    projection: { type: 'natural earth' },
                    showlakes: true,
                    lakecolor: 'hsl(var(--card))',
                    bgcolor: 'hsl(var(--card))',
                },
                margin: { t: 0, r: 0, b: 0, l: 0 },
                paper_bgcolor: 'hsl(var(--card))',
                plot_bgcolor: 'hsl(var(--card))',
                height: 500,
                width: null, // auto-width
                autosize: true,
                font: {
                    color: 'hsl(var(--foreground))'
                }
            },
            config: {
                responsive: true,
                displayModeBar: false
            }
        };
    }, [sortedCountries]);

    // --- Event Handlers ---
    
    const handleTabChange = useCallback((index: number) => {
        setActiveTabIndex(index);
    }, []);

    const handlePieEnter = useCallback((_, index: number) => {
        setActivePieIndex(index);
    }, []);

    const handleSetViewMode = useCallback((key: string, mode: ViewMode) => {
        setViewModes(prev => ({ ...prev, [key]: mode }));
    }, []);

    // Calculate total papers once
    const totalPapers = conferenceInfo.totalAcceptedPapers || sortedCountries.reduce((sum, country) => sum + country.paper_count, 0);

    return (
        <div className="min-h-screen bg-background text-foreground">
            <header className="mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-6">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-bold flex items-center text-foreground">
                            India @ {conferenceInfo.name} {conferenceInfo.year}
                        </h1>
                        <p className="text-muted-foreground mt-1 text-sm sm:text-base">An interactive report from India@ML by Lossfunk</p>
                    </div>
                    <div className="bg-card rounded-lg p-3 text-sm text-card-foreground border border-border shadow-sm whitespace-nowrap">
                        Total Accepted Papers: <span className="font-bold text-foreground">{totalPapers.toLocaleString()}</span>
                    </div>
                </div>
                {/* Tabs */}
                <div className="mt-6 border-b border-border">
                    <nav className="-mb-px flex space-x-1 sm:space-x-4 overflow-x-auto pb-0" aria-label="Tabs">
                        {TABS.map((tab, index) => (
                            <button
                                key={tab}
                                onClick={() => handleTabChange(index)}
                                className={`whitespace-nowrap py-3 px-3 sm:px-4 border-b-2 font-medium text-sm sm:text-base focus:outline-none transition-colors duration-200 ${
                                    activeTabIndex === index
                                        ? 'border-primary text-primary'
                                        : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
                                }`}
                                aria-current={activeTabIndex === index ? 'page' : undefined}
                            >
                                {tab}
                            </button>
                        ))}
                    </nav>
                </div>
            </header>

            {/* Tab Content */}
            <main className="mx-auto px-4 sm:px-6 lg:px-8 pb-16">
                {/* Overview Tab */}
                {activeTabIndex === 0 && (
                    <OverviewTab 
                        processedIndiaData={processedIndiaData}
                        totalPapers={totalPapers}
                        topIndianInstitution={topIndianInstitution}
                        topCountriesByPaper={topCountriesByPaper}
                        colorMap={colorMap}
                        conferenceInfo={conferenceInfo}
                        interpretations={interpretations}
                    />
                )}

                {/* Global Stats Tab */}
                {activeTabIndex === 1 && (
                    <GlobalStatsTab 
                        sortedCountries={sortedCountries}
                        topCountriesByPaper={topCountriesByPaper}
                        usVsChinaVsRest={usVsChinaVsRest}
                        apacCountries={apacCountries}
                        totalPapers={totalPapers}
                        colorMap={colorMap}
                        worldMapData={worldMapData}
                        interpretations={interpretations}
                        activePieIndex={activePieIndex}
                        handlePieEnter={handlePieEnter}
                        globalMapChartMode={globalMapChartMode}
                        setGlobalMapChartMode={setGlobalMapChartMode}
                        viewModes={viewModes}
                        handleSetViewMode={handleSetViewMode}
                    />
                )}

                {/* India Focus Tab */}
                {activeTabIndex === 2 && (
                    <IndiaFocusTab 
                        authorshipPieData={authorshipPieData}
                        institutionTypePieData={institutionTypePieData}
                        institutionChartData={institutionChartData}
                        institutionContributionPieData={institutionContributionPieData}
                        processedIndiaData={processedIndiaData}
                        interpretations={interpretations}
                        activePieIndex={activePieIndex}
                        handlePieEnter={handlePieEnter}
                        viewModes={viewModes}
                        handleSetViewMode={handleSetViewMode}
                        colorMap={colorMap}
                    />
                )}

                {/* Institutions Tab */}
                {activeTabIndex === 3 && (
                    <InstitutionsTab 
                        filteredInstitutions={filteredInstitutions}
                        institutionFilter={institutionFilter}
                        setInstitutionFilter={setInstitutionFilter}
                    />
                )}
            </main>
        </div>
    );
};

export default Dashboard;
