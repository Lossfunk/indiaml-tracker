import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend, CartesianGrid,
    PieChart, Pie, Sector, AreaChart, Area, LabelList, Label
} from 'recharts';
import {
    FaGlobeAsia, FaUniversity, FaUserFriends, FaSearch, FaFileAlt,
    FaInfoCircle, FaUserTie, FaTrophy, FaUsers, FaChartPie,
    FaGraduationCap, FaBuilding, FaChalkboardTeacher, FaStar,
    FaDownload, FaTable, FaChartBar, FaLightbulb, FaChevronDown, FaChevronUp,
    FaArrowRight, FaBalanceScale, FaProjectDiagram, FaBullseye, FaChartLine, FaArrowDown,
    FaLink, FaUnlink, FaGlobe, FaUser
} from 'react-icons/fa';

// Main wrapper component that handles data loading
const DynamicConferenceDashboard = () => {
    const [conferenceIndex, setConferenceIndex] = useState([]);
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Parse URL query parameters to get conference and year
    const getQueryParams = () => {
        if (typeof window !== 'undefined') {
            const params = new URLSearchParams(window.location.search);
            return {
                conference: params.get('conference') || 'ICLR',
                year: parseInt(params.get('year') || '2025', 10)
            };
        }
        return { conference: 'ICLR', year: 2025 }; // Default values
    };

    const { conference, year } = getQueryParams();

    // Fetch the conference index
    useEffect(() => {
        async function fetchConferenceIndex() {
            try {
                setLoading(true);
                const response = await fetch('/tracker/index.json');
                if (!response.ok) {
                    throw new Error('Failed to fetch conference index');
                }
                const data = await response.json();
                setConferenceIndex(data);
            } catch (error) {
                console.error("Error fetching conference index:", error);
                setError("Failed to load conference index. Please try again later.");
            }
        }

        fetchConferenceIndex();
    }, []);

    // Find and load the correct file when the index is available
    useEffect(() => {
        async function loadDashboardData() {
            if (!conferenceIndex.length) return;
            
            try {
                // Find the matching conference file
                const conferenceKey = conference.toLowerCase();
                const matchingConf = conferenceIndex.find(conf => 
                    conf.label.toLowerCase().includes(conferenceKey) && 
                    conf.label.includes(year.toString())
                );

                if (!matchingConf) {
                    throw new Error(`No data found for ${conference} ${year}`);
                }

                // Determine which file to load (analytics file if available, otherwise regular file)
                const fileToLoad = matchingConf.analytics || matchingConf.file;
                
                const response = await fetch(`/tracker/${fileToLoad}`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch dashboard data for ${conference} ${year}`);
                }
                
                const data = await response.json();
                setDashboardData(data);
                setLoading(false);
            } catch (error) {
                console.error("Error loading dashboard data:", error);
                setError(`Failed to load data for ${conference} ${year}. ${error.message}`);
                setLoading(false);
            }
        }

        loadDashboardData();
    }, [conferenceIndex, conference, year]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-lg font-medium">Loading dashboard data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center p-6">
                <div className="bg-destructive/10 border border-destructive/30 text-destructive px-6 py-4 rounded-lg shadow-lg text-center max-w-md">
                    <h2 className="font-bold text-lg mb-2">Error Loading Dashboard</h2>
                    <p>{error}</p>
                    <button 
                        onClick={() => window.location.reload()} 
                        className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    // Render the dashboard with the loaded data
    return dashboardData ? (
        <ConferenceDashboard data={dashboardData} />
    ) : null;
};

// --- Type definitions ---
// [All your existing type definitions here - I'm omitting for brevity]

// --- Reusable Helper Functions ---
const exportToCSV = (data, filename) => {
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
                // Handle potential arrays (like authors) - join them
                if (Array.isArray(value)) {
                    stringValue = value.join('; '); // Join authors with semicolon
                }
                stringValue = stringValue.replace(/"/g, '""'); // Escape double quotes
                if (stringValue.includes(',')) { stringValue = `"${stringValue}"`; } // Enclose in quotes if contains comma
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

// --- Reusable UI Components ---

// Section Component
const Section = ({ title, subtitle, children, id, className = '' }) => (
    <section id={id} className={`py-8 md:py-12 border-b border-border last:border-b-0 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-2">{title}</h2>
            {subtitle && <p className="text-base md:text-lg text-muted-foreground mb-6 md:mb-8">{subtitle}</p>}
            {children}
        </div>
    </section>
);

// StatCard Component
const StatCard = ({ title, value, icon, colorClass, subtitle, className = '' }) => (
    <div className={`bg-card border border-border p-6 rounded-xl shadow-lg flex flex-col text-center items-center ${className}`}>
        {icon && <div className={`${colorClass} text-3xl mb-3`}>{icon}</div>}
        <p className={`text-4xl md:text-5xl font-bold text-foreground mb-1`}>{value}</p>
        <h3 className="text-muted-foreground font-medium text-sm uppercase tracking-wider mb-2">{title}</h3>
        {subtitle && <p className="text-muted-foreground text-xs">{subtitle}</p>}
    </div>
);

// CustomTooltip Component
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;

        // Basic formatter
        const formatValue = (val) => typeof val === 'number' ? val.toLocaleString() : String(val);
        // Percentage formatter
        const formatPercent = (val) => typeof val === 'number' ? `${(val * 100).toFixed(1)}%` : String(val);
        // Fixed decimal formatter
        const formatDecimal = (val, places = 1) => typeof val === 'number' ? val.toFixed(places) : String(val);

        // Determine the title based on context
        let title = label || data?.country_name || data?.institute || data?.name || "Details";
        if (data?.stage) title = data.stage;
        if (data?.type && (data.type === 'Academic' || data.type === 'Corporate')) title = data.type;

        return (
            <div className="bg-popover border border-border p-3 rounded-lg shadow-xl opacity-95 text-sm max-w-xs">
                <p className="text-muted-foreground font-medium mb-1 break-words">{title}</p>

                {/* Iterate through the payload items shown in the tooltip */}
                {payload.map((pld, index) => (
                    <p key={index} style={{ color: pld.color || 'hsl(var(--foreground))' }} className="break-words">
                        {/* Display name: value */}
                        {`${pld.name}: ${formatValue(pld.value)}`}
                        {/* Display percentage if available (e.g., from Pie charts) */}
                        {pld.payload?.percent && ` (${formatPercent(pld.payload.percent)})`}
                    </p>
                ))}

                {/* --- Add specific details from the main payload object (data) --- */}

                {/* Rank (for countries) */}
                {data?.rank && <p className="text-muted-foreground text-xs mt-1">{`Rank: #${data.rank}`}</p>}

                {/* Paper Count (if not already shown in payload) */}
                {data?.paper_count !== undefined && !payload.some(p => p.dataKey === 'paper_count' || p.dataKey === 'unique_paper_count') &&
                    <p className="text-muted-foreground text-xs mt-1">{`Papers: ${formatValue(data.paper_count)}`}</p>}
                {data?.unique_paper_count !== undefined && !payload.some(p => p.dataKey === 'unique_paper_count' || p.dataKey === 'paper_count') &&
                    <p className="text-muted-foreground text-xs mt-1">{`Unique Papers: ${formatValue(data.unique_paper_count)}`}</p>}

                {/* Author Count (if available) */}
                {data?.author_count !== undefined && data.author_count > 0 && !payload.some(p => p.dataKey === 'author_count' || p.name === 'Authors') &&
                    <p className="text-muted-foreground text-xs mt-1">{`Authors: ${formatValue(data.author_count)}`}</p>}

                {/* Institution Type */}
                {data?.type && (data.type === 'academic' || data.type === 'corporate') && <p className="text-muted-foreground text-xs mt-1 capitalize">{`Type: ${data.type}`}</p>}

                {/* Spotlight/Oral Rate */}
                {data?.spotlight_oral_rate !== undefined && <p className="text-muted-foreground text-xs mt-1">{`Spotlight/Oral Rate: ${formatPercent(data.spotlight_oral_rate)}`}</p>}

                {/* Authors per Paper */}
                {data?.authors_per_paper !== undefined && <p className="text-muted-foreground text-xs mt-1">{`Authors/Paper: ${formatDecimal(data.authors_per_paper, 1)}`}</p>}

                {/* Spotlight/Oral Counts (if available, e.g., for scatter plot or bars) */}
                {(data?.spotlights !== undefined || data?.orals !== undefined) &&
                    <p className="text-muted-foreground text-xs mt-1">
                        Impact: {data.spotlights ?? 0} Spotlight(s), {data.orals ?? 0} Oral(s)
                    </p>
                }

                {/* Impact Score (for tooltips) */}
                {data?.impact_score !== undefined && !payload.some(p => p.name === 'Spotlights + Orals' || p.name === 'Impact (Spotlights+Orals)') &&
                    <p className="text-muted-foreground text-xs mt-1">{`Impact (Spotlights+Orals): ${formatValue(data.impact_score)}`}</p>
                }
            </div>
        );
    }
    return null;
};

// Pie Chart Active Shape Renderer
const renderActiveShape = (props) => {
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
            {/* Center Text */}
            <text x={cx} y={cy} dy={8} textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold">
                {payload?.name || name}
            </text>
            {/* Pie Sectors */}
            <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius} startAngle={startAngle} endAngle={endAngle} fill={fill} />
            <Sector cx={cx} cy={cy} startAngle={startAngle} endAngle={endAngle} innerRadius={outerRadius + 6} outerRadius={outerRadius + 10} fill={fill} />
            {/* Connector Line */}
            <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
            <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
            {/* Value Text */}
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill={textColor} fontSize="11">
                {`${value?.toLocaleString()}`}
            </text>
            {/* Percentage Text */}
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} dy={18} textAnchor={textAnchor} fill={mutedColor} fontSize="10">
                {`(${(percent * 100).toFixed(1)}%)`}
            </text>
        </g>
    );
};

// InterpretationPanel Component
const InterpretationPanel = ({ insights, title = "Key Insights", icon = <FaLightbulb />, iconColorClass = "text-amber-500 dark:text-amber-400" }) => (
    <div className="mt-6 bg-muted/50 rounded-lg border border-border p-4">
        <div className="flex items-start mb-3">
            <span className={`mr-3 mt-1 flex-shrink-0 ${iconColorClass}`}>{icon}</span>
            <h4 className="text-base font-semibold text-foreground">{title}</h4>
        </div>
        <ul className="space-y-2 list-disc list-inside text-muted-foreground text-sm">
            {insights.map((insight, idx) => <li key={idx}>{insight}</li>)}
        </ul>
    </div>
);

// TabButton Component
const TabButton = ({ active, onClick, children, icon }) => (
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

// InstitutionCard Component
const InstitutionCard = ({ institution, index }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [activeTab, setActiveTab] = useState('papers');
    
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
                        {/* Paper Count */}
                        <span className="flex items-center whitespace-nowrap">
                            <FaFileAlt className="mr-1.5 text-blue-500 dark:text-blue-400 flex-shrink-0" />
                            <span className="text-blue-500 dark:text-blue-400 font-medium">{institution.unique_paper_count}</span>
                            &nbsp;{institution.unique_paper_count === 1 ? 'Paper' : 'Papers'}
                        </span>
                        {/* Author Count */}
                        <span className="flex items-center whitespace-nowrap">
                            <FaUsers className="mr-1.5 text-pink-500 dark:text-pink-400 flex-shrink-0" />
                             <span className="text-pink-500 dark:text-pink-400 font-medium">{institution.author_count}</span>
                             &nbsp;{institution.author_count === 1 ? 'Author' : 'Authors'}
                        </span>
                        {/* Spotlights/Orals */}
                        {institution.spotlights > 0 && (
                            <span className="flex items-center whitespace-nowrap">
                                <FaStar className="mr-1.5 text-yellow-500 dark:text-yellow-400 flex-shrink-0" />
                                {institution.spotlights} {institution.spotlights === 1 ? 'Spotlight' : 'Spotlights'}
                            </span>
                        )}
                        {institution.orals > 0 && (
                            <span className="flex items-center whitespace-nowrap">
                                <FaTrophy className="mr-1.5 text-emerald-500 dark:text-emerald-400 flex-shrink-0" />
                                {institution.orals} {institution.orals === 1 ? 'Oral' : 'Orals'}
                            </span>
                        )}
                        {/* Type */}
                        <span className="flex items-center whitespace-nowrap capitalize">
                            {institution.type === 'academic' ? 
                                <FaGraduationCap className="mr-1.5 text-blue-500 dark:text-blue-400 flex-shrink-0" /> : 
                                <FaBuilding className="mr-1.5 text-pink-500 dark:text-pink-400 flex-shrink-0" />
                            } 
                            {institution.type}
                        </span>
                    </div>
                </div>
                <div className={`transform transition-transform duration-300 flex-shrink-0 ${isExpanded ? 'rotate-180' : ''}`}>
                    <FaChevronDown className="w-5 h-5 text-muted-foreground" />
                </div>
            </div>

            {/* --- Expanded Details --- */}
            {isExpanded && (
                <div id={detailsId} className="border-t border-border">
                    {/* Tabs */}
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
                    
                    {/* Tab Content */}
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
                                                {paper.isSpotlight && (
                                                    <span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300">
                                                        <FaStar className="mr-1" size={10} />Spotlight
                                                    </span>
                                                )}
                                                {paper.isOral && (
                                                    <span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300">
                                                        <FaTrophy className="mr-1" size={10} />Oral
                                                    </span>
                                                )}
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

// DataTable Component
const DataTable = ({ data, title, filename }) => {
    if (!data || data.length === 0) { 
        return <div className="text-muted-foreground p-4">No data available for the table.</div>; 
    }
    
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
                        <tr>
                            {headers.map((header) => (
                                <th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider whitespace-nowrap">
                                    {header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-card divide-y divide-border">
                        {data.map((row, rowIndex) => (
                            <tr key={rowIndex} className={`${row.highlight ? 'bg-amber-100 dark:bg-amber-900/30 font-medium' : ''} hover:bg-muted/50 transition-colors`}>
                                {headers.map((header, colIndex) => (
                                    <td key={`${rowIndex}-${colIndex}`} className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                                        {/* Handle array display in table (e.g., authors) */}
                                        {Array.isArray(row[header])
                                            ? (row[header]).slice(0, 3).join(', ') + (row[header].length > 3 ? '...' : '')
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

const ConferenceDashboard = ({ data }) => {
    const [institutionFilter, setInstitutionFilter] = useState('');
    const [activePieIndex, setActivePieIndex] = useState(0);

    // Destructure dashboard data
    const { conferenceInfo, globalStats, focusCountry, configuration } = data;
    const totalPapers = conferenceInfo.totalAcceptedPapers;
    const countryMap = configuration.countryMap;
    const colorScheme = configuration.colorScheme;
    const apacCountries = configuration.apacCountries;
    const focusCountryCode = focusCountry.country_code;

    // --- Memoized Data Processing ---

    const sortedCountries = useMemo(() => {
        const countryMap = new Map();
        globalStats.countries.forEach(rawCountry => {
            const countryCode = rawCountry.affiliation_country;
            // Combine UK and GB into United Kingdom if needed
            const countryName = (countryCode === 'UK' || countryCode === 'GB') 
                ? (configuration.countryMap['GB'] || 'United Kingdom') 
                : (configuration.countryMap[countryCode] || countryCode);
            
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
                // Keep the first affiliation code encountered (e.g., GB over UK if GB comes first)
            } else {
                countryMap.set(countryName, {
                    affiliation_country: countryCode === 'UK' ? 'GB' : countryCode, // Standardize to GB if UK
                    country_name: countryName,
                    paper_count: paperCount, author_count: authorCount,
                    spotlights: spotlights, orals: orals, rank: 0,
                    isHighlight: (countryCode === 'US' || countryCode === 'CN' || countryCode === focusCountryCode),
                });
            }
        });

        const sorted = Array.from(countryMap.values())
            .sort((a, b) => b.paper_count - a.paper_count || b.author_count - a.author_count);

        sorted.forEach((country, index) => {
            country.rank = index + 1;
            // Calculate Spotlight/Oral Rate
            country.spotlight_oral_rate = country.paper_count > 0 ? ((country.spotlights + country.orals) / country.paper_count) : 0;
            country.authors_per_paper = country.paper_count > 0 ? (country.author_count / country.paper_count) : 0;
        });
        return sorted;
    }, [globalStats.countries, configuration.countryMap, focusCountryCode]);

    // Rest of your memoized data processing functions...
    const topCountriesByPaper = useMemo(() => sortedCountries.slice(0, 15), [sortedCountries]);
    const usData = useMemo(() => sortedCountries.find(c => c.affiliation_country === 'US'), [sortedCountries]);
    const cnData = useMemo(() => sortedCountries.find(c => c.affiliation_country === 'CN'), [sortedCountries]);
    const focusCountryGlobalStats = useMemo(() => sortedCountries.find(c => c.affiliation_country === focusCountryCode), [sortedCountries, focusCountryCode]);

    // Process Focus Country Data
    const processedFocusData = useMemo(() => {
        if (!focusCountryGlobalStats) return null;

        // Process institutions first to add calculated fields
        const processedInstitutions = focusCountry.institutions.map(inst => ({
            ...inst,
            // Calculate authors per paper and impact score
            authors_per_paper: inst.unique_paper_count > 0 ? (inst.author_count / inst.unique_paper_count) : 0,
            impact_score: (inst.spotlights ?? 0) + (inst.orals ?? 0),
            // Ensure authors array exists (even if empty)
            authors: inst.authors || [],
        }));

        const data = {
            ...focusCountry,
            institutions: processedInstitutions,
        };

        data.rank = focusCountryGlobalStats.rank;
        data.paper_count = focusCountryGlobalStats.paper_count;
        data.author_count = focusCountryGlobalStats.author_count;
        data.spotlights = focusCountryGlobalStats.spotlights;
        data.orals = focusCountryGlobalStats.orals;
        data.spotlight_oral_rate = focusCountryGlobalStats.spotlight_oral_rate ?? 0;
        data.authors_per_paper = focusCountryGlobalStats.authors_per_paper ?? 0;
        return data;
    }, [focusCountry, focusCountryGlobalStats]);

    // Data for US/China Dominance Pie Chart
    const usChinaDominancePieData = useMemo(() => {
        if (!usData || !cnData || !totalPapers || totalPapers === 0) return [];
        const usCount = usData.paper_count;
        const cnCount = cnData.paper_count;
        const restCount = Math.max(0, totalPapers - usCount - cnCount);

        return [
            { name: 'United States', value: usCount, percent: usCount / totalPapers, fill: colorScheme.us }, 
            { name: 'China', value: cnCount, percent: cnCount / totalPapers, fill: colorScheme.cn },
            { name: 'Rest of World', value: restCount, percent: restCount / totalPapers, fill: 'hsl(var(--muted))' }
        ];
    }, [usData, cnData, totalPapers, colorScheme]);

    // Data for APAC Dynamics
    const apacCountriesData = useMemo(() => {
        return sortedCountries
            .filter(country => apacCountries.includes(country.affiliation_country))
            .sort((a, b) => b.paper_count - a.paper_count);
    }, [sortedCountries, apacCountries]);

    // Add other data processing functions as needed...

    // Filtered Institutions
    const filteredInstitutions = useMemo(() => {
        if (!processedFocusData?.institutions) return [];
        return processedFocusData.institutions
            .filter(inst => inst.institute?.toLowerCase().includes(institutionFilter.toLowerCase()))
            .sort((a, b) => 
                (b.unique_paper_count ?? 0) - (a.unique_paper_count ?? 0) || 
                (b.impact_score ?? 0) - (a.impact_score ?? 0) || 
                (b.author_count ?? 0) - (a.author_count ?? 0)
            );
    }, [processedFocusData, institutionFilter]);

    const topInstitutions = useMemo(() => filteredInstitutions.slice(0, 8), [filteredInstitutions]);

    // --- Event Handlers ---
    const handleFilterChange = useCallback((event) => setInstitutionFilter(event.target.value), []);
    const handlePieEnter = useCallback((_data, index) => setActivePieIndex(index), []);

    // --- Render Logic ---
    if (!processedFocusData || !usData || !cnData) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center p-6">
                <div className="bg-destructive/10 border border-destructive/30 text-destructive px-4 py-3 rounded-lg shadow-lg text-center">
                    <h2 className="font-bold text-lg mb-2">Data Loading Error</h2>
                    <p>Could not process essential dashboard data. Please check the data source.</p>
                </div>
            </div>
        );
    }

    // Color mapping for charts
    const colorMap = {
        us: colorScheme.us,
        cn: colorScheme.cn,
        focusCountry: colorScheme.focusCountry,
        primary: colorScheme.primary || 'hsl(var(--primary))',
        secondary: colorScheme.secondary || 'hsl(var(--secondary-foreground))',
        academic: colorScheme.academic,
        corporate: colorScheme.corporate,
        spotlight: colorScheme.spotlight,
        oral: colorScheme.oral,
        grid: 'hsl(var(--border))',
        textAxis: 'hsl(var(--muted-foreground))',
        highlight: 'hsl(142, 71%, 45%)',
        accent: 'hsl(330, 80%, 60%)',
        warning: 'hsl(36, 96%, 50%)',
        rest: 'hsl(var(--muted))',
    };

    // Custom label for Pie Chart percentages
    const RADIAN = Math.PI / 180;
    const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name, value }) => {
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);
        const percentValue = (percent * 100).toFixed(0);

        // Don't render label if percentage is too small
        if (percent < 0.05) return null;

        return (
            <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize="10" fontWeight="bold">
                {`${name} ${percentValue}%`}
            </text>
        );
    };

    // Render the dashboard
    return (
        <div className="min-h-screen bg-background text-foreground font-sans">
            {/* Dashboard header */}
            <header className="py-6 md:py-8 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 border-b border-border shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h1 className="text-3xl sm:text-4xl font-bold text-foreground flex items-center justify-center mb-2">
                        <FaTrophy className="mr-3 text-amber-500" /> {configuration.dashboardTitle}
                    </h1>
                    <p className="text-muted-foreground text-base sm:text-lg">{configuration.dashboardSubtitle}</p>
                    <p className="text-sm text-muted-foreground mt-3">Total Accepted Papers: <span className="font-semibold text-foreground">{totalPapers?.toLocaleString() ?? 'N/A'}</span></p>
                </div>
            </header>

            {/* Rest of the dashboard content... */}
            <main>
                {/* Summary section */}
                <Section title={configuration.sections.summary.title} id="summary" className="bg-muted/30">
                    {/* Hero Stats Grid */}
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
                            subtitle={`Average ${(processedFocusData?.authors_per_paper ?? 0).toFixed(1)} authors per paper | Building ${focusCountry.country_name || 'Local'}'s ML community`}
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

                    {/* Breakout Highlights */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div className="bg-card p-4 rounded-lg border border-border shadow-sm">
                            <div className="flex items-start mb-3">
                                <FaUniversity className="text-blue-500 mr-3 mt-1" size={20}/>
                                <div>
                                    <p className="text-foreground font-medium text-lg">Institutional Leaders:</p>
                                    <p className="text-muted-foreground">
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
                                    <p className="text-muted-foreground">
                                        {focusCountry.country_name || 'Focus country'} secured {processedFocusData.spotlights} spotlight {processedFocusData.spotlights === 1 ? 'paper' : 'papers'} at {conferenceInfo.name} {conferenceInfo.year}, demonstrating quality research capability{processedFocusData.paper_count && processedFocusData.paper_count < 100 ? ' despite smaller overall representation' : ''}.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Insights Panel */}
                    <InterpretationPanel
                        title="Dashboard Narrative Hook"
                        icon={<FaBullseye />}
                        iconColorClass='text-red-500 dark:text-red-400'
                        insights={configuration.sections.summary.insights}
                    />
                </Section>

                {/* Additional sections would go here... */}
            </main>

            {/* Footer */}
            <footer className="mt-10 md:mt-12 text-center text-muted-foreground text-xs border-t border-border pt-6 pb-6 bg-gradient-to-r from-amber-50/30 to-orange-50/30 dark:from-amber-950/10 dark:to-orange-950/10">
                <p>{conferenceInfo?.name ?? 'Conference'} {conferenceInfo?.year ?? ''} Dashboard | Data Updated {new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}</p>
                <p>{focusCountry.country_name || 'Focus Country'}'s Contribution: {processedFocusData.paper_count} Papers | {processedFocusData.author_count} Authors | {processedFocusData.first_focus_country_author?.count} First Authors | {processedFocusData.spotlights} Spotlight {processedFocusData.spotlights === 1 ? 'Paper' : 'Papers'}</p>
                <p className="mt-1">&copy; {new Date().getFullYear()} Analysis Dashboard</p>
            </footer>

            {/* Global Styles */}
            <style jsx global>{`
                body {
                    scroll-behavior: smooth;
                }
                /* Simple fade-in animation */
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in {
                    animation: fadeIn 0.5s ease-out forwards;
                }
                /* Custom scrollbar for institution paper/author list */
                .custom-scrollbar::-webkit-scrollbar { width: 6px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: hsl(var(--muted)); border-radius: 3px; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: hsl(var(--border)); border-radius: 3px; }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: hsl(var(--primary) / 0.7); }

                /* Ensure Recharts text is legible in dark/light mode */
                .recharts-default-tooltip {
                    background-color: hsl(var(--popover)) !important;
                    border: 1px solid hsl(var(--border)) !important;
                    color: hsl(var(--popover-foreground)) !important;
                }
                .recharts-text.recharts-pie-label-text {
                    fill: white !important; /* Ensure pie label text is white */
                    font-size: 10px;
                    font-weight: bold;
                }
                .recharts-legend-item-text { fill: hsl(var(--foreground)); }
                .recharts-label, .recharts-cartesian-axis-tick-value { fill: hsl(var(--muted-foreground)); }
                .recharts-label tspan { fill: hsl(var(--muted-foreground)); } /* Ensure label tspans are correct color */
                .recharts-tooltip-wrapper { outline: none; } /* Remove focus outline on tooltip */
            `}</style>
        </div>
    );
};

export default DynamicConferenceDashboard;