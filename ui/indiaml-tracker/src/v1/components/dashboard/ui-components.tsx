import React from 'react';
import { 
    FaDownload, FaTable, FaChartBar, FaMapMarkedAlt, FaChevronDown, FaChevronUp 
} from 'react-icons/fa';
import { 
    Tooltip as RechartsTooltip, 
    TooltipProps, 
    Sector 
} from 'recharts';
import { ActiveShapeProps, RechartsTooltipPayload, ViewMode, MapChartViewToggleProps } from './types';
import { exportToCSV } from './utils';

// ## StatCard Component ##
interface StatCardProps {
    title: string;
    value: string | number;
    icon: React.ReactNode;
    colorClass: string;
    bgColorClass: string;
    subtitle?: string;
    size?: 'small' | 'normal';
}

export const StatCard: React.FC<StatCardProps> = ({ 
    title, value, icon, colorClass, bgColorClass, subtitle, size = 'normal' 
}) => {
    return (
        <div className="bg-card rounded-xl border border-border shadow-sm p-4 relative flex flex-col">
            <div className={`absolute right-4 top-4 rounded-full ${bgColorClass} p-2 text-white`}>
                {icon}
            </div>
            <h3 className={`${colorClass} text-sm font-medium`}>{title}</h3>
            <div className={`text-foreground mt-2 ${size === 'normal' ? 'text-2xl' : 'text-xl'} font-semibold`}>
                {value}
            </div>
            {subtitle && <div className="text-xs text-muted-foreground mt-1">{subtitle}</div>}
        </div>
    );
};

// ## CustomTooltip Component ##
export const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ 
    active, payload, label 
}) => {
    if (!active || !payload || !payload.length) return null;

    // Function to check if a payload item is custom and not a standard recharts item
    const isCustomPayload = (item: RechartsTooltipPayload): boolean => {
        return (
            (typeof item.value !== 'undefined' && item.value !== null) ||
            (typeof item.name !== 'undefined' && item.name !== null)
        );
    };

    // Filter out non-essential payloads
    const filteredPayload = payload.filter(isCustomPayload);

    // Add support for percentage tooltips
    const getPercentageText = (item: RechartsTooltipPayload): JSX.Element | null => {
        if (item.payload && typeof item.payload.percent === 'number') {
            return (
                <span className="text-xs block mt-0.5">
                    ({(item.payload.percent * 100).toFixed(1)}%)
                </span>
            );
        }
        return null;
    };

    // Format values
    const formatValue = (value: any): string => {
        if (typeof value === 'number') {
            return value.toLocaleString();
        }
        return String(value);
    };

    // Determine if we show the country section
    const showCountryInfo = payload[0]?.payload?.country_name && payload[0]?.payload?.affiliation_country;

    return (
        <div className="bg-popover text-popover-foreground p-2.5 rounded-md shadow-md text-sm border border-border">
            {/* Showing label if provided */}
            {label && <div className="font-medium pb-1 border-b border-border mb-1.5">{label}</div>}

            {/* Country information for maps */}
            {showCountryInfo && (
                <div className="mb-1.5 pb-1 border-b border-border">
                    <div className="font-medium">{payload[0].payload.country_name}</div>
                    <div className="text-xs text-muted-foreground">{payload[0].payload.affiliation_country}</div>
                </div>
            )}

            {/* Data points */}
            <div className="space-y-1">
                {filteredPayload.map((item, index) => (
                    <div key={`tooltip-item-${index}`} className="flex items-center justify-between gap-3">
                        <div className="flex items-center">
                            {item.fill && (
                                <div
                                    className="h-2.5 w-2.5 rounded-full mr-1.5"
                                    style={{ backgroundColor: item.fill }}
                                />
                            )}
                            <span>{item.name}:</span>
                        </div>
                        <div className="font-medium">
                            {formatValue(item.value)}
                            {getPercentageText(item)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

// ## Pie Chart Active Shape Renderer ##
export const renderActiveShape = (props: ActiveShapeProps) => {
    const {
        cx = 0,
        cy = 0,
        midAngle = 0,
        innerRadius = 0,
        outerRadius = 0,
        startAngle = 0,
        endAngle = 0,
        fill,
        payload,
        percent = 0,
        value = 0,
        name = '',
    } = props;

    const sin = Math.sin(-midAngle * Math.PI / 180);
    const cos = Math.cos(-midAngle * Math.PI / 180);
    const sx = cx + (outerRadius + 10) * cos;
    const sy = cy + (outerRadius + 10) * sin;
    const mx = cx + (outerRadius + 30) * cos;
    const my = cy + (outerRadius + 30) * sin;
    const ex = mx + (cos >= 0 ? 1 : -1) * 22;
    const ey = my;
    const textAnchor = cos >= 0 ? 'start' : 'end';

    return (
        <g>
            <Sector
                cx={cx}
                cy={cy}
                innerRadius={innerRadius}
                outerRadius={outerRadius}
                startAngle={startAngle}
                endAngle={endAngle}
                fill={fill}
            />
            <Sector
                cx={cx}
                cy={cy}
                startAngle={startAngle}
                endAngle={endAngle}
                innerRadius={outerRadius + 6}
                outerRadius={outerRadius + 10}
                fill={fill}
            />
            <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
            <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill="hsl(var(--foreground))" fontSize={12} fontWeight={500}>{name}</text>
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} dy={18} textAnchor={textAnchor} fill="hsl(var(--foreground))" fontSize={11}>
                {`${value.toLocaleString()} (${(percent * 100).toFixed(1)}%)`}
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

export const InterpretationPanel: React.FC<InterpretationPanelProps> = ({ 
    title, insights, legend 
}) => {
    const [expanded, setExpanded] = React.useState(false);

    if (!insights.length) return null;

    return (
        <div className="mt-6 bg-muted/30 border border-border rounded-lg p-4">
            <div className="flex justify-between items-center">
                <div className="flex items-center">
                    <div className="mr-2 text-primary">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="16" x2="12" y2="12"></line>
                            <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                    </div>
                    <h3 className="text-sm sm:text-base font-medium text-foreground">
                        {title || "Interpretation & Insights"}
                    </h3>
                </div>
                <button 
                    className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-md"
                    onClick={() => setExpanded(!expanded)}
                    aria-expanded={expanded}
                    aria-label={expanded ? "Collapse insights" : "Expand insights"}
                >
                    {expanded ? <FaChevronUp size={14} /> : <FaChevronDown size={14} />}
                </button>
            </div>
            
            {expanded && (
                <div className="mt-3 space-y-3 text-sm text-foreground">
                    <ul className="space-y-2">
                        {insights.map((insight, i) => (
                            <li key={i} className="flex">
                                <span className="mr-2 text-primary font-medium">{i + 1}.</span>
                                <span>{insight}</span>
                            </li>
                        ))}
                    </ul>
                    {legend && (
                        <div className="mt-4 text-xs text-muted-foreground border-t border-border pt-3">
                            <span className="font-medium text-foreground">Note:</span> {legend}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// ## InstitutionCard Component ##
interface InstitutionCardProps {
    institution: any;
    index: number;
}

export const InstitutionCard: React.FC<InstitutionCardProps> = ({ 
    institution, index 
}) => {
    const [expanded, setExpanded] = React.useState(false);
    const [activeTab, setActiveTab] = React.useState<'papers' | 'authors'>('papers');
    const isAcademic = institution.type === 'academic';
    
    const hasPapers = institution.papers && institution.papers.length > 0;
    const hasAuthors = institution.authors && institution.authors.length > 0;

    return (
        <div className={`bg-card rounded-xl border border-border shadow-sm overflow-hidden`}>
            <div className="p-4">
                <div className="flex justify-between items-start">
                    <div className={`px-2 py-0.5 text-xs font-medium rounded ${isAcademic ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300'}`}>
                        {isAcademic ? 'Academic' : 'Corporate'}
                    </div>
                    <div className="text-sm font-medium text-muted-foreground">#{index + 1}</div>
                </div>
                
                <h3 className="mt-2 text-base font-semibold text-foreground line-clamp-2">
                    {institution.institute}
                </h3>
                
                <div className="mt-3 grid grid-cols-2 gap-2">
                    <div className="bg-muted/50 rounded p-2 text-center">
                        <div className="text-lg font-semibold text-foreground">{institution.unique_paper_count}</div>
                        <div className="text-xs text-muted-foreground">Papers</div>
                    </div>
                    <div className="bg-muted/50 rounded p-2 text-center">
                        <div className="text-lg font-semibold text-foreground">{institution.author_count}</div>
                        <div className="text-xs text-muted-foreground">Authors</div>
                    </div>
                </div>
                
                <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                    <div>Spotlights: <span className="font-medium text-foreground">{institution.spotlights}</span></div>
                    <div>Orals: <span className="font-medium text-foreground">{institution.orals}</span></div>
                </div>
                
                {(hasPapers || hasAuthors) && (
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="mt-3 text-xs flex items-center text-primary hover:text-primary/80 transition-colors"
                    >
                        {expanded ? 'Hide' : 'Show'} details
                        {expanded ? <FaChevronUp className="ml-1" size={10} /> : <FaChevronDown className="ml-1" size={10} />}
                    </button>
                )}
            </div>
            
            {expanded && (hasPapers || hasAuthors) && (
                <div className="border-t border-border bg-card/50">
                    <div className="flex border-b border-border">
                        <button
                            onClick={() => setActiveTab('papers')}
                            className={`flex-1 text-xs font-medium py-2 text-center transition-colors ${activeTab === 'papers' ? 'bg-muted/30 text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            Papers ({institution.papers?.length || 0})
                        </button>
                        <button
                            onClick={() => setActiveTab('authors')}
                            className={`flex-1 text-xs font-medium py-2 text-center transition-colors ${activeTab === 'authors' ? 'bg-muted/30 text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            Authors ({institution.authors?.length || 0})
                        </button>
                    </div>
                    
                    {activeTab === 'papers' && hasPapers && (
                        <div className="p-3">
                            <ul className="space-y-2">
                                {institution.papers.map((paper: any, idx: number) => (
                                    <li key={idx} className="text-xs">
                                        <div className="flex gap-x-1">
                                            {paper.isSpotlight && (
                                                <span className="shrink-0 px-1.5 py-0.5 bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300 text-[10px] rounded-sm">Spotlight</span>
                                            )}
                                            {paper.isOral && (
                                                <span className="shrink-0 px-1.5 py-0.5 bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 text-[10px] rounded-sm">Oral</span>
                                            )}
                                        </div>
                                        <div className="mt-1 text-foreground">{paper.title}</div>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                    
                    {activeTab === 'authors' && hasAuthors && (
                        <div className="p-3">
                            <ul className="space-y-2">
                                {institution.authors.map((author: any, idx: number) => (
                                    <li key={idx} className="text-xs">
                                        <div className="flex justify-between items-center">
                                            <span className="text-foreground">{author.name}</span>
                                            {author.paper_count && (
                                                <span className="text-[10px] text-muted-foreground">
                                                    {author.paper_count} {author.paper_count === 1 ? 'paper' : 'papers'}
                                                </span>
                                            )}
                                        </div>
                                        {author.affiliation && (
                                            <div className="text-[10px] text-muted-foreground mt-0.5">
                                                {author.affiliation}
                                            </div>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
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

export const DataTable: React.FC<DataTableProps> = ({ 
    data, title, filename 
}) => {
    if (!data || data.length === 0) return <div className="text-sm text-muted-foreground">No data available</div>;
    
    const headers = Object.keys(data[0]).filter(key => key !== 'highlight');
    
    const handleExport = () => {
        exportToCSV(data, filename);
    };
    
    return (
        <div>
            <div className="flex justify-between items-center mb-3">
                <h3 className="text-sm font-medium text-foreground">{title}</h3>
                <button 
                    onClick={handleExport}
                    className="flex items-center text-xs bg-primary/10 text-primary hover:bg-primary/20 transition-colors px-2 py-1 rounded"
                >
                    <FaDownload size={10} className="mr-1" />
                    Export CSV
                </button>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead className="bg-muted/50 text-xs">
                        <tr>
                            {headers.map(header => (
                                <th key={header} className="px-3 py-2 text-left font-medium text-muted-foreground border-b border-border">
                                    {header.replace(/_/g, ' ')}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((row, i) => (
                            <tr 
                                key={i} 
                                className={`
                                    hover:bg-muted/30 transition-colors
                                    ${row.highlight ? 'bg-amber-50/30 dark:bg-amber-900/10' : ''}
                                    ${i % 2 === 0 ? 'bg-muted/10' : ''}
                                `}
                            >
                                {headers.map(header => (
                                    <td key={`${i}-${header}`} className="px-3 py-2 border-t border-border">
                                        {row[header] !== null && row[header] !== undefined ? String(row[header]) : ''}
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

export const ViewToggle: React.FC<ViewToggleProps> = ({ 
    activeView, setActiveView 
}) => (
    <div className="flex items-center space-x-1 bg-muted p-1 rounded-lg shadow-inner">
        <button onClick={() => setActiveView('chart')} className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${activeView === 'chart' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-transparent text-muted-foreground hover:bg-background hover:text-foreground'}`} aria-pressed={activeView === 'chart'}>
            <FaChartBar size={12} /><span>Chart</span>
        </button>
        <button onClick={() => setActiveView('table')} className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${activeView === 'table' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-transparent text-muted-foreground hover:bg-background hover:text-foreground'}`} aria-pressed={activeView === 'table'}>
            <FaTable size={12} /><span>Table</span>
        </button>
    </div>
);

export const MapChartViewToggle: React.FC<MapChartViewToggleProps> = ({ 
    activeView, setActiveView 
}) => (
   <div className="flex items-center space-x-1 bg-muted p-1 rounded-lg shadow-inner">
       <button onClick={() => setActiveView('map')} className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${activeView === 'map' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-transparent text-muted-foreground hover:bg-background hover:text-foreground'}`} aria-pressed={activeView === 'map'}>
           <FaMapMarkedAlt size={12} /><span>Map</span>
       </button>
       <button onClick={() => setActiveView('chart')} className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${activeView === 'chart' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-transparent text-muted-foreground hover:bg-background hover:text-foreground'}`} aria-pressed={activeView === 'chart'}>
           <FaChartBar size={12} /><span>Chart</span>
       </button>
   </div>
);
