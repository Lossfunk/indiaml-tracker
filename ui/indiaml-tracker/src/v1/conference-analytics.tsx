import React, { useState, useMemo, useCallback } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend, CartesianGrid,
    PieChart, Pie, Sector, TooltipProps // Import TooltipProps for typing
} from 'recharts';
import {
    FaGlobeAsia, FaUniversity, FaUserFriends, FaSearch, FaFileAlt,
    FaInfoCircle, FaUserTie, FaTrophy, FaUsers, FaChartPie,
    FaGraduationCap, FaBuilding, FaChalkboardTeacher, FaStar,
    FaDownload, FaTable, FaChartBar, FaLightbulb, FaChevronDown, FaChevronUp
} from 'react-icons/fa';

// Import the data and its type
import { dashboardData, DashboardData } from '@/components/dashboard-data'; // Adjust path if needed

// --- Constants --- REMOVED COLORS OBJECT

// APAC country codes for filtering
const APAC_COUNTRIES: string[] = ['CN', 'IN', 'HK', 'SG', 'JP', 'KR', 'AU'];

const CountryMap: { [key: string]: string } = {
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

const TABS: string[] = ["Overview", "Global Stats", "India Focus", "Institutions"];

// --- Type Definitions (Add className where needed if passing styles, otherwise unchanged) ---

interface PaperSummary {
    id: string;
    title: string;
    isSpotlight?: boolean;
    isOral?: boolean;
}

interface InstitutionData {
    institute: string;
    total_paper_count: number;
    unique_paper_count: number;
    author_count: number;
    spotlights: number;
    orals: number;
    type: 'academic' | 'corporate' | 'unknown';
    papers: PaperSummary[];
    // Removed fill, total - handle in render
}

interface CountryData {
    affiliation_country: string;
    country_name: string;
    paper_count: number;
    author_count: number;
    spotlights: number;
    orals: number;
    rank: number;
    isHighlight?: boolean; // Flag for special styling (US, CN, IN)
    // Removed fill, opacity - handle in render
}

type ProcessedIndiaData = DashboardData['indiaFocus'] & {
    rank?: number;
    paper_count?: number;
    author_count: number;
    spotlights: number;
    orals: number;
}

interface RechartsTooltipPayload {
    dataKey?: string | number;
    name?: string;
    value?: number | string;
    payload?: any;
    fill?: string; // Keep for potential internal recharts use
    stroke?: string; // Keep for potential internal recharts use
    color?: string; // Keep for potential internal recharts use
}

interface ActiveShapeProps {
    cx?: number;
    cy?: number;
    midAngle?: number;
    innerRadius?: number;
    outerRadius?: number;
    startAngle?: number;
    endAngle?: number;
    fill?: string; // Recharts provides this
    payload?: any;
    percent?: number;
    value?: number;
    name?: string;
}

interface NameValueData {
    name: string;
    value: number;
    fillColorClass?: string; // Use for conditional Tailwind class
    fillVariable?: string; // Use for CSS variable fill
    percent?: number;
    // Allow any other properties
    [key: string]: any;
}

type ViewMode = 'chart' | 'table';

// --- Reusable Helper Functions (Unchanged) ---

const exportToCSV = (data: Record<string, any>[], filename: string): void => {
    if (!data || data.length === 0) {
        console.warn("Export Aborted: No data provided.");
        return;
    }
    try {
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => {
                const value = row[header] !== undefined && row[header] !== null ? row[header] : '';
                let stringValue = String(value);
                stringValue = stringValue.replace(/"/g, '""');
                if (stringValue.includes(',')) {
                    stringValue = `"${stringValue}"`;
                }
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
    } catch (error) {
        console.error("Error exporting to CSV:", error);
    }
};


// --- Reusable UI Components (Refactored for Tailwind/Dark Mode) ---

// ## StatCard Component ##
interface StatCardProps {
    title: string;
    value: string | number;
    icon?: React.ReactNode;
    colorClass: string; // e.g., "text-amber-500 dark:text-amber-400"
    bgColorClass: string; // e.g., "bg-amber-600 dark:bg-amber-500"
    subtitle?: string;
    size?: 'normal' | 'large';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, colorClass, bgColorClass, subtitle, size = 'normal' }) => (
    // Use semantic background/border/text colors from globals.css vars
    <div className={`bg-card border border-border p-6 rounded-xl shadow-md flex flex-col ${size === 'large' ? 'lg:col-span-2' : ''}`}>
        <div className="flex items-center mb-2">
            {icon && <span className={`${colorClass} mr-3 text-lg`}>{icon}</span>}
            <h3 className="text-muted-foreground font-medium text-sm uppercase tracking-wider">{title}</h3>
        </div>
        <div className="flex items-end justify-between mt-auto pt-2">
            <div>
                <p className={`text-foreground font-bold ${size === 'large' ? 'text-4xl' : 'text-3xl'}`}>{value}</p>
                {subtitle && <p className="text-muted-foreground text-xs mt-1">{subtitle}</p>}
            </div>
            {colorClass && (
                <div className={`h-2 w-16 ${bgColorClass} rounded-full opacity-75 self-end mb-1`}></div>
            )}
        </div>
    </div>
);


// ## CustomTooltip Component ##
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const payloadItem: RechartsTooltipPayload | undefined = payload[0];
        if (!payloadItem) return null;

        const data = payloadItem.payload;
        const dataKey = payloadItem.dataKey as string;

        let title: string = label ? String(label) : "Details";
        let content: React.ReactNode = null;

        // Use semantic colors from CSS Variables
        if (data && ('country_name' in data || 'affiliation_country' in data) && (dataKey === 'paper_count' || dataKey === 'author_count' || dataKey === 'value')) {
             title = data.country_name || CountryMap[data.affiliation_country] || label || "Country";
             const paperCount = data.paper_count ?? data.value ?? 0;
             const authorCount = data.author_count ?? 'N/A';
             const metricName = dataKey === 'author_count' ? 'Authors' : 'Papers';
             const metricValue = dataKey === 'author_count' ? authorCount : paperCount;
             content = (
                 <>
                     <p className="text-popover-foreground font-bold">{`${metricName}: ${metricValue?.toLocaleString()}`}</p>
                     {dataKey !== 'author_count' && authorCount !== 'N/A' && (
                         <p className="text-muted-foreground text-xs mt-1">{`Authors: ${authorCount?.toLocaleString()}`}</p>
                     )}
                     {data.rank && (dataKey === 'paper_count' || dataKey === 'value') && (
                         <p className="text-muted-foreground text-xs mt-1">{`Rank: #${data.rank}`}</p>
                     )}
                     {data.percent && (
                         <p className="text-muted-foreground text-xs mt-1">{`(${(typeof data.percent === 'number' ? data.percent * 100 : 0).toFixed(1)}%)`}</p>
                     )}
                 </>
             );
         }
         else if (data && 'institute' in data && (dataKey === 'unique_paper_count' || dataKey === 'author_count')) {
             title = data.institute;
             content = (
                 <>
                     <p className="text-primary font-bold">{`Papers: ${data.unique_paper_count?.toLocaleString() || 'N/A'}`}</p>
                     {/* Assuming Corporate uses 'accent' or similar */}
                     <p className="text-pink-600 dark:text-pink-400 font-bold">{`Authors: ${data.author_count?.toLocaleString() || 'N/A'}`}</p>
                     {data.spotlights > 0 && (
                         <p className="text-amber-600 dark:text-amber-400 font-bold">{`Spotlights: ${data.spotlights}`}</p>
                     )}
                     {data.orals > 0 && (
                         <p className="text-emerald-600 dark:text-emerald-400 font-bold">{`Orals: ${data.orals}`}</p>
                     )}
                     <p className="text-muted-foreground text-xs mt-1">{`Type: ${data.type || 'Unknown'}`}</p>
                 </>
             );
         }
         else if (data && 'spotlights' in data && 'orals' in data && dataKey === 'total') {
              title = data.name || label || "Comparison";
              const spotlightPercent = data.spotlight_percent !== undefined ? `${data.spotlight_percent}%` : 'N/A';
              const oralPercent = data.oral_percent !== undefined ? `${data.oral_percent}%` : 'N/A';
              content = (
                  <>
                      <p className="text-popover-foreground font-bold">{`Total Spotlights/Orals: ${data.total || 0}`}</p>
                      <p className="text-amber-600 dark:text-amber-400">{`Spotlights: ${data.spotlights || 0} (${spotlightPercent})`}</p>
                      <p className="text-pink-600 dark:text-pink-400">{`Orals: ${data.orals || 0} (${oralPercent})`}</p>
                  </>
              );
          }
        else if (data && dataKey === 'value') {
             title = data.name || label || "Category";
             const percentText = data.percent ? `(${(typeof data.percent === 'number' ? data.percent * 100 : 0).toFixed(1)}%)` : '';
             content = <p className="text-popover-foreground font-bold">{`${data.value?.toLocaleString() || 'N/A'} ${percentText}`}</p>;
         }
         else if (data && dataKey === 'ratio') {
             title = data.name || label || "Country";
             content = (
                 <>
                     <p className="text-popover-foreground font-bold">{`Authors per Paper: ${data.ratio}`}</p>
                     <p className="text-muted-foreground text-xs mt-1">{`Papers: ${data.papers?.toLocaleString()}`}</p>
                     <p className="text-muted-foreground text-xs mt-1">{`Authors: ${data.authors?.toLocaleString()}`}</p>
                 </>
             );
         }
         else {
             title = label ? String(label) : (data?.name || "Details");
             content = <p className="text-popover-foreground font-bold">{`${payloadItem.name || dataKey}: ${payloadItem.value?.toLocaleString()}`}</p>;
         }

        return (
            // Use semantic popover styles
            <div className="bg-popover border border-border p-3 rounded-lg shadow-xl opacity-95">
                <p className="text-muted-foreground font-medium mb-1">{title}</p>
                {content}
            </div>
        );
    }
    return null;
};

// ## Pie Chart Active Shape Renderer ##
const renderActiveShape = (props: ActiveShapeProps) => {
    const RADIAN = Math.PI / 180;
    const {
        cx = 0, cy = 0, midAngle = 0, innerRadius = 0, outerRadius = 0, startAngle = 0, endAngle = 0,
        fill = 'hsl(var(--primary))', // Default to primary CSS variable
        payload, percent = 0, value = 0, name = ''
    } = props;
    const sin = Math.sin(-RADIAN * midAngle);
    const cos = Math.cos(-RADIAN * midAngle);
    const sx = cx + (outerRadius + 10) * cos;
    const sy = cy + (outerRadius + 10) * sin;
    const mx = cx + (outerRadius + 30) * cos;
    const my = cy + (outerRadius + 30) * sin;
    const ex = mx + (cos >= 0 ? 1 : -1) * 22;
    const ey = my;
    const textAnchor = cos >= 0 ? 'start' : 'end';

    // Use CSS variables for text colors
    const textColor = 'hsl(var(--foreground))';
    const mutedColor = 'hsl(var(--muted-foreground))';

    return (
        <g>
            <text x={cx} y={cy} dy={8} textAnchor="middle" fill={fill || textColor} fontSize="12" fontWeight="bold">
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

// ## InterpretationPanel Component ##
interface InterpretationPanelProps {
    title?: string;
    insights: string[];
    legend?: string;
}

const InterpretationPanel: React.FC<InterpretationPanelProps> = ({ title, insights, legend }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const toggleExpansion = useCallback(() => setIsExpanded(prev => !prev), []);
    const contentId = `interpretation-content-${title?.replace(/\s+/g, '-') || Math.random().toString(36).substring(7)}`;

    return (
        // Use semantic bg/border/text colors
        <div className="mt-4 bg-muted/50 rounded-lg border border-border overflow-hidden transition-all duration-300">
            <div
                className="p-3 flex items-center justify-between cursor-pointer hover:bg-muted transition-colors"
                onClick={toggleExpansion}
                role="button"
                aria-expanded={isExpanded}
                aria-controls={contentId}
            >
                <div className="flex items-center">
                     {/* Use a theme color */}
                    <FaLightbulb className="text-amber-500 dark:text-amber-400 mr-2 flex-shrink-0" />
                    <h4 className="text-foreground font-medium">{title || 'Interpretation'}</h4>
                </div>
                <div>{isExpanded ? <FaChevronUp className="text-muted-foreground" /> : <FaChevronDown className="text-muted-foreground" />}</div>
            </div>
            {isExpanded && (
                // Use semantic bg/border/text colors
                <div id={contentId} className="p-4 bg-card border-t border-border">
                    <div className="text-muted-foreground text-sm leading-relaxed mb-3">
                        {insights.map((insight, idx) => <p key={idx} className="mb-2">{insight}</p>)}
                    </div>
                    {legend && (
                        <div className="mt-3 pt-3 border-t border-border">
                            <p className="text-amber-600 dark:text-amber-400 text-xs font-medium mb-1 flex items-center"><FaInfoCircle className="mr-1.5" /> LEGEND:</p>
                            <p className="text-muted-foreground text-xs">{legend}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};


// ## InstitutionCard Component ##
interface InstitutionCardProps {
    institution: InstitutionData;
    index: number;
}

const InstitutionCard: React.FC<InstitutionCardProps> = ({ institution, index }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const toggleExpansion = useCallback(() => setIsExpanded(prev => !prev), []);
    const animationDelay = `${index * 0.05}s`;
    const detailsId = `institution-details-${institution.institute.replace(/\s+/g, '-')}-${index}`;

    return (
        // Use semantic card styles, primary for hover border
        <div
            className="bg-card rounded-lg shadow-md overflow-hidden mb-4 border border-border hover:border-primary transition-all duration-300 animate-fade-in"
            style={{ animationDelay, opacity: 0, animationFillMode: 'forwards' }}
        >
            <div
                className="p-4 cursor-pointer flex justify-between items-center"
                onClick={toggleExpansion}
                role="button"
                aria-expanded={isExpanded}
                aria-controls={detailsId}
            >
                <div className="flex-1 mr-4 overflow-hidden">
                     {/* Use semantic text colors */}
                    <h3 className="text-card-foreground font-medium truncate" title={institution.institute}>{institution.institute}</h3>
                    <div className="flex items-center flex-wrap text-sm text-muted-foreground mt-1 space-x-4">
                         {/* Use specific colors for icons, could be themed later */}
                        <span className="flex items-center whitespace-nowrap"><FaFileAlt className="mr-1.5 text-blue-500 dark:text-blue-400 flex-shrink-0" />{institution.unique_paper_count} {institution.unique_paper_count === 1 ? 'Paper' : 'Papers'}</span>
                        <span className="flex items-center whitespace-nowrap"><FaUsers className="mr-1.5 text-pink-500 dark:text-pink-400 flex-shrink-0" />{institution.author_count} {institution.author_count === 1 ? 'Author' : 'Authors'}</span>
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
                 // Use semantic border/text colors, distinct bg for list items
                <div id={detailsId} className="px-4 pb-4 pt-2 border-t border-border">
                    <p className="text-foreground text-sm mb-3 font-medium">Published Papers ({institution.unique_paper_count}):</p>
                    {institution.papers && institution.papers.length > 0 ? (
                        <ul className="space-y-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                            {institution.papers.map((paper, idx) => (
                                // Use a slightly different background for list items
                                <li key={`${paper.id}-${idx}`} className="text-muted-foreground text-sm bg-background p-3 rounded-md shadow-sm">
                                     {/* Use primary color for link hover */}
                                    <a href={`https://openreview.net/forum?id=${paper.id}`} target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors block break-words" title={paper.title}>
                                        {paper.title} <span className="text-xs text-muted-foreground/70 ml-1">(ID: {paper.id})</span>
                                    </a>
                                    {/* Badge styling using appropriate light/dark pairings */}
                                    {paper.isSpotlight && (<span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"><FaStar className="mr-1" size={10} />Spotlight</span>)}
                                    {paper.isOral && (<span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300"><FaTrophy className="mr-1" size={10} />Oral</span>)}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-muted-foreground/70 text-sm italic">No specific paper details available.</p>
                    )}
                </div>
            )}
        </div>
    );
};

// ## DataTable Component ##
interface DataTableProps {
    data: Record<string, string | number | boolean | undefined | null>[];
    title: string;
    filename: string;
}

const DataTable: React.FC<DataTableProps> = ({ data, title, filename }) => {
    if (!data || data.length === 0) {
        return <div className="text-muted-foreground p-4">No data available for the table.</div>;
    }
    const headers = data.length > 0 ? Object.keys(data[0]) : [];
    const handleExport = useCallback(() => exportToCSV(data, filename), [data, filename]);

    return (
        <div className="overflow-x-auto">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                <h4 className="text-foreground font-medium text-lg">{title}</h4>
                 {/* Use primary button style */}
                <button onClick={handleExport} className="flex items-center bg-primary hover:bg-primary/90 text-primary-foreground text-xs px-3 py-1.5 rounded transition-colors shadow-sm" aria-label={`Export ${title} data to CSV`}>
                    <FaDownload className="mr-1.5" size={10} /> Export CSV
                </button>
            </div>
             {/* Use semantic borders */}
            <div className="border border-border rounded-lg overflow-hidden">
                 {/* Use semantic background/divide */}
                <table className="min-w-full divide-y divide-border">
                     {/* Use muted background for header */}
                    <thead className="bg-muted">
                        <tr>{headers.map((header) => (<th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider whitespace-nowrap">{header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>))}</tr>
                    </thead>
                     {/* Use card background for body, semantic divide */}
                    <tbody className="bg-card divide-y divide-border">
                        {data.map((row, rowIndex) => (
                             // Use semantic hover, conditional highlight using appropriate light/dark pairing
                            <tr key={rowIndex} className={`${row.highlight ? 'bg-amber-100 dark:bg-amber-900/30' : ''} hover:bg-muted/50 transition-colors`}>
                                {headers.map((header, colIndex) => (
                                    <td key={`${rowIndex}-${colIndex}`} className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                                        {typeof row[header] === 'boolean' ? (row[header] ? 'Yes' : 'No') : (row[header]?.toLocaleString() ?? '')}
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

// ## ViewToggle Component ##
interface ViewToggleProps {
    activeView: ViewMode;
    setActiveView: (view: ViewMode) => void;
}

const ViewToggle: React.FC<ViewToggleProps> = ({ activeView, setActiveView }) => (
     // Use muted background
    <div className="flex items-center space-x-1 bg-muted p-1 rounded-lg shadow-inner">
         {/* Use primary for active, muted for inactive */}
        <button onClick={() => setActiveView('chart')} className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${activeView === 'chart' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-transparent text-muted-foreground hover:bg-background hover:text-foreground'}`} aria-pressed={activeView === 'chart'}>
            <FaChartBar size={12} /><span>Chart</span>
        </button>
        <button onClick={() => setActiveView('table')} className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${activeView === 'table' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-transparent text-muted-foreground hover:bg-background hover:text-foreground'}`} aria-pressed={activeView === 'table'}>
            <FaTable size={12} /><span>Table</span>
        </button>
    </div>
);


// --- Main Dashboard Component ---

interface DashboardDataProps {
    dashboardData: DashboardData;
}

const ICLRDashboard: React.FC<DashboardDataProps> = ({ dashboardData }) => {
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

    const { conferenceInfo, globalStats, indiaFocus, interpretations } = dashboardData;

    // --- Memoized Data Processing (Add flags/variables for styling) ---

    const sortedCountries: CountryData[] = useMemo(() => {
        const countryMap = new Map<string, CountryData>();
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

    const processedIndiaData: ProcessedIndiaData | null = useMemo(() => {
        if (!indiaGlobalStats) return null;
        const data = { ...indiaFocus } as ProcessedIndiaData;
        data.rank = indiaGlobalStats.rank;
        data.paper_count = indiaGlobalStats.paper_count;
        data.author_count = indiaGlobalStats.author_count;
        data.spotlights = indiaGlobalStats.spotlights;
        data.orals = indiaGlobalStats.orals;
        return data;
    }, [indiaFocus, indiaGlobalStats]);

    // Data for charts now includes CSS variables or flags for conditional classing
     const usVsChinaVsRest: NameValueData[] = useMemo(() => {
        if (!usData || !cnData) return [];
        const usCount = usData.paper_count;
        const cnCount = cnData.paper_count;
        const totalCount = conferenceInfo.totalAcceptedPapers || sortedCountries.reduce((sum, country) => sum + country.paper_count, 0);
        const restCount = Math.max(0, totalCount - usCount - cnCount);
        const totalForPercent = usCount + cnCount + restCount || 1;

        return [
            // Reference specific theme colors or direct HSL values if needed
             { name: 'US + China', value: usCount + cnCount, fillVariable: 'hsl(221, 83%, 53%)', percent: (usCount + cnCount) / totalForPercent }, // Example: Blue-ish
             { name: 'Rest of World', value: restCount, fillVariable: 'hsl(var(--secondary-foreground))', percent: restCount / totalForPercent } // Example: Secondary
         ];
    }, [usData, cnData, sortedCountries, conferenceInfo.totalAcceptedPapers]);

     const apacCountries: NameValueData[] = useMemo(() => {
        const filtered = sortedCountries
            .filter(country => APAC_COUNTRIES.includes(country.affiliation_country))
            .sort((a, b) => b.paper_count - a.paper_count);
        const totalApacPapers = filtered.reduce((sum, c) => sum + c.paper_count, 0) || 1;

        return filtered.map(country => ({
            name: country.country_name,
            value: country.paper_count,
            // Use specific colors for highlighted countries, secondary for others
             fillVariable: country.country_name === 'China' ? 'hsl(0, 84%, 60%)' : // Red-ish
                           country.country_name === 'India' ? 'hsl(36, 96%, 50%)' : // Amber-ish
                           'hsl(var(--secondary-foreground))', // Default/Secondary
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
                { name: 'Majority Indian', value: majority, fillVariable: 'hsl(142, 71%, 45%)', percent: majority / totalWithIndianAuthor }, // Green-ish
                 { name: 'Minority Indian', value: minority, fillVariable: 'hsl(var(--primary))', percent: minority / totalWithIndianAuthor }
            ],
            firstAuthor: [
                { name: 'First Indian Author', value: firstAuthor, fillVariable: 'hsl(330, 80%, 60%)', percent: firstAuthor / totalWithIndianAuthor }, // Pink-ish
                 { name: 'Non-First Indian Author', value: nonFirstAuthor, fillVariable: 'hsl(var(--primary))', percent: nonFirstAuthor / totalWithIndianAuthor }
            ]
        };
    }, [processedIndiaData]);

    const institutionTypePieData: NameValueData[] = useMemo(() => {
        if (!processedIndiaData || !processedIndiaData.institution_types) return [];
        const academic = processedIndiaData.institution_types.academic || 0;
        const corporate = processedIndiaData.institution_types.corporate || 0;
        const total = academic + corporate || 1;
        return [
            { name: 'Academic', value: academic, fillVariable: 'hsl(221, 83%, 53%)', percent: academic / total }, // Blue-ish
             { name: 'Corporate', value: corporate, fillVariable: 'hsl(330, 80%, 60%)', percent: corporate / total } // Pink-ish
        ];
    }, [processedIndiaData]);

    const filteredInstitutions: InstitutionData[] = useMemo(() => {
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

     const institutionContributionPieData: NameValueData[] = useMemo(() => {
        if (!filteredInstitutions.length) return [];
        const academicPapers = filteredInstitutions.filter(inst => inst.type === 'academic').reduce((sum, inst) => sum + inst.unique_paper_count, 0);
        const corporatePapers = filteredInstitutions.filter(inst => inst.type === 'corporate').reduce((sum, inst) => sum + inst.unique_paper_count, 0);
        const total = academicPapers + corporatePapers || 1;
        return [
            { name: 'Academic', value: academicPapers, fillVariable: 'hsl(221, 83%, 53%)', percent: academicPapers / total },
             { name: 'Corporate', value: corporatePapers, fillVariable: 'hsl(330, 80%, 60%)', percent: corporatePapers / total }
        ];
    }, [filteredInstitutions]);


    // --- Event Handlers (Unchanged) ---
    const handleTabChange = useCallback((index: number) => setActiveTabIndex(index), []);
    const handleFilterChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => setInstitutionFilter(event.target.value), []);
    const handlePieEnter = useCallback((_: any, index: number) => setActivePieIndex(index), []);
    const handleSetViewMode = useCallback((viewKey: string, mode: ViewMode) => setViewModes(prev => ({ ...prev, [viewKey]: mode })), []);

    // --- Render Logic ---

    if (!processedIndiaData || !usData || !cnData) {
        return (
             // Use destructive or warning colors for error message
            <div className="min-h-screen bg-background flex items-center justify-center p-6">
                <div className="bg-destructive/10 border border-destructive/30 text-destructive px-4 py-3 rounded-lg shadow-lg text-center">
                    <h2 className="font-bold text-lg mb-2">Data Processing Issue</h2>
                    <p>Could not process the required dashboard data (e.g., US, China, or India stats missing/invalid).</p>
                </div>
            </div>
        );
    }

    const totalPapers = conferenceInfo.totalAcceptedPapers;

    // CSS variables for Recharts colors (can be defined here or globally)
    const colorMap = {
        us: 'hsl(221, 83%, 53%)', // Blue
        cn: 'hsl(0, 84%, 60%)',   // Red
        in: 'hsl(36, 96%, 50%)',  // Amber
        primary: 'hsl(var(--primary))',
        secondary: 'hsl(var(--secondary-foreground))', // Often a good contrast
        academic: 'hsl(221, 83%, 53%)', // Blue
        corporate: 'hsl(330, 80%, 60%)', // Pink
        spotlight: 'hsl(48, 96%, 50%)', // Yellow
        oral: 'hsl(330, 80%, 60%)', // Pink (reusing)
        grid: 'hsl(var(--border))',
        textAxis: 'hsl(var(--muted-foreground))',
        highlight: 'hsl(142, 71%, 45%)', // Green
        accent: 'hsl(330, 80%, 60%)', // Pink (reusing)
        warning: 'hsl(36, 96%, 50%)', // Amber
    };

    return (
        // Use semantic bg/text colors
        <div className="min-h-screen bg-background text-foreground p-4 sm:p-6 font-sans">
            {/* Header */}
            <header className="mb-6 md:mb-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-bold text-foreground flex items-center">
                             {/* Use primary color for icon */}
                            <FaTrophy className="mr-2 text-primary" /> {conferenceInfo.name} {conferenceInfo.year} Research Analysis
                        </h1>
                        <p className="text-muted-foreground mt-1 text-sm sm:text-base">Global Contributions & India Focus</p>
                    </div>
                     {/* Use card styles */}
                    <div className="bg-card rounded-lg p-3 text-sm text-card-foreground border border-border shadow-sm whitespace-nowrap">
                        Total Accepted Papers: <span className="font-bold text-foreground">{totalPapers.toLocaleString()}</span>
                    </div>
                </div>
                {/* Tabs */}
                 {/* Use semantic border */}
                <div className="mt-6 border-b border-border">
                    <nav className="-mb-px flex space-x-1 sm:space-x-4 overflow-x-auto pb-0" aria-label="Tabs">
                        {TABS.map((tab, index) => (
                            <button
                                key={tab}
                                onClick={() => handleTabChange(index)}
                                className={`whitespace-nowrap py-3 px-3 sm:px-4 border-b-2 font-medium text-sm sm:text-base focus:outline-none transition-colors duration-200 ${
                                    activeTabIndex === index
                                        // Use primary for active state
                                        ? 'border-primary text-primary'
                                         // Use muted for inactive state
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
            <main>
                {/* --- Overview Tab --- */}
                {activeTabIndex === 0 && (
                    <div className="space-y-6 md:space-y-8 animate-fade-in">
                         <h2 className="text-xl font-semibold text-foreground mb-4">India at {conferenceInfo.name} {conferenceInfo.year}: Overview</h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
                             {/* Pass appropriate color classes */}
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
                         {/* Use card styles */}
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

                        {/* Top Indian Institutions Preview */}
                         {/* Use card styles */}
                        <div className="bg-card rounded-xl p-4 sm:p-6 border border-border">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
                                <h2 className="text-xl font-bold text-foreground">Top Indian Institutions Preview</h2>
                                 {/* Use primary color for link */}
                                <button className="text-primary hover:text-primary/80 text-sm flex items-center font-medium" onClick={() => handleTabChange(3)}>
                                    View All Institutions <span className="ml-1">→</span>
                                </button>
                            </div>
                            {filteredInstitutions.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {filteredInstitutions.slice(0, 6).map((institution, index) => (
                                        <InstitutionCard key={`preview-${institution.institute}-${index}`} institution={institution} index={index} />
                                    ))}
                                </div>
                            ) : (
                                <p className="text-muted-foreground text-center py-4">No institutions found.</p>
                            )}
                        </div>
                    </div>
                )}

                {/* --- Global Stats Tab --- */}
                {activeTabIndex === 1 && (
                    <div className="space-y-6 md:space-y-8 animate-fade-in">
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
                                     {/* Use muted background for chart area */}
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
                )}

                {/* --- India Focus Tab --- */}
                 {activeTabIndex === 2 && (
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
                                                        {authorshipPieData.authorship.map((entry, index) => <Cell key={`cell-author-bar-${index}`} fill={entry.fillVariable} />)}
                                                    </Bar>
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                        <div className="h-64">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <PieChart>
                                                    <Pie data={authorshipPieData.authorship} cx="50%" cy="50%" outerRadius={70} dataKey="value" labelLine={false} >
                                                        {authorshipPieData.authorship.map((entry, index) => <Cell key={`cell-author-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'}/>)}
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
                                                         {authorshipPieData.firstAuthor.map((entry, index) => <Cell key={`cell-first-bar-${index}`} fill={entry.fillVariable} />)}
                                                     </Bar>
                                                 </BarChart>
                                             </ResponsiveContainer>
                                        </div>
                                        <div className="h-64">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <PieChart>
                                                    <Pie data={authorshipPieData.firstAuthor} cx="50%" cy="50%" outerRadius={70} dataKey="value" labelLine={false}>
                                                        {authorshipPieData.firstAuthor.map((entry, index) => <Cell key={`cell-first-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'} />)}
                                                    </Pie>
                                                    <Tooltip content={<CustomTooltip />} />
                                                    <Legend iconSize={10} wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}/>
                                                </PieChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                     {/* Chart Set 3: Institution Type */}
                                    <div className="space-y-4 bg-muted/30 rounded-lg p-4">
                                        <h3 className="text-center text-base font-semibold text-foreground">Institution Type (Papers)</h3>
                                         <div className="h-64">
                                             <ResponsiveContainer width="100%" height="100%">
                                                 <BarChart data={institutionTypePieData} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                                     <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false} />
                                                     <XAxis dataKey="name" stroke={colorMap.textAxis} fontSize={10} />
                                                     <YAxis stroke={colorMap.textAxis} fontSize={10} />
                                                     <Tooltip content={<CustomTooltip />} />
                                                     <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                                         {institutionTypePieData.map((entry, index) => <Cell key={`cell-instype-bar-${index}`} fill={entry.fillVariable} />)}
                                                     </Bar>
                                                 </BarChart>
                                             </ResponsiveContainer>
                                         </div>
                                         <div className="h-64">
                                             <ResponsiveContainer width="100%" height="100%">
                                                 <PieChart>
                                                     <Pie data={institutionTypePieData} cx="50%" cy="50%" outerRadius={70} dataKey="value" labelLine={false}>
                                                         {institutionTypePieData.map((entry, index) => <Cell key={`cell-instype-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'} />)}
                                                     </Pie>
                                                     <Tooltip content={<CustomTooltip />} />
                                                     <Legend iconSize={10} wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}/>
                                                 </PieChart>
                                             </ResponsiveContainer>
                                         </div>
                                    </div>
                                </div>
                            ) : (
                                <DataTable data={[ ...(authorshipPieData ? [ { Category: "Majority Indian Authors", Papers: authorshipPieData.authorship[0].value, Percentage: `${(authorshipPieData.authorship[0].percent * 100).toFixed(1)}%` }, { Category: "Minority Indian Authors", Papers: authorshipPieData.authorship[1].value, Percentage: `${(authorshipPieData.authorship[1].percent * 100).toFixed(1)}%` }, { Category: "First Indian Author", Papers: authorshipPieData.firstAuthor[0].value, Percentage: `${(authorshipPieData.firstAuthor[0].percent * 100).toFixed(1)}%` }, { Category: "Non-First Indian Author", Papers: authorshipPieData.firstAuthor[1].value, Percentage: `${(authorshipPieData.firstAuthor[1].percent * 100).toFixed(1)}%` }, ] : []), ...institutionTypePieData.map(item => ({ Category: `${item.name} Papers`, Papers: item.value, Percentage: `${(item.percent * 100).toFixed(1)}%` })) ]} title="Authorship & Institution Type Summary" filename="india_authorship_summary_iclr_2025" />
                            )}
                             <InterpretationPanel title={interpretations.indiaFocus.title} insights={interpretations.indiaFocus.insights} legend={interpretations.indiaFocus.legend} />
                        </div>

                        {/* Comparative Metrics */}
                        <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                                <div>
                                    <h2 className="text-xl font-bold text-foreground">India vs. US & China: Comparative Metrics</h2>
                                    <p className="text-sm text-muted-foreground">Comparing key research output indicators.</p>
                                </div>
                                <ViewToggle activeView={viewModes.comparison} setActiveView={(mode) => handleSetViewMode('comparison', mode)} />
                            </div>
                            {viewModes.comparison === 'chart' ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Chart 1: Paper Count */}
                                    <div className="bg-muted/30 p-4 rounded-lg">
                                        <h4 className="text-foreground font-medium mb-3 text-center text-base">Paper Count Comparison</h4>
                                        <div className="h-80">
                                            <ResponsiveContainer width="100%" height="100%">
                                                 <BarChart data={[ { name: 'US', Papers: usData.paper_count, fill: colorMap.us }, { name: 'China', Papers: cnData.paper_count, fill: colorMap.cn }, { name: 'India', Papers: processedIndiaData.paper_count, fill: colorMap.in } ]} margin={{ top: 5, right: 10, left: 10, bottom: 5 }} >
                                                     <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false}/>
                                                     <XAxis dataKey="name" stroke={colorMap.textAxis} fontSize={11}/>
                                                     <YAxis stroke={colorMap.textAxis} fontSize={11} />
                                                     <Tooltip content={<CustomTooltip />}/>
                                                     <Bar dataKey="Papers" name="Papers" radius={[4, 4, 0, 0]}>
                                                         {[colorMap.us, colorMap.cn, colorMap.in].map((color, index) => <Cell key={`cell-comp-paper-${index}`} fill={color} /> )}
                                                     </Bar>
                                                 </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                    {/* Chart 2: Spotlights & Orals */}
                                    <div className="bg-muted/30 p-4 rounded-lg">
                                         <h4 className="text-foreground font-medium mb-3 text-center text-base">Spotlight & Oral Count</h4>
                                         <div className="h-80">
                                             <ResponsiveContainer width="100%" height="100%">
                                                 <BarChart data={[ { name: 'US', spotlights: usData.spotlights, orals: usData.orals, total: usData.spotlights + usData.orals, spotlight_percent: ((usData.spotlights / usData.paper_count) * 100).toFixed(1), oral_percent: ((usData.orals / usData.paper_count) * 100).toFixed(1) }, { name: 'China', spotlights: cnData.spotlights, orals: cnData.orals, total: cnData.spotlights + cnData.orals, spotlight_percent: ((cnData.spotlights / cnData.paper_count) * 100).toFixed(1), oral_percent: ((cnData.orals / cnData.paper_count) * 100).toFixed(1) }, { name: 'India', spotlights: processedIndiaData.spotlights, orals: processedIndiaData.orals, total: (processedIndiaData.spotlights ?? 0) + (processedIndiaData.orals ?? 0), spotlight_percent: (((processedIndiaData.spotlights ?? 0) / (processedIndiaData.paper_count ?? 1)) * 100).toFixed(1), oral_percent: (((processedIndiaData.orals ?? 0) / (processedIndiaData.paper_count ?? 1)) * 100).toFixed(1) } ]} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                                                     <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false}/>
                                                     <XAxis dataKey="name" stroke={colorMap.textAxis} fontSize={11} />
                                                     <YAxis stroke={colorMap.textAxis} fontSize={11}/>
                                                     <Tooltip content={<CustomTooltip />} />
                                                     <Bar dataKey="total" name="Total Impact" fill="transparent" /> {/* Invisible bar for tooltip */}
                                                     <Bar dataKey="spotlights" name="Spotlights" stackId="a" fill={colorMap.warning} radius={[4, 4, 0, 0]}/>
                                                     <Bar dataKey="orals" name="Orals" stackId="a" fill={colorMap.accent} radius={[4, 4, 0, 0]}/>
                                                     <Legend iconSize={10} wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }}/>
                                                 </BarChart>
                                             </ResponsiveContainer>
                                         </div>
                                    </div>
                                    {/* Chart 3: Authors per Paper - Adjusted barSize */}
                                    <div className="bg-muted/30 p-4 rounded-lg md:col-span-2">
                                        <h4 className="text-foreground font-medium mb-3 text-center text-base">Average Authors per Paper</h4>
                                        <div className="h-64">
                                            <ResponsiveContainer width="100%" height="100%">
                                                {/* Adjusted: Removed barSize prop to use default/auto or match others e.g. barSize={20} */}
                                                <BarChart data={[ { name: 'US', ratio: parseFloat((usData.author_count / usData.paper_count).toFixed(2)), papers: usData.paper_count, authors: usData.author_count, fill: colorMap.us }, { name: 'China', ratio: parseFloat((cnData.author_count / cnData.paper_count).toFixed(2)), papers: cnData.paper_count, authors: cnData.author_count, fill: colorMap.cn }, { name: 'India', ratio: parseFloat(((processedIndiaData.author_count ?? 0) / (processedIndiaData.paper_count ?? 1)).toFixed(2)), papers: processedIndiaData.paper_count ?? 0, authors: processedIndiaData.author_count ?? 0, fill: colorMap.in } ]} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} vertical={false}/>
                                                    <XAxis dataKey="name" stroke={colorMap.textAxis} fontSize={11}/>
                                                    <YAxis stroke={colorMap.textAxis} fontSize={11} domain={[0, 'dataMax + 0.5']}/>
                                                    <Tooltip content={<CustomTooltip />}/>
                                                     {/* Explicitly set barSize to match others if desired, or remove for auto */}
                                                    <Bar dataKey="ratio" name="Authors per Paper" barSize={20} radius={[4, 4, 0, 0]}>
                                                         {[colorMap.us, colorMap.cn, colorMap.in].map((color, index) => <Cell key={`cell-comp-ratio-${index}`} fill={color} />)}
                                                    </Bar>
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <DataTable data={[ { Country: 'United States', Papers: usData.paper_count.toLocaleString(), Authors: usData.author_count.toLocaleString(), Spotlights: usData.spotlights, 'Spotlight_%': `${((usData.spotlights / usData.paper_count) * 100).toFixed(1)}%`, Orals: usData.orals, 'Oral_%': `${((usData.orals / usData.paper_count) * 100).toFixed(1)}%`, 'Authors_Paper': (usData.author_count / usData.paper_count).toFixed(2), highlight: false }, { Country: 'China', Papers: cnData.paper_count.toLocaleString(), Authors: cnData.author_count.toLocaleString(), Spotlights: cnData.spotlights, 'Spotlight_%': `${((cnData.spotlights / cnData.paper_count) * 100).toFixed(1)}%`, Orals: cnData.orals, 'Oral_%': `${((cnData.orals / cnData.paper_count) * 100).toFixed(1)}%`, 'Authors_Paper': (cnData.author_count / cnData.paper_count).toFixed(2), highlight: false }, { Country: 'India', Papers: (processedIndiaData.paper_count ?? 0).toLocaleString(), Authors: (processedIndiaData.author_count ?? 0).toLocaleString(), Spotlights: processedIndiaData.spotlights ?? 0, 'Spotlight_%': `${(((processedIndiaData.spotlights ?? 0) / (processedIndiaData.paper_count || 1)) * 100).toFixed(1)}%`, Orals: processedIndiaData.orals ?? 0, 'Oral_%': `${(((processedIndiaData.orals ?? 0) / (processedIndiaData.paper_count || 1)) * 100).toFixed(1)}%`, 'Authors_Paper': ((processedIndiaData.author_count ?? 0) / (processedIndiaData.paper_count || 1)).toFixed(2), highlight: true } ]} title="Country Comparison Summary" filename="country_comparison_summary_iclr_2025" />
                            )}
                             <InterpretationPanel title={interpretations.comparativePerformance.title} insights={interpretations.comparativePerformance.insights} legend={interpretations.comparativePerformance.legend} />
                        </div>

                        {/* Potential Research Focus Areas */}
                        <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                             <h2 className="text-xl font-bold mb-4 text-foreground">Potential Research Focus Areas for India</h2>
                            <div className="space-y-3">
                                 {/* Use muted background for focus items, specific icon colors */}
                                <div className="bg-muted p-4 rounded-lg shadow-sm flex items-start gap-3"><FaLightbulb className="text-blue-500 dark:text-blue-400 mt-1 flex-shrink-0" size={18}/><div><h3 className="font-medium text-foreground">LLMs & NLP</h3><p className="text-muted-foreground text-sm mt-1">Contributions observed in evaluation, multilingual understanding, efficiency, and specific applications (e.g., engagement, persuasiveness).</p></div></div>
                                <div className="bg-muted p-4 rounded-lg shadow-sm flex items-start gap-3"><FaLightbulb className="text-emerald-500 dark:text-emerald-400 mt-1 flex-shrink-0" size={18}/><div><h3 className="font-medium text-foreground">GNNs & Theory</h3><p className="text-muted-foreground text-sm mt-1">Activity seen in graph representations, condensation techniques, and theoretical underpinnings like sampling and sensitivity analysis.</p></div></div>
                                <div className="bg-muted p-4 rounded-lg shadow-sm flex items-start gap-3"><FaLightbulb className="text-amber-500 dark:text-amber-400 mt-1 flex-shrink-0" size={18}/><div><h3 className="font-medium text-foreground">Robustness & Efficiency</h3><p className="text-muted-foreground text-sm mt-1">Focus noted on debiasing methods, adversarial robustness, model compression, and designing efficient deep learning models.</p></div></div>
                             </div>
                             <InterpretationPanel title={interpretations.futureOpportunities.title} insights={interpretations.futureOpportunities.insights} legend={interpretations.futureOpportunities.legend} />
                        </div>
                     </div>
                 )}

                {/* --- Institutions Tab --- */}
                 {activeTabIndex === 3 && (
                     <div className="space-y-6 md:space-y-8 animate-fade-in">
                        {/* Header and Search */}
                        <div className="bg-card rounded-xl p-4 sm:p-6 border border-border shadow-lg">
                            <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                                <h2 className="text-xl font-bold text-foreground">Indian Research Institutions @ {conferenceInfo.name} {conferenceInfo.year}</h2>
                                <div className="relative w-full md:w-auto">
                                    <label htmlFor="institution-search" className="sr-only">Search Institutions</label>
                                     {/* Use input styles */}
                                    <input id="institution-search" type="search" placeholder="Search institutions..." className="bg-input border border-border rounded-lg py-2 pl-10 pr-4 text-foreground w-full md:w-72 focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent shadow-sm placeholder-muted-foreground" value={institutionFilter} onChange={handleFilterChange} />
                                    <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground pointer-events-none" />
                                </div>
                            </div>
                        </div>

                        {/* Institution Charts / Table */}
                        <div className="bg-card rounded-xl p-4 sm:p-6 border border-border mb-6">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                                <div>
                                    <h3 className="text-lg font-bold text-foreground">Institution Contribution Analysis</h3>
                                    <p className="text-sm text-muted-foreground">Top institutions by papers and academic/corporate split.</p>
                                </div>
                                <ViewToggle activeView={viewModes.institutions} setActiveView={(mode) => handleSetViewMode('institutions', mode)} />
                            </div>

                            {viewModes.institutions === 'chart' && institutionChartData.length > 0 ? (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
                                    {/* Bar Chart */}
                                    <div className="bg-muted/30 rounded-lg p-4">
                                        <h4 className="text-center text-base font-semibold text-foreground mb-2">Papers by Institution (Top {institutionChartData.length})</h4>
                                        <div className="h-96">
                                            <ResponsiveContainer width="100%" height="100%">
                                                 <BarChart data={institutionChartData} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
                                                     <CartesianGrid strokeDasharray="3 3" stroke={colorMap.grid} horizontal={false} />
                                                     <XAxis type="number" stroke={colorMap.textAxis} axisLine={false} tickLine={false} />
                                                     <YAxis type="category" dataKey="institute" stroke={colorMap.textAxis} width={120} tick={{ fontSize: 10, fill: colorMap.textAxis }} interval={0} axisLine={false} tickLine={false} />
                                                     <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }}/>
                                                     <Bar dataKey="unique_paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={18}>
                                                         {institutionChartData.map((entry, index) => <Cell key={`cell-inst-bar-${index}`} fill={entry.fillVariable} />)}
                                                     </Bar>
                                                 </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                    {/* Pie Chart */}
                                    <div className="bg-muted/30 rounded-lg p-4">
                                         <h4 className="text-center text-base font-semibold text-foreground mb-2">Academic vs. Corporate Papers</h4>
                                         <div className="h-80">
                                             <ResponsiveContainer width="100%" height="100%">
                                                 <PieChart>
                                                     <Pie activeIndex={activePieIndex} activeShape={renderActiveShape} data={institutionContributionPieData} cx="50%" cy="50%" innerRadius={70} outerRadius={100} dataKey="value" onMouseEnter={handlePieEnter}>
                                                         {institutionContributionPieData.map((entry, index) => <Cell key={`cell-inst-pie-${index}`} fill={entry.fillVariable} stroke={'hsl(var(--card))'} />)}
                                                     </Pie>
                                                     <Tooltip content={<CustomTooltip />} />
                                                     <Legend iconSize={10} wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--foreground))' }} layout="vertical" align="right" verticalAlign="middle" />
                                                 </PieChart>
                                             </ResponsiveContainer>
                                         </div>
                                         {/* Summary Cards - Use appropriate light/dark pairings */}
                                         <div className="mt-4 grid grid-cols-2 gap-3 text-center">
                                              <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded">
                                                  <p className="text-xs text-blue-700 dark:text-blue-300">Academic Spots/Orals</p>
                                                  <p className="text-lg font-bold text-blue-900 dark:text-blue-200">{filteredInstitutions.filter(i => i.type === 'academic').reduce((sum, i) => sum + i.spotlights + i.orals, 0)}</p>
                                              </div>
                                              <div className="bg-pink-100 dark:bg-pink-900/30 p-2 rounded">
                                                  <p className="text-xs text-pink-700 dark:text-pink-300">Corporate Spots/Orals</p>
                                                  <p className="text-lg font-bold text-pink-900 dark:text-pink-200">{filteredInstitutions.filter(i => i.type === 'corporate').reduce((sum, i) => sum + i.spotlights + i.orals, 0)}</p>
                                              </div>
                                         </div>
                                    </div>
                                </div>
                            ) : ( // Table View or No Data
                                institutionChartData.length > 0 ? (
                                    <DataTable data={filteredInstitutions.map(inst => ({ Institution: inst.institute, Type: inst.type || 'Unknown', Papers: inst.unique_paper_count, Authors: inst.author_count, Spotlights: inst.spotlights, Orals: inst.orals, 'Papers_Author': inst.author_count > 0 ? (inst.unique_paper_count / inst.author_count).toFixed(2) : 'N/A', highlight: inst.institute === topIndianInstitution?.institute }))} title="Indian Institution Summary" filename="indian_institutions_summary_iclr_2025" />
                                ) : (
                                    <p className="text-muted-foreground text-center py-4">No institutions match the current filter.</p>
                                )
                            )}
                            <InterpretationPanel title={interpretations.institutionAnalysis.title} insights={interpretations.institutionAnalysis.insights} legend={interpretations.institutionAnalysis.legend} />
                        </div>

                        {/* Detailed Institution List (Cards) */}
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-foreground">Detailed Institution List</h3>
                             {filteredInstitutions.length > 0 && (
                                 <button onClick={() => exportToCSV( filteredInstitutions.map(inst => ({ Institution: inst.institute, Type: inst.type || 'Unknown', Unique_Papers: inst.unique_paper_count, Authors: inst.author_count, Spotlights: inst.spotlights, Orals: inst.orals })), 'detailed_indian_institutions_iclr_2025' )} className="flex items-center bg-primary hover:bg-primary/90 text-primary-foreground text-xs px-3 py-1.5 rounded transition-colors shadow-sm" aria-label="Export detailed institution list to CSV">
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
                            <div className="text-center py-10 text-muted-foreground bg-card rounded-lg border border-border">
                                <FaUniversity size={36} className="mx-auto mb-3" />
                                <p>No institutions found matching "{institutionFilter}".</p>
                                <p className="text-sm mt-1">Try refining your search term.</p>
                            </div>
                        )}
                    </div>
                 )}
            </main>

            {/* Footer */}
             {/* Use muted text, semantic border */}
            <footer className="mt-10 md:mt-12 text-center text-muted-foreground text-xs border-t border-border pt-4">
                <p>{conferenceInfo.name} {conferenceInfo.year} Dashboard | Data based on provided structure.</p>
                <p>Data processing includes combining UK/GB entries. Other stats reflect the input data.</p>
                <p className="mt-1">&copy; {new Date().getFullYear()} Analysis Dashboard</p>
            </footer>

             {/* REMOVED inline <style jsx global> - Move styles to globals.css */}

        </div>
    );
};


// --- Example Usage ---
const App: React.FC = () => {
    // Add a simple dark mode toggle for demonstration if needed
    // Example: Add 'dark' class to document.documentElement
    // useEffect(() => {
    //     document.documentElement.classList.add('dark'); // Or toggle based on state
    // }, [])
    return <ICLRDashboard dashboardData={dashboardData} />;
}

export default App;