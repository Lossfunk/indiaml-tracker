import React from 'react';
import { chartColors } from '../../utils/chart-colors';
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
      <div className="flex items-center justify-center h-full min-h-[300px] bg-muted/20 rounded-lg border border-border animate-pulse shadow-inner">
        <span className="text-muted-foreground">Geographic distribution visualization unavailable</span>
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
        <div className="bg-card p-4 border border-border rounded-lg shadow-lg backdrop-blur-md bg-opacity-95 dark:bg-opacity-90">
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{
                backgroundColor: payload[0].fill,
                boxShadow: `0 0 10px 0 ${payload[0].fill}80`
              }}
            ></div>
            <p className="text-sm font-semibold">{data.country_name}</p>
          </div>
          <div className="text-xs space-y-2">
            <p className="flex justify-between">
              <span className="text-muted-foreground">Scientific Output:</span>
              <span className="font-bold">{data.paper_count}</span>
            </p>
            <p className="flex justify-between">
              <span className="text-muted-foreground">Academic Contributors:</span>
              <span className="font-bold">{data.author_count}</span>
            </p>
            <p className="flex justify-between">
              <span className="text-muted-foreground">Distinguished Publications:</span>
              <span className="font-bold">{data.spotlights + data.orals}</span>
            </p>
            <p className="flex justify-between border-t border-border pt-2 mt-2.5">
              <span className="text-muted-foreground">Global Impact Ranking:</span>
              <span className="font-bold text-sm">#{data.rank}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      {title && (
        <h4 className="text-lg font-semibold text-center mb-4.5 tracking-tight text-foreground">{title}</h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 30, bottom: 75 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={chartColors.withOpacity(chartColors.grid, 0.4)} />
          <XAxis
            dataKey="country_name"
            angle={-45}
            textAnchor="end"
            height={70}
            tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
            tickLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
            axisLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
          />
          <YAxis
            label={{
              value: 'Scientific Contributions',
              angle: -90,
              position: 'insideLeft',
              style: { fill: 'hsl(var(--muted-foreground))', fontSize: 11, fontWeight: 500 }
            }}
            tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
            tickLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
            axisLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: chartColors.withOpacity(chartColors.muted, 0.15) }} />
          <Legend
            wrapperStyle={{
              paddingTop: '18px',
              fontSize: '0.75rem',
              fontWeight: 500
            }}
            iconType="circle"
            iconSize={10}
          />
          <ReferenceLine y={0} stroke={chartColors.withOpacity(chartColors.grid, 0.6)} />
          <Bar
            dataKey="paper_count"
            name="Papers"
            animationDuration={1200}
            animationEasing="ease-in-out"
            barSize={28}
            radius={[8, 8, 0, 0]}
            fill={colorMap.rest} // Add this line to fix the legend color
          >
            {chartData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.fill}
                stroke="hsl(var(--background))"
                strokeWidth={1}
                style={{ filter: 'drop-shadow(0 6px 12px rgba(0, 0, 0, 0.32))' }}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};