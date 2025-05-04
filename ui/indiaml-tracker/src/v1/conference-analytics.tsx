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

// --- Constants ---

const COLORS = {
    primary: '#6366f1', // indigo-500
    secondary: '#8b5cf6', // violet-500
    accent: '#ec4899', // pink-500
    highlight: '#10b981', // emerald-500
    warning: '#f59e0b', // amber-500
    success: '#22c55e', // green-500
    info: '#3b82f6', // blue-500
    background: '#111827', // gray-900
    card: '#1f2937', // gray-800
    text: '#f9fafb', // gray-50
    textSecondary: '#94a3b8', // slate-400
    border: '#374151', // gray-700
    usColor: '#3b82f6', // blue-500
    cnColor: '#ef4444', // red-500
    inColor: '#f59e0b', // amber-500
    grid: '#2d3748', // gray-700 equivalent for grid lines
    academic: '#3b82f6', // blue-500 for academic institutions
    corporate: '#ec4899', // pink-500 for corporate institutions
    interpretation: '#4b5563', // gray-600
};

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

// --- Type Definitions (Mostly unchanged, but some might reference DashboardData types if needed) ---

interface PaperSummary {
    id: string;
    title: string;
    isSpotlight?: boolean;
    isOral?: boolean; // Added optional isOral
}

interface InstitutionData {
    institute: string;
    total_paper_count: number; // Raw count from data
    unique_paper_count: number; // Processed unique count
    author_count: number;
    spotlights: number;
    orals: number;
    type: 'academic' | 'corporate' | 'unknown'; // More specific type
    papers: PaperSummary[];
    // Optional properties for chart rendering
    fill?: string;
    total?: number; // For stacked chart
}

interface CountryData {
    affiliation_country: string; // Original code
    country_name: string; // Mapped name
    paper_count: number;
    author_count: number;
    spotlights: number;
    orals: number;
    rank: number;
    // Optional properties for chart rendering
    fill?: string;
    opacity?: number;
}

// Interface for the *processed* India data, combining specific and global stats
type ProcessedIndiaData = DashboardData['indiaFocus'] & {
    rank?: number; // Added from global rank calculation
    paper_count?: number; // Added from global stats for consistency
    author_count: number; // Overridden by global stats for consistency
    spotlights: number; // Overridden by global stats for consistency
    orals: number; // Overridden by global stats for consistency
}

// Simplified raw structure from data (already reflected in DashboardData structure)
// interface RawCountryData { ... }

// Type for recharts payload in Tooltip
interface RechartsTooltipPayload {
    dataKey?: string | number;
    name?: string;
    value?: number | string;
    payload?: any;
    fill?: string;
    stroke?: string;
    color?: string;
}

// Type for recharts active shape props
interface ActiveShapeProps {
    cx?: number;
    cy?: number;
    midAngle?: number;
    innerRadius?: number;
    outerRadius?: number;
    startAngle?: number;
    endAngle?: number;
    fill?: string;
    payload?: any;
    percent?: number;
    value?: number;
    name?: string;
}

// Type for generic data used in pie charts / simple bar charts
interface NameValueData {
    name: string;
    value: number;
    fill?: string;
    percent?: number; // Optional percentage for tooltips/labels
    // Allow any other properties that might be added in processing
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


// --- Reusable UI Components (Unchanged logic, just ensure props are satisfied) ---

// ## StatCard Component ##
interface StatCardProps {
    title: string;
    value: string | number;
    icon?: React.ReactNode;
    color: keyof typeof COLORS | string; // Allow specific color names or general strings
    subtitle?: string;
    size?: 'normal' | 'large';
}

// Helper to safely generate Tailwind color classes (requires Tailwind JIT or safelisting)
const getTextColorClass = (colorName: string): string => `text-${colorName}-400`;
const getBgColorClass = (colorName: string): string => `bg-${colorName}-500`;


const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, subtitle, size = 'normal' }) => (
    <div className={`bg-gray-800 p-6 rounded-xl shadow-md border border-gray-700 flex flex-col ${size === 'large' ? 'lg:col-span-2' : ''}`}>
        <div className="flex items-center mb-2">
             {/* Use helper functions to construct class names safely */}
             {icon && <span className={`${getTextColorClass(color)} mr-3 text-lg`}>{icon}</span>}
            <h3 className="text-gray-400 font-medium text-sm uppercase tracking-wider">{title}</h3>
        </div>
        <div className="flex items-end justify-between mt-auto pt-2">
            <div>
                <p className={`text-white font-bold ${size === 'large' ? 'text-4xl' : 'text-3xl'}`}>{value}</p>
                {subtitle && <p className="text-gray-400 text-xs mt-1">{subtitle}</p>}
            </div>
            {color && (
                 <div className={`h-2 w-16 ${getBgColorClass(color)} rounded-full opacity-75 self-end mb-1`}></div>
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

        // --- Tooltip Content Logic (remains the same, relies on 'data' structure) ---
        if (data && ('country_name' in data || 'affiliation_country' in data) && (dataKey === 'paper_count' || dataKey === 'author_count' || dataKey === 'value')) {
             title = data.country_name || CountryMap[data.affiliation_country] || label || "Country";
             const paperCount = data.paper_count ?? data.value ?? 0;
             const authorCount = data.author_count ?? 'N/A';
             const metricName = dataKey === 'author_count' ? 'Authors' : 'Papers';
             const metricValue = dataKey === 'author_count' ? authorCount : paperCount;
             content = (
                 <>
                     <p className="text-white font-bold">{`${metricName}: ${metricValue?.toLocaleString()}`}</p>
                     {dataKey !== 'author_count' && authorCount !== 'N/A' && (
                         <p className="text-gray-400 text-xs mt-1">{`Authors: ${authorCount?.toLocaleString()}`}</p>
                     )}
                     {data.rank && (dataKey === 'paper_count' || dataKey === 'value') && (
                         <p className="text-gray-400 text-xs mt-1">{`Rank: #${data.rank}`}</p>
                     )}
                     {data.percent && (
                         <p className="text-gray-400 text-xs mt-1">{`(${(typeof data.percent === 'number' ? data.percent * 100 : 0).toFixed(1)}%)`}</p>                     )}
                 </>
             );
         }
         else if (data && 'institute' in data && (dataKey === 'unique_paper_count' || dataKey === 'author_count')) {
             title = data.institute;
             content = (
                 <>
                     <p className="text-indigo-300 font-bold">{`Papers: ${data.unique_paper_count?.toLocaleString() || 'N/A'}`}</p>
                     <p className="text-pink-300 font-bold">{`Authors: ${data.author_count?.toLocaleString() || 'N/A'}`}</p>
                     {data.spotlights > 0 && (
                         <p className="text-amber-300 font-bold">{`Spotlights: ${data.spotlights}`}</p>
                     )}
                     {data.orals > 0 && (
                         <p className="text-emerald-300 font-bold">{`Orals: ${data.orals}`}</p>
                     )}
                     <p className="text-gray-400 text-xs mt-1">{`Type: ${data.type || 'Unknown'}`}</p>
                 </>
             );
          }
          else if (data && 'spotlights' in data && 'orals' in data && dataKey === 'total') {
              title = data.name || label || "Comparison";
              const spotlightPercent = data.spotlight_percent !== undefined ? `${data.spotlight_percent}%` : 'N/A';
              const oralPercent = data.oral_percent !== undefined ? `${data.oral_percent}%` : 'N/A';
              content = (
                  <>
                      <p className="text-white font-bold">{`Total Spotlights/Orals: ${data.total || 0}`}</p>
                      <p className="text-amber-300">{`Spotlights: ${data.spotlights || 0} (${spotlightPercent})`}</p>
                      <p className="text-pink-300">{`Orals: ${data.orals || 0} (${oralPercent})`}</p>
                  </>
              );
          }
         else if (data && dataKey === 'value') {
             title = data.name || label || "Category";
             const percentText = data.percent ? `(${(typeof data.percent === 'number' ? data.percent * 100 : 0).toFixed(1)}%)` : '';
            content = <p className="text-white font-bold">{`${data.value?.toLocaleString() || 'N/A'} ${percentText}`}</p>;
         }
         else if (data && dataKey === 'ratio') {
             title = data.name || label || "Country";
             content = (
                 <>
                     <p className="text-white font-bold">{`Authors per Paper: ${data.ratio}`}</p>
                     <p className="text-gray-400 text-xs mt-1">{`Papers: ${data.papers?.toLocaleString()}`}</p>
                     <p className="text-gray-400 text-xs mt-1">{`Authors: ${data.authors?.toLocaleString()}`}</p>
                 </>
             );
         }
         else {
             title = label ? String(label) : (data?.name || "Details");
             content = <p className="text-white font-bold">{`${payloadItem.name || dataKey}: ${payloadItem.value?.toLocaleString()}`}</p>;
         }

        return (
            <div className="bg-gray-900 border border-gray-700 p-3 rounded-lg shadow-xl opacity-95">
                <p className="text-gray-300 font-medium mb-1">{title}</p>
                {content}
            </div>
        );
    }
    return null;
};

// ## Pie Chart Active Shape Renderer ## (Unchanged)
const renderActiveShape = (props: ActiveShapeProps) => {
    const RADIAN = Math.PI / 180;
    const {
        cx = 0, cy = 0, midAngle = 0, innerRadius = 0, outerRadius = 0, startAngle = 0, endAngle = 0,
        fill = COLORS.primary, payload, percent = 0, value = 0, name = ''
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

    return (
        <g>
            <text x={cx} y={cy} dy={8} textAnchor="middle" fill={fill || COLORS.text} fontSize="12" fontWeight="bold">
                {payload?.name || name}
            </text>
            <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius} startAngle={startAngle} endAngle={endAngle} fill={fill} />
            <Sector cx={cx} cy={cy} startAngle={startAngle} endAngle={endAngle} innerRadius={outerRadius + 6} outerRadius={outerRadius + 10} fill={fill} />
            <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
            <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill={COLORS.text} fontSize="11">
                {`${value?.toLocaleString()}`}
            </text>
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} dy={18} textAnchor={textAnchor} fill={COLORS.textSecondary} fontSize="10">
                {`(${(percent * 100).toFixed(1)}%)`}
            </text>
        </g>
    );
};

// ## InterpretationPanel Component ## (Unchanged)
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
        <div className="mt-4 bg-gray-700 rounded-lg border border-gray-600 overflow-hidden transition-all duration-300">
            <div
                className="p-3 flex items-center justify-between cursor-pointer bg-gray-700 hover:bg-gray-600 transition-colors"
                onClick={toggleExpansion}
                role="button"
                aria-expanded={isExpanded}
                aria-controls={contentId}
            >
                <div className="flex items-center">
                    <FaLightbulb className="text-amber-400 mr-2 flex-shrink-0" />
                    <h4 className="text-white font-medium">{title || 'Interpretation'}</h4>
                </div>
                <div>{isExpanded ? <FaChevronUp className="text-gray-400" /> : <FaChevronDown className="text-gray-400" />}</div>
            </div>
            {isExpanded && (
                <div id={contentId} className="p-4 bg-gray-800 border-t border-gray-600">
                    <div className="text-gray-300 text-sm leading-relaxed mb-3">
                        {insights.map((insight, idx) => <p key={idx} className="mb-2">{insight}</p>)}
                    </div>
                    {legend && (
                        <div className="mt-3 pt-3 border-t border-gray-600">
                            <p className="text-amber-400 text-xs font-medium mb-1 flex items-center"><FaInfoCircle className="mr-1.5" /> LEGEND:</p>
                            <p className="text-gray-400 text-xs">{legend}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};


// ## InstitutionCard Component ## (Unchanged)
interface InstitutionCardProps {
    institution: InstitutionData;
    index: number;
}

const InstitutionCard: React.FC<InstitutionCardProps> = ({ institution, index }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const toggleExpansion = useCallback(() => setIsExpanded(prev => !prev), []);
    const animationDelay = `${index * 0.05}s`;
    const detailsId = `institution-details-${institution.institute.replace(/\s+/g, '-')}-${index}`; // More unique ID

    return (
        <div
            className="bg-gray-800 rounded-lg shadow-md overflow-hidden mb-4 border border-gray-700 hover:border-indigo-500 transition-all duration-300 animate-fade-in"
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
                    <h3 className="text-white font-medium truncate" title={institution.institute}>{institution.institute}</h3>
                    <div className="flex items-center flex-wrap text-sm text-gray-400 mt-1 space-x-4">
                        <span className="flex items-center whitespace-nowrap"><FaFileAlt className="mr-1.5 text-indigo-400 flex-shrink-0" />{institution.unique_paper_count} {institution.unique_paper_count === 1 ? 'Paper' : 'Papers'}</span>
                        <span className="flex items-center whitespace-nowrap"><FaUsers className="mr-1.5 text-pink-400 flex-shrink-0" />{institution.author_count} {institution.author_count === 1 ? 'Author' : 'Authors'}</span>
                        {institution.spotlights > 0 && (<span className="flex items-center whitespace-nowrap"><FaStar className="mr-1.5 text-yellow-400 flex-shrink-0" />{institution.spotlights} {institution.spotlights === 1 ? 'Spotlight' : 'Spotlights'}</span>)}
                        {institution.orals > 0 && (<span className="flex items-center whitespace-nowrap"><FaTrophy className="mr-1.5 text-emerald-400 flex-shrink-0" />{institution.orals} {institution.orals === 1 ? 'Oral' : 'Orals'}</span>)}
                        <span className="flex items-center whitespace-nowrap capitalize">
                            {institution.type === 'academic' ? <FaGraduationCap className="mr-1.5 text-blue-400 flex-shrink-0" /> : <FaBuilding className="mr-1.5 text-pink-400 flex-shrink-0" />} {institution.type}
                         </span>
                    </div>
                </div>
                <div className={`transform transition-transform duration-300 flex-shrink-0 ${isExpanded ? 'rotate-180' : ''}`}><FaChevronDown className="w-5 h-5 text-gray-400" /></div>
            </div>
            {isExpanded && (
                <div id={detailsId} className="px-4 pb-4 pt-2 border-t border-gray-700">
                    <p className="text-gray-300 text-sm mb-3 font-medium">Published Papers ({institution.unique_paper_count}):</p>
                    {institution.papers && institution.papers.length > 0 ? (
                        <ul className="space-y-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                            {institution.papers.map((paper, idx) => (
                                <li key={`${paper.id}-${idx}`} className="text-gray-400 text-sm bg-gray-900 p-3 rounded-md shadow-sm">
                                    <a href={`https://openreview.net/forum?id=${paper.id}`} target="_blank" rel="noopener noreferrer" className="hover:text-indigo-300 transition-colors block break-words" title={paper.title}>
                                        {paper.title} <span className="text-xs text-gray-500 ml-1">(ID: {paper.id})</span>
                                    </a>
                                    {paper.isSpotlight && (<span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-900 text-yellow-300"><FaStar className="mr-1" size={10} />Spotlight</span>)}
                                    {paper.isOral && (<span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-900 text-emerald-300"><FaTrophy className="mr-1" size={10} />Oral</span>)}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-gray-500 text-sm italic">No specific paper details available.</p>
                    )}
                </div>
            )}
        </div>
    );
};

// ## DataTable Component ## (Unchanged)
interface DataTableProps {
    data: Record<string, string | number | boolean | undefined | null>[];
    title: string;
    filename: string;
}

const DataTable: React.FC<DataTableProps> = ({ data, title, filename }) => {
    if (!data || data.length === 0) {
        return <div className="text-gray-500 p-4">No data available for the table.</div>;
    }
    const headers = data.length > 0 ? Object.keys(data[0]) : [];
    const handleExport = useCallback(() => exportToCSV(data, filename), [data, filename]);

    return (
        <div className="overflow-x-auto">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                <h4 className="text-white font-medium text-lg">{title}</h4>
                <button onClick={handleExport} className="flex items-center bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3 py-1.5 rounded transition-colors shadow-sm" aria-label={`Export ${title} data to CSV`}>
                    <FaDownload className="mr-1.5" size={10} /> Export CSV
                </button>
            </div>
            <div className="border border-gray-700 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-700">
                    <thead className="bg-gray-700">
                        <tr>{headers.map((header) => (<th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider whitespace-nowrap">{header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>))}</tr>
                    </thead>
                    <tbody className="bg-gray-800 divide-y divide-gray-700">
                        {data.map((row, rowIndex) => (
                            <tr key={rowIndex} className={`${row.highlight ? 'bg-amber-900 bg-opacity-20' : ''} hover:bg-gray-700/50 transition-colors`}>
                                {headers.map((header, colIndex) => (
                                    <td key={`${rowIndex}-${colIndex}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
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

// ## ViewToggle Component ## (Unchanged)
interface ViewToggleProps {
    activeView: ViewMode;
    setActiveView: (view: ViewMode) => void;
}

const ViewToggle: React.FC<ViewToggleProps> = ({ activeView, setActiveView }) => (
    <div className="flex items-center space-x-1 bg-gray-900 p-1 rounded-lg shadow-inner">
        <button onClick={() => setActiveView('chart')} className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${activeView === 'chart' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-transparent text-gray-400 hover:bg-gray-700 hover:text-gray-200'}`} aria-pressed={activeView === 'chart'}>
            <FaChartBar size={12} /><span>Chart</span>
        </button>
        <button onClick={() => setActiveView('table')} className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${activeView === 'table' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-transparent text-gray-400 hover:bg-gray-700 hover:text-gray-200'}`} aria-pressed={activeView === 'table'}>
            <FaTable size={12} /><span>Table</span>
        </button>
    </div>
);


// --- Main Dashboard Component ---

// Define props interface to accept the dashboard data
interface DashboardDataProps {
    dashboardData: DashboardData;
}

const ICLRDashboard: React.FC<DashboardDataProps> = ({ dashboardData }) => {
    // --- State (UI state remains) ---
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

    // --- Data is now passed via props: `dashboardData` ---
    const { conferenceInfo, globalStats, indiaFocus, interpretations } = dashboardData;

    // --- Memoized Data Processing (Uses data from props) ---

    const sortedCountries: CountryData[] = useMemo(() => {
        const countryMap = new Map<string, CountryData>();
        globalStats.countries.forEach(rawCountry => {
            const countryCode = rawCountry.affiliation_country;
            const countryName = CountryMap[countryCode] || countryCode; // Maps GB/UK to "United Kingdom"
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
                    affiliation_country: countryCode, // Keep first encountered code for consistency (e.g., GB over UK if both map)
                    country_name: countryName,
                    paper_count: paperCount,
                    author_count: authorCount,
                    spotlights: spotlights,
                    orals: orals,
                    rank: 0, // To be assigned
                    fill: countryCode === 'US' ? COLORS.usColor :
                          countryCode === 'CN' ? COLORS.cnColor :
                          countryCode === 'IN' ? COLORS.inColor :
                          COLORS.primary,
                    opacity: (countryCode === 'US' || countryCode === 'CN' || countryCode === 'IN') ? 1 : 0.8
                });
            }
        });

        const sorted = Array.from(countryMap.values())
                           .sort((a, b) => b.paper_count - a.paper_count || b.author_count - a.author_count);
        sorted.forEach((country, index) => { country.rank = index + 1; });
        return sorted;
    }, [globalStats.countries]); // Depends on the raw country data from props

    const topCountriesByPaper = useMemo(() => sortedCountries.slice(0, 15), [sortedCountries]);
    const usData = useMemo(() => sortedCountries.find(c => c.country_name === 'United States'), [sortedCountries]);
    const cnData = useMemo(() => sortedCountries.find(c => c.country_name === 'China'), [sortedCountries]);
    const indiaGlobalStats = useMemo(() => sortedCountries.find(c => c.country_name === 'India'), [sortedCountries]);

    // Combined India data (merging specific details with global stats)
    const processedIndiaData: ProcessedIndiaData | null = useMemo(() => {
        if (!indiaGlobalStats) return null;
        // Type assertion needed as we are adding properties
        const data = { ...indiaFocus } as ProcessedIndiaData;
        data.rank = indiaGlobalStats.rank;
        data.paper_count = indiaGlobalStats.paper_count;
        data.author_count = indiaGlobalStats.author_count; // Use consistent global count
        data.spotlights = indiaGlobalStats.spotlights; // Use consistent global count
        data.orals = indiaGlobalStats.orals; // Use consistent global count
        return data;
    }, [indiaFocus, indiaGlobalStats]); // Depends on indiaFocus from props and derived global stats

    const usVsChinaVsRest: NameValueData[] = useMemo(() => {
        if (!usData || !cnData) return [];
        const usCount = usData.paper_count;
        const cnCount = cnData.paper_count;
        const totalCount = conferenceInfo.totalAcceptedPapers || sortedCountries.reduce((sum, country) => sum + country.paper_count, 0);
        const restCount = Math.max(0, totalCount - usCount - cnCount); // Ensure non-negative
        const totalForPercent = usCount + cnCount + restCount || 1; // Avoid division by zero

        return [
            { name: 'US + China', value: usCount + cnCount, fill: COLORS.usColor, percent: (usCount + cnCount) / totalForPercent },
            { name: 'Rest of World', value: restCount, fill: COLORS.secondary, percent: restCount / totalForPercent }
        ];
    }, [usData, cnData, sortedCountries, conferenceInfo.totalAcceptedPapers]);

    const apacCountries: NameValueData[] = useMemo(() => {
        const filtered = sortedCountries
            .filter(country => APAC_COUNTRIES.includes(country.affiliation_country))
            .sort((a, b) => b.paper_count - a.paper_count);
        const totalApacPapers = filtered.reduce((sum, c) => sum + c.paper_count, 0) || 1; // Avoid division by zero

        return filtered.map(country => ({
            name: country.country_name,
            value: country.paper_count,
            fill: country.country_name === 'China' ? COLORS.cnColor :
                  country.country_name === 'India' ? COLORS.inColor : COLORS.secondary,
            percent: country.paper_count / totalApacPapers
        }));
    }, [sortedCountries]);

    const authorshipPieData = useMemo(() => {
        if (!processedIndiaData || !processedIndiaData.at_least_one_indian_author) return null;
        const totalWithIndianAuthor = processedIndiaData.at_least_one_indian_author.count || 1; // Avoid division by zero
        const majority = processedIndiaData.majority_indian_authors.count;
        const minority = totalWithIndianAuthor - majority;
        const firstAuthor = processedIndiaData.first_indian_author.count;
        const nonFirstAuthor = totalWithIndianAuthor - firstAuthor;

        return {
            authorship: [
                { name: 'Majority Indian', value: majority, fill: COLORS.highlight, percent: majority / totalWithIndianAuthor },
                { name: 'Minority Indian', value: minority, fill: COLORS.primary, percent: minority / totalWithIndianAuthor }
            ],
            firstAuthor: [
                { name: 'First Indian Author', value: firstAuthor, fill: COLORS.accent, percent: firstAuthor / totalWithIndianAuthor },
                { name: 'Non-First Indian Author', value: nonFirstAuthor, fill: COLORS.primary, percent: nonFirstAuthor / totalWithIndianAuthor }
            ]
        };
    }, [processedIndiaData]);

    const institutionTypePieData: NameValueData[] = useMemo(() => {
        if (!processedIndiaData || !processedIndiaData.institution_types) return [];
        const academic = processedIndiaData.institution_types.academic || 0;
        const corporate = processedIndiaData.institution_types.corporate || 0;
        const total = academic + corporate || 1; // Avoid division by zero
        return [
            { name: 'Academic', value: academic, fill: COLORS.academic, percent: academic / total },
            { name: 'Corporate', value: corporate, fill: COLORS.corporate, percent: corporate / total }
        ];
    }, [processedIndiaData]);

    const filteredInstitutions: InstitutionData[] = useMemo(() => {
        if (!processedIndiaData || !processedIndiaData.institutions) return [];
        return processedIndiaData.institutions
            .filter(inst => inst.institute.toLowerCase().includes(institutionFilter.toLowerCase()))
            .sort((a, b) => b.unique_paper_count - a.unique_paper_count || b.spotlights - a.spotlights || b.orals - a.orals || b.author_count - a.author_count);
    }, [processedIndiaData, institutionFilter]); // Depends on processed India data and filter state

    const topIndianInstitution = useMemo(() => filteredInstitutions[0] || null, [filteredInstitutions]);

    const institutionChartData: InstitutionData[] = useMemo(() => {
        return filteredInstitutions.slice(0, 8).map(institution => ({
            ...institution,
            fill: institution.type === 'academic' ? COLORS.academic : COLORS.corporate
        }));
    }, [filteredInstitutions]);

    const institutionContributionPieData: NameValueData[] = useMemo(() => {
        if (!filteredInstitutions.length) return [];
        const academicPapers = filteredInstitutions.filter(inst => inst.type === 'academic').reduce((sum, inst) => sum + inst.unique_paper_count, 0);
        const corporatePapers = filteredInstitutions.filter(inst => inst.type === 'corporate').reduce((sum, inst) => sum + inst.unique_paper_count, 0);
        const total = academicPapers + corporatePapers || 1; // Avoid division by zero
        return [
            { name: 'Academic', value: academicPapers, fill: COLORS.academic, percent: academicPapers / total },
            { name: 'Corporate', value: corporatePapers, fill: COLORS.corporate, percent: corporatePapers / total }
        ];
    }, [filteredInstitutions]);


    // --- Event Handlers (Unchanged) ---
    const handleTabChange = useCallback((index: number) => setActiveTabIndex(index), []);
    const handleFilterChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => setInstitutionFilter(event.target.value), []);
    const handlePieEnter = useCallback((_: any, index: number) => setActivePieIndex(index), []);
    const handleSetViewMode = useCallback((viewKey: string, mode: ViewMode) => setViewModes(prev => ({ ...prev, [viewKey]: mode })), []);

    // --- Render Logic ---

    // Basic check if essential processed data is available
    if (!processedIndiaData || !usData || !cnData) {
        // This case might indicate an issue with data processing or incomplete input data.
        // Render a simple message or a more specific error state.
         return (
             <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
                 <div className="bg-yellow-900 border border-yellow-700 text-yellow-100 px-4 py-3 rounded-lg shadow-lg text-center">
                     <h2 className="font-bold text-lg mb-2">Data Processing Issue</h2>
                     <p>Could not process the required dashboard data (e.g., US, China, or India stats missing/invalid).</p>
                 </div>
             </div>
         );
    }

    const totalPapers = conferenceInfo.totalAcceptedPapers;

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 p-4 sm:p-6 font-sans">
            {/* Header */}
            <header className="mb-6 md:mb-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center">
                            <FaTrophy className="mr-2 text-indigo-400" /> {conferenceInfo.name} {conferenceInfo.year} Research Analysis
                        </h1>
                        <p className="text-gray-400 mt-1 text-sm sm:text-base">Global Contributions & India Focus</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-3 text-sm text-gray-300 border border-gray-700 shadow-sm whitespace-nowrap">
                        Total Accepted Papers: <span className="font-bold text-white">{totalPapers.toLocaleString()}</span>
                    </div>
                </div>
                {/* Tabs */}
                 <div className="mt-6 border-b border-gray-700">
                     <nav className="-mb-px flex space-x-1 sm:space-x-4 overflow-x-auto pb-0" aria-label="Tabs">
                         {TABS.map((tab, index) => (
                             <button
                                 key={tab}
                                 onClick={() => handleTabChange(index)}
                                 className={`whitespace-nowrap py-3 px-3 sm:px-4 border-b-2 font-medium text-sm sm:text-base focus:outline-none transition-colors duration-200 ${
                                     activeTabIndex === index
                                         ? 'border-indigo-500 text-indigo-400'
                                         : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-500'
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
                        <h2 className="text-xl font-semibold text-white mb-4">India at {conferenceInfo.name} {conferenceInfo.year}: Overview</h2>
                         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
                             <StatCard
                                 title="India Papers"
                                 value={processedIndiaData.paper_count?.toLocaleString() ?? 'N/A'}
                                 icon={<FaFileAlt />}
                                 color="amber" // Use string directly
                                 subtitle={`${((processedIndiaData.paper_count ?? 0) / totalPapers * 100).toFixed(1)}% of total`}
                             />
                             <StatCard
                                 title="India's Global Rank"
                                 value={`#${processedIndiaData.rank ?? 'N/A'}`}
                                 icon={<FaGlobeAsia />}
                                 color="blue"
                                 subtitle={`By papers | ${processedIndiaData.author_count?.toLocaleString() ?? 'N/A'} authors`}
                             />
                             <StatCard
                                 title="Spotlights & Orals"
                                 value={(processedIndiaData.spotlights ?? 0) + (processedIndiaData.orals ?? 0)}
                                 icon={<FaStar />}
                                 color="yellow"
                                 subtitle={`${processedIndiaData.spotlights ?? 0} spotlights, ${processedIndiaData.orals ?? 0} orals`}
                             />
                             <StatCard
                                 title="Top Indian Institution"
                                 value={topIndianInstitution?.institute || 'N/A'}
                                 icon={<FaUniversity />}
                                 color="emerald"
                                 subtitle={`${topIndianInstitution?.unique_paper_count || 0} papers | ${topIndianInstitution?.type || 'N/A'}`}
                             />
                         </div>

                        <InterpretationPanel
                            title={interpretations.overview.title}
                            insights={interpretations.overview.insights}
                            legend={interpretations.overview.legend}
                        />

                         {/* Global Leaderboard Chart */}
                         <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 shadow-lg">
                             <h2 className="text-xl font-bold mb-1 text-white">Global Leaderboard (Top 10)</h2>
                             <p className="text-sm text-gray-400 mb-6">Countries ranked by accepted paper count at {conferenceInfo.name} {conferenceInfo.year}.</p>
                             <div className="h-96">
                                 <ResponsiveContainer width="100%" height="100%">
                                     <BarChart data={topCountriesByPaper.slice(0, 10)} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                                         <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} horizontal={false} />
                                         <XAxis type="number" stroke={COLORS.textSecondary} axisLine={false} tickLine={false} />
                                         <YAxis type="category" dataKey="country_name" stroke={COLORS.textSecondary} width={100} tick={{ fontSize: 11, fill: COLORS.textSecondary }} interval={0} axisLine={false} tickLine={false} />
                                         <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(100, 116, 139, 0.1)' }} />
                                         <Bar dataKey="paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={20}>
                                             {topCountriesByPaper.slice(0, 10).map((entry, index) => (
                                                 <Cell key={`cell-paper-${index}`} fill={entry.fill} fillOpacity={entry.opacity} />
                                             ))}
                                         </Bar>
                                     </BarChart>
                                 </ResponsiveContainer>
                             </div>
                         </div>

                        {/* Top Indian Institutions Preview */}
                         <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
                                <h2 className="text-xl font-bold text-white">Top Indian Institutions Preview</h2>
                                <button className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center font-medium" onClick={() => handleTabChange(3)}>
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
                                <p className="text-gray-500 text-center py-4">No institutions found.</p>
                            )}
                         </div>
                    </div>
                )}

                {/* --- Global Stats Tab --- */}
                {activeTabIndex === 1 && (
                     <div className="space-y-6 md:space-y-8 animate-fade-in">
                         {/* US + China vs Rest of World */}
                         <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 shadow-lg">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                                <div>
                                    <h2 className="text-xl font-bold text-white">Global Distribution: US+China vs. Rest</h2>
                                    <p className="text-sm text-gray-400">Paper share showing the concentration of research output.</p>
                                </div>
                                <ViewToggle activeView={viewModes.global} setActiveView={(mode) => handleSetViewMode('global', mode)} />
                            </div>
                             {viewModes.global === 'chart' ? (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
                                    <div className="h-80 bg-gray-900/30 rounded-lg p-4">
                                        <h3 className="text-center text-sm font-medium text-gray-300 mb-2">Absolute Paper Count</h3>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={usVsChinaVsRest} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                                                <XAxis dataKey="name" stroke={COLORS.textSecondary} fontSize={11} />
                                                <YAxis stroke={COLORS.textSecondary} fontSize={11} />
                                                <Tooltip content={<CustomTooltip />} />
                                                <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                                    {usVsChinaVsRest.map((entry, index) => <Cell key={`cell-global-bar-${index}`} fill={entry.fill} />)}
                                                </Bar>
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div className="h-80 bg-gray-900/30 rounded-lg p-4">
                                        <h3 className="text-center text-sm font-medium text-gray-300 mb-2">Percentage Share</h3>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie activeIndex={activePieIndex} activeShape={renderActiveShape} data={usVsChinaVsRest} cx="50%" cy="50%" innerRadius={60} outerRadius={85} fill={COLORS.primary} dataKey="value" onMouseEnter={handlePieEnter}>
                                                    {usVsChinaVsRest.map((entry, index) => <Cell key={`cell-global-pie-${index}`} fill={entry.fill} stroke={COLORS.card} />)}
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
                         <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 shadow-lg">
                             <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                                 <div>
                                     <h2 className="text-xl font-bold text-white">APAC Contributions</h2>
                                     <p className="text-sm text-gray-400">Paper distribution within key Asia-Pacific countries.</p>
                                 </div>
                                 <ViewToggle activeView={viewModes.apac} setActiveView={(mode) => handleSetViewMode('apac', mode)} />
                             </div>
                             {viewModes.apac === 'chart' ? (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
                                    <div className="h-96 bg-gray-900/30 rounded-lg p-4">
                                        <h3 className="text-center text-sm font-medium text-gray-300 mb-2">Papers by APAC Country</h3>
                                        <ResponsiveContainer width="100%" height="100%">
                                             <BarChart data={apacCountries} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                                                 <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} horizontal={false} />
                                                 <XAxis type="number" stroke={COLORS.textSecondary} axisLine={false} tickLine={false} />
                                                 <YAxis type="category" dataKey="name" stroke={COLORS.textSecondary} width={100} tick={{ fontSize: 11, fill: COLORS.textSecondary }} interval={0} axisLine={false} tickLine={false} />
                                                 <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(100, 116, 139, 0.1)' }} />
                                                 <Bar dataKey="value" name="Papers" radius={[0, 4, 4, 0]} barSize={18}>
                                                     {apacCountries.map((entry, index) => <Cell key={`cell-apac-bar-${index}`} fill={entry.fill} />)}
                                                 </Bar>
                                             </BarChart>
                                         </ResponsiveContainer>
                                    </div>
                                    <div className="h-96 bg-gray-900/30 rounded-lg p-4">
                                        <h3 className="text-center text-sm font-medium text-gray-300 mb-2">APAC Contribution Share</h3>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie activeIndex={activePieIndex} activeShape={renderActiveShape} data={apacCountries} cx="50%" cy="50%" innerRadius={70} outerRadius={100} fill={COLORS.primary} dataKey="value" onMouseEnter={handlePieEnter}>
                                                    {apacCountries.map((entry, index) => <Cell key={`cell-apac-pie-${index}`} fill={entry.fill} stroke={COLORS.card} />)}
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
                         <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 shadow-lg">
                             <h2 className="text-xl font-bold mb-4 text-white">Complete Country Contributions</h2>
                             <DataTable data={sortedCountries.map(country => ({ Rank: country.rank, Country: country.country_name, Papers: country.paper_count.toLocaleString(), 'Percentage': `${((country.paper_count / totalPapers) * 100).toFixed(2)}%`, Authors: country.author_count.toLocaleString(), Spotlights: country.spotlights, Orals: country.orals, highlight: country.country_name === 'India' }))} title="All Countries Ranked by Paper Count" filename="all_countries_ranked_iclr_2025" />
                         </div>
                     </div>
                )}

                {/* --- India Focus Tab --- */}
                 {activeTabIndex === 2 && (
                    <div className="space-y-6 md:space-y-8 animate-fade-in">
                        {/* Authorship Patterns */}
                        <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 shadow-lg">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                                <div>
                                    <h2 className="text-xl font-bold text-white">Indian Authorship Patterns</h2>
                                    <p className="text-sm text-gray-400">Analysis of authorship roles in papers with Indian affiliation.</p>
                                </div>
                                <ViewToggle activeView={viewModes.authorship} setActiveView={(mode) => handleSetViewMode('authorship', mode)} />
                            </div>

                             {viewModes.authorship === 'chart' && authorshipPieData ? (
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                     {/* Chart Set 1: Majority/Minority */}
                                     <div className="space-y-4 bg-gray-900/30 rounded-lg p-4">
                                         <h3 className="text-center text-base font-semibold text-gray-100">Authorship Distribution</h3>
                                         <div className="h-64">
                                             <ResponsiveContainer width="100%" height="100%">
                                                 <BarChart data={authorshipPieData.authorship} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                                     <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                                                     <XAxis dataKey="name" stroke={COLORS.textSecondary} fontSize={10} interval={0}/>
                                                     <YAxis stroke={COLORS.textSecondary} fontSize={10} />
                                                     <Tooltip content={<CustomTooltip />} />
                                                     <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                                         {authorshipPieData.authorship.map((entry, index) => <Cell key={`cell-author-bar-${index}`} fill={entry.fill} />)}
                                                     </Bar>
                                                 </BarChart>
                                             </ResponsiveContainer>
                                         </div>
                                         <div className="h-64">
                                             <ResponsiveContainer width="100%" height="100%">
                                                 <PieChart>
                                                     <Pie data={authorshipPieData.authorship} cx="50%" cy="50%" outerRadius={70} fill={COLORS.primary} dataKey="value" labelLine={false} >
                                                         {authorshipPieData.authorship.map((entry, index) => <Cell key={`cell-author-pie-${index}`} fill={entry.fill} stroke={COLORS.card}/>)}
                                                     </Pie>
                                                     <Tooltip content={<CustomTooltip />} />
                                                     <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }}/>
                                                 </PieChart>
                                             </ResponsiveContainer>
                                         </div>
                                     </div>
                                     {/* Chart Set 2: First Author */}
                                     <div className="space-y-4 bg-gray-900/30 rounded-lg p-4">
                                         <h3 className="text-center text-base font-semibold text-gray-100">First Author Distribution</h3>
                                         <div className="h-64">
                                              <ResponsiveContainer width="100%" height="100%">
                                                  <BarChart data={authorshipPieData.firstAuthor} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                                      <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                                                      <XAxis dataKey="name" stroke={COLORS.textSecondary} fontSize={10} interval={0}/>
                                                      <YAxis stroke={COLORS.textSecondary} fontSize={10} />
                                                      <Tooltip content={<CustomTooltip />} />
                                                      <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                                          {authorshipPieData.firstAuthor.map((entry, index) => <Cell key={`cell-first-bar-${index}`} fill={entry.fill} />)}
                                                      </Bar>
                                                  </BarChart>
                                              </ResponsiveContainer>
                                         </div>
                                         <div className="h-64">
                                             <ResponsiveContainer width="100%" height="100%">
                                                 <PieChart>
                                                     <Pie data={authorshipPieData.firstAuthor} cx="50%" cy="50%" outerRadius={70} fill={COLORS.primary} dataKey="value" labelLine={false}>
                                                         {authorshipPieData.firstAuthor.map((entry, index) => <Cell key={`cell-first-pie-${index}`} fill={entry.fill} stroke={COLORS.card} />)}
                                                     </Pie>
                                                     <Tooltip content={<CustomTooltip />} />
                                                     <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }}/>
                                                 </PieChart>
                                             </ResponsiveContainer>
                                         </div>
                                     </div>
                                     {/* Chart Set 3: Institution Type */}
                                     <div className="space-y-4 bg-gray-900/30 rounded-lg p-4">
                                         <h3 className="text-center text-base font-semibold text-gray-100">Institution Type (Papers)</h3>
                                          <div className="h-64">
                                              <ResponsiveContainer width="100%" height="100%">
                                                  <BarChart data={institutionTypePieData} margin={{ top: 20, right: 20, left: 0, bottom: 5 }}>
                                                      <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                                                      <XAxis dataKey="name" stroke={COLORS.textSecondary} fontSize={10} />
                                                      <YAxis stroke={COLORS.textSecondary} fontSize={10} />
                                                      <Tooltip content={<CustomTooltip />} />
                                                      <Bar dataKey="value" name="Papers" radius={[4, 4, 0, 0]}>
                                                          {institutionTypePieData.map((entry, index) => <Cell key={`cell-instype-bar-${index}`} fill={entry.fill} />)}
                                                      </Bar>
                                                  </BarChart>
                                              </ResponsiveContainer>
                                          </div>
                                          <div className="h-64">
                                              <ResponsiveContainer width="100%" height="100%">
                                                  <PieChart>
                                                      <Pie data={institutionTypePieData} cx="50%" cy="50%" outerRadius={70} fill={COLORS.primary} dataKey="value" labelLine={false}>
                                                          {institutionTypePieData.map((entry, index) => <Cell key={`cell-instype-pie-${index}`} fill={entry.fill} stroke={COLORS.card} />)}
                                                      </Pie>
                                                      <Tooltip content={<CustomTooltip />} />
                                                      <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }}/>
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
                         <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 shadow-lg">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                                <div>
                                    <h2 className="text-xl font-bold text-white">India vs. US & China: Comparative Metrics</h2>
                                    <p className="text-sm text-gray-400">Comparing key research output indicators.</p>
                                </div>
                                <ViewToggle activeView={viewModes.comparison} setActiveView={(mode) => handleSetViewMode('comparison', mode)} />
                            </div>
                             {viewModes.comparison === 'chart' ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Chart 1: Paper Count */}
                                    <div className="bg-gray-900/30 p-4 rounded-lg">
                                        <h4 className="text-white font-medium mb-3 text-center text-base">Paper Count Comparison</h4>
                                        <div className="h-80">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={[ { name: 'US', Papers: usData.paper_count, fill: COLORS.usColor }, { name: 'China', Papers: cnData.paper_count, fill: COLORS.cnColor }, { name: 'India', Papers: processedIndiaData.paper_count, fill: COLORS.inColor } ]} margin={{ top: 5, right: 10, left: 10, bottom: 5 }} >
                                                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false}/>
                                                    <XAxis dataKey="name" stroke={COLORS.textSecondary} fontSize={11}/>
                                                    <YAxis stroke={COLORS.textSecondary} fontSize={11} />
                                                    <Tooltip content={<CustomTooltip />}/>
                                                    <Bar dataKey="Papers" name="Papers" radius={[4, 4, 0, 0]}>
                                                        {[COLORS.usColor, COLORS.cnColor, COLORS.inColor].map((color, index) => <Cell key={`cell-comp-paper-${index}`} fill={color} /> )}
                                                    </Bar>
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                    {/* Chart 2: Spotlights & Orals */}
                                    <div className="bg-gray-900/30 p-4 rounded-lg">
                                         <h4 className="text-white font-medium mb-3 text-center text-base">Spotlight & Oral Count</h4>
                                         <div className="h-80">
                                             <ResponsiveContainer width="100%" height="100%">
                                                 <BarChart data={[ { name: 'US', spotlights: usData.spotlights, orals: usData.orals, total: usData.spotlights + usData.orals, spotlight_percent: ((usData.spotlights / usData.paper_count) * 100).toFixed(1), oral_percent: ((usData.orals / usData.paper_count) * 100).toFixed(1) }, { name: 'China', spotlights: cnData.spotlights, orals: cnData.orals, total: cnData.spotlights + cnData.orals, spotlight_percent: ((cnData.spotlights / cnData.paper_count) * 100).toFixed(1), oral_percent: ((cnData.orals / cnData.paper_count) * 100).toFixed(1) }, { name: 'India', spotlights: processedIndiaData.spotlights, orals: processedIndiaData.orals, total: (processedIndiaData.spotlights ?? 0) + (processedIndiaData.orals ?? 0), spotlight_percent: (((processedIndiaData.spotlights ?? 0) / (processedIndiaData.paper_count ?? 1)) * 100).toFixed(1), oral_percent: (((processedIndiaData.orals ?? 0) / (processedIndiaData.paper_count ?? 1)) * 100).toFixed(1) } ]} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                                                     <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false}/>
                                                     <XAxis dataKey="name" stroke={COLORS.textSecondary} fontSize={11} />
                                                     <YAxis stroke={COLORS.textSecondary} fontSize={11}/>
                                                     <Tooltip content={<CustomTooltip />} />
                                                     <Bar dataKey="total" name="Total Impact" fill="transparent" /> {/* Invisible bar for tooltip trigger */}
                                                     <Bar dataKey="spotlights" name="Spotlights" stackId="a" fill={COLORS.warning} radius={[4, 4, 0, 0]}/>
                                                     <Bar dataKey="orals" name="Orals" stackId="a" fill={COLORS.accent} radius={[4, 4, 0, 0]}/>
                                                     <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }}/>
                                                 </BarChart>
                                             </ResponsiveContainer>
                                         </div>
                                    </div>
                                     {/* Chart 3: Authors per Paper */}
                                     <div className="bg-gray-900/30 p-4 rounded-lg md:col-span-2">
                                         <h4 className="text-white font-medium mb-3 text-center text-base">Average Authors per Paper</h4>
                                         <div className="h-64">
                                             <ResponsiveContainer width="100%" height="100%">
                                                  <BarChart data={[ { name: 'US', ratio: parseFloat((usData.author_count / usData.paper_count).toFixed(2)), papers: usData.paper_count, authors: usData.author_count, fill: COLORS.usColor }, { name: 'China', ratio: parseFloat((cnData.author_count / cnData.paper_count).toFixed(2)), papers: cnData.paper_count, authors: cnData.author_count, fill: COLORS.cnColor }, { name: 'India', ratio: parseFloat(((processedIndiaData.author_count ?? 0) / (processedIndiaData.paper_count ?? 1)).toFixed(2)), papers: processedIndiaData.paper_count ?? 0, authors: processedIndiaData.author_count ?? 0, fill: COLORS.inColor } ]} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                                                      <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false}/>
                                                      <XAxis dataKey="name" stroke={COLORS.textSecondary} fontSize={11}/>
                                                      <YAxis stroke={COLORS.textSecondary} fontSize={11} domain={[0, 'dataMax + 0.5']}/>
                                                      <Tooltip content={<CustomTooltip />}/>
                                                      <Bar dataKey="ratio" name="Authors per Paper" barSize={40} radius={[4, 4, 0, 0]}>
                                                          {[COLORS.usColor, COLORS.cnColor, COLORS.inColor].map((color, index) => <Cell key={`cell-comp-ratio-${index}`} fill={color} />)}
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
                        <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 shadow-lg">
                            <h2 className="text-xl font-bold mb-4 text-white">Potential Research Focus Areas for India</h2>
                            <div className="space-y-3">
                                <div className="bg-gray-700 p-4 rounded-lg shadow-sm flex items-start gap-3"><FaLightbulb className="text-blue-400 mt-1 flex-shrink-0" size={18}/><div><h3 className="font-medium text-white">LLMs & NLP</h3><p className="text-gray-300 text-sm mt-1">Contributions observed in evaluation, multilingual understanding, efficiency, and specific applications (e.g., engagement, persuasiveness).</p></div></div>
                                <div className="bg-gray-700 p-4 rounded-lg shadow-sm flex items-start gap-3"><FaLightbulb className="text-emerald-400 mt-1 flex-shrink-0" size={18}/><div><h3 className="font-medium text-white">GNNs & Theory</h3><p className="text-gray-300 text-sm mt-1">Activity seen in graph representations, condensation techniques, and theoretical underpinnings like sampling and sensitivity analysis.</p></div></div>
                                <div className="bg-gray-700 p-4 rounded-lg shadow-sm flex items-start gap-3"><FaLightbulb className="text-amber-400 mt-1 flex-shrink-0" size={18}/><div><h3 className="font-medium text-white">Robustness & Efficiency</h3><p className="text-gray-300 text-sm mt-1">Focus noted on debiasing methods, adversarial robustness, model compression, and designing efficient deep learning models.</p></div></div>
                             </div>
                            <InterpretationPanel title={interpretations.futureOpportunities.title} insights={interpretations.futureOpportunities.insights} legend={interpretations.futureOpportunities.legend} />
                        </div>
                    </div>
                 )}

                {/* --- Institutions Tab --- */}
                 {activeTabIndex === 3 && (
                    <div className="space-y-6 md:space-y-8 animate-fade-in">
                        {/* Header and Search */}
                        <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 shadow-lg">
                            <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                                <h2 className="text-xl font-bold text-white">Indian Research Institutions @ {conferenceInfo.name} {conferenceInfo.year}</h2>
                                <div className="relative w-full md:w-auto">
                                    <label htmlFor="institution-search" className="sr-only">Search Institutions</label>
                                    <input id="institution-search" type="search" placeholder="Search institutions..." className="bg-gray-700 border border-gray-600 rounded-lg py-2 pl-10 pr-4 text-white w-full md:w-72 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm placeholder-gray-400" value={institutionFilter} onChange={handleFilterChange} />
                                    <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none" />
                                </div>
                            </div>
                        </div>

                        {/* Institution Charts / Table */}
                        <div className="bg-gray-800 rounded-xl p-4 sm:p-6 border border-gray-700 mb-6">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                                <div>
                                    <h3 className="text-lg font-bold text-white">Institution Contribution Analysis</h3>
                                    <p className="text-sm text-gray-400">Top institutions by papers and academic/corporate split.</p>
                                </div>
                                <ViewToggle activeView={viewModes.institutions} setActiveView={(mode) => handleSetViewMode('institutions', mode)} />
                            </div>

                            {viewModes.institutions === 'chart' && institutionChartData.length > 0 ? (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
                                    {/* Bar Chart */}
                                    <div className="bg-gray-900/30 rounded-lg p-4">
                                        <h4 className="text-center text-base font-semibold text-gray-100 mb-2">Papers by Institution (Top {institutionChartData.length})</h4>
                                        <div className="h-96">
                                            <ResponsiveContainer width="100%" height="100%">
                                                 <BarChart data={institutionChartData} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
                                                     <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} horizontal={false} />
                                                     <XAxis type="number" stroke={COLORS.textSecondary} axisLine={false} tickLine={false} />
                                                     <YAxis type="category" dataKey="institute" stroke={COLORS.textSecondary} width={120} tick={{ fontSize: 10, fill: COLORS.textSecondary }} interval={0} axisLine={false} tickLine={false} />
                                                     <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(100, 116, 139, 0.1)' }}/>
                                                     <Bar dataKey="unique_paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={18}>
                                                         {institutionChartData.map((entry, index) => <Cell key={`cell-inst-bar-${index}`} fill={entry.fill} />)}
                                                     </Bar>
                                                 </BarChart>
                                             </ResponsiveContainer>
                                        </div>
                                    </div>
                                    {/* Pie Chart */}
                                    <div className="bg-gray-900/30 rounded-lg p-4">
                                        <h4 className="text-center text-base font-semibold text-gray-100 mb-2">Academic vs. Corporate Papers</h4>
                                        <div className="h-80">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <PieChart>
                                                    <Pie activeIndex={activePieIndex} activeShape={renderActiveShape} data={institutionContributionPieData} cx="50%" cy="50%" innerRadius={70} outerRadius={100} fill={COLORS.primary} dataKey="value" onMouseEnter={handlePieEnter}>
                                                        {institutionContributionPieData.map((entry, index) => <Cell key={`cell-inst-pie-${index}`} fill={entry.fill} stroke={COLORS.card} />)}
                                                    </Pie>
                                                    <Tooltip content={<CustomTooltip />} />
                                                    <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} layout="vertical" align="right" verticalAlign="middle" />
                                                </PieChart>
                                            </ResponsiveContainer>
                                        </div>
                                         {/* Summary Cards */}
                                        <div className="mt-4 grid grid-cols-2 gap-3 text-center">
                                             <div className="bg-blue-900/30 p-2 rounded">
                                                 <p className="text-xs text-blue-300">Academic Spots/Orals</p>
                                                 <p className="text-lg font-bold text-white">{filteredInstitutions.filter(i => i.type === 'academic').reduce((sum, i) => sum + i.spotlights + i.orals, 0)}</p>
                                             </div>
                                             <div className="bg-pink-900/30 p-2 rounded">
                                                 <p className="text-xs text-pink-300">Corporate Spots/Orals</p>
                                                 <p className="text-lg font-bold text-white">{filteredInstitutions.filter(i => i.type === 'corporate').reduce((sum, i) => sum + i.spotlights + i.orals, 0)}</p>
                                             </div>
                                         </div>
                                    </div>
                                </div>
                            ) : ( // Table View or No Data
                                institutionChartData.length > 0 ? (
                                    <DataTable data={filteredInstitutions.map(inst => ({ Institution: inst.institute, Type: inst.type || 'Unknown', Papers: inst.unique_paper_count, Authors: inst.author_count, Spotlights: inst.spotlights, Orals: inst.orals, 'Papers_Author': inst.author_count > 0 ? (inst.unique_paper_count / inst.author_count).toFixed(2) : 'N/A', highlight: inst.institute === topIndianInstitution?.institute }))} title="Indian Institution Summary" filename="indian_institutions_summary_iclr_2025" />
                                ) : (
                                    <p className="text-gray-500 text-center py-4">No institutions match the current filter.</p>
                                )
                            )}
                             <InterpretationPanel title={interpretations.institutionAnalysis.title} insights={interpretations.institutionAnalysis.insights} legend={interpretations.institutionAnalysis.legend} />
                        </div>

                        {/* Detailed Institution List (Cards) */}
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-white">Detailed Institution List</h3>
                             {filteredInstitutions.length > 0 && (
                                <button onClick={() => exportToCSV( filteredInstitutions.map(inst => ({ Institution: inst.institute, Type: inst.type || 'Unknown', Unique_Papers: inst.unique_paper_count, Authors: inst.author_count, Spotlights: inst.spotlights, Orals: inst.orals })), 'detailed_indian_institutions_iclr_2025' )} className="flex items-center bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3 py-1.5 rounded transition-colors shadow-sm" aria-label="Export detailed institution list to CSV">
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
                            <div className="text-center py-10 text-gray-500 bg-gray-800 rounded-lg border border-gray-700">
                                <FaUniversity size={36} className="mx-auto mb-3 text-gray-600" />
                                <p>No institutions found matching "{institutionFilter}".</p>
                                <p className="text-sm mt-1">Try refining your search term.</p>
                            </div>
                        )}
                    </div>
                 )}
            </main>

            {/* Footer */}
            <footer className="mt-10 md:mt-12 text-center text-gray-500 text-xs border-t border-gray-700 pt-4">
                <p>{conferenceInfo.name} {conferenceInfo.year} Dashboard | Data based on provided structure.</p>
                <p>Data processing includes combining UK/GB entries. Other stats reflect the input data.</p>
                <p className="mt-1">&copy; {new Date().getFullYear()} Analysis Dashboard</p>
            </footer>

            {/* Global Styles */}
             <style jsx global>{`
                 @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
                 .animate-fade-in { animation: fadeIn 0.5s ease-out forwards; }
                 .custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
                 .custom-scrollbar::-webkit-scrollbar-track { background: ${COLORS.card}; border-radius: 3px; }
                 .custom-scrollbar::-webkit-scrollbar-thumb { background: ${COLORS.interpretation}; border-radius: 3px; }
                 .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: ${COLORS.textSecondary}; }
                 .custom-scrollbar { scrollbar-width: thin; scrollbar-color: ${COLORS.interpretation} ${COLORS.card}; }
                  *:focus-visible { outline: 2px solid ${COLORS.primary}; outline-offset: 2px; border-radius: 2px; }
                  *:focus:not(:focus-visible) { outline: none; }

                  /* Ensure Tailwind JIT picks up dynamic color classes if not using safelist */
                  /* Example (not exhaustive, may need more for different colors/shades used): */
                  .bg-amber-500 { background-color: ${COLORS.warning}; }
                  .text-amber-400 { color: ${COLORS.warning}; } /* Adjust shade if needed */
                  .bg-blue-500 { background-color: ${COLORS.info}; }
                  .text-blue-400 { color: ${COLORS.info}; }
                  .bg-yellow-500 { background-color: ${COLORS.warning}; } /* Reuse amber for yellow */
                  .text-yellow-400 { color: ${COLORS.warning}; }
                  .bg-emerald-500 { background-color: ${COLORS.success}; }
                  .text-emerald-400 { color: ${COLORS.success}; }
                  .bg-indigo-500 { background-color: ${COLORS.primary}; }
                  .text-indigo-400 { color: ${COLORS.primary}; }
                  .bg-pink-500 { background-color: ${COLORS.corporate}; }
                  .text-pink-400 { color: ${COLORS.corporate}; }
             `}</style>
        </div>
    );
};


// --- Example Usage ---
// In a real application, you might fetch `dashboardData` and pass it.
// For this example, we import the static data and pass it directly.

const App: React.FC = () => {
    // `dashboardData` is imported from the separate data definition
    return <ICLRDashboard dashboardData={dashboardData} />;
}

export default App; // Export the wrapper App or the ICLRDashboard directly as needed