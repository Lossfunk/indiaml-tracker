import React from 'react';
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
  highlightColor = 'hsl(var(--primary))',
  labelFormatter
}) => {
  // Don't render if no data or empty data
  if (!data || data.length === 0 || !bars || bars.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[200px] bg-muted/20 rounded-lg border border-border">
        <span className="text-muted-foreground">No data available</span>
      </div>
    );
  }

  // Generate custom tooltip content
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip bg-card p-2 border border-border rounded-md shadow-sm">
          <p className="font-medium text-xs mb-1">{labelFormatter ? labelFormatter(label) : label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={`tooltip-item-${index}`} className="text-xs" style={{ color: entry.color }}>
              {`${entry.name || entry.dataKey}: ${entry.value}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`w-full ${className}`}>
      {title && (
        <h4 className="text-sm font-medium text-center mb-3 text-foreground">{title}</h4>
      )}
      <ResponsiveContainer width={width} height={height}>
        <RechartsBarChart
          data={data}
          margin={margin}
          layout={layout}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />}
          
          {layout === 'horizontal' ? (
            <>
              <XAxis 
                dataKey={xAxisDataKey} 
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              />
            </>
          ) : (
            <>
              <XAxis 
                type="number"
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis 
                dataKey={xAxisDataKey}
                type="category" 
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                width={100}
              />
            </>
          )}
          
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          
          {showLegend && (
            <Legend 
              wrapperStyle={{
                fontSize: '0.75rem',
                paddingTop: '10px'
              }}
            />
          )}
          
          {bars.map((bar, index) => (
            <Bar
              key={`bar-${index}-${bar.dataKey}`}
              dataKey={bar.dataKey}
              fill={bar.fill}
              name={bar.name || bar.dataKey}
              stackId={bar.stackId}
            >
              {highlightIndex !== null && 
                data.map((entry, i) => (
                  <Cell 
                    key={`cell-${i}`} 
                    fill={i === highlightIndex ? highlightColor : bar.fill} 
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