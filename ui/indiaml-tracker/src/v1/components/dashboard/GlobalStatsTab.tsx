import React from 'react';
import { 
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid,
    PieChart, Pie
} from 'recharts';
import Plot from 'react-plotly.js';
import { CountryData, NameValueData } from './types';
import { 
    CustomTooltip, DataTable, InterpretationPanel, MapChartViewToggle, 
    ViewToggle, renderActiveShape 
} from './ui-components';

interface GlobalStatsTabProps {
    sortedCountries: CountryData[];
    topCountriesByPaper: CountryData[];
    usVsChinaVsRest: NameValueData[];
    apacCountries: NameValueData[];
    totalPapers: number;
    colorMap: any;
    worldMapData: any;
    interpretations: any;
    activePieIndex: number;
    handlePieEnter: (data: any, index: number) => void;
    globalMapChartMode: 'map' | 'chart';
    setGlobalMapChartMode: (mode: 'map' | 'chart') => void;
    viewModes: Record<string, 'chart' | 'table'>;
    handleSetViewMode: (key: string, mode: 'chart' | 'table') => void;
}

const GlobalStatsTab: React.FC<GlobalStatsTabProps> = ({
    sortedCountries,
    topCountriesByPaper,
    usVsChinaVsRest,
    apacCountries,
    totalPapers,
    colorMap,
    worldMapData,
    interpretations,
    activePieIndex,
    handlePieEnter,
    globalMapChartMode,
    setGlobalMapChartMode,
    viewModes,
    handleSetViewMode
}) => {
    return (
        <div className="space-y-6 md:space-y-8 animate-fade-in">
            {/* Global Map/Chart */}
            <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                    <div>
                        <h2 className="text-xl font-bold text-foreground">Global Research Distribution</h2>
                        <p className="text-sm text-muted-foreground">Interactive world map and chart of geographical research concentration.</p>
                    </div>
                    <MapChartViewToggle 
                        activeView={globalMapChartMode} 
                        setActiveView={setGlobalMapChartMode} 
                    />
                </div>
                {globalMapChartMode === 'map' ? (
                    <div className="h-[500px]">
                        <Plot
                            data={worldMapData.data}
                            layout={worldMapData.layout}
                            config={worldMapData.config}
                            style={{ width: '100%', height: '100%' }}
                        />
                    </div>
                ) : (
                    <div className="h-96">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={topCountriesByPaper} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false} />
                                <XAxis type="number" stroke={colorMap.textAxis} axisLine={false} tickLine={false} />
                                <YAxis type="category" dataKey="country_name" stroke={colorMap.textAxis} width={100} tick={{ fontSize: 11, fill: colorMap.textAxis }} interval={0} axisLine={false} tickLine={false} />
                                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }} />
                                <Bar dataKey="paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={20}>
                                    {topCountriesByPaper.map((entry, index) => (
                                        <Cell key={`cell-global-bar-${index}`}
                                            fill={entry.affiliation_country === 'US' ? colorMap.us :
                                                    entry.affiliation_country === 'CN' ? colorMap.cn :
                                                    entry.affiliation_country === 'IN' ? colorMap.in :
                                                    colorMap.primary}
                                            fillOpacity={entry.isHighlight ? 1 : 0.8} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}
                <InterpretationPanel
                    title="Global Research Distribution: Understanding the Landscape"
                    insights={[
                        "The map and chart reveal significant geographic concentration in AI research, with the US, China, and select regions dominating paper output.",
                        "Countries with darker shading on the map indicate higher paper counts. This visualization helps identify both established leaders and emerging research hubs.",
                        "Notable secondary hubs include UK, Singapore, South Korea, Germany, and Canada, each contributing substantial research output.",
                        "Geographic patterns suggest clustering of research activity around major institutions and technology centers."
                    ]}
                    legend="Toggle between the interactive world map and bar chart to explore different perspectives on the global research distribution."
                />
            </div>

            {/* US + China vs Rest of World */}
            <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                    <div>
                        <h2 className="text-xl font-bold text-foreground">Global Distribution: US+China vs. Rest</h2>
                        <p className="text-sm text-muted-foreground">Paper share showing the concentration of research output.</p>
                    </div>
                    <ViewToggle activeView={viewModes.global} setActiveView={(mode) => handleSetViewMode('global', mode)} />
                </div>
                {viewModes.global === 'chart' ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
                        <div className="h-80 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-sm font-medium text-foreground mb-2">Absolute Paper Count</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={usVsChinaVsRest} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false} />
                                    <XAxis dataKey="name" stroke={colorMap.textAxis} fontSize={11} />
                                    <YAxis stroke={colorMap.textAxis} fontSize={11} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                        {usVsChinaVsRest.map((entry, index) => <Cell key={`cell-global-bar-${index}`} fill={entry.fillVariable} />)}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="h-80 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-sm font-medium text-foreground mb-2">Percentage Share</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie activeIndex={activePieIndex} activeShape={renderActiveShape} data={usVsChinaVsRest} cx="50%" cy="50%" innerRadius={60} outerRadius={85} dataKey="value" onMouseEnter={handlePieEnter}>
                                        {usVsChinaVsRest.map((entry, index) => <Cell key={`cell-global-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'} />)}
                                    </Pie>
                                    <Tooltip content={<CustomTooltip />} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                ) : (
                    <DataTable data={usVsChinaVsRest.map(item => ({ Region: item.name, Papers: item.value.toLocaleString(), Percentage: `${(item.percent * 100).toFixed(1)}%` }))} title="Global Distribution Summary" filename="global_distribution_iclr_2025" />
                )}
                <InterpretationPanel title={interpretations.globalDistribution.title} insights={interpretations.globalDistribution.insights} legend={interpretations.globalDistribution.legend} />
            </div>

            {/* APAC Countries */}
            <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                    <div>
                        <h2 className="text-xl font-bold text-foreground">APAC Contributions</h2>
                        <p className="text-sm text-muted-foreground">Paper distribution within key Asia-Pacific countries.</p>
                    </div>
                    <ViewToggle activeView={viewModes.apac} setActiveView={(mode) => handleSetViewMode('apac', mode)} />
                </div>
                {viewModes.apac === 'chart' ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
                        <div className="h-96 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-sm font-medium text-foreground mb-2">Papers by APAC Country</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={apacCountries} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false} />
                                    <XAxis type="number" stroke={colorMap.textAxis} axisLine={false} tickLine={false} />
                                    <YAxis type="category" dataKey="name" stroke={colorMap.textAxis} width={100} tick={{ fontSize: 11, fill: colorMap.textAxis }} interval={0} axisLine={false} tickLine={false} />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }} />
                                    <Bar dataKey="value" name="Papers" radius={[0, 4, 4, 0]} barSize={18}>
                                        {apacCountries.map((entry, index) => <Cell key={`cell-apac-bar-${index}`} fill={entry.fillVariable} />)}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="h-96 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-sm font-medium text-foreground mb-2">APAC Contribution Share</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie activeIndex={activePieIndex} activeShape={renderActiveShape} data={apacCountries} cx="50%" cy="50%" innerRadius={70} outerRadius={100} dataKey="value" onMouseEnter={handlePieEnter}>
                                        {apacCountries.map((entry, index) => <Cell key={`cell-apac-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'} />)}
                                    </Pie>
                                    <Tooltip content={<CustomTooltip />} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                ) : (
                    <DataTable data={apacCountries.map(item => ({ Country: item.name, Papers: item.value.toLocaleString(), '%_of_APAC_Group': `${(item.percent * 100).toFixed(1)}%`, '%_of_Global_Total': `${((item.value / totalPapers) * 100).toFixed(1)}%`, highlight: item.name === 'China' || item.name === 'India' }))} title="APAC Country Distribution Summary" filename="apac_distribution_iclr_2025" />
                )}
                <InterpretationPanel title={interpretations.apacContributions.title} insights={interpretations.apacContributions.insights} legend={interpretations.apacContributions.legend} />
            </div>

            {/* Complete Country List Table */}
            <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                <h2 className="text-xl font-bold mb-4 text-foreground">Complete Country Contributions</h2>
                <DataTable data={sortedCountries.map(country => ({ Rank: country.rank, Country: country.country_name, Papers: country.paper_count.toLocaleString(), 'Percentage': `${((country.paper_count / totalPapers) * 100).toFixed(2)}%`, Authors: country.author_count.toLocaleString(), Spotlights: country.spotlights, Orals: country.orals, highlight: country.country_name === 'India' }))} title="All Countries Ranked by Paper Count" filename="all_countries_ranked_iclr_2025" />
            </div>
        </div>
    );
};

export default GlobalStatsTab;
