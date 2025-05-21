import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  Cell
} from 'recharts';
import { CountryData } from '../../types/dashboard';

interface GlobalDistributionChartProps {
  countries: CountryData[];
  focusCountry?: CountryData;
  colorMap: {
    us: string;
    cn: string;
    focusCountry: string;
    rest: string;
    [key: string]: string;
  };
  height?: number;
  maxBars?: number;
  showFocusCountryIfOutsideMax?: boolean;
  title?: string;
}

export const GlobalDistributionChart: React.FC<GlobalDistributionChartProps> = ({
  countries,
  focusCountry,
  colorMap,
  height = 400,
  maxBars = 15,
  showFocusCountryIfOutsideMax = true,
  title
}) => {
  // Don't render if no data
  if (!countries || countries.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[300px] bg-muted/20 rounded-lg border border-border">
        <span className="text-muted-foreground">No country data available</span>
      </div>
    );
  }

  // Create chart data with top countries
  const prepareChartData = (): Array<CountryData & { fill: string }> => {
    // Get top N countries
    const topCountries = [...countries]
      .sort((a, b) => b.paper_count - a.paper_count)
      .slice(0, maxBars);
    
    // Find focus country index in top countries
    let focusCountryIndex = -1;
    if (focusCountry) {
      focusCountryIndex = topCountries.findIndex(
        country => country.affiliation_country === focusCountry.affiliation_country
      );
    }
    
    // If focus country is not in top countries but should be shown, add it at the end
    if (focusCountry && focusCountryIndex === -1 && showFocusCountryIfOutsideMax) {
      topCountries.push(focusCountry);
    }
    
    // Map colors to countries
    return topCountries.map(country => {
      let fill = colorMap.rest;
      
      if (country.affiliation_country === 'US') {
        fill = colorMap.us;
      } else if (country.affiliation_country === 'CN') {
        fill = colorMap.cn;
      } else if (focusCountry && country.affiliation_country === focusCountry.affiliation_country) {
        fill = colorMap.focusCountry;
      }
      
      return {
        ...country,
        fill
      };
    });
  };
  
  const chartData = prepareChartData();
  
  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as CountryData;
      return (
        <div className="bg-card p-2 border border-border rounded-md shadow-sm">
          <p className="text-sm font-medium">{data.country_name}</p>
          <div className="text-xs space-y-1 mt-1">
            <p>Papers: {data.paper_count}</p>
            <p>Authors: {data.author_count}</p>
            <p>Spotlights/Orals: {data.spotlights + data.orals}</p>
            <p>Global Rank: #{data.rank}</p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      {title && (
        <h4 className="text-lg font-medium text-center mb-3">{title}</h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 30, bottom: 70 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis 
            dataKey="country_name" 
            angle={-45}
            textAnchor="end"
            height={70}
            tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
          />
          <YAxis 
            label={{ 
              value: 'Papers', 
              angle: -90, 
              position: 'insideLeft',
              style: { fill: 'hsl(var(--muted-foreground))', fontSize: 12 }
            }}
            tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <ReferenceLine y={0} stroke="hsl(var(--border))" />
          <Bar 
            dataKey="paper_count" 
            name="Papers"
          >
            {chartData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.fill}
                stroke="hsl(var(--border))"
                strokeWidth={1}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};