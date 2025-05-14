import React, { useState, useMemo, useCallback, useEffect } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend, CartesianGrid,
    PieChart, Pie, Sector, TooltipProps, AreaChart, Area, LabelList, Label
} from 'recharts';
import {
    FaGlobeAsia, FaUniversity, FaUserFriends, FaSearch, FaFileAlt,
    FaInfoCircle, FaUserTie, FaTrophy, FaUsers, FaChartPie,
    FaGraduationCap, FaBuilding, FaChalkboardTeacher, FaStar,
    FaDownload, FaTable, FaChartBar, FaLightbulb, FaChevronDown, FaChevronUp,
    FaArrowRight, FaBalanceScale, FaProjectDiagram, FaBullseye, FaChartLine, FaArrowDown,
    FaLink, FaUnlink, FaGlobe, FaUser
} from 'react-icons/fa';

// --- Type definitions (from ConferenceDashboard) ---
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
            papers: any[];
        };
        majority_focus_country_authors: {
            count: number;
            papers: any[];
        };
        first_focus_country_author: {
            count: number;
            papers: any[];
        };
        institutions: Array<{
            institute: string;
            total_paper_count: number;
            unique_paper_count: number;
            author_count: number;
            spotlights: number;
            orals: number;
            type: 'academic' | 'corporate' | 'unknown';
            papers: Array<{
                id: string;
                title: string;
                isSpotlight?: boolean;
                isOral?: boolean;
            }>;
            authors: string[];
        }>;
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
            summary: { title: string; insights: string[]; };
            context: { title: string; subtitle: string; insights: string[]; };
            focusCountry: { title: string; subtitle: string; insights: string[]; };
            institutions: { title: string; subtitle: string; insights: string[]; };
        }
    };
}

interface PaperSummary { id: string; title: string; isSpotlight?: boolean; isOral?: boolean; }
interface InstitutionData {
    institute: string;
    total_paper_count: number;
    unique_paper_count: number;
    author_count: number;
    spotlights: number;
    orals: number;
    type: 'academic' | 'corporate' | 'unknown';
    papers: PaperSummary[];
    authors?: string[];
    authors_per_paper?: number;
    impact_score?: number;
    normalized_papers?: number;
    normalized_authors?: number;
}
interface CountryData { 
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
type ProcessedFocusCountryData = DashboardDataInterface['focusCountry'] & { 
    rank?: number; 
    paper_count?: number; 
    author_count: number; 
    spotlights: number; 
    orals: number; 
    spotlight_oral_rate?: number; 
    authors_per_paper?: number; 
    institutions: InstitutionData[]; 
}

// Index file entry structure
interface TrackerIndexEntry {
    label: string;
    file: string;
    analytics: string;
    venue: string;
    year: string;
}


// --- Reusable Helper Functions ---
const exportToCSV = (data: Record<string, any>[], filename: string): void => {
    if (!data || data.length === 0) { console.warn("Export Aborted: No data provided."); return; }
    try {
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => {
                const value = row[header] !== undefined && row[header] !== null ? row[header] : '';
                let stringValue = String(value);
                if (Array.isArray(value)) {
                    stringValue = value.join('; '); 
                }
                stringValue = stringValue.replace(/"/g, '""'); 
                if (stringValue.includes(',')) { stringValue = `"${stringValue}"`; } 
                return stringValue;
            }).join(','))
        ].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `${filename}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    } catch (error) { console.error("Error exporting to CSV:", error); }
};

const normalizeValues = (data: any[], key: string) => {
    if (!data || data.length === 0) return [];
    const values = data.map(item => item[key] || 0);
    if (values.length === 0) return data.map(item => ({ ...item, [`normalized_${key}`]: 0 }));

    const maxValue = Math.max(...values);
    return data.map(item => ({
        ...item,
        [`normalized_${key}`]: maxValue > 0 ? (item[key] || 0) / maxValue : 0
    }));
};

// --- Reusable UI Components (Section, StatCard, etc. - unchanged) ---
interface SectionProps {
    title: string;
    subtitle?: string;
    children: React.ReactNode;
    id?: string;
    className?: string;
}
const Section: React.FC<SectionProps> = ({ title, subtitle, children, id, className = '' }) => (
    <section id={id} className={`py-8 md:py-12 border-b border-border last:border-b-0 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-2">{title}</h2>
            {subtitle && <p className="text-base md:text-lg text-muted-foreground mb-6 md:mb-8">{subtitle}</p>}
            {children}
        </div>
    </section>
);

interface StatCardProps {
    title: string;
    value: string | number;
    icon?: React.ReactNode;
    colorClass: string;
    subtitle?: string;
    className?: string;
}
const StatCard: React.FC<StatCardProps> = ({ title, value, icon, colorClass, subtitle, className = '' }) => (
    <div className={`bg-card border border-border p-6 rounded-xl shadow-lg flex flex-col text-center items-center ${className}`}>
        {icon && <div className={`${colorClass} text-3xl mb-3`}>{icon}</div>}
        <p className={`text-4xl md:text-5xl font-bold text-foreground mb-1`}>{value}</p>
        <h3 className="text-muted-foreground font-medium text-sm uppercase tracking-wider mb-2">{title}</h3>
        {subtitle && <p className="text-muted-foreground text-xs">{subtitle}</p>}
    </div>
);

const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload; 
        const formatValue = (val: any) => typeof val === 'number' ? val.toLocaleString() : String(val);
        const formatPercent = (val: any) => typeof val === 'number' ? `${(val * 100).toFixed(1)}%` : String(val);
        const formatDecimal = (val: any, places = 1) => typeof val === 'number' ? val.toFixed(places) : String(val);
        let title = label || data?.country_name || data?.institute || data?.name || "Details";
        if (data?.stage) title = data.stage;
        if (data?.type && (data.type === 'Academic' || data.type === 'Corporate')) title = data.type;

        return (
            <div className="bg-popover border border-border p-3 rounded-lg shadow-xl opacity-95 text-sm max-w-xs">
                <p className="text-muted-foreground font-medium mb-1 break-words">{title}</p>
                {payload.map((pld, index) => (
                    <p key={index} style={{ color: pld.color || 'hsl(var(--foreground))' }} className="break-words">
                        {`${pld.name}: ${formatValue(pld.value)}`}
                        {pld.payload?.percent && ` (${formatPercent(pld.payload.percent)})`}
                    </p>
                ))}
                {data?.rank && <p className="text-muted-foreground text-xs mt-1">{`Rank: #${data.rank}`}</p>}
                {data?.paper_count !== undefined && !payload.some(p => p.dataKey === 'paper_count' || p.dataKey === 'unique_paper_count') &&
                    <p className="text-muted-foreground text-xs mt-1">{`Papers: ${formatValue(data.paper_count)}`}</p>}
                {data?.unique_paper_count !== undefined && !payload.some(p => p.dataKey === 'unique_paper_count' || p.dataKey === 'paper_count') &&
                    <p className="text-muted-foreground text-xs mt-1">{`Unique Papers: ${formatValue(data.unique_paper_count)}`}</p>}
                {data?.author_count !== undefined && data.author_count > 0 && !payload.some(p => p.dataKey === 'author_count' || p.name === 'Authors') &&
                    <p className="text-muted-foreground text-xs mt-1">{`Authors: ${formatValue(data.author_count)}`}</p>}
                {data?.type && (data.type === 'academic' || data.type === 'corporate') && <p className="text-muted-foreground text-xs mt-1 capitalize">{`Type: ${data.type}`}</p>}
                {data?.spotlight_oral_rate !== undefined && <p className="text-muted-foreground text-xs mt-1">{`Spotlight/Oral Rate: ${formatPercent(data.spotlight_oral_rate)}`}</p>}
                {data?.authors_per_paper !== undefined && <p className="text-muted-foreground text-xs mt-1">{`Authors/Paper: ${formatDecimal(data.authors_per_paper, 1)}`}</p>}
                {(data?.spotlights !== undefined || data?.orals !== undefined) &&
                    <p className="text-muted-foreground text-xs mt-1">
                        Impact: {data.spotlights ?? 0} Spotlight(s), {data.orals ?? 0} Oral(s)
                    </p>
                }
                {data?.impact_score !== undefined && !payload.some(p => p.name === 'Spotlights + Orals' || p.name === 'Impact (Spotlights+Orals)') &&
                    <p className="text-muted-foreground text-xs mt-1">{`Impact (Spotlights+Orals): ${formatValue(data.impact_score)}`}</p>
                }
            </div>
        );
    }
    return null;
};

const renderActiveShape = (props: any) => {
    const RADIAN = Math.PI / 180;
    const { cx = 0, cy = 0, midAngle = 0, innerRadius = 0, outerRadius = 0, startAngle = 0, endAngle = 0, fill = 'hsl(var(--primary))', payload, percent = 0, value = 0, name = '' } = props;
    const sin = Math.sin(-RADIAN * midAngle);
    const cos = Math.cos(-RADIAN * midAngle);
    const sx = cx + (outerRadius + 10) * cos;
    const sy = cy + (outerRadius + 10) * sin;
    const mx = cx + (outerRadius + 30) * cos;
    const my = cy + (outerRadius + 30) * sin;
    const ex = mx + (cos >= 0 ? 1 : -1) * 22;
    const ey = my;
    const textAnchor = cos >= 0 ? 'start' : 'end';
    const textColor = 'hsl(var(--foreground))';
    const mutedColor = 'hsl(var(--muted-foreground))';

    return (
        <g>
            <text x={cx} y={cy} dy={8} textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold">
                {payload?.name || name}
            </text>
            <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius} startAngle={startAngle} endAngle={endAngle} fill={fill} />
            <Sector cx={cx} cy={cy} startAngle={startAngle} endAngle={endAngle} innerRadius={outerRadius + 6} outerRadius={outerRadius + 10} fill={fill} />
            <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
            <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill={textColor} fontSize="11">
                {`${value?.toLocaleString()}`}
            </text>
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} dy={18} textAnchor={textAnchor} fill={mutedColor} fontSize="10">
                {`(${(percent * 100).toFixed(1)}%)`}
            </text>
        </g>
    );
};

interface InterpretationPanelProps {
    insights: string[];
    title?: string;
    icon?: React.ReactNode;
    iconColorClass?: string;
}
const InterpretationPanel: React.FC<InterpretationPanelProps> = ({ insights, title = "Key Insights", icon = <FaLightbulb />, iconColorClass = "text-amber-500 dark:text-amber-400" }) => (
    <div className="mt-6 bg-muted/50 rounded-lg border border-border p-4">
        <div className="flex items-start mb-3">
            <span className={`mr-3 mt-1 flex-shrink-0 ${iconColorClass}`}>{icon}</span>
            <h4 className="text-base font-semibold text-foreground">{title}</h4>
        </div>
        <ul className="space-y-2 list-disc list-inside text-muted-foreground text-sm">
            {(insights || []).map((insight, idx) => <li key={idx}>{insight}</li>)}
        </ul>
    </div>
);

interface TabButtonProps {
    active: boolean;
    onClick: () => void;
    children: React.ReactNode;
    icon?: React.ReactNode;
}
const TabButton: React.FC<TabButtonProps> = ({ active, onClick, children, icon }) => (
    <button
        onClick={onClick}
        className={`flex items-center justify-center px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            active 
                ? 'bg-card text-foreground border-t border-l border-r border-border'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
        }`}
    >
        {icon && <span className="mr-2">{icon}</span>}
        {children}
    </button>
);

interface InstitutionCardProps { institution: InstitutionData; index: number; }
const InstitutionCard: React.FC<InstitutionCardProps> = ({ institution, index }) => {
    const [isExpanded, setIsExpanded] = useState(index === 0);
    const [activeTab, setActiveTab] = useState<'papers' | 'authors'>('papers');
    
    const toggleExpansion = useCallback(() => setIsExpanded(prev => !prev), []);
    const animationDelay = `${index * 0.05}s`;
    const detailsId = `institution-details-${institution.institute.replace(/\s+/g, '-')}-${index}`;

    return (
        <div
            className="bg-card rounded-lg shadow-md overflow-hidden mb-4 border border-border hover:border-primary transition-all duration-300 animate-fade-in"
            style={{ animationDelay, opacity: 0, animationFillMode: 'forwards' }}
        >
            <div
                className="p-4 cursor-pointer flex justify-between items-center"
                onClick={toggleExpansion} role="button" aria-expanded={isExpanded} aria-controls={detailsId}
            >
                <div className="flex-1 mr-4 overflow-hidden">
                    <h3 className="text-card-foreground font-medium truncate" title={institution.institute}>{institution.institute}</h3>
                    <div className="flex items-center flex-wrap text-sm text-muted-foreground mt-1 space-x-4">
                        <span className="flex items-center whitespace-nowrap">
                            <FaFileAlt className="mr-1.5 text-blue-500 dark:text-blue-400 flex-shrink-0" />
                            <span className="text-blue-500 dark:text-blue-400 font-medium">{institution.unique_paper_count}</span>
                            &nbsp;{institution.unique_paper_count === 1 ? 'Paper' : 'Papers'}
                        </span>
                        <span className="flex items-center whitespace-nowrap">
                            <FaUsers className="mr-1.5 text-pink-500 dark:text-pink-400 flex-shrink-0" />
                            <span className="text-pink-500 dark:text-pink-400 font-medium">{institution.author_count}</span>
                            &nbsp;{institution.author_count === 1 ? 'Author' : 'Authors'}
                        </span>
                        {institution.spotlights > 0 && (<span className="flex items-center whitespace-nowrap"><FaStar className="mr-1.5 text-yellow-500 dark:text-yellow-400 flex-shrink-0" />{institution.spotlights} {institution.spotlights === 1 ? 'Spotlight' : 'Spotlights'}</span>)}
                        {institution.orals > 0 && (<span className="flex items-center whitespace-nowrap"><FaTrophy className="mr-1.5 text-emerald-500 dark:text-emerald-400 flex-shrink-0" />{institution.orals} {institution.orals === 1 ? 'Oral' : 'Orals'}</span>)}
                        <span className="flex items-center whitespace-nowrap capitalize">
                            {institution.type === 'academic' ? <FaGraduationCap className="mr-1.5 text-blue-500 dark:text-blue-400 flex-shrink-0" /> : <FaBuilding className="mr-1.5 text-pink-500 dark:text-pink-400 flex-shrink-0" />} {institution.type}
                        </span>
                    </div>
                </div>
                <div className={`transform transition-transform duration-300 flex-shrink-0 ${isExpanded ? 'rotate-180' : ''}`}><FaChevronDown className="w-5 h-5 text-muted-foreground" /></div>
            </div>
            {isExpanded && (
                <div id={detailsId} className="border-t border-border">
                    <div className="flex border-b border-border px-4 pt-3 bg-muted/20">
                        <TabButton 
                            active={activeTab === 'papers'} 
                            onClick={() => setActiveTab('papers')}
                            icon={<FaFileAlt className="text-blue-500" size={14} />}
                        >
                            Papers ({institution.unique_paper_count})
                        </TabButton>
                        <TabButton 
                            active={activeTab === 'authors'} 
                            onClick={() => setActiveTab('authors')}
                            icon={<FaUser className="text-pink-500" size={14} />}
                        >
                            Authors ({institution.author_count})
                        </TabButton>
                    </div>
                    <div className="px-4 pb-4 pt-3">
                        {activeTab === 'papers' && (
                            <div>
                                {institution.papers && institution.papers.length > 0 ? (
                                    <ul className="space-y-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                                        {institution.papers.map((paper, idx) => (
                                            <li key={`${paper.id}-${idx}`} className="text-muted-foreground text-sm bg-background p-3 rounded-md shadow-sm">
                                                <a href={`https://openreview.net/forum?id=${paper.id}`} target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors block break-words" title={paper.title}>
                                                    {paper.title} <span className="text-xs text-muted-foreground/70 ml-1">(ID: {paper.id})</span>
                                                </a>
                                                {paper.isSpotlight && (<span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"><FaStar className="mr-1" size={10} />Spotlight</span>)}
                                                {paper.isOral && (<span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300"><FaTrophy className="mr-1" size={10} />Oral</span>)}
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="text-muted-foreground/70 text-sm italic py-3">No specific paper details available.</p>
                                )}
                            </div>
                        )}
                        {activeTab === 'authors' && (
                            <div>
                                {institution.authors && institution.authors.length > 0 ? (
                                    <ul className="space-y-1.5 max-h-60 overflow-y-auto pr-2 custom-scrollbar text-sm text-muted-foreground">
                                        {institution.authors.map((author, idx) => (
                                            <li key={`author-${idx}`} className="flex items-center bg-background p-2 rounded-md">
                                                <FaUser className="mr-2 text-pink-400 flex-shrink-0" size={12}/>
                                                <span>{author}</span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="text-muted-foreground/70 text-sm italic py-3">Author details not available.</p>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

interface DataTableProps { data: Record<string, string | number | boolean | undefined | null>[]; title: string; filename: string; }
const DataTable: React.FC<DataTableProps> = ({ data, title, filename }) => {
    if (!data || data.length === 0) { return <div className="text-muted-foreground p-4">No data available for the table.</div>; }
    const headers = data.length > 0 ? Object.keys(data[0]) : [];
    const handleExport = useCallback(() => exportToCSV(data, filename), [data, filename]);

    return (
        <div className="overflow-x-auto mt-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                <h4 className="text-foreground font-medium text-lg">{title}</h4>
                <button onClick={handleExport} className="flex items-center bg-primary hover:bg-primary/90 text-primary-foreground text-xs px-3 py-1.5 rounded transition-colors shadow-sm" aria-label={`Export ${title} data to CSV`}>
                    <FaDownload className="mr-1.5" size={10} /> Export CSV
                </button>
            </div>
            <div className="border border-border rounded-lg overflow-hidden shadow-sm">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted">
                        <tr>{headers.map((header) => (<th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider whitespace-nowrap">{header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>))}</tr>
                    </thead>
                    <tbody className="bg-card divide-y divide-border">
                        {data.map((row, rowIndex) => (
                            <tr key={rowIndex} className={`${row.highlight ? 'bg-amber-100 dark:bg-amber-900/30 font-medium' : ''} hover:bg-muted/50 transition-colors`}>
                                {headers.map((header, colIndex) => (
                                    <td key={`${rowIndex}-${colIndex}`} className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                                        {Array.isArray(row[header])
                                            ? (row[header] as (string | number)[]).slice(0, 3).join(', ') + ((row[header] as any[]).length > 3 ? '...' : '')
                                            : typeof row[header] === 'boolean'
                                                ? (row[header] ? 'Yes' : 'No')
                                                : (row[header]?.toLocaleString() ?? '')
                                        }
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};


// --- Main Dashboard Component ---
interface ConferenceDashboardProps {
    conference: string; 
    year: string;
    conferenceSelectorElement: React.ReactNode; // Prop to pass the selector UI
}

const ConferenceDashboard: React.FC<ConferenceDashboardProps> = ({ conference, year, conferenceSelectorElement }) => {
    // State Hooks
    const [fetchedDashboardData, setFetchedDashboardData] = useState<DashboardDataInterface | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [institutionFilter, setInstitutionFilter] = useState<string>('');
    const [activePieIndex, setActivePieIndex] = useState<number>(0);

    // Effect Hook for data fetching
    useEffect(() => {
        const fetchData = async () => {
            if (!conference || !year) { 
                setLoading(false);
                setError("Conference and year must be selected.");
                return;
            }
            setLoading(true);
            setError(null);
            setFetchedDashboardData(null); 
            try {
                const indexResponse = await fetch('/tracker/index.json');
                if (!indexResponse.ok) throw new Error(`Failed to fetch /tracker/index.json: ${indexResponse.status} ${indexResponse.statusText}`);
                const indexData: TrackerIndexEntry[] = await indexResponse.json();
                const conferenceEntry = indexData.find(item => item.venue.toLowerCase() === conference.toLowerCase() && String(item.year) === String(year));
                if (!conferenceEntry || !conferenceEntry.analytics) throw new Error(`No analytics data configuration found for ${conference.toUpperCase()} ${year}.`);
                
                const analyticsUrl = `/tracker/${conferenceEntry.analytics}`;
                const analyticsResponse = await fetch(analyticsUrl);
                if (!analyticsResponse.ok) throw new Error(`Failed to fetch ${analyticsUrl}: ${analyticsResponse.status} ${analyticsResponse.statusText}`);
                const analyticsData = await analyticsResponse.json();
                setFetchedDashboardData(analyticsData as DashboardDataInterface);
            } catch (e: any) {
                console.error("Dashboard data fetching error:", e);
                setError(e.message || 'An unknown error occurred.');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [conference, year]);

    // Memoized Data Processing Hooks
    const sortedCountries: CountryData[] = useMemo(() => {
        if (!fetchedDashboardData?.globalStats?.countries || !fetchedDashboardData?.configuration?.countryMap || !fetchedDashboardData?.focusCountry?.country_code) {
            return [];
        }
        const { globalStats, configuration, focusCountry } = fetchedDashboardData;
        const focusCountryCodeVal = focusCountry.country_code;

        const currentCountryMap = new Map<string, CountryData>();
        globalStats.countries.forEach(rawCountry => {
            const countryCode = rawCountry.affiliation_country;
            const countryName = (countryCode === 'UK' || countryCode === 'GB') 
                ? (configuration.countryMap['GB'] || 'United Kingdom') 
                : (configuration.countryMap[countryCode] || countryCode);
            
            const existing = currentCountryMap.get(countryName);
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
                currentCountryMap.set(countryName, {
                    affiliation_country: countryCode === 'UK' ? 'GB' : countryCode,
                    country_name: countryName,
                    paper_count: paperCount, author_count: authorCount,
                    spotlights: spotlights, orals: orals, rank: 0,
                    isHighlight: (countryCode === 'US' || countryCode === 'CN' || countryCode === focusCountryCodeVal),
                });
            }
        });

        const sorted = Array.from(currentCountryMap.values())
            .sort((a, b) => b.paper_count - a.paper_count || b.author_count - a.author_count);

        sorted.forEach((country, index) => {
            country.rank = index + 1;
            country.spotlight_oral_rate = country.paper_count > 0 ? ((country.spotlights + country.orals) / country.paper_count) : 0;
            country.authors_per_paper = country.paper_count > 0 ? (country.author_count / country.paper_count) : 0;
        });
        
        const normalizedPapers = normalizeValues(sorted, 'paper_count');
        return normalizeValues(normalizedPapers, 'author_count');
    }, [fetchedDashboardData]); 

    const topCountriesByPaper = useMemo(() => sortedCountries.slice(0, 15), [sortedCountries]);
    const usData = useMemo(() => sortedCountries.find(c => c.affiliation_country === 'US'), [sortedCountries]);
    const cnData = useMemo(() => sortedCountries.find(c => c.affiliation_country === 'CN'), [sortedCountries]);
    const focusCountryGlobalStats = useMemo(() => {
        const focusCode = fetchedDashboardData?.focusCountry?.country_code;
        if (!focusCode) return undefined;
        return sortedCountries.find(c => c.affiliation_country === focusCode);
    }, [sortedCountries, fetchedDashboardData?.focusCountry?.country_code]);

    const processedFocusData: ProcessedFocusCountryData | null = useMemo(() => {
        if (!focusCountryGlobalStats || !fetchedDashboardData?.focusCountry) return null;
        const { focusCountry } = fetchedDashboardData;
        const institutions = (focusCountry.institutions || []).map(inst => ({
            ...inst,
            authors_per_paper: inst.unique_paper_count > 0 ? (inst.author_count / inst.unique_paper_count) : 0,
            impact_score: (inst.spotlights ?? 0) + (inst.orals ?? 0),
            authors: inst.authors || [],
        }));
        const normalizedInstitutions = normalizeValues(institutions, 'unique_paper_count');
        const processedInstitutions = normalizeValues(normalizedInstitutions, 'author_count');
        const data: ProcessedFocusCountryData = {
            ...focusCountry, 
            institutions: processedInstitutions,
            rank: focusCountryGlobalStats.rank,
            paper_count: focusCountryGlobalStats.paper_count,
            author_count: focusCountryGlobalStats.author_count, 
            spotlights: focusCountryGlobalStats.spotlights, 
            orals: focusCountryGlobalStats.orals, 
            spotlight_oral_rate: focusCountryGlobalStats.spotlight_oral_rate ?? 0,
            authors_per_paper: focusCountryGlobalStats.authors_per_paper ?? 0,
        };
        return data;
    }, [focusCountryGlobalStats, fetchedDashboardData?.focusCountry]);
    
    const usChinaDominancePieData = useMemo(() => {
        if (!usData || !cnData || !fetchedDashboardData?.conferenceInfo?.totalAcceptedPapers || !fetchedDashboardData?.configuration?.colorScheme) return [];
        const totalPapers = fetchedDashboardData.conferenceInfo.totalAcceptedPapers;
        if (totalPapers === 0) return [];
        const usCount = usData.paper_count;
        const cnCount = cnData.paper_count;
        const restCount = Math.max(0, totalPapers - usCount - cnCount);
        return [
            { name: 'United States', value: usCount, percent: usCount / totalPapers, fill: fetchedDashboardData.configuration.colorScheme.us }, 
            { name: 'China', value: cnCount, percent: cnCount / totalPapers, fill: fetchedDashboardData.configuration.colorScheme.cn },
            { name: 'Rest of World', value: restCount, percent: restCount / totalPapers, fill: 'hsl(var(--muted))' }
        ];
    }, [usData, cnData, fetchedDashboardData?.conferenceInfo?.totalAcceptedPapers, fetchedDashboardData?.configuration?.colorScheme]);

    const apacCountriesData = useMemo(() => {
        if (!fetchedDashboardData?.configuration?.apacCountries) return [];
        return sortedCountries
            .filter(country => fetchedDashboardData.configuration.apacCountries.includes(country.affiliation_country))
            .sort((a, b) => b.paper_count - a.paper_count);
    }, [sortedCountries, fetchedDashboardData?.configuration?.apacCountries]);

    const authorshipMajorityMinorityData = useMemo(() => {
        if (!processedFocusData || !fetchedDashboardData?.focusCountry) return [];
        const focusCountryName = fetchedDashboardData.focusCountry.country_name || 'Focus Country';
        const totalWithFocusCountry = processedFocusData.at_least_one_focus_country_author?.count ?? 0;
        if (totalWithFocusCountry === 0) return [];
        const majorityFocusCountry = processedFocusData.majority_focus_country_authors?.count ?? 0;
        const minorityFocusCountry = Math.max(0, totalWithFocusCountry - majorityFocusCountry);
        return [
            { name: `Majority ${focusCountryName}`, value: majorityFocusCountry, fill: 'hsl(142, 71%, 45%)' },
            { name: `Minority ${focusCountryName}`, value: minorityFocusCountry, fill: 'hsl(var(--secondary-foreground))' },
        ];
    }, [processedFocusData, fetchedDashboardData?.focusCountry]);

    const authorshipFirstAuthorData = useMemo(() => {
        if (!processedFocusData || !fetchedDashboardData?.focusCountry) return [];
        const focusCountryName = fetchedDashboardData.focusCountry.country_name || 'Focus Country';
        const totalWithFocusCountry = processedFocusData.at_least_one_focus_country_author?.count ?? 0;
        if (totalWithFocusCountry === 0) return [];
        const firstAuthorFocusCountry = processedFocusData.first_focus_country_author?.count ?? 0;
        const nonFirstAuthorFocusCountry = Math.max(0, totalWithFocusCountry - firstAuthorFocusCountry);
        return [
            { name: `First Author ${focusCountryName}`, value: firstAuthorFocusCountry, fill: 'hsl(330, 80%, 60%)' },
            { name: 'Other Position', value: nonFirstAuthorFocusCountry, fill: 'hsl(36, 96%, 50%)' },
        ];
    }, [processedFocusData, fetchedDashboardData?.focusCountry]);
    
    const institutionTypeComparisonData = useMemo(() => {
        if (!processedFocusData?.institutions || !processedFocusData?.institution_types) return [];
        const academicPapers = processedFocusData.institution_types?.academic ?? 0;
        const corporatePapers = processedFocusData.institution_types?.corporate ?? 0;
        const academicImpact = processedFocusData.institutions
            .filter(i => i.type === 'academic')
            .reduce((sum, i) => sum + (i.spotlights ?? 0) + (i.orals ?? 0), 0);
        const corporateImpact = processedFocusData.institutions
            .filter(i => i.type === 'corporate')
            .reduce((sum, i) => sum + (i.spotlights ?? 0) + (i.orals ?? 0), 0);
        return [
            { type: 'Academic', Papers: academicPapers, 'Spotlights/Orals': academicImpact },
            { type: 'Corporate', Papers: corporatePapers, 'Spotlights/Orals': corporateImpact },
        ];
    }, [processedFocusData]);

    const institutionTypePieData = useMemo(() => {
        if (!processedFocusData?.institution_types || !fetchedDashboardData?.configuration?.colorScheme) return [];
        const academicCount = processedFocusData.institution_types.academic ?? 0;
        const corporateCount = processedFocusData.institution_types.corporate ?? 0;
        const total = academicCount + corporateCount;
        if (total === 0) return [];
        return [
            { name: 'Academic', value: academicCount, percent: academicCount / total, fill: fetchedDashboardData.configuration.colorScheme.academic }, 
            { name: 'Corporate', value: corporateCount, percent: corporateCount / total, fill: fetchedDashboardData.configuration.colorScheme.corporate }, 
        ];
    }, [processedFocusData, fetchedDashboardData?.configuration?.colorScheme]);

    const filteredInstitutions: InstitutionData[] = useMemo(() => {
        if (!processedFocusData?.institutions) return [];
        return processedFocusData.institutions
            .filter(inst => inst.institute?.toLowerCase().includes(institutionFilter.toLowerCase()))
            .sort((a, b) => (b.unique_paper_count ?? 0) - (a.unique_paper_count ?? 0) || (b.impact_score ?? 0) - (a.impact_score ?? 0) || (b.author_count ?? 0) - (a.author_count ?? 0));
    }, [processedFocusData, institutionFilter]);

    const topInstitutions = useMemo(() => filteredInstitutions.slice(0, 8), [filteredInstitutions]);

    // Event Handlers
    const handleFilterChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => setInstitutionFilter(event.target.value), []);
    const handlePieEnter = useCallback((_: any, index: number) => setActivePieIndex(index), []);

    // Early returns
    if (loading) {
        return <div className="min-h-screen bg-background flex items-center justify-center p-6 text-foreground"><div className="text-xl">Loading dashboard data for {conference.toUpperCase()} {year}...</div></div>;
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
    if (!fetchedDashboardData) { 
        return <div className="min-h-screen bg-background flex items-center justify-center p-6 text-muted-foreground">No data available for {conference.toUpperCase()} {year}.</div>;
    }

    // Destructure for render logic
    const { conferenceInfo, focusCountry, configuration } = fetchedDashboardData;
    const totalPapers = conferenceInfo.totalAcceptedPapers;
    const totalAuthors = conferenceInfo.totalAcceptedAuthors;
    const colorScheme = configuration.colorScheme;
    const focusCountryCode = focusCountry.country_code;

    if (!processedFocusData || !usData || !cnData || !focusCountryGlobalStats) {
        return (
             <div className="min-h-screen bg-background flex items-center justify-center p-6">
                 <div className="bg-destructive/10 border border-destructive/30 text-destructive px-4 py-3 rounded-lg shadow-lg text-center">
                     <h2 className="font-bold text-lg mb-2">Data Processing Error</h2>
                     <p className="text-sm">Could not process essential derived data. Check analytics file structure.</p>
                 </div>
             </div>
         );
     }

    const colorMap = {
        us: colorScheme.us, cn: colorScheme.cn, focusCountry: colorScheme.focusCountry,
        primary: colorScheme.primary || 'hsl(var(--primary))', secondary: colorScheme.secondary || 'hsl(var(--secondary-foreground))',
        academic: colorScheme.academic, corporate: colorScheme.corporate, spotlight: colorScheme.spotlight, oral: colorScheme.oral,
        grid: 'hsl(var(--border))', textAxis: 'hsl(var(--muted-foreground))', highlight: 'hsl(142, 60%, 55%)',
        accent: 'hsl(330, 60%, 70%)', warning: 'hsl(36, 80%, 65%)', rest: 'hsl(var(--muted))',
        papers: 'hsl(210, 70%, 60%)', authors: 'hsl(330, 60%, 70%)',
    };

    const RADIAN = Math.PI / 180;
    const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name, value }: any) => {
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);
        const percentValue = (percent * 100).toFixed(0);
        if (percent < 0.05) return null;
        return (
            <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize="10" fontWeight="bold">
                {`${name.substring(0,10)}${name.length > 10 ? '...' : ''} ${percentValue}%`}
            </text>
        );
    };

    // Main Render Logic
    return (
        <div className="min-h-screen bg-background text-foreground font-sans">
            {/* Header: Modified to include conferenceSelectorElement and improved stat display */}
            <header className="py-6 md:py-8 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 border-b border-border shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-col sm:flex-row justify-between items-center mb-2 sm:mb-3">
                        <div className="flex-grow text-center sm:text-left mb-3 sm:mb-0">
                            <h1 className="text-3xl sm:text-4xl font-bold text-foreground flex items-center justify-center sm:justify-start">
                                <FaTrophy className="mr-3 text-amber-500" /> {configuration.dashboardTitle}
                            </h1>
                        </div>
                        <div className="ml-0 sm:ml-4 flex-shrink-0">
                            {conferenceSelectorElement} 
                        </div>
                    </div>
                    
                    <div className="text-center sm:text-left">
                        <p className="text-muted-foreground text-base sm:text-lg mb-3">{configuration.dashboardSubtitle}</p>
                        
                        {/* Improved Stats Display */}
                        <div className="flex flex-col sm:flex-row items-center justify-center sm:justify-start gap-3 mb-2">
                            <div className="bg-card/70 dark:bg-card/40 border border-border rounded-lg px-3 py-1.5 shadow-sm text-sm">
                                <span className="text-muted-foreground">Total Papers: </span>
                                <span className="font-semibold text-foreground">{totalPapers?.toLocaleString() ?? 'N/A'}</span>
                            </div>
                            <div className="bg-card/70 dark:bg-card/40 border border-border rounded-lg px-3 py-1.5 shadow-sm text-sm">
                                <span className="text-muted-foreground">Total Authors: </span>
                                <span className="font-semibold text-foreground">{totalAuthors?.toLocaleString() ?? 'N/A'}</span>
                            </div>
                        </div>
                        
                        <p className="text-xs text-muted-foreground">Displaying: {conferenceInfo.name} {conferenceInfo.year} (Focus: {focusCountry.country_name || focusCountry.country_code})</p>
                    </div>
                </div>
            </header>

            <main>
                {/* Sections remain the same */}
                <Section title={configuration.sections.summary.title} id="summary" className="bg-muted/30">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <StatCard
                            title="Papers Accepted"
                            value={processedFocusData.paper_count ?? 0}
                            icon={<FaFileAlt />}
                            colorClass="text-amber-500 dark:text-amber-400"
                            subtitle={`#${processedFocusData.rank ?? 'N/A'} globally | ${((processedFocusData.paper_count ?? 0) / (totalPapers || 1) * 100).toFixed(1)}% of all ${conferenceInfo.name} papers`}
                        />
                        <StatCard
                            title="Authors Accepted"
                            value={processedFocusData.author_count ?? 0}
                            icon={<FaUsers />}
                            colorClass="text-blue-500 dark:text-blue-400"
                            subtitle={`Avg ${(processedFocusData?.authors_per_paper ?? 0).toFixed(1)} authors/paper | Building ${focusCountry.country_name || 'Local'}'s ML community`}
                        />
                        <StatCard
                            title="First Authors"
                            value={processedFocusData?.first_focus_country_author?.count ?? 0}
                            icon={<FaUserTie />}
                            colorClass="text-emerald-500 dark:text-emerald-400"
                            subtitle={`${((processedFocusData?.first_focus_country_author?.count ?? 0) / (processedFocusData?.paper_count || 1) * 100).toFixed(0)}% of papers led by ${focusCountry.country_name || 'Focus Country'} first authors`}
                        />
                        <StatCard
                            title="Spotlight Papers"
                            value={processedFocusData.spotlights ?? 0}
                            icon={<FaStar />}
                            colorClass="text-yellow-500 dark:text-yellow-400"
                            subtitle={`Demonstrating high-quality research impact on the global stage`}
                        />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                         <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
                             <div className="flex items-start mb-3">
                                 <FaUniversity className="text-blue-500 mr-3 mt-1" size={20}/>
                                 <div>
                                     <p className="text-foreground font-medium text-lg">Institutional Leaders:</p>
                                     <p className="text-muted-foreground text-sm">
                                         {topInstitutions.length > 0 ? 
                                            `${topInstitutions[0].institute} leads volume (${topInstitutions[0].unique_paper_count} papers, ${topInstitutions[0].author_count} authors)${topInstitutions.length > 1 ? `; ${topInstitutions[1].institute} follows with ${topInstitutions[1].unique_paper_count} papers and ${topInstitutions[1].author_count} authors` : ''}` 
                                            : 'Institution data unavailable'}
                                     </p>
                                 </div>
                             </div>
                         </div>
                         <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
                             <div className="flex items-start mb-3">
                                 <FaBalanceScale className="text-green-500 mr-3 mt-1" size={20}/>
                                 <div>
                                     <p className="text-foreground font-medium text-lg">Quality Focus:</p>
                                     <p className="text-muted-foreground text-sm">
                                         {focusCountry.country_name || 'Focus country'} secured {processedFocusData.spotlights} spotlight {processedFocusData.spotlights === 1 ? 'paper' : 'papers'} at {conferenceInfo.name} {conferenceInfo.year}, demonstrating quality research capability{processedFocusData.paper_count && processedFocusData.paper_count < 100 ? ' despite smaller overall representation' : ''}.
                                     </p>
                                 </div>
                             </div>
                         </div>
                     </div>
                    <InterpretationPanel
                        title="Dashboard Narrative Hook"
                        icon={<FaBullseye />}
                        iconColorClass='text-red-500 dark:text-red-400'
                        insights={configuration.sections.summary.insights}
                    />
                </Section>

                <Section title={configuration.sections.context.title} id="context" subtitle={configuration.sections.context.subtitle}>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                        <div className="lg:col-span-2 bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg">
                            <h3 className="text-xl font-semibold text-foreground mb-1">Global Rankings (Top 15 by Papers)</h3>
                            <p className="text-sm text-muted-foreground mb-4">{focusCountry.country_name || 'Focus country'} highlighted at #{processedFocusData?.rank ?? 'N/A'}. Bar color indicates country (Blue: US, Red: CN, {colorScheme.focusCountry ? 'Amber' : 'Highlight'}: {focusCountry.country_name || 'Focus'}, Primary: Others). Second bar shows author count.</p>
                            <div className="h-96">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={topCountriesByPaper} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false} />
                                        <XAxis type="number" stroke={colorMap.textAxis} axisLine={false} tickLine={false} />
                                        <YAxis type="category" dataKey="country_name" stroke={colorMap.textAxis} width={100} tick={{ fontSize: 11, fill: colorMap.textAxis }} interval={0} axisLine={false} tickLine={false} />
                                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }} />
                                        <Bar dataKey="normalized_paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={18}>
                                            {topCountriesByPaper.map((entry) => (
                                                <Cell key={`cell-global-${entry.affiliation_country}`}
                                                      fill={entry.affiliation_country === 'US' ? colorMap.us :
                                                            entry.affiliation_country === 'CN' ? colorMap.cn :
                                                            entry.affiliation_country === focusCountry.country_code ? colorMap.focusCountry :
                                                            colorMap.papers}
                                                      fillOpacity={entry.isHighlight ? 1 : 0.7} />
                                            ))}
                                            <LabelList dataKey="paper_count" position="right" style={{ fill: 'hsl(var(--foreground))', fontSize: 10 }} />
                                        </Bar>
                                         <Bar dataKey="normalized_author_count" name="Authors" radius={[0, 4, 4, 0]} barSize={10} fill={colorMap.authors} />
                                         <Legend 
                                             iconSize={10} 
                                             wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}
                                             payload={[
                                                 { value: 'Papers', type: 'square', color: colorMap.papers },
                                                 { value: 'Authors', type: 'square', color: colorMap.authors }
                                             ]}
                                         />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                        <div className="bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg flex flex-col">
                            <h3 className="text-xl font-semibold text-foreground mb-1 text-center">US-China Dominance</h3>
                            <p className="text-sm text-muted-foreground mb-4 text-center">Share of total accepted papers.</p>
                            <div className="h-64 flex-grow">
                                <ResponsiveContainer width="100%" height="100%">
                                    {usChinaDominancePieData.length > 0 ? (
                                        <PieChart>
                                            <Pie
                                                data={usChinaDominancePieData} cx="50%" cy="50%" labelLine={false}
                                                label={renderCustomizedLabel} outerRadius={80} dataKey="value" nameKey="name"
                                                stroke={'hsl(var(--card))'} strokeWidth={2}
                                            >
                                                {usChinaDominancePieData.map((entry, index) => (
                                                    <Cell key={`cell-dominance-${index}`} fill={entry.fill} />
                                                ))}
                                            </Pie>
                                            <Tooltip content={<CustomTooltip />} />
                                        </PieChart>
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-muted-foreground">Data unavailable</div>
                                    )}
                                </ResponsiveContainer>
                            </div>
                             <div className="mt-4 text-center text-sm text-muted-foreground">
                                 <p>US + China: <span className="font-bold text-foreground">{(((usData?.paper_count ?? 0) + (cnData?.paper_count ?? 0)) / (totalPapers || 1) * 100).toFixed(1)}%</span> papers</p>
                                 <p>{focusCountry.country_name || 'Focus country'}: <span className="font-bold text-foreground">{((processedFocusData?.paper_count ?? 0) / (totalPapers || 1) * 100).toFixed(1)}%</span> papers
                                 {processedFocusData.spotlights > 0 && <span className="text-amber-600 dark:text-amber-400"> ({processedFocusData.spotlights} {processedFocusData.spotlights === 1 ? 'Spotlight' : 'Spotlights'})</span>}</p>
                             </div>
                        </div>
                    </div>
                    <div className="mb-8">
                        <h3 className="text-xl font-semibold text-foreground mb-4">APAC Dynamics</h3>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            <div className="bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg">
                                <h4 className="text-lg font-semibold text-foreground mb-1">Regional Players Comparison</h4>
                                <p className="text-sm text-muted-foreground mb-4">Papers vs. Authors for key APAC countries. {focusCountry.country_name || 'Focus country'} highlighted.</p>
                                <div className="h-80">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={apacCountriesData} layout="vertical" margin={{ top: 5, right: 20, left: 80, bottom: 5 }}>
                                            <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false}/>
                                            <XAxis type="number" stroke={colorMap.textAxis} fontSize={10}/>
                                            <YAxis type="category" dataKey="country_name" width={80} stroke={colorMap.textAxis} fontSize={10} interval={0}/>
                                            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }}/>
                                            <Legend 
                                                iconSize={10} 
                                                wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}
                                                payload={[
                                                    { value: 'Papers', type: 'square', color: colorMap.papers },
                                                    { value: 'Authors', type: 'square', color: colorMap.authors }
                                                ]}
                                            />
                                            <Bar dataKey="normalized_paper_count" name="Papers" barSize={12} fill={colorMap.papers}>
                                                {apacCountriesData.map((entry) => ( <Cell key={`cell-apac-paper-${entry.affiliation_country}`} fill={entry.affiliation_country === focusCountry.country_code ? colorMap.focusCountry : colorMap.papers} /> ))}
                                                <LabelList dataKey="paper_count" position="right" style={{ fill: 'hsl(var(--foreground))', fontSize: 10 }} />
                                            </Bar>
                                             <Bar dataKey="normalized_author_count" name="Authors" barSize={12} fill={colorMap.authors}>
                                                 {apacCountriesData.map((entry) => ( <Cell key={`cell-apac-author-${entry.affiliation_country}`} fill={entry.affiliation_country === focusCountry.country_code ? colorMap.warning : colorMap.authors} /> ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                            <div className="bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg">
                                <h4 className="text-lg font-semibold text-foreground mb-1 text-center">APAC Paper Distribution</h4>
                                <p className="text-sm text-muted-foreground mb-4 text-center">Share of papers across major APAC countries.</p>
                                <div className="h-80">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={apacCountriesData} cx="50%" cy="50%" labelLine={false} label={renderCustomizedLabel}
                                                outerRadius={80} dataKey="paper_count" nameKey="country_name"
                                                stroke={'hsl(var(--card))'} strokeWidth={2}
                                                activeIndex={activePieIndex} activeShape={renderActiveShape} onMouseEnter={handlePieEnter}
                                            >
                                                {apacCountriesData.map((entry, index) => (
                                                    <Cell 
                                                        key={`cell-apac-pie-${index}`} 
                                                        fill={entry.affiliation_country === 'CN' ? colorMap.cn :
                                                              entry.affiliation_country === focusCountry.country_code ? colorMap.focusCountry :
                                                              entry.affiliation_country === 'KR' ? colorMap.highlight :
                                                              entry.affiliation_country === 'SG' ? colorMap.accent :
                                                              entry.affiliation_country === 'JP' ? 'hsl(var(--primary))' :
                                                              entry.affiliation_country === 'HK' ? 'hsl(200, 80%, 50%)' :
                                                              entry.affiliation_country === 'AU' ? 'hsl(140, 60%, 45%)' :
                                                              colorMap.primary} 
                                                    />
                                                ))}
                                            </Pie>
                                            <Tooltip content={<CustomTooltip />} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    </div>
                    <InterpretationPanel
                        title="APAC Narrative"
                        icon={<FaGlobeAsia />}
                        iconColorClass='text-blue-500 dark:text-blue-400'
                        insights={configuration.sections.context.insights}
                    />
                </Section>

                <Section title={configuration.sections.focusCountry.title} id="focus-country" subtitle={configuration.sections.focusCountry.subtitle} className="bg-muted/30">
                    <div className="mb-12">
                        <h3 className="text-xl font-semibold text-foreground mb-4">Authorship & Collaboration Patterns ({focusCountry.country_name || 'Focus Country'}-Centric)</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg">
                                <h4 className="text-lg font-semibold text-foreground mb-1 text-center">Majority vs Minority {focusCountry.country_name || 'Focus Country'} Authors</h4>
                                <p className="text-sm text-muted-foreground mb-4 text-center">Breakdown of the {processedFocusData?.at_least_one_focus_country_author?.count ?? 0} papers with {focusCountry.country_name || 'Focus Country'} authors.</p>
                                <div className="h-60">
                                    <ResponsiveContainer width="100%" height="100%">
                                        {authorshipMajorityMinorityData.length > 0 ? (
                                            <BarChart data={authorshipMajorityMinorityData} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false}/>
                                                <XAxis type="number" stroke={colorMap.textAxis} fontSize={10} />
                                                <YAxis type="category" dataKey="name" stroke={colorMap.textAxis} fontSize={10} width={80} interval={0}/>
                                                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }}/>
                                                <Bar dataKey="value" name="Papers" barSize={35}>
                                                    {authorshipMajorityMinorityData.map((entry, index) => (
                                                        <Cell key={`cell-maj-${index}`} fill={entry.fill} />
                                                    ))}
                                                     <LabelList dataKey="value" position="right" style={{ fill: 'hsl(var(--foreground))', fontSize: 10 }} />
                                                </Bar>
                                            </BarChart>
                                        ) : <div className="flex items-center justify-center h-full text-muted-foreground">Data unavailable</div>}
                                    </ResponsiveContainer>
                                </div>
                            </div>
                            <div className="bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg">
                                <h4 className="text-lg font-semibold text-foreground mb-1 text-center">First Author Position</h4>
                                <p className="text-sm text-muted-foreground mb-4 text-center">Breakdown of the {processedFocusData?.at_least_one_focus_country_author?.count ?? 0} papers with {focusCountry.country_name || 'Focus Country'} authors.</p>
                                <div className="h-60">
                                    <ResponsiveContainer width="100%" height="100%">
                                        {authorshipFirstAuthorData.length > 0 ? (
                                            <BarChart data={authorshipFirstAuthorData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false}/>
                                                <XAxis type="number" stroke={colorMap.textAxis} fontSize={10} />
                                                <YAxis type="category" dataKey="name" stroke={colorMap.textAxis} fontSize={10} width={100} interval={0}/>
                                                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }}/>
                                                <Bar dataKey="value" name="Papers" barSize={35}>
                                                    {authorshipFirstAuthorData.map((entry, index) => (
                                                        <Cell key={`cell-first-${index}`} fill={entry.fill} />
                                                    ))}
                                                    <LabelList dataKey="value" position="right" style={{ fill: 'hsl(var(--foreground))', fontSize: 10 }} />
                                                </Bar>
                                            </BarChart>
                                        ) : <div className="flex items-center justify-center h-full text-muted-foreground">Data unavailable</div>}
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    </div>
                     <div className="mb-8">
                        <h3 className="text-xl font-semibold text-foreground mb-4">Institution Types ({focusCountry.country_name || 'Focus Country'}-Specific)</h3>
                         <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                             <div className="bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg md:col-span-2">
                                 <h4 className="text-lg font-semibold text-foreground mb-1 text-center">Academic vs Corporate Contribution</h4>
                                 <p className="text-sm text-muted-foreground mb-4 text-center">Comparing paper volume and high-impact papers (Spotlights/Orals).</p>
                                 <div className="h-80">
                                     <ResponsiveContainer width="100%" height="100%">
                                         {institutionTypeComparisonData.length > 0 ? (
                                             <BarChart data={institutionTypeComparisonData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                                 <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false}/>
                                                 <XAxis dataKey="type" stroke={colorMap.textAxis} fontSize={12}/>
                                                 <YAxis stroke={colorMap.textAxis} fontSize={10}/>
                                                 <Tooltip content={<CustomTooltip />}/>
                                                 <Legend 
                                                    iconSize={10} 
                                                    wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}
                                                    payload={[
                                                        { value: 'Papers', type: 'square', color: colorMap.academic }, 
                                                        { value: 'Spotlights/Orals', type: 'square', color: colorMap.spotlight } 
                                                    ]}
                                                />
                                                 <Bar dataKey="Papers" name="Papers" barSize={40}>
                                                     {institutionTypeComparisonData.map((entry, index) => (
                                                         <Cell key={`cell-type-paper-${index}`} fill={entry.type === 'Academic' ? colorMap.academic : colorMap.corporate} />
                                                     ))}
                                                      <LabelList dataKey="Papers" position="top" style={{ fill: 'hsl(var(--foreground))', fontSize: 10 }} />
                                                 </Bar>
                                                 <Bar dataKey="Spotlights/Orals" name="Spotlights/Orals" barSize={40}>
                                                      {institutionTypeComparisonData.map((entry, index) => (
                                                         <Cell key={`cell-type-impact-${index}`} fill={entry.type === 'Academic' ? colorMap.spotlight : colorMap.oral} /> 
                                                     ))}
                                                     <LabelList dataKey="Spotlights/Orals" position="top" style={{ fill: 'hsl(var(--foreground))', fontSize: 10 }} />
                                                 </Bar>
                                             </BarChart>
                                         ) : <div className="flex items-center justify-center h-full text-muted-foreground">Data unavailable</div>}
                                     </ResponsiveContainer>
                                 </div>
                             </div>
                             <div className="bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg flex flex-col">
                                 <h4 className="text-lg font-semibold text-foreground mb-1 text-center">Paper Split by Type</h4>
                                 <p className="text-sm text-muted-foreground mb-4 text-center">Share of {focusCountry.country_name || 'Focus Country'} papers by institution type.</p>
                                 <div className="h-80 flex-grow">
                                     <ResponsiveContainer width="100%" height="100%">
                                         {institutionTypePieData.length > 0 ? (
                                             <PieChart>
                                                 <Pie
                                                     data={institutionTypePieData} cx="50%" cy="50%" labelLine={false} label={renderCustomizedLabel} outerRadius={80} dataKey="value" nameKey="name"
                                                     stroke={'hsl(var(--card))'} strokeWidth={2}
                                                     activeIndex={activePieIndex} activeShape={renderActiveShape} onMouseEnter={handlePieEnter}
                                                 >
                                                     {institutionTypePieData.map((entry, index) => (
                                                         <Cell key={`cell-type-pie-${index}`} fill={entry.fill} />
                                                     ))}
                                                 </Pie>
                                                 <Tooltip content={<CustomTooltip />} />
                                             </PieChart>
                                         ) : (
                                             <div className="flex items-center justify-center h-full text-muted-foreground">Data unavailable</div>
                                         )}
                                     </ResponsiveContainer>
                                 </div>
                             </div>
                         </div>
                     </div>
                    <InterpretationPanel
                        title={`${focusCountry.country_name || 'Focus Country'}-Specific Insights`}
                        icon={<FaProjectDiagram />}
                        iconColorClass='text-purple-500 dark:text-purple-400'
                        insights={configuration.sections.focusCountry.insights}
                    />
                </Section>

                <Section title={configuration.sections.institutions.title} id="institutions" subtitle={configuration.sections.institutions.subtitle}>
                    <div className="mb-6 max-w-md mx-auto">
                        <div className="relative">
                            <label htmlFor="institution-search" className="sr-only">Search Institutions</label>
                            <input id="institution-search" type="search" placeholder={`Search ${focusCountry.country_name || 'Focus Country'} institutions...`} className="bg-input border border-border rounded-lg py-2 pl-10 pr-4 text-foreground w-full focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent shadow-sm placeholder-muted-foreground" value={institutionFilter} onChange={handleFilterChange} />
                            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground pointer-events-none" />
                        </div>
                    </div>
                    <div className="mb-12">
                        <h3 className="text-xl font-semibold text-foreground mb-4">Top Performing Institutions</h3>
                        <div className="bg-card p-4 sm:p-6 rounded-xl border border-border shadow-lg">
                            <h4 className="text-lg font-semibold text-foreground mb-1">Leaderboard (Top 8 by Papers)</h4>
                            <p className="text-sm text-muted-foreground mb-4">Papers vs. Authors. Bar color indicates type (Academic/Corporate). Markers show Spotlights (⭐) & Orals (🏆).</p>
                            <div className="h-[450px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={topInstitutions} layout="vertical" margin={{ top: 5, right: 40, left: 150, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false}/>
                                        <XAxis type="number" stroke={colorMap.textAxis} fontSize={10}/>
                                        <YAxis type="category" dataKey="institute" width={150} stroke={colorMap.textAxis} fontSize={10} interval={0}/>
                                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }}/>
                                         <Legend 
                                             iconSize={10} 
                                             wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}
                                             payload={[
                                                 { value: 'Papers (Academic)', type: 'square', color: colorMap.academic },
                                                 { value: 'Papers (Corporate)', type: 'square', color: colorMap.corporate },
                                                 { value: 'Authors', type: 'square', color: colorMap.authors }
                                             ]}
                                         />
                                        <Bar dataKey="normalized_unique_paper_count" name="Papers" barSize={12}>
                                            {topInstitutions.map((entry, index) => (
                                                <Cell key={`cell-leader-paper-${index}`} fill={entry.type === 'academic' ? colorMap.academic : colorMap.corporate}/>
                                            ))}
                                            <LabelList dataKey="unique_paper_count" position="right" style={{ fill: 'hsl(var(--foreground))', fontSize: 10 }} />
                                            <LabelList dataKey="institute" content={({ x, y, width, height, value, index }) => {
                                                 const inst = topInstitutions[index];
                                                 const spotlights = inst?.spotlights ?? 0;
                                                 const orals = inst?.orals ?? 0;
                                                 const impactCount = spotlights + orals;
                                                 if (!inst || impactCount === 0) return null;

                                                 const iconX = (x ?? 0) + (width ?? 0) + 5; 
                                                 const iconY = (y ?? 0) + (height ?? 0) / 2;
                                                 return (
                                                     <g>
                                                         {spotlights > 0 && <text x={iconX} y={iconY} fill={colorMap.spotlight} fontSize="12" textAnchor="start" dominantBaseline="middle">⭐{spotlights > 1 ? `x${spotlights}`: ''}</text>}
                                                         {orals > 0 && <text x={iconX + (spotlights > 0 ? 25 : 0) } y={iconY} fill={colorMap.oral} fontSize="12" textAnchor="start" dominantBaseline="middle">🏆{orals > 1 ? `x${orals}`: ''}</text>}
                                                     </g>
                                                 );
                                             }} />
                                        </Bar>
                                         <Bar dataKey="normalized_author_count" name="Authors" barSize={12} fill={colorMap.authors} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                            <h3 className="text-xl font-semibold text-foreground">Detailed Institution List</h3>
                            {filteredInstitutions.length > 0 && (
                                <button onClick={() => exportToCSV( filteredInstitutions.map(inst => ({ Institution: inst.institute, Type: inst.type || 'Unknown', Unique_Papers: inst.unique_paper_count, Authors_Count: inst.author_count, Authors_List: inst.authors?.join('; ') || '', Authors_Per_Paper: inst.authors_per_paper?.toFixed(1), Spotlights: inst.spotlights, Orals: inst.orals, Impact_Score: inst.impact_score })), `detailed_${focusCountryCode.toLowerCase()}_institutions_${conferenceInfo.name.toLowerCase().replace(/\s+/g, '_')}_${conferenceInfo.year}` )} className="flex items-center bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs px-3 py-1.5 rounded transition-colors shadow-sm" aria-label="Export detailed institution list to CSV">
                                    <FaDownload className="mr-1.5" size={10} /> Export Details
                                </button>
                            )}
                        </div>
                        {filteredInstitutions.length > 0 ? (
                            <div className="space-y-4">
                                {filteredInstitutions.map((institution, index) => (
                                    <InstitutionCard key={`${institution.institute}-${index}`} institution={institution} index={index} />
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-10 text-muted-foreground bg-card rounded-lg border border-border shadow-sm">
                                <FaUniversity size={36} className="mx-auto mb-3" />
                                <p>No institutions found matching "{institutionFilter}".</p>
                                <p className="text-sm mt-1">Try refining your search term or clear the filter.</p>
                            </div>
                        )}
                    </div>
                    <InterpretationPanel
                        title="Institutional Ecosystem Insights"
                        icon={<FaUniversity />}
                        iconColorClass='text-green-500 dark:text-green-400'
                        insights={configuration.sections.institutions.insights}
                    />
                </Section>
            </main>

            <footer className="mt-10 md:mt-12 text-center text-muted-foreground text-xs border-t border-border pt-6 pb-6 bg-gradient-to-r from-amber-50/30 to-orange-50/30 dark:from-amber-950/10 dark:to-orange-950/10">
                <p>{conferenceInfo?.name ?? 'Conference'} {conferenceInfo?.year ?? ''} Dashboard | Data Updated {new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}</p>
                {processedFocusData && (
                     <p>{focusCountry.country_name || 'Focus Country'}'s Contribution: {processedFocusData.paper_count} Papers | {processedFocusData.author_count} Authors | {processedFocusData.first_focus_country_author?.count} First Authors | {processedFocusData.spotlights} Spotlight {processedFocusData.spotlights === 1 ? 'Paper' : 'Papers'}</p>
                )}
                <p className="mt-1">&copy; {new Date().getFullYear()} Analysis Dashboard</p>
            </footer>

            <style jsx global>{`
                body { scroll-behavior: smooth; }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in { animation: fadeIn 0.5s ease-out forwards; }
                .custom-scrollbar::-webkit-scrollbar { width: 6px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: hsl(var(--muted)); border-radius: 3px; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: hsl(var(--border)); border-radius: 3px; }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: hsl(var(--primary) / 0.7); }
                .recharts-default-tooltip {
                    background-color: hsl(var(--popover)) !important;
                    border: 1px solid hsl(var(--border)) !important;
                    color: hsl(var(--popover-foreground)) !important;
                }
                 .recharts-text.recharts-pie-label-text {
                     fill: white !important; 
                     font-size: 10px;
                     font-weight: bold;
                 }
                .recharts-legend-item-text { fill: hsl(var(--foreground)); }
                .recharts-label, .recharts-cartesian-axis-tick-value { fill: hsl(var(--muted-foreground)); }
                .recharts-label tspan { fill: hsl(var(--muted-foreground)); } 
                .recharts-tooltip-wrapper { outline: none; } 
            `}</style>
        </div>
    );
};

// --- App Component (Modified for Dropdown in Header) ---
const App = () => {
  const [currentConference, setCurrentConference] = useState<string>("");
  const [currentYear, setCurrentYear] = useState<string>("");
  const [conferenceOptions, setConferenceOptions] = useState<TrackerIndexEntry[]>([]);
  const [isLoadingOptions, setIsLoadingOptions] = useState<boolean>(true);
  const [optionsError, setOptionsError] = useState<string | null>(null);

  const handleConferenceChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedValue = event.target.value;
    if (selectedValue) {
      const [venue, year] = selectedValue.split('|');
      setCurrentConference(venue);
      setCurrentYear(year);
      // Update URL without page reload if you want the URL to reflect dropdown changes
      // const newUrl = `${window.location.pathname}?conference=${venue}&year=${year}${window.location.hash}`;
      // window.history.pushState({ path: newUrl }, '', newUrl);
    }
  }, []); // Empty: setCurrentConference and setCurrentYear are stable

  useEffect(() => {
    const fetchConferenceOptions = async () => {
      setIsLoadingOptions(true);
      setOptionsError(null);
      try {
        const response = await fetch('/tracker/index.json');
        if (!response.ok) {
          throw new Error(`Failed to fetch /tracker/index.json: ${response.status} ${response.statusText}`);
        }
        const data: TrackerIndexEntry[] = await response.json();
        
        const sortedData = data.sort((a, b) => {
          const yearComparison = parseInt(b.year, 10) - parseInt(a.year, 10);
          if (yearComparison !== 0) return yearComparison;
          return a.label.localeCompare(b.label);
        });
        
        setConferenceOptions(sortedData);

        const queryParams = new URLSearchParams(window.location.search);
        const queryConference = queryParams.get('conference');
        const queryYear = queryParams.get('year');

        let foundInQuery = false;
        if (queryConference && queryYear) {
          const matchingOption = sortedData.find(
            opt => opt.venue.toLowerCase() === queryConference.toLowerCase() && opt.year === queryYear
          );
          if (matchingOption) {
            setCurrentConference(matchingOption.venue);
            setCurrentYear(matchingOption.year);
            foundInQuery = true;
          } else {
            console.warn(`Conference/year from URL (${queryConference}/${queryYear}) not found. Defaulting.`);
          }
        }

        if (!foundInQuery && sortedData.length > 0) {
          setCurrentConference(sortedData[0].venue);
          setCurrentYear(sortedData[0].year);
        } else if (!foundInQuery && sortedData.length === 0) {
            // setError("No conference options available and no valid URL parameters."); // This setError is for ConferenceDashboard
            setOptionsError("No conference options available in index.json."); // This is for App component's options loading
        }

      } catch (e: any) {
        console.error("Error fetching conference options:", e);
        setOptionsError(e.message || "Failed to load conference options.");
      } finally {
        setIsLoadingOptions(false);
      }
    };

    fetchConferenceOptions();
  }, []);

  // Memoize the conference selector element to pass as a prop
  const conferenceSelectorElement = useMemo(() => {
    if (isLoadingOptions) {
      return <p className="text-xs sm:text-sm text-muted-foreground animate-pulse">Loading...</p>;
    }
    if (optionsError && conferenceOptions.length === 0) { // Only show critical error if no options loaded
      return <p className="text-xs sm:text-sm text-destructive">Error loading list!</p>; 
    }
    if (conferenceOptions.length === 0 && !isLoadingOptions) { // No options, not loading, no error
        return <p className="text-xs sm:text-sm text-muted-foreground">N/A</p>;
    }


    return (
      <div className="flex items-center gap-1 sm:gap-2">
        <label htmlFor="conference-select-header" className="sr-only text-xs sm:text-sm font-medium text-muted-foreground whitespace-nowrap">
          Data:
        </label>
        <select
          id="conference-select-header"
          value={currentConference && currentYear ? `${currentConference}|${currentYear}` : ""}
          onChange={handleConferenceChange}
          className="bg-card/80 dark:bg-card/50 border-border text-foreground text-xs sm:text-sm rounded-md focus:ring-primary focus:border-primary p-1.5 sm:p-2 shadow-sm w-auto appearance-none focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-background"
          aria-label="Select a conference and year"
        >
          {/* Show placeholder only if no valid selection AND options are available */}
          {(!currentConference || !currentYear) && conferenceOptions.length > 0 && <option value="" disabled>Select...</option>}
          {conferenceOptions.map((option) => (
            <option key={`${option.venue}-${option.year}`} value={`${option.venue}|${option.year}`}>
              {option.label} 
            </option>
          ))}
        </select>
      </div>
    );
  }, [isLoadingOptions, optionsError, conferenceOptions, currentConference, currentYear, handleConferenceChange]);

  return (
    <div className="bg-background text-foreground min-h-screen">
      {/* ConferenceDashboard now receives the selector as a prop */}
      {/* Conditionally render dashboard once essential states are set */}
      {(currentConference && currentYear) || isLoadingOptions ? ( 
        <ConferenceDashboard 
            conference={currentConference} 
            year={currentYear} 
            conferenceSelectorElement={conferenceSelectorElement} 
        />
      ) : ( 
        <div className="min-h-[calc(100vh-100px)] flex flex-col items-center justify-center p-6">
            {optionsError ? (
                <>
                    <p className="text-destructive text-lg mb-2">Error loading conference data.</p>
                    <p className="text-muted-foreground text-sm">{optionsError}</p>
                </>
            ) : (
                 <p className="text-muted-foreground text-lg">Please select a conference or provide valid URL parameters.</p>
            )}
        </div>
      )}
    </div>
  );
};

export default App;
