import React from 'react';
import { chartColors } from '../../utils/chart-colors';
import {
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell
} from 'recharts';

interface BarChartProps {
  data: Array<any>;
  width?: string | number;
  height?: number;
  xAxisDataKey: string;
  bars: Array<{
    dataKey: string;
    fill: string;
    name?: string;
    stackId?: string | number;
  }>;
  showGrid?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
  title?: string;
  className?: string;
  margin?: { top: number; right: number; left: number; bottom: number };
  layout?: 'vertical' | 'horizontal';
  highlightIndex?: number | null;
  highlightColor?: string;
  labelFormatter?: (value: any) => string;
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  width = '100%',
  height = 300,
  xAxisDataKey,
  bars,
  showGrid = true,
  showTooltip = true,
  showLegend = true,
  title,
  className = '',
  margin = { top: 5, right: 20, left: 0, bottom: 5 },
  layout = 'horizontal',
  highlightIndex = null,
  highlightColor = chartColors.highlight,
  labelFormatter
}) => {
  // Don't render if no data or empty data
  if (!data || data.length === 0 || !bars || bars.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[200px] bg-muted/20 rounded-lg border border-border animate-pulse shadow-inner">
        <span className="text-muted-foreground">Visualization dataset unavailable</span>
      </div>
    );
  }

  // Generate custom tooltip content
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip bg-card p-4 border border-border rounded-lg shadow-lg backdrop-blur-md bg-opacity-95 dark:bg-opacity-90">
          <p className="font-medium text-sm mb-2.5 border-b border-border pb-2">{labelFormatter ? labelFormatter(label) : label}</p>
          <div className="space-y-2">
            {payload.map((entry: any, index: number) => (
              <p
                key={`tooltip-item-${index}`}
                className="text-xs flex justify-between items-center"
              >
                <span className="flex items-center">
                  <span
                    className="w-3 h-3 mr-2.5 rounded-full inline-block"
                    style={{
                      backgroundColor: entry.color,
                      boxShadow: `0 0 8px 0 ${entry.color}70`
                    }}
                  ></span>
                  <span className="text-muted-foreground">{entry.name || entry.dataKey}:</span>
                </span>
                <span className="font-semibold">{entry.value}</span>
              </p>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`w-full ${className}`}>
      {title && (
        <h4 className="text-sm font-semibold text-center mb-3.5 text-foreground tracking-tight">{title}</h4>
      )}
      <ResponsiveContainer width={width} height={height}>
        <RechartsBarChart
          data={data}
          margin={margin}
          layout={layout}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={chartColors.withOpacity(chartColors.grid, 0.4)} />}
          
          {layout === 'horizontal' ? (
            <>
              <XAxis
                dataKey={xAxisDataKey}
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                tickLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
                axisLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                tickLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
                axisLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
              />
            </>
          ) : (
            <>
              <XAxis
                type="number"
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                tickLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
                axisLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
              />
              <YAxis
                dataKey={xAxisDataKey}
                type="category"
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                tickLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
                axisLine={{ stroke: chartColors.withOpacity(chartColors.grid, 0.6) }}
                width={100}
              />
            </>
          )}
          
          {showTooltip && <Tooltip content={<CustomTooltip />} cursor={{ fill: chartColors.withOpacity(chartColors.muted, 0.15) }} />}
          
          {showLegend && (
            <Legend
              wrapperStyle={{
                fontSize: '0.75rem',
                paddingTop: '12px',
                paddingBottom: '8px'
              }}
              iconSize={10}
              iconType="circle"
            />
          )}
          
          {bars.map((bar, index) => (
            <Bar
              key={`bar-${index}-${bar.dataKey}`}
              dataKey={bar.dataKey}
              fill={bar.fill}
              name={bar.name || bar.dataKey}
              stackId={bar.stackId}
              animationDuration={1200}
              animationEasing="ease-in-out"
              barSize={28}
              radius={[8, 8, 0, 0]}
              stroke="hsl(var(--background))"
              strokeWidth={1}
              style={{ filter: 'drop-shadow(0 5px 10px rgba(0, 0, 0, 0.25))' }}
            >
              {highlightIndex !== null &&
                data.map((entry, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={i === highlightIndex ? highlightColor : bar.fill}
                    style={{
                      filter: i === highlightIndex
                        ? 'drop-shadow(0 8px 16px rgba(0, 0, 0, 0.4))'
                        : 'drop-shadow(0 5px 8px rgba(0, 0, 0, 0.22))',
                      opacity: i === highlightIndex ? 1 : 0.9
                    }}
                  />
                ))
              }
            </Bar>
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
};