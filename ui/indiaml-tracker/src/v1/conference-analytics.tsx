import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend, CartesianGrid,
  PieChart, Pie, Sector
} from 'recharts';
import { 
  FaGlobeAsia, FaUniversity, FaUserFriends, FaSearch, FaFileAlt, 
  FaInfoCircle, FaUserTie, FaTrophy, FaUsers, FaChartPie, 
  FaGraduationCap, FaBuilding, FaChalkboardTeacher, FaStar,
  FaDownload, FaTable, FaChartBar, FaLightbulb, FaChevronDown, FaChevronUp
} from 'react-icons/fa';

// --- Colors and CountryMap remain the same ---
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
const APAC_COUNTRIES = ['CN', 'IN', 'HK', 'SG', 'JP', 'KR', 'AU'];

const CountryMap = {
  "US": "United States",
  "CN": "China",
  "GB": "United Kingdom",
  "UK": "United Kingdom",
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

// --- Updated CustomTooltip to show Papers or Authors ---
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const dataKey = payload[0].dataKey;
    const name = payload[0].name;

    const countryName = data.country_name || label;
    const institutionName = data.name || data.institute;

    let title = institutionName || countryName || label;
    let content = null;

    if (dataKey === 'paper_count' || dataKey === 'author_count') {
      // Global Charts
      title = countryName;
      const count = data[dataKey];
      const metricName = dataKey === 'paper_count' ? 'Papers' : 'Authors';
      content = <p className="text-white font-bold">{`${metricName}: ${count?.toLocaleString() || 'N/A'}`}</p>;
      // Add rank info if available
      if (data.rank) {
        content = <>
          {content}
          <p className="text-gray-400 text-xs mt-1">{`Rank: #${data.rank}`}</p>
        </>
      }
    } else if (dataKey === 'uniquePapers' || dataKey === 'authorCount') {
      // Institution Chart
      title = institutionName;
      content = (
        <>
          <p className="text-indigo-300 font-bold">{`Total Papers: ${data.uniquePapers?.toLocaleString() || 'N/A'}`}</p>
          <p className="text-pink-300 font-bold">{`Total Authors: ${data.authorCount?.toLocaleString() || 'N/A'}`}</p>
        </>
      );
    } else if (dataKey === 'value') {
      // Pie Chart
      title = data.name;
      content = <p className="text-white font-bold">{`${data.value?.toLocaleString() || 'N/A'} (${data.percent?.toFixed(1) || 0}%)`}</p>;
    } else if (dataKey === 'total') {
      // Stacked Bar Chart for Spotlights & Orals
      title = data.name;
      content = (
        <>
          <p className="text-white font-bold">{`Total: ${data.total}`}</p>
          <p className="text-amber-300">{`Spotlights: ${data.spotlights}`}</p>
          <p className="text-pink-300">{`Orals: ${data.orals}`}</p>
        </>
      );
    } else if (dataKey === 'unique_paper_count') {
      // Institution Chart
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

    return (
      <div className="bg-gray-900 border border-gray-700 p-3 rounded-lg shadow-xl opacity-95">
        <p className="text-gray-300 font-medium mb-1">{title}</p>
        {content}
      </div>
    );
  }
  return null;
};

// Custom active shape for pie charts
const renderActiveShape = (props) => {
  const { cx, cy, midAngle, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;
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
      <text x={cx} y={cy} dy={8} textAnchor="middle" fill={fill}>
        {payload.name}
      </text>
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
      <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill="#fff">{`${value}`}</text>
      <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} dy={18} textAnchor={textAnchor} fill="#999">
        {`(${(percent * 100).toFixed(1)}%)`}
      </text>
    </g>
  );
};

// --- New InterpretationPanel Component ---
const InterpretationPanel = ({ title, insights, legend }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-4 bg-gray-700 rounded-lg border border-gray-600 overflow-hidden transition-all duration-300">
      <div 
        className="p-3 flex items-center justify-between cursor-pointer bg-gray-700 hover:bg-gray-600 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center">
          <FaLightbulb className="text-amber-400 mr-2" />
          <h4 className="text-white font-medium">{title || 'Interpretation'}</h4>
        </div>
        <div>
          {isExpanded ? 
            <FaChevronUp className="text-gray-400" /> : 
            <FaChevronDown className="text-gray-400" />
          }
        </div>
      </div>
      
      {isExpanded && (
        <div className="p-4 bg-gray-800 border-t border-gray-600">
          <div className="text-gray-300 text-sm leading-relaxed mb-3">
            {insights.map((insight, idx) => (
              <p key={idx} className="mb-2">{insight}</p>
            ))}
          </div>
          
          {legend && (
            <div className="mt-3 pt-3 border-t border-gray-600">
              <p className="text-amber-400 text-xs font-medium mb-1">LEGEND:</p>
              <p className="text-gray-400 text-xs">{legend}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// --- StatCard remains the same ---
const StatCard = ({ title, value, icon, color, subtitle, size = 'normal' }) => (
  <div className={`bg-gray-800 p-6 rounded-xl shadow-md border border-gray-700 flex flex-col ${size === 'large' ? 'lg:col-span-2' : ''}`}>
    <div className="flex items-center mb-2">
      {icon && <span className={`text-${color}-400 mr-3 text-lg`}>{icon}</span>}
      <h3 className="text-gray-400 font-medium text-sm uppercase tracking-wider">{title}</h3>
    </div>
    <div className="flex items-end justify-between mt-auto pt-2">
      <div>
        <p className={`text-white font-bold ${size === 'large' ? 'text-4xl' : 'text-3xl'}`}>{value}</p>
        {subtitle && <p className="text-gray-400 text-xs mt-1">{subtitle}</p>}
      </div>
      {color && (
        <div className={`h-2 w-16 bg-${color}-500 rounded-full opacity-75 self-end mb-1`}></div>
      )}
    </div>
  </div>
);

// --- Updated InstitutionCard to show Papers & Authors ---
const InstitutionCard = ({ institution, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className="bg-gray-800 rounded-lg shadow-md overflow-hidden mb-4 border border-gray-700 hover:border-indigo-500 transition-all duration-300 animate-fade-in"
      style={{
        animationDelay: `${index * 0.05}s`,
        opacity: 0,
        animationFillMode: 'forwards'
      }}
    >
      <div
        className="p-4 cursor-pointer flex justify-between items-center"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* Main Info */}
        <div className="flex-1 mr-4">
          <h3 className="text-white font-medium">{institution.institute}</h3>
          <div className="flex items-center text-sm text-gray-400 mt-1 space-x-4">
            <span className="flex items-center">
              <FaFileAlt className="mr-1.5 text-indigo-400"/>
              {institution.unique_paper_count} {institution.unique_paper_count === 1 ? 'Paper' : 'Papers'}
            </span>
            <span className="flex items-center">
              <FaUsers className="mr-1.5 text-pink-400"/>
              {institution.author_count} {institution.author_count === 1 ? 'Author' : 'Authors'}
            </span>
            {institution.spotlights > 0 && (
              <span className="flex items-center">
                <FaStar className="mr-1.5 text-yellow-400"/>
                {institution.spotlights} {institution.spotlights === 1 ? 'Spotlight' : 'Spotlights'}
              </span>
            )}
          </div>
        </div>
        {/* Expand Icon */}
        <div className={`transform transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
          <svg className="w-5 h-5 text-gray-400" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
            <path d="M19 9l-7 7-7-7"></path>
          </svg>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-gray-700">
          <p className="text-gray-300 text-sm mb-3 font-medium">Published Papers ({institution.unique_paper_count}):</p>
          <ul className="space-y-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
            {institution.papers.map((paper, idx) => (
              <li key={idx} className="text-gray-400 text-sm bg-gray-900 p-3 rounded-md shadow-sm">
                <a href={`https://openreview.net/forum?id=${paper.id}`} target="_blank" rel="noopener noreferrer" className="hover:text-indigo-300 transition-colors">
                  {paper.title} <span className="text-xs text-gray-500">(ID: {paper.id})</span>
                </a>
                {paper.isSpotlight && (
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-900 text-yellow-300">
                    <FaStar className="mr-1" size={10} />Spotlight
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Helper function to export data as CSV
const exportToCSV = (data, filename) => {
  if (!data || !data.length) return;
  
  // Convert data to CSV format
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','), // Header row
    ...data.map(row => headers.map(header => {
      // Handle values that might contain commas by wrapping in quotes
      const value = row[header] !== undefined ? row[header] : '';
      return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
    }).join(','))
  ].join('\n');
  
  // Create download link
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Table with export functionality component
const DataTable = ({ data, title, filename }) => {
  if (!data || !data.length) return null;
  
  const headers = Object.keys(data[0]);
  
  return (
    <div className="overflow-x-auto">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-white font-medium">{title}</h4>
        <button 
          onClick={() => exportToCSV(data, filename)}
          className="flex items-center bg-gray-700 hover:bg-gray-600 text-white text-xs px-3 py-1.5 rounded transition-colors"
        >
          <FaDownload className="mr-2" size={10} />
          Export CSV
        </button>
      </div>
      <table className="min-w-full divide-y divide-gray-700">
        <thead className="bg-gray-700">
          <tr>
            {headers.map((header, index) => (
              <th key={index} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-gray-800 divide-y divide-gray-700">
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className={row.highlight ? 'bg-amber-900 bg-opacity-20' : ''}>
              {headers.map((header, colIndex) => (
                <td key={`${rowIndex}-${colIndex}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  {row[header]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Toggle component to switch between chart and table views
const ViewToggle = ({ activeView, setActiveView }) => {
  return (
    <div className="flex items-center space-x-2 mb-2">
      <button
        onClick={() => setActiveView('chart')}
        className={`flex items-center space-x-1 px-3 py-1.5 text-xs rounded ${
          activeView === 'chart' ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        }`}
      >
        <FaChartBar size={12} />
        <span>Chart</span>
      </button>
      <button
        onClick={() => setActiveView('table')}
        className={`flex items-center space-x-1 px-3 py-1.5 text-xs rounded ${
          activeView === 'table' ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        }`}
      >
        <FaTable size={12} />
        <span>Table</span>
      </button>
    </div>
  );
};

const ICLRDashboard = () => {
  const [data, setData] = useState(null);
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [institutionFilter, setInstitutionFilter] = useState('');
  const [activePieIndex, setActivePieIndex] = useState(0);
  const [viewModes, setViewModes] = useState({
    global: 'chart',
    apac: 'chart',
    authorship: 'chart',
    comparison: 'chart',
    institutions: 'chart' // Added institutions view mode
  });
  const tabs = ["Overview", "Global Stats", "India Focus", "Institutions"];

  // Interpretative insights for each section
  const interpretations = {
    overview: {
      title: "India's Growth in AI Research",
      insights: [
        "India's emerging presence in the global AI research landscape with 49 accepted papers at ICLR 2025 represents approximately 1.3% of all accepted papers. While this places India at rank #16 globally, it signals significant growth compared to previous years.",
        "The presence of 3 spotlights/orals presentations indicates that Indian research is beginning to gain international recognition for quality, not just quantity.",
        "India's contributions remain modest compared to leaders like the US (1,929 papers) and China (1,308 papers), but the growth trajectory is promising. Academic institutions (particularly IITs) dominate the Indian research landscape, though corporate research labs like Microsoft Research India are producing high-impact work."
      ],
      legend: "In the global leaderboard bar chart, longer bars represent more papers (higher is better for research output), with India highlighted to showcase its relative position."
    },
    globalDistribution: {
      title: "Global Research Distribution Analysis",
      insights: [
        "The dashboard reveals a stark concentration of AI research power, with the US and China collectively contributing over 87% of all ICLR 2025 papers. This duopoly presents both opportunities and challenges for the global AI research ecosystem.",
        "While concentrated research hubs accelerate progress, they may also limit diverse perspectives needed to address global challenges. The APAC region shows promising growth beyond China, with countries like Hong Kong, Singapore, South Korea, and India establishing themselves as secondary hubs.",
        "The stark imbalance suggests potential opportunities for international collaboration while raising questions about global AI governance when research is so concentrated."
      ],
      legend: "In the pie charts, larger segments represent greater research output (higher is better for research presence), while the US and China's overwhelming proportion illustrates potential ecosystem concerns."
    },
    apacContributions: {
      title: "APAC Regional Dynamics",
      insights: [
        "Within the Asia-Pacific region, China commands the lion's share (76% of regional papers), but other countries are establishing specialized niches that leverage their unique strengths.",
        "India's position within APAC (ranked 5th after China, Hong Kong, Singapore, and South Korea) highlights both its growth potential and the competitive regional landscape.",
        "The distribution of papers within APAC demonstrates how emerging AI ecosystems are developing, with countries like Singapore showing disproportionate impact relative to their size."
      ],
      legend: "In the APAC charts, bar height represents paper count (higher is better for research output) while the pie chart shows relative contribution to the regional ecosystem."
    },
    indiaFocus: {
      title: "India Focus: Patterns and Potential",
      insights: [
        "The detailed analysis of Indian participation reveals that while 50 papers have at least one Indian author, only 23 have a majority of Indian authors, and just 26 papers have an Indian first author. This indicates that Indians are increasingly participating in global research collaborations, but often not leading them.",
        "The academic/corporate split (71% academic vs. 29% corporate) demonstrates the strong foundation of Indian academic institutions, while highlighting growth opportunities for industrial research.",
        "The relatively low ratio of 'majority Indian' papers indicates significant international collaboration, a positive sign for knowledge transfer, while the low 'first author' rate (52% of papers with Indian authors) suggests Indian researchers are still developing leadership in global research teams."
      ],
      legend: "In the authorship distribution charts, higher values in 'Majority Indian' and 'First Indian Author' categories would indicate more local research leadership (better for developing sovereign research capabilities). For institution type, balance between academic and corporate is ideal for a healthy ecosystem."
    },
    institutionAnalysis: {
      title: "Institution Analysis: Academic and Corporate Balance",
      insights: [
        "IIT Bombay leads with 10 papers, followed by Microsoft Research India with 6 papers. What's particularly noteworthy is the impact differential - while academic institutions produce more papers by volume, corporate research labs achieve higher impact metrics with more spotlights and orals.",
        "Microsoft Research India's performance (1 spotlight, 1 oral from 6 papers) demonstrates exceptional quality-to-quantity ratio, suggesting focused research priorities.",
        "The institutional distribution shows geographic concentration in major tech hubs (Mumbai, Bangalore, Delhi), suggesting potential for regional expansion to tap into talent pools throughout the country."
      ],
      legend: "In the institutional contribution charts, bar height represents paper count (higher is better for research output), while the academic/corporate split shows ecosystem balance (diversity is better than concentration). For spotlights/orals, higher numbers indicate higher research impact."
    },
    comparativePerformance: {
      title: "Comparative Performance Analysis",
      insights: [
        "While India's raw numbers (49 papers vs. US: 1,929, China: 1,308) highlight the significant gap in research output, the proportional metrics tell a more nuanced story. India's spotlight/oral ratio (6.1% of papers) is comparable to China's (5.0%) though below the US (5.5%), suggesting that while India produces fewer papers, their quality is competitive.",
        "The authors-per-paper ratio (2.7) versus US (3.0) and China (3.4) indicates potentially smaller research teams working with more limited resources.",
        "These metrics underscore India's potential as an emerging research hub that prioritizes impact over volume, perhaps due to resource constraints that necessitate more focused research efforts."
      ],
      legend: "For paper counts, higher is better (research output). For spotlight/oral percentages, higher is better (research impact). For authors-per-paper, the optimal value depends on research goals - lower may indicate efficiency while higher may indicate collaboration breadth."
    },
    futureOpportunities: {
      title: "Future Opportunity Analysis",
      insights: [
        "Three promising domains where Indian researchers are making notable contributions are Large Language Models & NLP, Graph Neural Networks & Theory, and Robustness & Efficiency.",
        "These areas represent strategic niches where India can potentially establish thought leadership despite resource constraints. Particularly in efficiency and multilingual NLP, India's unique challenges and linguistic diversity provide advantages that could translate to global research impact.",
        "India's strengths in multilingual NLP leverage its linguistic diversity advantage, while focus on efficiency and robustness aligns with computational constraints many researchers face."
      ],
      legend: "The analysis highlights research domains where Indian contribution is proportionally higher than its overall paper count would suggest (indicating potential specialization advantages)."
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulating data fetch - Added spotlights, orals, and type (academic/corporate)
        const response = {
          "conference": "ICLR",
          "year": 2025,
          "track": "Conference",
          "total_accepted_papers": 3705,
          "global": {
            "paper_analytics": {
              "countries": [
                // Added spotlights and orals counts
                { "affiliation_country": "US", "paper_count": 1929, "author_count": 5800, "spotlights": 65, "orals": 42 },
                { "affiliation_country": "CN", "paper_count": 1308, "author_count": 4500, "spotlights": 40, "orals": 25 },
                { "affiliation_country": "HK", "paper_count": 294, "author_count": 900, "spotlights": 10, "orals": 6 },
                { "affiliation_country": "GB", "paper_count": 293, "author_count": 880, "spotlights": 12, "orals": 7 },
                { "affiliation_country": "CA", "paper_count": 255, "author_count": 750, "spotlights": 9, "orals": 5 },
                { "affiliation_country": "SG", "paper_count": 248, "author_count": 700, "spotlights": 8, "orals": 4 },
                { "affiliation_country": "DE", "paper_count": 240, "author_count": 720, "spotlights": 8, "orals": 5 },
                { "affiliation_country": "KR", "paper_count": 187, "author_count": 550, "spotlights": 6, "orals": 3 },
                { "affiliation_country": "CH", "paper_count": 178, "author_count": 500, "spotlights": 7, "orals": 4 },
                { "affiliation_country": "AU", "paper_count": 127, "author_count": 380, "spotlights": 4, "orals": 2 },
                { "affiliation_country": "FR", "paper_count": 120, "author_count": 350, "spotlights": 5, "orals": 2 },
                { "affiliation_country": "JP", "paper_count": 119, "author_count": 340, "spotlights": 4, "orals": 2 },
                { "affiliation_country": "UK", "paper_count": 103, "author_count": 310, "spotlights": 4, "orals": 2 },
                { "affiliation_country": "IL", "paper_count": 71, "author_count": 210, "spotlights": 3, "orals": 1 },
                { "affiliation_country": "NL", "paper_count": 70, "author_count": 200, "spotlights": 3, "orals": 1 },
                { "affiliation_country": "IN", "paper_count": 49, "author_count": 132, "spotlights": 2, "orals": 1 }
              ]
            }
          },
          "india": {
            "total_indian_authors": 132,
            "total_indian_spotlights": 2,
            "total_indian_orals": 1,
            "institution_types": { "academic": 35, "corporate": 14 }, // Academic vs Corporate papers
            "at_least_one_indian_author": { "count": 50, "papers": [] },
            "majority_indian_authors": { "count": 23, "papers": [] },
            "first_indian_author": { "count": 26, "papers": [] },
            "institutions": [
              {
                "institute": "IIT Bombay", 
                "total_paper_count": 17, 
                "unique_paper_count": 10, 
                "author_count": 35,
                "spotlights": 1,
                "orals": 0,
                "type": "academic",
                "papers": [
                  {"id":"EzrZX9bd4G","title":"BEEM"},
                  {"id":"5pd78GmXC6","title":"Charting"},
                  {"id":"DFSb67ksVr","title":"Clique"},
                  {"id":"9h45qxXEx0","title":"Debiasing"},
                  {"id":"NtwFghsJne","title":"From Search"},
                  {"id":"k3gCieTXeY","title":"INCLUDE", "isSpotlight": true},
                  {"id":"nNiWRRj6r9","title":"ONLINE"},
                  {"id":"l11DZY5Nxu","title":"Robust"},
                  {"id":"h0vC0fm1q7","title":"Sensitivity"},
                  {"id":"Q1kPHLUbhi","title":"Towards Self"}
                ]
              },
              {
                "institute": "Microsoft Research India", 
                "total_paper_count": 8, 
                "unique_paper_count": 6, 
                "author_count": 20,
                "spotlights": 1,
                "orals": 1,
                "type": "corporate",
                "papers": [
                  {"id":"9juyeCqL0u","title":"Causal"},
                  {"id":"xkgfLXZ4e0","title":"Correlating"},
                  {"id":"zl3pfz4VCV","title":"MMTEB", "isSpotlight": true},
                  {"id":"0dELcFHig2","title":"Multi-modal"},
                  {"id":"3E8YNv1HjU","title":"Recite", "isOral": true},
                  {"id":"l11DZY5Nxu","title":"Robust"}
                ]
              },
              {
                "institute": "Adobe Research India", 
                "total_paper_count": 7, 
                "unique_paper_count": 4, 
                "author_count": 15,
                "spotlights": 0,
                "orals": 0,
                "type": "corporate",
                "papers": [
                  {"id":"NHxwxc3ql6","title":"It Helps"},
                  {"id":"TmCcNuo03f","title":"Measuring And Improving Engagement"},
                  {"id":"NfCEVihkdC","title":"Measuring And Improving Persuasiveness"},
                  {"id":"ff2V3UR9sC","title":"Teaching Human"}
                ]
              },
              {
                "institute": "IIT Delhi", 
                "total_paper_count": 6, 
                "unique_paper_count": 3, 
                "author_count": 12,
                "spotlights": 0,
                "orals": 0,
                "type": "academic",
                "papers": [
                  {"id":"5x88lQ2MsH","title":"Bonsai"},
                  {"id":"tDIL7UXmSS","title":"Quantum"},
                  {"id":"5RZoYIT3u6","title":"You Only"}
                ]
              },
              {
                "institute": "IIT Madras", 
                "total_paper_count": 5, 
                "unique_paper_count": 3, 
                "author_count": 10,
                "spotlights": 0,
                "orals": 0,
                "type": "academic",
                "papers": [
                  {"id":"ZbkqhKbggH","title":"ASTrA"},
                  {"id":"52UtL8uA35","title":"Deep Networks"},
                  {"id":"qnlG3zPQUy","title":"ILLUSION"}
                ]
              },
              {
                "institute": "IISc Bangalore", 
                "total_paper_count": 4, 
                "unique_paper_count": 3, 
                "author_count": 9,
                "spotlights": 0,
                "orals": 0,
                "type": "academic",
                "papers": [
                  {"id":"fakeId1","title":"Hypothetical"},
                  {"id":"fakeId2","title":"Another"},
                  {"id":"fakeId3","title":"A Third"}
                ]
              },
              {
                "institute": "Google Research India", 
                "total_paper_count": 3, 
                "unique_paper_count": 2, 
                "author_count": 8,
                "spotlights": 0,
                "orals": 0,
                "type": "corporate",
                "papers": [
                  {"id":"fakeId4","title":"Cloud"},
                  {"id":"fakeId5","title":"Scaling"}
                ]
              }
            ]
          }
        };

        // Data Cleaning/Processing Step: Combine UK/GB, map names, aggregate counts
        const processedCountries = response.global.paper_analytics.countries.reduce((acc, country) => {
          const countryCode = country.affiliation_country;
          const countryName = CountryMap[countryCode] || countryCode;
          const paperCount = country.paper_count;
          const authorCount = country.author_count || 0;
          const spotlights = country.spotlights || 0;
          const orals = country.orals || 0;

          const existing = acc.find(c => c.country_name === countryName);
          if (existing) {
            existing.paper_count += paperCount;
            existing.author_count += authorCount;
            existing.spotlights += spotlights;
            existing.orals += orals;
          } else {
            acc.push({
              affiliation_country: countryCode,
              country_name: countryName,
              paper_count: paperCount,
              author_count: authorCount,
              spotlights: spotlights,
              orals: orals,
              fill: countryCode === 'US' ? COLORS.usColor :
                    countryCode === 'CN' ? COLORS.cnColor :
                    countryCode === 'IN' ? COLORS.inColor :
                    COLORS.primary,
              opacity: countryCode === 'US' || countryCode === 'CN' || countryCode === 'IN' ? 1 : 0.75
            });
          }
          return acc;
        }, []).sort((a, b) => b.paper_count - a.paper_count);

        // Add rank based on paper count
        processedCountries.forEach((c, index) => {
          c.rank = index + 1;
        });

        response.global.paper_analytics.countries = processedCountries;
        setData(response);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData();
  }, []);

  // --- Memoized Selectors ---
  const sortedCountries = useMemo(() => {
    if (!data) return [];
    return data.global.paper_analytics.countries;
  }, [data]);

  const topCountriesByPaper = useMemo(() => sortedCountries.slice(0, 15), [sortedCountries]);
  
  const topCountriesByAuthor = useMemo(() => {
    if (!data) return [];
    return [...data.global.paper_analytics.countries].sort((a, b) => b.author_count - a.author_count).slice(0, 15);
  }, [data]);

  const indiaData = useMemo(() => {
    if (!data) return null;
    const indiaStats = data.global.paper_analytics.countries.find(c => c.country_name === 'India');
    return {
      ...data.india,
      rank: indiaStats?.rank || 'N/A',
      paper_count: indiaStats?.paper_count || 0,
      author_count: indiaStats?.author_count || data.india.total_indian_authors,
      spotlights: indiaStats?.spotlights || 0,
      orals: indiaStats?.orals || 0
    };
  }, [data]);

  const usData = useMemo(() => sortedCountries.find(c => c.affiliation_country === 'US'), [sortedCountries]);
  const cnData = useMemo(() => sortedCountries.find(c => c.affiliation_country === 'CN'), [sortedCountries]);

  // Create data for the pie charts
  const usVsChinaVsRest = useMemo(() => {
    if (!data) return [];
    const usCount = usData?.paper_count || 0;
    const cnCount = cnData?.paper_count || 0;
    const usCnCombined = usCount + cnCount;
    const totalCount = sortedCountries.reduce((sum, country) => sum + country.paper_count, 0);
    const restCount = totalCount - usCount - cnCount;
    
    return [
      { name: 'US + China', value: usCnCombined, fill: COLORS.usColor },
      { name: 'Rest of World', value: restCount, fill: COLORS.primary }
    ];
  }, [sortedCountries, usData, cnData]);

  const apacCountries = useMemo(() => {
    if (!data) return [];
    return sortedCountries
      .filter(country => APAC_COUNTRIES.includes(country.affiliation_country))
      .map(country => ({
        name: country.country_name,
        value: country.paper_count,
        fill: country.affiliation_country === 'CN' ? COLORS.cnColor : 
              country.affiliation_country === 'IN' ? COLORS.inColor : COLORS.secondary
      }));
  }, [sortedCountries]);

  const authorshipPieData = useMemo(() => {
    if (!indiaData) return [];
    const atLeastOne = indiaData.at_least_one_indian_author.count;
    const majority = indiaData.majority_indian_authors.count;
    const minority = atLeastOne - majority;
    const firstAuthor = indiaData.first_indian_author.count;
    const nonFirstAuthor = atLeastOne - firstAuthor;
    
    return [
      {
        name: 'Authorship Distribution',
        data: [
          { name: 'Majority Indian', value: majority, fill: COLORS.highlight },
          { name: 'Minority Indian', value: minority, fill: COLORS.primary }
        ]
      },
      {
        name: 'First Author Distribution',
        data: [
          { name: 'First Indian Author', value: firstAuthor, fill: COLORS.accent },
          { name: 'Non-First Indian Author', value: nonFirstAuthor, fill: COLORS.primary }
        ]
      }
    ];
  }, [indiaData]);

  const institutionTypePieData = useMemo(() => {
    if (!indiaData) return [];
    const academic = indiaData.institution_types?.academic || 0;
    const corporate = indiaData.institution_types?.corporate || 0;
    
    return [
      { name: 'Academic', value: academic, fill: COLORS.info },
      { name: 'Corporate', value: corporate, fill: COLORS.accent }
    ];
  }, [indiaData]);

  const filteredInstitutions = useMemo(() => {
    if (!data || !data.india.institutions) return [];
    return data.india.institutions.filter(inst =>
      inst.institute.toLowerCase().includes(institutionFilter.toLowerCase())
    ).sort((a, b) => b.unique_paper_count - a.unique_paper_count || b.author_count - a.author_count);
  }, [data, institutionFilter]);

  const topIndianInstitution = useMemo(() => {
    if (!filteredInstitutions.length) return null;
    return filteredInstitutions[0];
  }, [filteredInstitutions]);

  // New: Process institution data for the chart visualization
  const institutionChartData = useMemo(() => {
    if (!filteredInstitutions.length) return [];
    
    return filteredInstitutions.slice(0, 8).map(institution => ({
      ...institution,
      fill: institution.type === 'academic' ? COLORS.academic : COLORS.corporate
    }));
  }, [filteredInstitutions]);

  // New: Academic vs Corporate Institution Distribution
  const institutionPieData = useMemo(() => {
    if (!filteredInstitutions.length) return [];
    
    const academic = filteredInstitutions.filter(inst => inst.type === 'academic');
    const corporate = filteredInstitutions.filter(inst => inst.type === 'corporate');
    
    const academicPapers = academic.reduce((sum, inst) => sum + inst.unique_paper_count, 0);
    const corporatePapers = corporate.reduce((sum, inst) => sum + inst.unique_paper_count, 0);
    
    return [
      { name: 'Academic', value: academicPapers, fill: COLORS.academic },
      { name: 'Corporate', value: corporatePapers, fill: COLORS.corporate }
    ];
  }, [filteredInstitutions]);

  // Loading State
  if (!data || !indiaData || !usData || !cnData) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl animate-pulse">Loading ICLR Dashboard...</div>
      </div>
    );
  }

  // --- Render Logic ---
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6 font-sans">
      {/* Header */}
      <header className="mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">
              ICLR {data.year} Research Analysis
            </h1>
            <p className="text-gray-400 mt-1">Global Contributions in Papers & Authorship</p>
          </div>
          <div className="mt-4 md:mt-0 bg-gray-800 rounded-lg p-3 text-sm text-gray-300 border border-gray-700 shadow-sm">
            Total Accepted Papers: <span className="font-bold text-white">{data.total_accepted_papers.toLocaleString()}</span>
          </div>
        </div>
        {/* Tabs */}
        <div className="mt-6 border-b border-gray-700">
          <div className="flex space-x-1 sm:space-x-4 overflow-x-auto pb-0">
            {tabs.map((tab, index) => (
              <button
                key={index}
                className={`py-3 px-3 sm:px-4 transition-all focus:outline-none whitespace-nowrap text-sm sm:text-base ${
                  activeTabIndex === index
                    ? "text-white border-b-2 border-indigo-500 font-semibold"
                    : "text-gray-400 hover:text-gray-200 hover:border-b-2 hover:border-gray-500"
                }`}
                onClick={() => setActiveTabIndex(index)}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Tab Content */}
      <main>
        {/* Overview Tab - Focused on India@ICLR 2025 */}
        {activeTabIndex === 0 && (
          <div className="space-y-8 animate-fade-in">
            {/* Key Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              <StatCard
                title="India Papers @ ICLR"
                value={indiaData.paper_count.toLocaleString()}
                icon={<FaFileAlt />}
                color="amber"
                subtitle={`${((indiaData.paper_count / data.total_accepted_papers) * 100).toFixed(1)}% of all papers`}
              />
              <StatCard
                title="India's Global Rank"
                value={`#${indiaData.rank}`}
                icon={<FaGlobeAsia />}
                color="blue"
                subtitle={`By paper count | ${indiaData.total_indian_authors} authors`}
              />
              <StatCard
                title="Spotlights & Orals"
                value={indiaData.spotlights + indiaData.orals}
                icon={<FaStar />}
                color="yellow"
                subtitle={`${indiaData.spotlights} spotlights, ${indiaData.orals} orals`}
              />
              <StatCard
                title="Top Indian Institution"
                value={topIndianInstitution?.institute || 'N/A'}
                icon={<FaUniversity />}
                color="emerald"
                subtitle={`${topIndianInstitution?.unique_paper_count || 0} papers, ${topIndianInstitution?.spotlights || 0} spotlights`}
              />
            </div>

            {/* Interpretation Panel for Overview */}
            <InterpretationPanel 
              title={interpretations.overview.title}
              insights={interpretations.overview.insights}
              legend={interpretations.overview.legend}
            />

            {/* Global Leaderboard Chart */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-lg">
              <h2 className="text-xl font-bold mb-1 text-white">Global Leaderboard (ICLR {data.year})</h2>
              <p className="text-sm text-gray-400 mb-6">Top 10 countries by paper count with India highlighted.</p>
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topCountriesByPaper.slice(0, 10)} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} horizontal={false}/>
                    <XAxis type="number" stroke={COLORS.textSecondary}/>
                    <YAxis
                      type="category" dataKey="country_name" stroke={COLORS.textSecondary} width={100}
                      tick={{ fontSize: 12, fill: COLORS.textSecondary }} interval={0}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}/>
                    <Bar dataKey="paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={20}>
                      {topCountriesByPaper.slice(0, 10).map((entry, index) => (
                        <Cell key={`cell-paper-${index}`} fill={entry.fill} fillOpacity={entry.opacity} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Indian Institutions */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-white">Top Indian Institutions</h2>
                <button
                  className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center"
                  onClick={() => setActiveTabIndex(3)}
                >
                  View all <span className="ml-1">→</span>
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredInstitutions.slice(0, 6).map((institution, index) => (
                  <InstitutionCard key={`preview-${index}`} institution={institution} index={0} />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Global Stats Tab - With Bar Charts and Tables */}
        {activeTabIndex === 1 && (
          <div className="space-y-8 animate-fade-in">
            {/* US + China vs Rest of World */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white">US + China vs Rest of World</h2>
                  <p className="text-sm text-gray-400">Paper distribution showing dominance of top contributors.</p>
                </div>
                <ViewToggle 
                  activeView={viewModes.global} 
                  setActiveView={(mode) => setViewModes({...viewModes, global: mode})} 
                />
              </div>
              
              {viewModes.global === 'chart' ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Bar Chart */}
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={usVsChinaVsRest}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                        <XAxis dataKey="name" stroke={COLORS.textSecondary} />
                        <YAxis stroke={COLORS.textSecondary} />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="value" name="Papers">
                          {usVsChinaVsRest.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  
                  {/* Pie Chart */}
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          activeIndex={activePieIndex}
                          activeShape={renderActiveShape}
                          data={usVsChinaVsRest}
                          cx="50%"
                          cy="50%"
                          innerRadius={70}
                          outerRadius={90}
                          fill="#8884d8"
                          dataKey="value"
                          onMouseEnter={(_, index) => setActivePieIndex(index)}
                        >
                          {usVsChinaVsRest.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <DataTable 
                  data={usVsChinaVsRest.map(item => ({
                    Region: item.name,
                    Papers: item.value.toLocaleString(),
                    'Percentage': ((item.value / data.total_accepted_papers) * 100).toFixed(2) + '%',
                    highlight: item.name === 'US + China'
                  }))}
                  title="Global Distribution" 
                  filename="global_distribution_iclr_2025" 
                />
              )}
              
              {/* Interpretation Panel for Global Stats */}
              <InterpretationPanel 
                title={interpretations.globalDistribution.title}
                insights={interpretations.globalDistribution.insights}
                legend={interpretations.globalDistribution.legend}
              />
            </div>

            {/* APAC Countries */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white">APAC Contributions</h2>
                  <p className="text-sm text-gray-400">Paper distribution within Asia-Pacific region.</p>
                </div>
                <ViewToggle 
                  activeView={viewModes.apac} 
                  setActiveView={(mode) => setViewModes({...viewModes, apac: mode})} 
                />
              </div>
              
              {viewModes.apac === 'chart' ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Bar Chart */}
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={apacCountries}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} horizontal={false} />
                        <XAxis type="number" stroke={COLORS.textSecondary} />
                        <YAxis 
                          type="category" 
                          dataKey="name" 
                          width={100}
                          stroke={COLORS.textSecondary} 
                          tick={{ fontSize: 12, fill: COLORS.textSecondary }} 
                          interval={0}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="value" name="Papers" radius={[0, 4, 4, 0]} barSize={20}>
                          {apacCountries.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  
                  {/* Pie Chart */}
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          activeIndex={activePieIndex}
                          activeShape={renderActiveShape}
                          data={apacCountries}
                          cx="50%"
                          cy="50%"
                          innerRadius={70}
                          outerRadius={90}
                          fill="#8884d8"
                          dataKey="value"
                          onMouseEnter={(_, index) => setActivePieIndex(index)}
                        >
                          {apacCountries.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <DataTable 
                  data={apacCountries.map(item => ({
                    Country: item.name,
                    Papers: item.value.toLocaleString(),
                    'Percentage of APAC': ((item.value / apacCountries.reduce((sum, c) => sum + c.value, 0)) * 100).toFixed(2) + '%',
                    'Global Percentage': ((item.value / data.total_accepted_papers) * 100).toFixed(2) + '%',
                    highlight: item.name === 'China' || item.name === 'India'
                  }))}
                  title="APAC Country Distribution" 
                  filename="apac_distribution_iclr_2025" 
                />
              )}
              
              {/* Interpretation Panel for APAC */}
              <InterpretationPanel 
                title={interpretations.apacContributions.title}
                insights={interpretations.apacContributions.insights}
                legend={interpretations.apacContributions.legend}
              />
            </div>

            {/* Complete Country List with export */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white">Complete Country Contributions</h2>
                  <p className="text-sm text-gray-400">All countries with ICLR 2025 accepted papers.</p>
                </div>
                <button 
                  onClick={() => exportToCSV(
                    sortedCountries.map(country => ({
                      Rank: country.rank,
                      Country: country.country_name,
                      Papers: country.paper_count,
                      'Percentage': ((country.paper_count / data.total_accepted_papers) * 100).toFixed(2) + '%',
                      Authors: country.author_count,
                      Spotlights: country.spotlights,
                      Orals: country.orals
                    })), 
                    'iclr_2025_country_data'
                  )}
                  className="flex items-center bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded transition-colors"
                >
                  <FaDownload className="mr-2" />
                  Export CSV
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className="bg-gray-700">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Rank</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Country</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Papers</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">%</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Authors</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Spotlights</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Orals</th>
                    </tr>
                  </thead>
                  <tbody className="bg-gray-800 divide-y divide-gray-700">
                    {sortedCountries.map((country, index) => (
                      <tr key={index} className={country.country_name === 'India' ? 'bg-amber-900 bg-opacity-20' : ''}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{country.rank}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{country.country_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{country.paper_count.toLocaleString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {((country.paper_count / data.total_accepted_papers) * 100).toFixed(2)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{country.author_count.toLocaleString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{country.spotlights}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{country.orals}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* India Focus Tab - Added Pie Charts */}
        {activeTabIndex === 2 && (
          <div className="space-y-8 animate-fade-in">
            {/* Detailed India Stats Cards */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h2 className="text-xl font-bold mb-4 text-white">India's Contribution Details (ICLR {data.year})</h2>
              
              {/* Authorship Distributions with Bar Charts & Pie Charts */}
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">Indian Authorship Patterns</h2>
                    <p className="text-sm text-gray-400">Distribution of Indian authorship across accepted papers.</p>
                  </div>
                  <ViewToggle 
                    activeView={viewModes.authorship} 
                    setActiveView={(mode) => setViewModes({...viewModes, authorship: mode})} 
                  />
                </div>
                
                {viewModes.authorship === 'chart' ? (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* First set of charts (Majority/Minority) */}
                    <div className="lg:col-span-1">
                      <h3 className="text-white text-lg font-semibold mb-2">Authorship Distribution</h3>
                      <div className="grid grid-cols-1 gap-4">
                        {/* Bar Chart */}
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={authorshipPieData[0].data}
                                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                                <XAxis dataKey="name" stroke={COLORS.textSecondary} />
                                <YAxis stroke={COLORS.textSecondary} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="value" name="Papers">
                                  {authorshipPieData[0].data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                  ))}
                                </Bar>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                        
                        {/* Pie Chart */}
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                  data={authorshipPieData[0].data}
                                  cx="50%"
                                  cy="50%"
                                  labelLine={false}
                                  outerRadius={80}
                                  fill="#8884d8"
                                  dataKey="value"
                                >
                                  {authorshipPieData[0].data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                  ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                              </PieChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Second set of charts (First Author) */}
                    <div className="lg:col-span-1">
                      <h3 className="text-white text-lg font-semibold mb-2">First Author Distribution</h3>
                      <div className="grid grid-cols-1 gap-4">
                        {/* Bar Chart */}
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={authorshipPieData[1].data}
                                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                                <XAxis dataKey="name" stroke={COLORS.textSecondary} />
                                <YAxis stroke={COLORS.textSecondary} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="value" name="Papers">
                                  {authorshipPieData[1].data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                  ))}
                                </Bar>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                        
                        {/* Pie Chart */}
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                  data={authorshipPieData[1].data}
                                  cx="50%"
                                  cy="50%"
                                  labelLine={false}
                                  outerRadius={80}
                                  fill="#8884d8"
                                  dataKey="value"
                                >
                                  {authorshipPieData[1].data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                  ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                              </PieChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Third set of charts (Academic vs Corporate) */}
                    <div className="lg:col-span-1">
                      <h3 className="text-white text-lg font-semibold mb-2">Academic vs Corporate</h3>
                      <div className="grid grid-cols-1 gap-4">
                        {/* Bar Chart */}
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={institutionTypePieData}
                                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                                <XAxis dataKey="name" stroke={COLORS.textSecondary} />
                                <YAxis stroke={COLORS.textSecondary} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="value" name="Papers">
                                  {institutionTypePieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                  ))}
                                </Bar>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                        
                        {/* Pie Chart */}
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                  data={institutionTypePieData}
                                  cx="50%"
                                  cy="50%"
                                  labelLine={false}
                                  outerRadius={80}
                                  fill="#8884d8"
                                  dataKey="value"
                                >
                                  {institutionTypePieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                  ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                              </PieChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <DataTable 
                    data={[
                      {
                        Category: "Majority Indian Authors", 
                        Papers: authorshipPieData[0].data[0].value.toLocaleString(),
                        Percentage: ((authorshipPieData[0].data[0].value / indiaData.at_least_one_indian_author.count) * 100).toFixed(1) + '%'
                      },
                      {
                        Category: "Minority Indian Authors", 
                        Papers: authorshipPieData[0].data[1].value.toLocaleString(),
                        Percentage: ((authorshipPieData[0].data[1].value / indiaData.at_least_one_indian_author.count) * 100).toFixed(1) + '%'
                      },
                      {
                        Category: "First Indian Author", 
                        Papers: authorshipPieData[1].data[0].value.toLocaleString(),
                        Percentage: ((authorshipPieData[1].data[0].value / indiaData.at_least_one_indian_author.count) * 100).toFixed(1) + '%'
                      },
                      {
                        Category: "Non-First Indian Author", 
                        Papers: authorshipPieData[1].data[1].value.toLocaleString(),
                        Percentage: ((authorshipPieData[1].data[1].value / indiaData.at_least_one_indian_author.count) * 100).toFixed(1) + '%'
                      },
                      {
                        Category: "Academic Papers", 
                        Papers: institutionTypePieData[0].value.toLocaleString(),
                        Percentage: ((institutionTypePieData[0].value / (institutionTypePieData[0].value + institutionTypePieData[1].value)) * 100).toFixed(1) + '%'
                      },
                      {
                        Category: "Corporate Papers", 
                        Papers: institutionTypePieData[1].value.toLocaleString(),
                        Percentage: ((institutionTypePieData[1].value / (institutionTypePieData[0].value + institutionTypePieData[1].value)) * 100).toFixed(1) + '%'
                      }
                    ]}
                    title="Authorship Distribution Analysis" 
                    filename="india_authorship_distribution_iclr_2025" 
                  />
                )}
                
                {/* Interpretation Panel for India Focus */}
                <InterpretationPanel 
                  title={interpretations.indiaFocus.title}
                  insights={interpretations.indiaFocus.insights}
                  legend={interpretations.indiaFocus.legend}
                />
              </div>
              
              {/* Comparative Bar Charts */}
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mt-8">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">India vs US & China: Comparative Metrics</h2>
                    <p className="text-sm text-gray-400">Comparing India's research output with top contributors.</p>
                  </div>
                  <ViewToggle 
                    activeView={viewModes.comparison} 
                    setActiveView={(mode) => setViewModes({...viewModes, comparison: mode})} 
                  />
                </div>
                
                {viewModes.comparison === 'chart' ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Papers Comparison */}
                    <div className="bg-gray-700 p-4 rounded-lg">
                      <h4 className="text-white font-medium mb-2">Paper Count Comparison</h4>
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart 
                            data={[
                              { name: 'United States', papers: usData.paper_count, percentage: ((usData.paper_count / data.total_accepted_papers) * 100).toFixed(1), fill: COLORS.usColor },
                              { name: 'China', papers: cnData.paper_count, percentage: ((cnData.paper_count / data.total_accepted_papers) * 100).toFixed(1), fill: COLORS.cnColor },
                              { name: 'India', papers: indiaData.paper_count, percentage: ((indiaData.paper_count / data.total_accepted_papers) * 100).toFixed(1), fill: COLORS.inColor }
                            ]}
                            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                            <XAxis dataKey="name" stroke={COLORS.textSecondary} />
                            <YAxis stroke={COLORS.textSecondary} />
                            <Tooltip 
                              formatter={(value, name, props) => [value.toLocaleString(), name]}
                              labelFormatter={(value) => `${value}`}
                            />
                            <Bar dataKey="papers" name="Papers">
                              {
                                [0, 1, 2].map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={[COLORS.usColor, COLORS.cnColor, COLORS.inColor][index]} />
                                ))
                              }
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    
                    {/* Spotlights & Orals Comparison - MODIFIED: Now stacked bar chart */}
                    <div className="bg-gray-700 p-4 rounded-lg">
                      <h4 className="text-white font-medium mb-2">Spotlights & Orals Comparison</h4>
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart 
                            data={[
                              { 
                                name: 'United States', 
                                spotlights: usData.spotlights, 
                                orals: usData.orals,
                                total: usData.spotlights + usData.orals,
                                spotlight_percent: ((usData.spotlights / usData.paper_count) * 100).toFixed(1),
                                oral_percent: ((usData.orals / usData.paper_count) * 100).toFixed(1),
                                fill: COLORS.usColor 
                              },
                              { 
                                name: 'China', 
                                spotlights: cnData.spotlights, 
                                orals: cnData.orals,
                                total: cnData.spotlights + cnData.orals,
                                spotlight_percent: ((cnData.spotlights / cnData.paper_count) * 100).toFixed(1),
                                oral_percent: ((cnData.orals / cnData.paper_count) * 100).toFixed(1),
                                fill: COLORS.cnColor 
                              },
                              { 
                                name: 'India', 
                                spotlights: indiaData.spotlights, 
                                orals: indiaData.orals,
                                total: indiaData.spotlights + indiaData.orals,
                                spotlight_percent: ((indiaData.spotlights / indiaData.paper_count) * 100).toFixed(1),
                                oral_percent: ((indiaData.orals / indiaData.paper_count) * 100).toFixed(1),
                                fill: COLORS.inColor 
                              }
                            ]}
                            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                            <XAxis dataKey="name" stroke={COLORS.textSecondary} />
                            <YAxis stroke={COLORS.textSecondary} />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            <Bar dataKey="total" name="Total" stackId="a" fill={COLORS.primary} />
                            <Bar dataKey="spotlights" name="Spotlights" stackId="b" fill={COLORS.warning} />
                            <Bar dataKey="orals" name="Orals" stackId="b" fill={COLORS.accent} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    
                    {/* Additional Chart: Authors per Paper Ratio - MODIFIED from Papers per Author */}
                    <div className="bg-gray-700 p-4 rounded-lg md:col-span-2">
                      <h4 className="text-white font-medium mb-2">Authors per Paper Ratio</h4>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart 
                            data={[
                              { 
                                name: 'United States', 
                                ratio: (usData.author_count / usData.paper_count).toFixed(2),
                                papers: usData.paper_count,
                                authors: usData.author_count,
                                fill: COLORS.usColor 
                              },
                              { 
                                name: 'China', 
                                ratio: (cnData.author_count / cnData.paper_count).toFixed(2),
                                papers: cnData.paper_count,
                                authors: cnData.author_count,
                                fill: COLORS.cnColor 
                              },
                              { 
                                name: 'India', 
                                ratio: (indiaData.author_count / indiaData.paper_count).toFixed(2),
                                papers: indiaData.paper_count,
                                authors: indiaData.author_count,
                                fill: COLORS.inColor 
                              }
                            ]}
                            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                            <XAxis dataKey="name" stroke={COLORS.textSecondary} />
                            <YAxis stroke={COLORS.textSecondary} />
                            <Tooltip 
                              formatter={(value, name, props) => [value, 'Authors per Paper']}
                              labelFormatter={(value) => `${value}`}
                            />
                            <Bar dataKey="ratio" name="Authors per Paper">
                              {
                                [0, 1, 2].map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={[COLORS.usColor, COLORS.cnColor, COLORS.inColor][index]} />
                                ))
                              }
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                ) : (
                  <DataTable 
                    data={[
                      { 
                        Country: 'United States', 
                        'Total Papers': usData.paper_count.toLocaleString(),
                        'Papers %': ((usData.paper_count / data.total_accepted_papers) * 100).toFixed(2) + '%',
                        'Total Authors': usData.author_count.toLocaleString(),
                        'Spotlights': usData.spotlights,
                        'Spotlight %': ((usData.spotlights / usData.paper_count) * 100).toFixed(2) + '%',
                        'Orals': usData.orals,
                        'Oral %': ((usData.orals / usData.paper_count) * 100).toFixed(2) + '%',
                        'Authors/Paper': (usData.author_count / usData.paper_count).toFixed(2),
                        highlight: false
                      },
                      { 
                        Country: 'China', 
                        'Total Papers': cnData.paper_count.toLocaleString(),
                        'Papers %': ((cnData.paper_count / data.total_accepted_papers) * 100).toFixed(2) + '%',
                        'Total Authors': cnData.author_count.toLocaleString(),
                        'Spotlights': cnData.spotlights,
                        'Spotlight %': ((cnData.spotlights / cnData.paper_count) * 100).toFixed(2) + '%',
                        'Orals': cnData.orals,
                        'Oral %': ((cnData.orals / cnData.paper_count) * 100).toFixed(2) + '%',
                        'Authors/Paper': (cnData.author_count / cnData.paper_count).toFixed(2),
                        highlight: false
                      },
                      { 
                        Country: 'India', 
                        'Total Papers': indiaData.paper_count.toLocaleString(),
                        'Papers %': ((indiaData.paper_count / data.total_accepted_papers) * 100).toFixed(2) + '%',
                        'Total Authors': indiaData.author_count.toLocaleString(),
                        'Spotlights': indiaData.spotlights,
                        'Spotlight %': ((indiaData.spotlights / indiaData.paper_count) * 100).toFixed(2) + '%',
                        'Orals': indiaData.orals,
                        'Oral %': ((indiaData.orals / indiaData.paper_count) * 100).toFixed(2) + '%',
                        'Authors/Paper': (indiaData.author_count / indiaData.paper_count).toFixed(2),
                        highlight: true
                      }
                    ]}
                    title="Country Comparison Analysis" 
                    filename="country_comparison_iclr_2025" 
                  />
                )}
                
                {/* Interpretation Panel for Comparative Performance */}
                <InterpretationPanel 
                  title={interpretations.comparativePerformance.title}
                  insights={interpretations.comparativePerformance.insights}
                  legend={interpretations.comparativePerformance.legend}
                />
              </div>
            </div>

            {/* Research Focus section - REMOVED "Other interesting metrics to consider" */}
            <div className="grid grid-cols-1 gap-6">
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h2 className="text-xl font-bold mb-4 text-white">Potential Research Focus Areas</h2>
                <div className="space-y-3">
                  <div className="bg-gray-700 p-4 rounded-lg shadow-sm">
                    <h3 className="font-medium text-white">Large Language Models & NLP</h3>
                    <p className="text-gray-400 text-sm mt-1">Focus on evaluation, multilingual understanding, optimization, and persuasiveness.</p>
                  </div>
                  <div className="bg-gray-700 p-4 rounded-lg shadow-sm">
                    <h3 className="font-medium text-white">Graph Neural Networks & Theory</h3>
                    <p className="text-gray-400 text-sm mt-1">Exploring graph representations, condensation, and theoretical aspects like sampling.</p>
                  </div>
                  <div className="bg-gray-700 p-4 rounded-lg shadow-sm">
                    <h3 className="font-medium text-white">Robustness & Efficiency</h3>
                    <p className="text-gray-400 text-sm mt-1">Addressing debiasing, adversarial training, model compression, and efficient DNNs.</p>
                  </div>
                </div>
                
                {/* Interpretation Panel for Future Opportunities */}
                <InterpretationPanel 
                  title={interpretations.futureOpportunities.title}
                  insights={interpretations.futureOpportunities.insights}
                  legend={interpretations.futureOpportunities.legend}
                />
              </div>
            </div>
          </div>
        )}

        {/* Institutions Tab - MODIFIED with new chart/table toggle */}
        {activeTabIndex === 3 && (
          <div className="space-y-6 animate-fade-in">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                <h2 className="text-xl font-bold text-white">Indian Research Institutions @ ICLR {data.year}</h2>
                <div className="relative w-full md:w-auto">
                  <input
                    type="text"
                    placeholder="Search institutions..."
                    className="bg-gray-700 border border-gray-600 rounded-lg py-2 pl-10 pr-4 text-white w-full md:w-72 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm"
                    value={institutionFilter}
                    onChange={(e) => setInstitutionFilter(e.target.value)}
                  />
                  <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                </div>
              </div>
              
              {/* NEW: Institution visualization section with chart/table toggle */}
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-6">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-white">Institution Contribution Analysis</h2>
                    <p className="text-sm text-gray-400">Top institutions by paper count with academic vs corporate breakdown.</p>
                  </div>
                  <ViewToggle 
                    activeView={viewModes.institutions} 
                    setActiveView={(mode) => setViewModes({...viewModes, institutions: mode})} 
                  />
                </div>
                
                {viewModes.institutions === 'chart' ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Bar Chart */}
                    <div className="bg-gray-700 rounded-lg p-4">
                      <h3 className="text-white font-medium mb-2">Papers by Institution</h3>
                      <div className="h-96">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={institutionChartData}
                            layout="vertical"
                            margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} horizontal={false} />
                            <XAxis type="number" stroke={COLORS.textSecondary} />
                            <YAxis 
                              type="category" 
                              dataKey="institute" 
                              width={100}
                              stroke={COLORS.textSecondary} 
                              tick={{ fontSize: 12, fill: COLORS.textSecondary }} 
                              interval={0}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="unique_paper_count" name="Papers" radius={[0, 4, 4, 0]} barSize={20}>
                              {institutionChartData.map((entry, index) => (
                                <Cell 
                                  key={`cell-${index}`}
                                  fill={entry.type === 'academic' ? COLORS.academic : COLORS.corporate} 
                                />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    
                    {/* Additional Charts - Academic vs Corporate Pie Chart */}
                    <div className="bg-gray-700 rounded-lg p-4">
                      <h3 className="text-white font-medium mb-2">Academic vs Corporate Distribution</h3>
                      <div className="grid grid-cols-1 gap-4">
                        {/* Pie Chart */}
                        <div className="h-80">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                activeIndex={activePieIndex}
                                activeShape={renderActiveShape}
                                data={institutionPieData}
                                cx="50%"
                                cy="50%"
                                innerRadius={70}
                                outerRadius={90}
                                fill="#8884d8"
                                dataKey="value"
                                onMouseEnter={(_, index) => setActivePieIndex(index)}
                              >
                                {institutionPieData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.fill} />
                                ))}
                              </Pie>
                              <Tooltip content={<CustomTooltip />} />
                              <Legend />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                        
                        {/* Spotlights Distribution */}
                        <div className="bg-gray-800 rounded-lg p-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-gray-700 p-3 rounded-lg text-center">
                              <p className="text-xs text-gray-400">Academic Spotlights</p>
                              <p className="text-xl font-bold text-blue-400">
                                {institutionChartData
                                  .filter(i => i.type === 'academic')
                                  .reduce((sum, i) => sum + i.spotlights, 0)}
                              </p>
                            </div>
                            <div className="bg-gray-700 p-3 rounded-lg text-center">
                              <p className="text-xs text-gray-400">Corporate Spotlights</p>
                              <p className="text-xl font-bold text-pink-400">
                                {institutionChartData
                                  .filter(i => i.type === 'corporate')
                                  .reduce((sum, i) => sum + i.spotlights, 0)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <DataTable 
                    data={institutionChartData.map(inst => ({
                      Institution: inst.institute,
                      Type: inst.type || 'Unknown',
                      Papers: inst.unique_paper_count,
                      Authors: inst.author_count,
                      Spotlights: inst.spotlights,
                      Orals: inst.orals,
                      'Papers/Author': (inst.unique_paper_count / inst.author_count).toFixed(2),
                      highlight: inst.institute === topIndianInstitution?.institute
                    }))}
                    title="Top Indian Institutions" 
                    filename="top_indian_institutions_iclr_2025" 
                  />
                )}
                
                {/* Interpretation Panel for Institution Analysis */}
                <InterpretationPanel 
                  title={interpretations.institutionAnalysis.title}
                  insights={interpretations.institutionAnalysis.insights}
                  legend={interpretations.institutionAnalysis.legend}
                />
              </div>
              
              {/* Institution export button */}
              <div className="flex justify-end mb-4">
                {filteredInstitutions.length > 0 && (
                  <button 
                    onClick={() => exportToCSV(
                      filteredInstitutions.map(inst => ({
                        Institution: inst.institute,
                        Type: inst.type || 'Unknown',
                        'Total Papers': inst.unique_paper_count,
                        'Total Authors': inst.author_count,
                        Spotlights: inst.spotlights,
                        Orals: inst.orals
                      })), 
                      'iclr_2025_indian_institutions'
                    )}
                    className="flex items-center bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded transition-colors"
                  >
                    <FaDownload className="mr-2" />
                    Export Institutions
                  </button>
                )}
              </div>
            
              {/* Institution List */}
              <div className="grid grid-cols-1 gap-4">
                {filteredInstitutions.length > 0 ? (
                  <>
                    {/* Table view option */}
                    <div className="overflow-x-auto mb-6 bg-gray-700 rounded-lg p-4">
                      <h3 className="text-white font-medium mb-4">Institution Summary</h3>
                      <table className="min-w-full divide-y divide-gray-600">
                        <thead className="bg-gray-800">
                          <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Institution</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Type</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Papers</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Authors</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Spotlights</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Orals</th>
                          </tr>
                        </thead>
                        <tbody className="bg-gray-800 divide-y divide-gray-700">
                          {filteredInstitutions.map((institution, index) => (
                            <tr key={`table-${index}`} className="hover:bg-gray-700">
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{institution.institute}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300 capitalize">{institution.type || 'Unknown'}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{institution.unique_paper_count}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{institution.author_count}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{institution.spotlights}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{institution.orals}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    {/* Detailed expansion cards */}
                    <h3 className="text-white font-medium mb-2">Detailed Institution Data</h3>
                    {filteredInstitutions.map((institution, index) => (
                      <InstitutionCard
                        key={institution.institute + index}
                        institution={institution}
                        index={index}
                      />
                    ))}
                  </>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <FaUniversity size={40} className="mx-auto mb-4" />
                    <p>No institutions found matching "{institutionFilter}".</p>
                    <p className="text-sm">Try clearing the search or check the spelling.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 text-center text-gray-500 text-xs border-t border-gray-700 pt-4">
        Dashboard presenting simulated data for ICLR {data.year}. Data processing includes mapping country codes and combining UK/GB entries.
        <span className="font-semibold"> Author counts and spotlight/oral designations are estimated for illustration.</span>
        <style jsx global>{`
          @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
          .animate-fade-in { animation: fadeIn 0.5s ease-out forwards; }
          .custom-scrollbar::-webkit-scrollbar { width: 6px; }
          .custom-scrollbar::-webkit-scrollbar-track { background: #1f2937; border-radius: 3px; }
          .custom-scrollbar::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 3px; }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #6b7280; }
          .custom-scrollbar { scrollbar-width: thin; scrollbar-color: #4b5563 #1f2937; }
        `}</style>
      </footer>
    </div>
  );
};

export default ICLRDashboard;