import React from 'react';
import { FaFileAlt, FaGlobeAsia, FaStar, FaUniversity } from 'react-icons/fa';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { CountryData, ProcessedIndiaData } from './types';
import { CustomTooltip, InterpretationPanel, StatCard } from './ui-components';

interface OverviewTabProps {
    processedIndiaData: ProcessedIndiaData;
    totalPapers: number;
    topIndianInstitution: any;
    topCountriesByPaper: CountryData[];
    colorMap: any;
    conferenceInfo: any;
    interpretations: any;
}

const OverviewTab: React.FC<OverviewTabProps> = ({
    processedIndiaData,
    totalPapers,
    topIndianInstitution,
    topCountriesByPaper,
    colorMap,
    conferenceInfo,
    interpretations
}) => {
    return (
        <div className="space-y-6 md:space-y-8 animate-fade-in">
            <h2 className="text-xl font-semibold text-foreground mb-4">India at {conferenceInfo.name} {conferenceInfo.year}: Overview</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
                <StatCard
                    title="India Papers"
                    value={processedIndiaData.paper_count?.toLocaleString() ?? 'N/A'}
                    icon={<FaFileAlt />}
                    colorClass="text-amber-500 dark:text-amber-400"
                    bgColorClass="bg-amber-600 dark:bg-amber-500"
                    subtitle={`${((processedIndiaData.paper_count ?? 0) / totalPapers * 100).toFixed(1)}% of total`}
                />
                <StatCard
                    title="India's Global Rank"
                    value={`#${processedIndiaData.rank ?? 'N/A'}`}
                    icon={<FaGlobeAsia />}
                    colorClass="text-blue-500 dark:text-blue-400"
                    bgColorClass="bg-blue-600 dark:bg-blue-500"
                    subtitle={`By papers | ${processedIndiaData.author_count?.toLocaleString() ?? 'N/A'} authors`}
                />
                <StatCard
                    title="Spotlights & Orals"
                    value={(processedIndiaData.spotlights ?? 0) + (processedIndiaData.orals ?? 0)}
                    icon={<FaStar />}
                    colorClass="text-yellow-500 dark:text-yellow-400"
                    bgColorClass="bg-yellow-600 dark:bg-yellow-500"
                    subtitle={`${processedIndiaData.spotlights ?? 0} spotlights, ${processedIndiaData.orals ?? 0} orals`}
                />
                <StatCard
                    title="Top Indian Institution"
                    value={topIndianInstitution?.institute || 'N/A'}
                    icon={<FaUniversity />}
                    colorClass="text-emerald-500 dark:text-emerald-400"
                    bgColorClass="bg-emerald-600 dark:bg-emerald-500"
                    subtitle={`${topIndianInstitution?.unique_paper_count || 0} papers | ${topIndianInstitution?.type || 'N/A'}`}
                />
            </div>

            <InterpretationPanel
                title={interpretations.overview.title}
                insights={interpretations.overview.insights}
                legend={interpretations.overview.legend}
            />

            {/* Global Leaderboard Chart */}
            <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                <h2 className="text-xl font-bold mb-1 text-foreground">Global Leaderboard (Top 10)</h2>
                <p className="text-sm text-muted-foreground mb-6">Countries ranked by accepted paper count at {conferenceInfo.name} {conferenceInfo.year}.</p>
                <div className="h-96">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={topCountriesByPaper.slice(0, 10)} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false} />
                            <XAxis type="number" stroke={colorMap.textAxis} axisLine={false} tickLine={false} />
                            <YAxis type="category" dataKey="country_name" stroke={colorMap.textAxis} width={100} tick={{ fontSize: 11, fill: colorMap.textAxis }} interval={0} axisLine={false} tickLine={false} />
                            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }} />
                            <Bar dataKey="paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={20}>
                                {topCountriesByPaper.slice(0, 10).map((entry, index) => (
                                    <Cell key={`cell-paper-${index}`}
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
            </div>
        </div>
    );
};

export default OverviewTab;
