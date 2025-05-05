import React from 'react';
import { 
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid,
    PieChart, Pie, Legend
} from 'recharts';
import { NameValueData } from './types';
import { 
    CustomTooltip, DataTable, InterpretationPanel, 
    ViewToggle, renderActiveShape 
} from './ui-components';

interface IndiaFocusTabProps {
    authorshipPieData: any;
    institutionTypePieData: NameValueData[];
    institutionChartData: any[];
    institutionContributionPieData: NameValueData[];
    processedIndiaData: any;
    interpretations: any;
    activePieIndex: number;
    handlePieEnter: (data: any, index: number) => void;
    viewModes: Record<string, 'chart' | 'table'>;
    handleSetViewMode: (key: string, mode: 'chart' | 'table') => void;
    colorMap: any;
}

const IndiaFocusTab: React.FC<IndiaFocusTabProps> = ({
    authorshipPieData,
    institutionTypePieData,
    institutionChartData,
    institutionContributionPieData,
    processedIndiaData,
    interpretations,
    activePieIndex,
    handlePieEnter,
    viewModes,
    handleSetViewMode,
    colorMap
}) => {
    return (
        <div className="space-y-6 md:space-y-8 animate-fade-in">
            {/* Authorship Patterns */}
            <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                    <div>
                        <h2 className="text-xl font-bold text-foreground">Indian Authorship Patterns</h2>
                        <p className="text-sm text-muted-foreground">Analysis of authorship roles in papers with Indian affiliation.</p>
                    </div>
                    <ViewToggle activeView={viewModes.authorship} setActiveView={(mode) => handleSetViewMode('authorship', mode)} />
                </div>

                {viewModes.authorship === 'chart' && authorshipPieData ? (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Chart Set 1: Majority/Minority */}
                        <div className="space-y-4 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-base font-semibold text-foreground">Authorship Distribution</h3>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={authorshipPieData.authorship} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false} />
                                        <XAxis dataKey="name" stroke={colorMap.textAxis} fontSize={10} interval={0}/>
                                        <YAxis stroke={colorMap.textAxis} fontSize={10} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                            {authorshipPieData.authorship.map((entry: any, index: number) => <Cell key={`cell-author-bar-${index}`} fill={entry.fillVariable} />)}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie data={authorshipPieData.authorship} cx="50%" cy="50%" outerRadius={70} dataKey="value" labelLine={false} >
                                            {authorshipPieData.authorship.map((entry: any, index: number) => <Cell key={`cell-author-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'}/>)}
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend iconSize={10} wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}/>
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                        {/* Chart Set 2: First Author */}
                        <div className="space-y-4 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-base font-semibold text-foreground">First Author Distribution</h3>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={authorshipPieData.firstAuthor} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false} />
                                        <XAxis dataKey="name" stroke={colorMap.textAxis} fontSize={10} interval={0}/>
                                        <YAxis stroke={colorMap.textAxis} fontSize={10} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                            {authorshipPieData.firstAuthor.map((entry: any, index: number) => <Cell key={`cell-first-bar-${index}`} fill={entry.fillVariable} />)}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie data={authorshipPieData.firstAuthor} cx="50%" cy="50%" outerRadius={70} dataKey="value" labelLine={false}>
                                            {authorshipPieData.firstAuthor.map((entry: any, index: number) => <Cell key={`cell-first-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'} />)}
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend iconSize={10} wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}/>
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                        
                        {/* Chart Set 3: Institutional Types */}
                        <div className="space-y-4 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-base font-semibold text-foreground">Institution Types</h3>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={institutionTypePieData} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false} />
                                        <XAxis dataKey="name" stroke={colorMap.textAxis} fontSize={10} />
                                        <YAxis stroke={colorMap.textAxis} fontSize={10} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                            {institutionTypePieData.map((entry, index) => <Cell key={`cell-inst-bar-${index}`} fill={entry.fillVariable} />)}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie data={institutionTypePieData} cx="50%" cy="50%" outerRadius={70} dataKey="value" labelLine={false}>
                                            {institutionTypePieData.map((entry, index) => <Cell key={`cell-inst-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'} />)}
                                        </Pie>
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend iconSize={10} wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}/>
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-8">
                        <DataTable data={authorshipPieData?.authorship.map((item: any) => ({ Category: item.name, Papers: item.value.toLocaleString(), Percentage: `${(item.percent * 100).toFixed(1)}%` })) || []} title="Indian Authorship Distribution" filename="india_authorship_distribution_iclr_2025" />
                        <DataTable data={authorshipPieData?.firstAuthor.map((item: any) => ({ Category: item.name, Papers: item.value.toLocaleString(), Percentage: `${(item.percent * 100).toFixed(1)}%` })) || []} title="First Indian Author Distribution" filename="india_first_author_distribution_iclr_2025" />
                        <DataTable data={institutionTypePieData.map(item => ({ Type: item.name, Papers: item.value.toLocaleString(), Percentage: `${(item.percent * 100).toFixed(1)}%` }))} title="Indian Institution Types" filename="india_institution_types_iclr_2025" />
                    </div>
                )}
                
                <InterpretationPanel title={interpretations.authorshipPatterns.title} insights={interpretations.authorshipPatterns.insights} legend={interpretations.authorshipPatterns.legend} />
            </div>

            {/* Top Indian Institutions */}
            <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                    <div>
                        <h2 className="text-xl font-bold text-foreground">Top Indian Institutions</h2>
                        <p className="text-sm text-muted-foreground">Top contributing institutions based on paper count.</p>
                    </div>
                    <ViewToggle activeView={viewModes.comparison} setActiveView={(mode) => handleSetViewMode('comparison', mode)} />
                </div>
                {viewModes.comparison === 'chart' ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
                        <div className="h-96 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-sm font-medium text-foreground mb-2">Institution Paper Contributions</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={institutionChartData} layout="vertical" margin={{ top: 5, right: 30, left: 140, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false} />
                                    <XAxis type="number" stroke={colorMap.textAxis} axisLine={false} tickLine={false} />
                                    <YAxis type="category" dataKey="institute" stroke={colorMap.textAxis} width={140} tick={{ fontSize: 11, fill: colorMap.textAxis }} interval={0} axisLine={false} tickLine={false} />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }} />
                                    <Bar dataKey="unique_paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={18}>
                                        {institutionChartData.map((entry, index) => <Cell key={`cell-inst-chart-${index}`} fill={entry.fillVariable} />)}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="h-96 bg-muted/30 rounded-lg p-4">
                            <h3 className="text-center text-sm font-medium text-foreground mb-2">Academic vs Corporate Papers</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie activeIndex={activePieIndex} activeShape={renderActiveShape} data={institutionContributionPieData} cx="50%" cy="50%" innerRadius={70} outerRadius={100} dataKey="value" onMouseEnter={handlePieEnter}>
                                        {institutionContributionPieData.map((entry, index) => <Cell key={`cell-inst-contrib-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'} />)}
                                    </Pie>
                                    <Tooltip content={<CustomTooltip />} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                ) : (
                    <DataTable 
                        data={institutionChartData.map(inst => ({ 
                            Institution: inst.institute, 
                            Type: inst.type.charAt(0).toUpperCase() + inst.type.slice(1), 
                            Papers: inst.unique_paper_count,
                            Authors: inst.author_count,
                            Spotlights: inst.spotlights,
                            Orals: inst.orals,
                        }))} 
                        title="Top Indian Institutions" 
                        filename="top_indian_institutions_iclr_2025" 
                    />
                )}
                <InterpretationPanel title={interpretations.institutionComparison.title} insights={interpretations.institutionComparison.insights} legend={interpretations.institutionComparison.legend} />
            </div>

            {/* Trends Section */}
            <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                <h2 className="text-xl font-bold mb-4 text-foreground">Global vs Indian Research Focus</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <h3 className="text-base font-medium text-foreground">Top Global Research Areas:</h3>
                        <ul className="space-y-1.5 ml-4 list-disc text-sm">
                            {processedIndiaData?.global_top_areas?.map((area: string, i: number) => (
                                <li key={i} className="text-foreground">{area}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-base font-medium text-foreground">Top Indian Research Areas:</h3>
                        <ul className="space-y-1.5 ml-4 list-disc text-sm">
                            {processedIndiaData?.india_top_areas?.map((area: string, i: number) => (
                                <li key={i} className="text-foreground">{area}</li>
                            ))}
                        </ul>
                    </div>
                </div>
                <InterpretationPanel title={interpretations.researchFocus.title} insights={interpretations.researchFocus.insights} legend={interpretations.researchFocus.legend} />
            </div>
        </div>
    );
};

export default IndiaFocusTab;
